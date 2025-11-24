# lb_sticky.py
import uuid
from itertools import cycle
from typing import Dict

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# 3 backend instances (our "pool")
BACKENDS = [
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003",
]

backend_cycle = cycle(BACKENDS)

# session_id -> backend_url
session_backend_map: Dict[str, str] = {}


def choose_backend(session_id: str) -> str:
    """Return backend URL for this session, keeping it sticky."""
    if session_id in session_backend_map:
        return session_backend_map[session_id]

    backend = next(backend_cycle)
    session_backend_map[session_id] = backend
    return backend


@app.get("/hello")
async def lb_hello(request: Request):
    # 1. Get (or create) session_id
    session_id = request.cookies.get("session_id")
    new_session = False

    if not session_id:
        session_id = str(uuid.uuid4())
        new_session = True

    # 2. Resolve which backend this session should go to
    backend = choose_backend(session_id)
    target_url = f"{backend}/hello"

    # 3. Forward the request to the backend
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(target_url)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {e}")

    backend_json = resp.json()

    # 4. Build response back to client and ensure cookie is set
    response = JSONResponse(
        {
            "load_balancer": "lb-sticky",
            "backend_chosen": backend,
            "session_id": session_id,
            "backend_response": backend_json,
        }
    )

    if new_session:
        # HttpOnly cookie so JS can't read it (more realistic)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,   # True in production with HTTPS
            samesite="lax",
        )

    return response
