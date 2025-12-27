# Byzantine Consensus Demo

A demonstration of Byzantine fault detection in a distributed consensus system using FastAPI servers. This demo shows how honest nodes can detect when a Byzantine (malicious) node sends conflicting messages to different peers.

## What is Byzantine Fault Tolerance?

Byzantine fault tolerance is the ability of a distributed system to continue operating correctly even when some nodes fail or behave arbitrarily (not just crash, but also send incorrect or conflicting messages). This demo focuses on **detecting** Byzantine faults rather than tolerating them.

## How it Works

- **4 nodes** participate in a consensus protocol (node1, node2, node3, node4)
- **Node 4 is Byzantine** - it sends different values to different peers
- **Honest nodes** (node1, node2, node3) exchange messages and detect inconsistencies
- When a node receives **conflicting values** from the same sender in the same round, it **detects a Byzantine fault** and **alerts**

### Byzantine Behavior

The Byzantine node (node4) demonstrates a "split-brain" attack:

- Sends value `X` to half the peers
- Sends value `X_BYZANTINE` to the other half
- This creates inconsistency that honest nodes can detect

## Running the Demo

### Option 1: Start all nodes together (Recommended)

```bash
python start_byzantine_cluster.py
```

This will start all 4 nodes. Node 4 will be configured as Byzantine.

### Option 2: Start nodes individually

Terminal 1 (Honest node):

```bash
python byzantine_node.py node1 8001
```

Terminal 2 (Honest node):

```bash
python byzantine_node.py node2 8002
```

Terminal 3 (Honest node):

```bash
python byzantine_node.py node3 8003
```

Terminal 4 (Byzantine node):

```bash
python byzantine_node.py node4 8004 --byzantine
```

## Testing Byzantine Fault Detection

1. **Start the cluster:**

   ```bash
   python start_byzantine_cluster.py
   ```

2. **Wait a few seconds** for all nodes to start up

3. **Trigger a proposal** (in a new terminal):

   **Bash/Linux/Mac:**

   ```bash
   curl -X POST "http://127.0.0.1:8001/propose?value=test123"
   ```

   **PowerShell (Windows):**

   ```powershell
   Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/propose?value=test123"
   ```

   Or use `curl.exe` explicitly:

   ```powershell
   curl.exe -X POST "http://127.0.0.1:8001/propose?value=test123"
   ```

4. **Watch the console output** - you should see:

   ```
   [node4] ⚠️ BYZANTINE: Sent conflicting values to different peers!
   [node1] 🚨 BYZANTINE FAULT DETECTED!
       Node: node4
       Round: 1
       Conflicting values: {'test123', 'test123_BYZANTINE'}
   ```

5. **Check detections** on any honest node:

   **Bash/Linux/Mac:**

   ```bash
   curl http://127.0.0.1:8001/detections
   ```

   **PowerShell (Windows):**

   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8001/detections"
   ```

6. **Check node status:**

   **Bash/Linux/Mac:**

   ```bash
   curl http://127.0.0.1:8001/status
   ```

   **PowerShell (Windows):**

   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8001/status"
   ```

## API Endpoints

### `POST /propose?value=<value>`

Propose a value for consensus. The Byzantine node will send conflicting values to different peers.

**Example:**

**Bash/Linux/Mac:**

```bash
curl -X POST "http://127.0.0.1:8001/propose?value=transaction123"
```

**PowerShell (Windows):**

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/propose?value=transaction123"
```

### `POST /receive_message`

Internal endpoint used by nodes to exchange consensus messages.

### `GET /status`

Get the current status of the node, including:

- Node ID and whether it's Byzantine
- Current consensus round
- Consensus value (if reached)
- List of peers

**Example:**

**Bash/Linux/Mac:**

```bash
curl http://127.0.0.1:8001/status
```

**PowerShell (Windows):**

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/status"
```

### `GET /detections`

Get all Byzantine fault detections made by this node.

**Example:**

**Bash/Linux/Mac:**

```bash
curl http://127.0.0.1:8001/detections
```

**PowerShell (Windows):**

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/detections"
```

**Response format:**

```json
{
  "node_id": "node1",
  "detections": [
    {
      "detected_at": "2025-12-27T12:00:00",
      "byzantine_node": "node4",
      "round": 1,
      "conflicting_values": ["test123", "test123_BYZANTINE"],
      "detected_by": "node1"
    }
  ],
  "total_detections": 1
}
```

## How Detection Works

1. **Message Exchange**: When a value is proposed, nodes exchange messages about the proposal
2. **Message Forwarding (Gossip)**: When a node receives a PROPOSE message, it forwards it to all other peers (except the original sender). This ensures all nodes eventually see all messages, even if they weren't the direct recipient
3. **Message Tracking**: Each node tracks all messages received in each consensus round, including both direct messages and forwarded messages
4. **Inconsistency Detection**: If a node receives **different values** from the **same sender** in the **same round** (either directly or via forwarding), it detects Byzantine behavior
5. **Alerting**: When detected, the node logs an alert with details about the Byzantine node and conflicting values

**Example**: If node4 sends "test123" to node1 and "test123_BYZANTINE" to node2, node2 will forward its message to node1. Node1 will then have both conflicting values from node4 and can detect the Byzantine fault.

## Reliability Perspective

This demo demonstrates:

- **Fault Detection**: The ability to identify when nodes are behaving maliciously
- **Message Integrity**: Tracking message sources and detecting inconsistencies
- **Distributed Monitoring**: Multiple nodes independently detecting faults
- **Alerting**: Immediate notification when Byzantine behavior is detected

## Configuration

The demo uses these default settings:

- **4 nodes** (3 honest + 1 Byzantine)
- **Ports**: 8001, 8002, 8003, 8004
- **Message timeout**: 2 seconds

You can modify `NODES` dictionary in `byzantine_node.py` to add more nodes or change ports.

## Notes

- This is a **simplified demo** for educational purposes
- Real Byzantine fault tolerance requires more sophisticated protocols (e.g., PBFT, Raft with Byzantine support)
- The detection mechanism here is basic - real systems need cryptographic signatures and more robust consensus algorithms
- For production systems, you'd need at least **3f+1 nodes** to tolerate **f Byzantine nodes**
