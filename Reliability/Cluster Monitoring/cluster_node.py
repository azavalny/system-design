import sys
import asyncio
from typing import Dict
from datetime import datetime

from fastapi import FastAPI
from contextlib import asynccontextmanager
import httpx
import uvicorn

# Configuration
HEARTBEAT_INTERVAL = 2.0
HEARTBEAT_TIMEOUT = 5.0

# Cluster configuration: all nodes know about each other
CLUSTER_NODES = {
    "node1": "http://127.0.0.1:8001",
    "node2": "http://127.0.0.1:8002",
    "node3": "http://127.0.0.1:8003",
}

# State tracking
node_id = None
peer_status: Dict[str, Dict] = {}

async def monitor_peers():
    """Background task that periodically checks peer heartbeats"""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        
        for peer_id, peer_url in CLUSTER_NODES.items():
            if peer_id == node_id:
                continue
            
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"{peer_url}/heartbeat")
                    if resp.status_code == 200:
                        peer_status[peer_id] = {
                            "status": "up",
                            "last_heartbeat": datetime.now().isoformat(),
                            "last_check": datetime.now().isoformat()
                        }
                    else:
                        peer_status[peer_id] = {
                            "status": "down",
                            "last_check": datetime.now().isoformat()
                        }
                        print(f"[{node_id}] ✗ {peer_id} returned status {resp.status_code}")
            except Exception as e:
                current_status = peer_status.get(peer_id, {}).get("status", "unknown")
                peer_status[peer_id] = {
                    "status": "down",
                    "last_check": datetime.now().isoformat(),
                    "error": str(e)
                }
                if current_status != "down":
                    print(f"[{node_id}] ✗ {peer_id} is DOWN - {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(monitor_peers())
    yield

app = FastAPI(title="Cluster Node", lifespan=lifespan)

@app.get("/heartbeat")
async def heartbeat():
    """Endpoint for other nodes to check if this node is alive"""
    return {
        "node_id": node_id,
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def get_status():
    """Get the status of all nodes in the cluster"""
    status = {
        "self": node_id,
        "peers": {}
    }
    for peer_id, peer_url in CLUSTER_NODES.items():
        if peer_id == node_id:
            continue
        peer_info = peer_status.get(peer_id, {})
        status["peers"][peer_id] = {
            "url": peer_url,
            "status": peer_info.get("status", "unknown"),
            "last_heartbeat": peer_info.get("last_heartbeat"),
            "last_check": peer_info.get("last_check")
        }
    return status

def run_node(node_id_arg: str, port: int):
    global node_id
    node_id = node_id_arg
    
    print(f"[{node_id}] Starting cluster node on port {port}")
    print(f"[{node_id}] Monitoring peers: {[pid for pid in CLUSTER_NODES.keys() if pid != node_id]}")
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python cluster_node.py <node_id> <port>")
        print("Example: python cluster_node.py node1 8001")
        sys.exit(1)
    
    node_id_arg = sys.argv[1]
    port = int(sys.argv[2])
    run_node(node_id_arg, port)
