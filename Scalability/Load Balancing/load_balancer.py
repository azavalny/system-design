from itertools import cycle
import httpx
import asyncio
import random
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

BACKENDS = [
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003",
]

backend_pool = cycle(BACKENDS)

# Track active connections per backend for least-connections algorithm
connection_counts = {backend: 0 for backend in BACKENDS}
connection_lock = asyncio.Lock()

def get_least_connections_backend():
    """Select the backend with the least active connections"""
    return min(connection_counts.items(), key=lambda x: x[1])[0]

# round robin
@app.get("/work") 
async def proxy_work(request: Request):
    backend = next(backend_pool)
    target_url = f"{backend}/work"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(target_url, params=dict(request.query_params))

    return JSONResponse({
        "load_balancer": "lb-1",
        "forwarded_to": backend,
        "backend_response": resp.json()
    })

# least connections
@app.get("/work2")
async def proxy_work2(request: Request):
    # Randomly distribute 1-3 connections across random backends
    # This creates a realistic scenario where different backends have different loads
    num_backends_to_use = random.randint(1, 2)  # Use 1 or 2 backends
    busy_backends = random.sample(BACKENDS, num_backends_to_use)
    
    async def send_work_request(backend_url):
        """Send a /work request to a backend and track the connection"""
        async with connection_lock:
            connection_counts[backend_url] += 1
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.get(f"{backend_url}/work", params=dict(request.query_params))
        finally:
            async with connection_lock:
                connection_counts[backend_url] -= 1
    
    # For each selected backend, send 1-3 requests
    background_tasks = []
    for backend in busy_backends:
        num_connections = random.randint(2, 5)
        for _ in range(num_connections):
            background_tasks.append(asyncio.create_task(send_work_request(backend)))
    
    # Give a small delay to ensure connection counts are updated
    await asyncio.sleep(0.01)
    
    # Capture connection counts BEFORE incrementing for this request
    # This shows the state that was used for selection
    async with connection_lock:
        counts_at_selection = dict(connection_counts)
        backend = get_least_connections_backend()
        connection_counts[backend] += 1
    
    target_url = f"{backend}/work2"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(target_url, params=dict(request.query_params))
        
        # Return response with counts at selection time (before increment)
        return JSONResponse({
            "load_balancer": "lb-2",
            "forwarded_to": backend,
            "backend_response": resp.json(),
            "connection_counts_at_selection": counts_at_selection
        })
    finally:
        # Decrement connection count when request completes
        async with connection_lock:
            connection_counts[backend] -= 1
        # Wait for background tasks to complete
        await asyncio.gather(*background_tasks, return_exceptions=True)