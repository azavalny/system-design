import subprocess
import sys
import time
import signal
import os

processes = []
node_processes = {}  # node_id -> process mapping

def cleanup():
    """Stop all cluster nodes"""
    print("\n[cleanup] Stopping all cluster nodes...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            try:
                proc.kill()
            except:
                pass
    print("[cleanup] All nodes stopped")

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

try:
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
except (ValueError, OSError):
    pass

if __name__ == "__main__":
    print("Starting 3-node cluster...")
    print("Press Ctrl+C to stop all nodes\n")
    
    # Start 3 nodes
    nodes = [
        ("node1", 8001),
        ("node2", 8002),
        ("node3", 8003),
    ]
    
    for node_id, port in nodes:
        proc = subprocess.Popen(
            [sys.executable, "cluster_node.py", node_id, str(port)]
        )
        processes.append(proc)
        node_processes[node_id] = proc
        print(f"Started {node_id} on port {port} (PID: {proc.pid})")
        time.sleep(0.5)
    
    print("\n" + "="*50)
    print("Cluster is running!")
    print("="*50)
    print("\nNode PIDs (for killing individual nodes):")
    for node_id, proc in node_processes.items():
        print(f"  {node_id}: PID {proc.pid}")
    print("\nTo test failure detection:")
    print("1. Open a NEW terminal window")
    print("2. Kill a node using one of these methods:")
    print(f"   Windows: taskkill /F /PID {node_processes['node1'].pid}")
    print("3. Check status: curl http://127.0.0.1:8001/status")
    print("4. The killed node should show as 'down' within a few seconds")
    print("\nPress Ctrl+C in this window to stop all nodes\n")
    
    # Wait for all processes
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        cleanup()

