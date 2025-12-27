import sys
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
import uvicorn

class MessageType(str, Enum):
    PROPOSE = "propose"
    VOTE = "vote"
    COMMIT = "commit"

class ConsensusMessage(BaseModel):
    message_type: MessageType
    node_id: str
    value: str
    round: int
    timestamp: str

class ByzantineNode:
    def __init__(self, node_id: str, port: int, is_byzantine: bool = False):
        self.node_id = node_id
        self.port = port
        self.is_byzantine = is_byzantine
        
        self.peers: Dict[str, str] = {}
        self.received_messages: Dict[int, List[ConsensusMessage]] = {}
        self.votes: Dict[int, Dict[str, str]] = {}
        self.byzantine_detections: List[Dict] = []
        self.current_round = 0
        self.consensus_value: Optional[str] = None
        self.forwarded_messages: Set[str] = set()
        
    def add_peer(self, peer_id: str, peer_url: str):
        self.peers[peer_id] = peer_url
    
    async def propose_value(self, value: str):
        """Propose a value for consensus"""
        self.current_round += 1
        round_num = self.current_round
        
        message = ConsensusMessage(
            message_type=MessageType.PROPOSE,
            node_id=self.node_id,
            value=value,
            round=round_num,
            timestamp=datetime.now().isoformat()
        )
        
        if self.is_byzantine:
            await self._byzantine_propose(round_num, value)
        else:
            await self._broadcast_message(message)
    
    async def _byzantine_propose(self, round_num: int, value: str):
        """Byzantine node sends different values to different peers"""
        peer_list = list(self.peers.keys())
        if len(peer_list) >= 2:
            first_half = peer_list[:len(peer_list)//2]
            second_half = peer_list[len(peer_list)//2:]
            
            for peer_id in first_half:
                message = ConsensusMessage(
                    message_type=MessageType.PROPOSE,
                    node_id=self.node_id,
                    value=value,
                    round=round_num,
                    timestamp=datetime.now().isoformat()
                )
                await self._send_message(peer_id, message)
            
            for peer_id in second_half:
                message = ConsensusMessage(
                    message_type=MessageType.PROPOSE,
                    node_id=self.node_id,
                    value=f"{value}_BYZANTINE",
                    round=round_num,
                    timestamp=datetime.now().isoformat()
                )
                await self._send_message(peer_id, message)
            
            print(f"[{self.node_id}] ⚠️ BYZANTINE: Sent conflicting values to different peers!")
        else:
            await self._broadcast_message(ConsensusMessage(
                message_type=MessageType.PROPOSE,
                node_id=self.node_id,
                value=value,
                round=round_num,
                timestamp=datetime.now().isoformat()
            ))
    
    async def _broadcast_message(self, message: ConsensusMessage):
        """Send message to all peers"""
        tasks = [self._send_message(peer_id, message) for peer_id in self.peers.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_message(self, peer_id: str, message: ConsensusMessage):
        """Send message to a specific peer"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{self.peers[peer_id]}/receive_message",
                    json=message.model_dump()
                )
        except Exception as e:
            print(f"[{self.node_id}] Failed to send to {peer_id}: {e}")
    
    def _get_message_id(self, message: ConsensusMessage) -> str:
        """Generate a unique ID for a message to track forwarding"""
        return f"{message.node_id}:{message.round}:{message.value}:{message.timestamp}"
    
    async def _forward_message(self, message: ConsensusMessage, sender_id: str):
        """Forward a received message to other peers (gossip protocol)"""
        if message.message_type != MessageType.PROPOSE:
            return
        
        message_id = self._get_message_id(message)
        if message_id in self.forwarded_messages:
            return
        
        self.forwarded_messages.add(message_id)
        
        forward_tasks = []
        for peer_id in self.peers.keys():
            if peer_id != sender_id:
                forward_tasks.append(self._send_message(peer_id, message))
        
        if forward_tasks:
            await asyncio.gather(*forward_tasks, return_exceptions=True)
    
    async def receive_message(self, message: ConsensusMessage, sender_id: Optional[str] = None):
        """Receive a message from another node"""
        if message.round not in self.received_messages:
            self.received_messages[message.round] = []
        
        self.received_messages[message.round].append(message)
        
        if message.message_type == MessageType.PROPOSE:
            self._check_byzantine_behavior(message)
            if sender_id:
                await self._forward_message(message, sender_id)
    
    def _check_byzantine_behavior(self, message: ConsensusMessage):
        """Check if a node is sending conflicting messages (Byzantine behavior)"""
        round_messages = self.received_messages.get(message.round, [])
        
        node_messages = [m for m in round_messages if m.node_id == message.node_id]
        
        if len(node_messages) > 1:
            values = set(m.value for m in node_messages)
            if len(values) > 1:
                detection = {
                    "detected_at": datetime.now().isoformat(),
                    "byzantine_node": message.node_id,
                    "round": message.round,
                    "conflicting_values": list(values),
                    "detected_by": self.node_id
                }
                
                if not any(d["byzantine_node"] == message.node_id and d["round"] == message.round 
                          for d in self.byzantine_detections):
                    self.byzantine_detections.append(detection)
                    print(f"\n[{self.node_id}] 🚨 BYZANTINE FAULT DETECTED!")
                    print(f"    Node: {message.node_id}")
                    print(f"    Round: {message.round}")
                    print(f"    Conflicting values: {values}")
                    print(f"    Time: {detection['detected_at']}\n")

NODES = {
    "node1": "http://127.0.0.1:8001",
    "node2": "http://127.0.0.1:8002",
    "node3": "http://127.0.0.1:8003",
    "node4": "http://127.0.0.1:8004",
}

node_instance: Optional[ByzantineNode] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Byzantine Consensus Node")

@app.post("/receive_message")
async def receive_message(message: ConsensusMessage):
    """Receive a consensus message from another node"""
    if node_instance:
        await node_instance.receive_message(message, sender_id=message.node_id)
    return {"status": "received"}

@app.post("/propose")
async def propose_value(value: str):
    """Propose a value for consensus"""
    if node_instance:
        await node_instance.propose_value(value)
        return {"status": "proposed", "value": value, "round": node_instance.current_round}
    return {"status": "error", "message": "Node not initialized"}

@app.get("/status")
async def get_status():
    """Get the status of this node"""
    if not node_instance:
        return {"status": "error", "message": "Node not initialized"}
    
    return {
        "node_id": node_instance.node_id,
        "is_byzantine": node_instance.is_byzantine,
        "current_round": node_instance.current_round,
        "consensus_value": node_instance.consensus_value,
        "byzantine_detections": node_instance.byzantine_detections,
        "peers": list(node_instance.peers.keys())
    }

@app.get("/detections")
async def get_detections():
    """Get all Byzantine fault detections"""
    if not node_instance:
        return {"detections": []}
    
    return {
        "node_id": node_instance.node_id,
        "detections": node_instance.byzantine_detections,
        "total_detections": len(node_instance.byzantine_detections)
    }

def run_node(node_id_arg: str, port: int, is_byzantine: bool = False):
    global node_instance
    
    node_instance = ByzantineNode(node_id_arg, port, is_byzantine)
    
    for peer_id, peer_url in NODES.items():
        if peer_id != node_id_arg:
            node_instance.add_peer(peer_id, peer_url)
    
    byzantine_status = "⚠️ BYZANTINE" if is_byzantine else "✓ Honest"
    print(f"[{node_id_arg}] Starting Byzantine consensus node on port {port} ({byzantine_status})")
    print(f"[{node_id_arg}] Peers: {list(node_instance.peers.keys())}")
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python byzantine_node.py <node_id> <port> [--byzantine]")
        print("Example: python byzantine_node.py node1 8001")
        print("Example: python byzantine_node.py node1 8001 --byzantine")
        sys.exit(1)
    
    node_id_arg = sys.argv[1]
    port = int(sys.argv[2])
    is_byzantine = "--byzantine" in sys.argv
    
    run_node(node_id_arg, port, is_byzantine)

