# Terminal 1: Service Discovery
uvicorn service_discovery:app --port 8000

# Terminal 2: Backend 1
BACKEND_PORT=8001 BACKEND_NAME=backend-1 uvicorn backend:app --port 8001

# Terminal 3: Backend 2
BACKEND_PORT=8002 BACKEND_NAME=backend-2 uvicorn backend:app --port 8002

# Terminal 4: Backend 3
BACKEND_PORT=8003 BACKEND_NAME=backend-3 uvicorn backend:app --port 8003