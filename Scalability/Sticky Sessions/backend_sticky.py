# backend_sticky.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

INSTANCE_NAME = os.getenv("INSTANCE_NAME", "instance-unknown")
request_counter = 0


@app.get("/hello")
async def hello(request: Request):
    global request_counter
    request_counter += 1

    session_id = request.cookies.get("session_id", "no-session")

    return JSONResponse(
        {
            "instance": INSTANCE_NAME,
            "requests_seen_by_this_instance": request_counter,
            "session_id_seen_by_backend": session_id,
        }
    )
