import sys
import time
import asyncio
import subprocess
import threading
from typing import List, Dict

from fastapi import FastAPI
import httpx
import uvicorn

# -----------------------------
# Global state (in gateway process)
# -----------------------------
SERVERS: List[Dict] = []        # [{ "port": int, "process": Popen }]
SERVERS_LOCK = threading.Lock()

REQUESTS_IN_INTERVAL = 0
METRICS_LOCK = threading.Lock()
RPS = 0.0

NEXT_SERVER_INDEX = 0
NEXT_SERVER_LOCK = threading.Lock()

# Autoscaling settings (tweak these)
CHECK_INTERVAL = 5.0        # seconds between autoscaler checks
SCALE_UP_RPS = 5.0          # if RPS > this, try to scale up
SCALE_DOWN_RPS = 1.0        # if RPS < this, try to scale down
MIN_SERVERS = 1
MAX_SERVERS = 5

# -----------------------------
# Backend FastAPI app
# -----------------------------
backend_app = FastAPI(title="Backend worker")

@backend_app.get("/work")
async def do_work(delay_ms: int = 200):
    """
    Simulate some work. You can change delay_ms to make workers slower/faster.
    """
    await asyncio.sleep(delay_ms / 1000.0)
    return {"status": "ok", "delay_ms": delay_ms}


# -----------------------------
# Gateway FastAPI app
# -----------------------------
gateway_app = FastAPI(title="Gateway with autoscaler demo")

@gateway_app.get("/work")
async def gateway_work(delay_ms: int = 200):
    """
    Public endpoint clients call.
    Load-balances across backend instances in SERVERS (round-robin).
    """
    global REQUESTS_IN_INTERVAL

    # count the request for RPS calculation
    with METRICS_LOCK:
        REQUESTS_IN_INTERVAL += 1

    # pick a backend server
    with SERVERS_LOCK:
        if not SERVERS:
            # Shouldn't happen if autoscaler always keeps >= 1
            raise RuntimeError("No backend servers are running!")
        servers_snapshot = list(SERVERS)

    # simple round-robin selection
    global NEXT_SERVER_INDEX
    with NEXT_SERVER_LOCK:
        server = servers_snapshot[NEXT_SERVER_INDEX % len(servers_snapshot)]
        NEXT_SERVER_INDEX += 1

    backend_url = f"http://127.0.0.1:{server['port']}/work"

    async with httpx.AsyncClient() as client:
        resp = await client.get(backend_url, params={"delay_ms": delay_ms})
        return {
            "gateway": "ok",
            "backend_port": server["port"],
            "backend_response": resp.json(),
        }


@gateway_app.get("/metrics")
async def metrics():
    """
    Expose simple metrics so you can see what the autoscaler is doing.
    """
    with METRICS_LOCK:
        rps_snapshot = RPS
    with SERVERS_LOCK:
        ports = [s["port"] for s in SERVERS]

    return {
        "requests per second": rps_snapshot,
        "num_servers": len(ports),
        "server_ports": ports,
    }


# -----------------------------
# Process management helpers
# -----------------------------
def start_backend(port: int):
    """
    Spawn a new backend FastAPI worker (uvicorn) as a subprocess
    running this same file in 'worker' mode.
    """
    proc = subprocess.Popen(
        [sys.executable, __file__, "worker", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    with SERVERS_LOCK:
        SERVERS.append({"port": port, "process": proc})
    print(f"[autoscaler] Started backend on port {port}")


def stop_backend():
    """
    Stop one backend instance (last in the list).
    """
    with SERVERS_LOCK:
        if len(SERVERS) <= MIN_SERVERS:
            return
        server = SERVERS.pop()
    proc = server["process"]
    port = server["port"]
    proc.terminate()
    print(f"[autoscaler] Stopped backend on port {port}")


def get_next_port() -> int:
    with SERVERS_LOCK:
        if not SERVERS:
            return 8001
        max_port = max(s["port"] for s in SERVERS)
        return max_port + 1


# -----------------------------
# Autoscaler loop (runs in thread)
# -----------------------------
def autoscaler_loop():
    global REQUESTS_IN_INTERVAL, RPS

    while True:
        time.sleep(CHECK_INTERVAL)

        # compute RPS
        with METRICS_LOCK:
            current_requests = REQUESTS_IN_INTERVAL
            REQUESTS_IN_INTERVAL = 0
        rps = current_requests / CHECK_INTERVAL
        with METRICS_LOCK:
            RPS = rps

        with SERVERS_LOCK:
            num_servers = len(SERVERS)

        print(
            f"[autoscaler] rps={rps:.2f}, servers={num_servers}"
        )

        # scale up
        if rps > SCALE_UP_RPS and num_servers < MAX_SERVERS:
            port = get_next_port()
            start_backend(port)

        # scale down
        elif rps < SCALE_DOWN_RPS and num_servers > MIN_SERVERS:
            stop_backend()


# -----------------------------
# Entrypoints
# -----------------------------
def run_gateway():
    # start initial backend(s)
    for i in range(MIN_SERVERS):
        start_backend(8001 + i)

    # start autoscaler thread
    t = threading.Thread(target=autoscaler_loop, daemon=True)
    t.start()

    print("[main] Starting gateway on http://127.0.0.1:8000")
    uvicorn.run(gateway_app, host="127.0.0.1", port=8000, log_level="info")


def run_worker(port: int):
    print(f"[worker] Starting backend worker on port {port}")
    uvicorn.run(backend_app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "worker":
        # worker mode: run backend only
        port = int(sys.argv[2])
        run_worker(port)
    else:
        # main mode: run gateway + autoscaler + initial backend(s)
        run_gateway()
