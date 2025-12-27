# Cluster Monitoring Demo

A simple demonstration of cluster monitoring where 3 FastAPI servers monitor each other's heartbeats.

`taskkill /F /PID <pid>`
`python cluster_node.py node1 8001`

## How it works

- Each node runs a FastAPI server on a different port (8001, 8002, 8003)
- Each node periodically sends heartbeat requests to the other 2 nodes
- If a node doesn't respond within the timeout period, it's marked as "down"
- Each node exposes a `/status` endpoint to view the health of all peers

## Running the cluster

### Option 1: Start all nodes together

```bash
python start_cluster.py
```

This will start all 3 nodes. Press Ctrl+C to stop them all.

### Option 2: Start nodes individually (for testing failures)

Terminal 1:

```bash
python cluster_node.py node1 8001
```

Terminal 2:

```bash
python cluster_node.py node2 8002
```

Terminal 3:

```bash
python cluster_node.py node3 8003
```

## Testing failure detection

### Method 1: Using start_cluster.py (all nodes in one terminal)

1. Start the cluster:

   ```bash
   python start_cluster.py
   ```

   Note the PIDs shown for each node.

2. Open a **NEW terminal window** (keep the cluster running in the first terminal)

3. Kill a node using one of these methods:

   **Option A: Using the helper script (easiest)**

   ```bash
   python kill_node.py node1
   ```

   **Option B: Using taskkill with PID (Windows)**

   ```bash
   taskkill /F /PID <pid>
   ```

   Replace `<pid>` with the PID shown when you started the cluster.

4. Check the status:
   ```bash
   curl http://127.0.0.1:8001/status
   ```
   The killed node should show as "down" within a few seconds.

### Method 2: Running nodes individually

1. Start each node in a separate terminal:

   ```bash
   # Terminal 1
   python cluster_node.py node1 8001

   # Terminal 2
   python cluster_node.py node2 8002

   # Terminal 3
   python cluster_node.py node3 8003
   ```

2. To kill a node, simply close its terminal or press Ctrl+C in that terminal

3. Check status from any other terminal - the killed node will be detected as down

## Endpoints

- `GET /heartbeat` - Returns the node's heartbeat (used by other nodes)
- `GET /status` - Returns the status of all nodes in the cluster

## Configuration

You can adjust these constants in `cluster_node.py`:

- `HEARTBEAT_INTERVAL` - How often to check peers (default: 2 seconds)
- `HEARTBEAT_TIMEOUT` - How long to wait before marking a peer as down (default: 5 seconds)
