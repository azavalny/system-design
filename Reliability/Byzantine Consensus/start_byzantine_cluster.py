import subprocess
import sys
import time
import signal
import os

processes = []
node_processes = {}

def cleanup():
    """Stop all cluster nodes"""
    print("\n[cleanup] Stopping all Byzantine consensus nodes...")
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
    print("Starting 4-node Byzantine consensus cluster...")
    print("Node 4 will be Byzantine (sends conflicting messages)")
    print("Press Ctrl+C to stop all nodes\n")
    
    nodes = [
        ("node1", 8001, False),
        ("node2", 8002, False),
        ("node3", 8003, False),
        ("node4", 8004, True),
    ]
    
    for node_id, port, is_byzantine in nodes:
        cmd = [sys.executable, "byzantine_node.py", node_id, str(port)]
        if is_byzantine:
            cmd.append("--byzantine")
        
        proc = subprocess.Popen(cmd)
        processes.append(proc)
        node_processes[node_id] = proc
        status = "⚠️ BYZANTINE" if is_byzantine else "✓ Honest"
        print(f"Started {node_id} on port {port} (PID: {proc.pid}) [{status}]")
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print("Byzantine Consensus Cluster is running!")
    print("="*60)
    print("\nNode PIDs (for killing individual nodes):")
    for node_id, proc in node_processes.items():
        is_byzantine = node_id == "node4"
        status = "⚠️ BYZANTINE" if is_byzantine else "✓ Honest"
        print(f"  {node_id}: PID {proc.pid} [{status}]")
    
    print("\n" + "="*60)
    print("Testing Byzantine Fault Detection:")
    print("="*60)
    print("\n1. Wait a few seconds for all nodes to start")
    print("2. In a NEW terminal, trigger a proposal:")
    print("   Bash/Linux/Mac: curl -X POST http://127.0.0.1:8001/propose?value=test123")
    print("   PowerShell: Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/propose?value=test123")
    print("\n3. Watch the console - Byzantine fault should be detected!")
    print("   Node 4 will send conflicting values to different peers")
    print("\n4. Check detections on any honest node:")
    print("   Bash/Linux/Mac: curl http://127.0.0.1:8001/detections")
    print("   PowerShell: Invoke-RestMethod -Uri http://127.0.0.1:8001/detections")
    print("\n5. Check status:")
    print("   Bash/Linux/Mac: curl http://127.0.0.1:8001/status")
    print("   PowerShell: Invoke-RestMethod -Uri http://127.0.0.1:8001/status")
    print("\nPress Ctrl+C in this window to stop all nodes\n")
    
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        cleanup()

