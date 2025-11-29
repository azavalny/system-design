import json
import asyncio
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Registry file path - use absolute path to avoid issues with working directory
REGISTRY_FILE = Path(__file__).parent / "backend_registry.json"

# Lock for thread-safe file operations
registry_lock = asyncio.Lock()


class BackendRegistration(BaseModel):
    """Model for backend registration"""
    url: str
    name: Optional[str] = None
    port: Optional[int] = None


def load_registry() -> dict:
    """Load the registry from JSON file"""
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"backends": []}
    return {"backends": []}


def save_registry(registry: dict):
    """Save the registry to JSON file"""
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)


@app.post("/register")
async def register_backend(backend: BackendRegistration):
    """Register a new backend instance"""
    async with registry_lock:
        registry = load_registry()
        
        # Log current state for debugging
        existing_urls = [b["url"] for b in registry["backends"]]
        existing_names = [b.get("name", "unknown") for b in registry["backends"]]
        print(f"📝 Registration request: {backend.name} at {backend.url}")
        print(f"   Current registry has {len(registry['backends'])} backends:")
        for b in registry["backends"]:
            print(f"      - {b.get('name', 'unknown')} at {b['url']}")
        
        # Check if backend URL already exists
        if backend.url in existing_urls:
            # URL already exists, ignore the registration
            existing_backend = next((b for b in registry["backends"] if b["url"] == backend.url), None)
            existing_name = existing_backend.get("name", "unknown") if existing_backend else "unknown"
            print(f"   ⏭ Ignored registration: {backend.url} already exists (registered as '{existing_name}')")
            print(f"   ⚠️  WARNING: Multiple backends trying to register with the same URL!")
            print(f"   💡 Make sure each backend sets BACKEND_PORT to a unique port number")
        else:
            # URL doesn't exist, append new backend
            registry["backends"].append({
                "url": backend.url,
                "name": backend.name or "backend-unknown",
                "port": backend.port,
                "registered_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            })
            print(f"   ✓ Added new backend: {backend.url} (name: {backend.name})")
        
        save_registry(registry)
        print(f"   💾 Saved registry with {len(registry['backends'])} backends")
    
    return JSONResponse({
        "status": "registered",
        "backend": backend.url,
        "name": backend.name,
        "total_backends": len(registry["backends"]),
        "all_backends": [b["url"] for b in registry["backends"]]
    })


@app.get("/backends")
async def list_backends():
    """List all registered backend instances"""
    async with registry_lock:
        registry = load_registry()
    
    return JSONResponse({
        "total": len(registry["backends"]),
        "backends": registry["backends"]
    })


@app.delete("/unregister")
async def unregister_backend(url: str):
    """Unregister a backend instance"""
    async with registry_lock:
        registry = load_registry()
        
        initial_count = len(registry["backends"])
        registry["backends"] = [
            b for b in registry["backends"] 
            if b["url"] != url
        ]
        
        if len(registry["backends"]) == initial_count:
            raise HTTPException(status_code=404, detail=f"Backend {url} not found in registry")
        
        save_registry(registry)
    
    return JSONResponse({
        "status": "unregistered",
        "backend": url,
        "remaining_backends": len(registry["backends"])
    })


@app.post("/heartbeat")
async def heartbeat(backend: BackendRegistration):
    """Update last_seen timestamp for a backend (heartbeat mechanism)"""
    async with registry_lock:
        registry = load_registry()
        
        backend_found = False
        for b in registry["backends"]:
            if b["url"] == backend.url:
                b["last_seen"] = datetime.now().isoformat()
                backend_found = True
                break
        
        if not backend_found:
            # If not found, register it
            registry["backends"].append({
                "url": backend.url,
                "name": backend.name or "backend-unknown",
                "port": backend.port,
                "registered_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            })
        
        save_registry(registry)
    
    return JSONResponse({
        "status": "heartbeat_received",
        "backend": backend.url
    })


@app.get("/health")
async def health_check():
    """Health check endpoint for the service discovery service"""
    return JSONResponse({
        "status": "healthy",
        "service": "service_discovery",
        "registry_file": str(REGISTRY_FILE)
    })

