# backend.py
import asyncio
import random
import os
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Configuration from environment variables
BACKEND_NAME = os.getenv("BACKEND_NAME", "backend-unknown")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
SERVICE_DISCOVERY_URL = os.getenv("SERVICE_DISCOVERY_URL", "http://127.0.0.1:8000")

# Construct backend URL
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# Warn if using default port (likely means BACKEND_PORT wasn't set)
if BACKEND_PORT == 8000 and "BACKEND_PORT" not in os.environ:
    print("⚠️  WARNING: BACKEND_PORT not set! Using default port 8000.")
    print("   This will cause registration conflicts if multiple backends use the same port.")
    print(f"   Set BACKEND_PORT environment variable when starting: BACKEND_PORT=<port> uvicorn backend:app --port <port>")

# Global flag to control background tasks
registration_task = None
heartbeat_task = None
shutdown_event = asyncio.Event()


async def register_with_service_discovery(retry_count=0, max_retries=5):
    """Register this backend instance with the service discovery service"""
    registration_data = {
        "url": BACKEND_URL,
        "name": BACKEND_NAME,
        "port": BACKEND_PORT
    }
    
    print(f"🔄 Attempting to register {BACKEND_NAME} at {BACKEND_URL} (port: {BACKEND_PORT})")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{SERVICE_DISCOVERY_URL}/register",
                json=registration_data
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Successfully registered {BACKEND_NAME} at {BACKEND_URL}")
                print(f"   Total backends in registry: {result.get('total_backends', 'unknown')}")
                print(f"   All registered backends: {result.get('all_backends', [])}")
                return True
            else:
                print(f"⚠ Failed to register: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        if retry_count < max_retries:
            # Exponential backoff: wait 2^retry_count seconds
            wait_time = min(2 ** retry_count, 30)  # Cap at 30 seconds
            print(f"⚠ Could not register with service discovery (attempt {retry_count + 1}/{max_retries}): {e}")
            print(f"  Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return await register_with_service_discovery(retry_count + 1, max_retries)
        else:
            print(f"⚠ Could not register with service discovery after {max_retries} attempts: {e}")
            print(f"  Service discovery URL: {SERVICE_DISCOVERY_URL}")
            print(f"  Backend will continue running and retry periodically...")
            return False


async def send_heartbeat():
    """Send heartbeat to service discovery to keep registration alive"""
    registration_data = {
        "url": BACKEND_URL,
        "name": BACKEND_NAME,
        "port": BACKEND_PORT
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{SERVICE_DISCOVERY_URL}/heartbeat",
                json=registration_data
            )
            if response.status_code != 200:
                # If heartbeat fails, try to re-register
                await register_with_service_discovery()
    except Exception as e:
        # If heartbeat fails, try to re-register
        await register_with_service_discovery()


async def registration_retry_loop():
    """Background task to periodically retry registration if it failed"""
    while not shutdown_event.is_set():
        # Try to register every 30 seconds if not already registered
        await asyncio.sleep(30)
        if not shutdown_event.is_set():
            await register_with_service_discovery(max_retries=1)


async def heartbeat_loop():
    """Background task to send periodic heartbeats"""
    # Wait a bit before starting heartbeats to allow initial registration
    await asyncio.sleep(10)
    
    while not shutdown_event.is_set():
        await send_heartbeat()
        # Send heartbeat every 30 seconds
        await asyncio.sleep(30)


async def unregister_from_service_discovery():
    """Unregister this backend instance from the service discovery service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.delete(
                f"{SERVICE_DISCOVERY_URL}/unregister",
                params={"url": BACKEND_URL}
            )
            if response.status_code == 200:
                print(f"✓ Successfully unregistered {BACKEND_NAME} from service discovery")
            else:
                print(f"⚠ Failed to unregister: {response.status_code}")
    except Exception as e:
        print(f"⚠ Could not unregister from service discovery: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global registration_task, heartbeat_task
    
    # Startup: Try to register (non-blocking, will retry in background if it fails)
    asyncio.create_task(register_with_service_discovery())
    
    # Start background tasks for retry and heartbeat
    registration_task = asyncio.create_task(registration_retry_loop())
    heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    yield
    
    # Shutdown: Stop background tasks and unregister
    shutdown_event.set()
    if registration_task:
        registration_task.cancel()
    if heartbeat_task:
        heartbeat_task.cancel()
    
    # Wait a moment for tasks to cancel
    await asyncio.sleep(0.5)
    
    # Unregister from service discovery
    await unregister_from_service_discovery()


app = FastAPI(lifespan=lifespan)


@app.get("/work")
async def do_work():
    # simulate variable processing time
    processing_time = round(random.uniform(0.1, 0.7), 3)
    await asyncio.sleep(processing_time)

    return {
        "backend": BACKEND_NAME, #backend n
        "processing_time_seconds": processing_time,
    }

@app.get("/work2")
async def do_work2():
    # simulate variable processing time
    processing_time = round(random.uniform(0.1, 0.7), 3)
    await asyncio.sleep(processing_time)

    return {
        "backend": BACKEND_NAME,
        "processing_time_seconds": processing_time,
    }


@app.get("/info")
async def get_backend_info():
    """Get information about this backend instance"""
    return {
        "name": BACKEND_NAME,
        "url": BACKEND_URL,
        "host": BACKEND_HOST,
        "port": BACKEND_PORT,
        "service_discovery_url": SERVICE_DISCOVERY_URL,
        "backends_in_registry": "Check service discovery /backends endpoint"
    }