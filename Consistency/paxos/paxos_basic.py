"""
Basic Paxos Consensus Algorithm Implementation

Paxos is a family of protocols for solving consensus in a network of unreliable processors.
This implementation demonstrates Basic Paxos (single-decree Paxos).

Key roles:
- Proposer: Proposes values
- Acceptor: Votes on proposals
- Learner: Learns the chosen value
"""

import time
from typing import Optional, Dict, Set, Any
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    PREPARE = "prepare"
    PROMISE = "promise"
    ACCEPT = "accept"
    ACCEPTED = "accepted"
    NACK = "nack"


@dataclass
class Message:
    msg_type: MessageType
    proposal_id: tuple
    value: Any = None
    accepted_id: tuple = None
    accepted_value: Any = None
    from_node: int = None
    to_node: int = None


class PaxosNode:
    """
    A node that can act as Proposer, Acceptor, and Learner
    """
    
    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        
        self.promised_id: Optional[tuple] = None
        self.accepted_id: Optional[tuple] = None
        self.accepted_value: Any = None
        
        self.proposal_number = 0
        self.promises_received: Dict[tuple, Set[int]] = {}
        self.accepts_received: Dict[tuple, Set[int]] = {}
        self.learned_value: Any = None
        
        self.message_log = []
    
    def generate_proposal_id(self) -> tuple:
        """Generate unique proposal ID (round_number, node_id)"""
        self.proposal_number += 1
        return (self.proposal_number, self.node_id)
    
    def majority(self) -> int:
        """Calculate majority threshold"""
        return (self.total_nodes // 2) + 1
    
    def propose_value(self, value: Any) -> Message:
        """
        Phase 1a: Proposer generates proposal and sends PREPARE
        """
        proposal_id = self.generate_proposal_id()
        self.promises_received[proposal_id] = set()
        
        message = Message(
            msg_type=MessageType.PREPARE,
            proposal_id=proposal_id,
            from_node=self.node_id
        )
        self.message_log.append(f"Node {self.node_id}: Proposing value '{value}' with ID {proposal_id}")
        return message, value
    
    def receive_prepare(self, message: Message) -> Message:
        """
        Phase 1b: Acceptor responds to PREPARE with PROMISE or NACK
        """
        proposal_id = message.proposal_id
        
        if self.promised_id is None or proposal_id > self.promised_id:
            self.promised_id = proposal_id
            
            response = Message(
                msg_type=MessageType.PROMISE,
                proposal_id=proposal_id,
                accepted_id=self.accepted_id,
                accepted_value=self.accepted_value,
                from_node=self.node_id
            )
            self.message_log.append(
                f"Node {self.node_id}: Promised to proposal {proposal_id}"
            )
            return response
        else:
            response = Message(
                msg_type=MessageType.NACK,
                proposal_id=proposal_id,
                from_node=self.node_id
            )
            self.message_log.append(
                f"Node {self.node_id}: Rejected proposal {proposal_id} (promised to {self.promised_id})"
            )
            return response
    
    def receive_promise(self, message: Message, proposed_value: Any) -> Optional[Message]:
        """
        Phase 2a: Proposer collects promises and sends ACCEPT request
        """
        proposal_id = message.proposal_id
        
        if proposal_id not in self.promises_received:
            return None
        
        self.promises_received[proposal_id].add(message.from_node)
        
        if len(self.promises_received[proposal_id]) >= self.majority():
            value_to_propose = proposed_value
            
            highest_accepted_id = None
            for pid in self.promises_received[proposal_id]:
                if message.accepted_id and (
                    highest_accepted_id is None or message.accepted_id > highest_accepted_id
                ):
                    highest_accepted_id = message.accepted_id
                    value_to_propose = message.accepted_value
            
            accept_message = Message(
                msg_type=MessageType.ACCEPT,
                proposal_id=proposal_id,
                value=value_to_propose,
                from_node=self.node_id
            )
            
            self.accepts_received[proposal_id] = set()
            self.message_log.append(
                f"Node {self.node_id}: Received majority promises for {proposal_id}, sending ACCEPT for value '{value_to_propose}'"
            )
            return accept_message
        
        return None
    
    def receive_accept(self, message: Message) -> Message:
        """
        Phase 2b: Acceptor responds to ACCEPT request with ACCEPTED
        """
        proposal_id = message.proposal_id
        
        if self.promised_id is None or proposal_id >= self.promised_id:
            self.promised_id = proposal_id
            self.accepted_id = proposal_id
            self.accepted_value = message.value
            
            response = Message(
                msg_type=MessageType.ACCEPTED,
                proposal_id=proposal_id,
                value=message.value,
                from_node=self.node_id
            )
            self.message_log.append(
                f"Node {self.node_id}: Accepted proposal {proposal_id} with value '{message.value}'"
            )
            return response
        else:
            response = Message(
                msg_type=MessageType.NACK,
                proposal_id=proposal_id,
                from_node=self.node_id
            )
            self.message_log.append(
                f"Node {self.node_id}: Rejected accept {proposal_id} (promised to {self.promised_id})"
            )
            return response
    
    def receive_accepted(self, message: Message) -> bool:
        """
        Learner learns the chosen value when majority accepts
        """
        proposal_id = message.proposal_id
        
        if proposal_id not in self.accepts_received:
            self.accepts_received[proposal_id] = set()
        
        self.accepts_received[proposal_id].add(message.from_node)
        
        if len(self.accepts_received[proposal_id]) >= self.majority():
            self.learned_value = message.value
            self.message_log.append(
                f"Node {self.node_id}: LEARNED value '{message.value}' from proposal {proposal_id}"
            )
            return True
        
        return False


class PaxosCluster:
    """
    Simulates a cluster of Paxos nodes
    """
    
    def __init__(self, num_nodes: int):
        self.nodes = [PaxosNode(i, num_nodes) for i in range(num_nodes)]
        self.num_nodes = num_nodes
    
    def run_consensus(self, proposer_id: int, value: Any) -> Optional[Any]:
        """
        Run full Paxos consensus protocol
        """
        proposer = self.nodes[proposer_id]
        
        prepare_msg, proposed_value = proposer.propose_value(value)
        
        promises = []
        for node in self.nodes:
            promise = node.receive_prepare(prepare_msg)
            if promise.msg_type == MessageType.PROMISE:
                promises.append(promise)
        
        if len(promises) < proposer.majority():
            print(f"Failed to get majority promises. Got {len(promises)}, need {proposer.majority()}")
            return None
        
        accept_msg = None
        for promise in promises:
            result = proposer.receive_promise(promise, proposed_value)
            if result:
                accept_msg = result
                break
        
        if not accept_msg:
            print("Failed to generate accept message")
            return None
        
        accepted_responses = []
        for node in self.nodes:
            accepted = node.receive_accept(accept_msg)
            if accepted.msg_type == MessageType.ACCEPTED:
                accepted_responses.append(accepted)
        
        if len(accepted_responses) < proposer.majority():
            print(f"Failed to get majority accepts. Got {len(accepted_responses)}, need {proposer.majority()}")
            return None
        
        for accepted in accepted_responses:
            for node in self.nodes:
                if node.receive_accepted(accepted):
                    return node.learned_value
        
        return None
    
    def print_logs(self):
        """Print all node logs"""
        print("\n=== Paxos Execution Log ===")
        for node in self.nodes:
            for log in node.message_log:
                print(log)


def demo_paxos():
    """
    Demonstrate Paxos consensus
    """
    print("=" * 60)
    print("PAXOS CONSENSUS ALGORITHM DEMONSTRATION")
    print("=" * 60)
    
    num_nodes = 5
    cluster = PaxosCluster(num_nodes)
    
    print(f"\nInitializing cluster with {num_nodes} nodes")
    print(f"Majority required: {cluster.nodes[0].majority()} nodes\n")
    
    print("Scenario 1: Single proposer")
    print("-" * 40)
    result = cluster.run_consensus(proposer_id=0, value="Alice")
    cluster.print_logs()
    
    if result:
        print(f"\n[SUCCESS] Consensus reached! Chosen value: '{result}'")
    else:
        print("\n[FAILED] Consensus failed")
    
    print("\n" + "=" * 60)
    print("Scenario 2: Competing proposers")
    print("-" * 40)
    
    cluster2 = PaxosCluster(num_nodes)
    
    proposer1 = cluster2.nodes[0]
    proposer2 = cluster2.nodes[1]
    
    prepare1, value1 = proposer1.propose_value("Bob")
    prepare2, value2 = proposer2.propose_value("Charlie")
    
    for node in cluster2.nodes:
        node.receive_prepare(prepare1)
        node.receive_prepare(prepare2)
    
    result = cluster2.run_consensus(proposer_id=2, value="David")
    cluster2.print_logs()
    
    if result:
        print(f"\n[SUCCESS] Consensus reached despite competition! Chosen value: '{result}'")
    else:
        print("\n[FAILED] Consensus failed")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_paxos()
