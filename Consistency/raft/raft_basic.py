"""
Raft Consensus Algorithm Implementation

Raft is a consensus algorithm designed to be more understandable than Paxos.
It separates leader election, log replication, and safety.

Key components:
- Leader Election: Elect a leader to manage the replicated log
- Log Replication: Leader accepts client requests and replicates to followers
- Safety: Ensure committed entries are durable
"""

import time
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class MessageType(Enum):
    REQUEST_VOTE = "request_vote"
    VOTE_RESPONSE = "vote_response"
    APPEND_ENTRIES = "append_entries"
    APPEND_RESPONSE = "append_response"


@dataclass
class LogEntry:
    term: int
    index: int
    command: Any


@dataclass
class Message:
    msg_type: MessageType
    term: int
    from_node: int
    to_node: int = None
    
    candidate_id: int = None
    last_log_index: int = 0
    last_log_term: int = 0
    vote_granted: bool = False
    
    leader_id: int = None
    prev_log_index: int = 0
    prev_log_term: int = 0
    entries: List[LogEntry] = field(default_factory=list)
    leader_commit: int = 0
    success: bool = False


class RaftNode:
    """
    A node in the Raft cluster
    """
    
    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.log: List[LogEntry] = []
        
        self.commit_index = 0
        self.last_applied = 0
        
        self.next_index: Dict[int, int] = {}
        self.match_index: Dict[int, int] = {}
        
        self.votes_received: set = set()
        self.current_leader: Optional[int] = None
        
        self.message_log = []
        self.election_timeout = random.uniform(150, 300)
        self.last_heartbeat = time.time()
    
    def majority(self) -> int:
        """Calculate majority threshold"""
        return (self.total_nodes // 2) + 1
    
    def start_election(self) -> List[Message]:
        """
        Transition to candidate and start election
        """
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        
        last_log_index = len(self.log) - 1 if self.log else 0
        last_log_term = self.log[-1].term if self.log else 0
        
        self.message_log.append(
            f"Node {self.node_id}: Starting election for term {self.current_term}"
        )
        
        messages = []
        for node_id in range(self.total_nodes):
            if node_id != self.node_id:
                msg = Message(
                    msg_type=MessageType.REQUEST_VOTE,
                    term=self.current_term,
                    from_node=self.node_id,
                    to_node=node_id,
                    candidate_id=self.node_id,
                    last_log_index=last_log_index,
                    last_log_term=last_log_term
                )
                messages.append(msg)
        
        return messages
    
    def handle_request_vote(self, message: Message) -> Message:
        """
        Handle RequestVote RPC
        """
        vote_granted = False
        
        if message.term > self.current_term:
            self.current_term = message.term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
        
        last_log_index = len(self.log) - 1 if self.log else 0
        last_log_term = self.log[-1].term if self.log else 0
        
        log_ok = (message.last_log_term > last_log_term or
                  (message.last_log_term == last_log_term and 
                   message.last_log_index >= last_log_index))
        
        if (message.term == self.current_term and 
            (self.voted_for is None or self.voted_for == message.candidate_id) and
            log_ok):
            vote_granted = True
            self.voted_for = message.candidate_id
            self.message_log.append(
                f"Node {self.node_id}: Voted for Node {message.candidate_id} in term {self.current_term}"
            )
        else:
            self.message_log.append(
                f"Node {self.node_id}: Denied vote for Node {message.candidate_id} in term {self.current_term}"
            )
        
        return Message(
            msg_type=MessageType.VOTE_RESPONSE,
            term=self.current_term,
            from_node=self.node_id,
            to_node=message.from_node,
            vote_granted=vote_granted
        )
    
    def handle_vote_response(self, message: Message) -> bool:
        """
        Handle vote response and check if won election
        """
        if message.term > self.current_term:
            self.current_term = message.term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
            return False
        
        if self.state == NodeState.CANDIDATE and message.term == self.current_term:
            if message.vote_granted:
                self.votes_received.add(message.from_node)
                
                if len(self.votes_received) >= self.majority():
                    self.become_leader()
                    return True
        
        return False
    
    def become_leader(self):
        """
        Transition to leader state
        """
        self.state = NodeState.LEADER
        self.current_leader = self.node_id
        
        self.next_index = {i: len(self.log) for i in range(self.total_nodes)}
        self.match_index = {i: 0 for i in range(self.total_nodes)}
        
        self.message_log.append(
            f"Node {self.node_id}: Became LEADER for term {self.current_term} with {len(self.votes_received)} votes"
        )
    
    def append_entry(self, command: Any) -> LogEntry:
        """
        Leader appends new entry to log
        """
        entry = LogEntry(
            term=self.current_term,
            index=len(self.log),
            command=command
        )
        self.log.append(entry)
        
        self.message_log.append(
            f"Node {self.node_id}: Appended entry at index {entry.index} with command '{command}'"
        )
        
        return entry
    
    def create_append_entries(self, follower_id: int) -> Message:
        """
        Create AppendEntries RPC for a follower
        """
        prev_log_index = self.next_index[follower_id] - 1
        prev_log_term = self.log[prev_log_index].term if prev_log_index >= 0 and prev_log_index < len(self.log) else 0
        
        entries = []
        if self.next_index[follower_id] < len(self.log):
            entries = self.log[self.next_index[follower_id]:]
        
        return Message(
            msg_type=MessageType.APPEND_ENTRIES,
            term=self.current_term,
            from_node=self.node_id,
            to_node=follower_id,
            leader_id=self.node_id,
            prev_log_index=prev_log_index,
            prev_log_term=prev_log_term,
            entries=entries,
            leader_commit=self.commit_index
        )
    
    def handle_append_entries(self, message: Message) -> Message:
        """
        Handle AppendEntries RPC
        """
        success = False
        
        if message.term > self.current_term:
            self.current_term = message.term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
        
        if message.term == self.current_term:
            self.state = NodeState.FOLLOWER
            self.current_leader = message.leader_id
            self.last_heartbeat = time.time()
            
            if message.prev_log_index < 0 or (
                message.prev_log_index < len(self.log) and
                (message.prev_log_index < 0 or 
                 self.log[message.prev_log_index].term == message.prev_log_term)
            ):
                success = True
                
                if message.entries:
                    insert_index = message.prev_log_index + 1
                    self.log = self.log[:insert_index] + message.entries
                    
                    self.message_log.append(
                        f"Node {self.node_id}: Appended {len(message.entries)} entries from Leader {message.leader_id}"
                    )
                
                if message.leader_commit > self.commit_index:
                    self.commit_index = min(message.leader_commit, len(self.log) - 1)
                    self.message_log.append(
                        f"Node {self.node_id}: Updated commit_index to {self.commit_index}"
                    )
        
        return Message(
            msg_type=MessageType.APPEND_RESPONSE,
            term=self.current_term,
            from_node=self.node_id,
            to_node=message.from_node,
            success=success
        )
    
    def handle_append_response(self, message: Message):
        """
        Leader handles AppendEntries response
        """
        if message.term > self.current_term:
            self.current_term = message.term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
            return
        
        if self.state == NodeState.LEADER and message.term == self.current_term:
            if message.success:
                self.next_index[message.from_node] = len(self.log)
                self.match_index[message.from_node] = len(self.log) - 1
                
                self.update_commit_index()
            else:
                self.next_index[message.from_node] = max(0, self.next_index[message.from_node] - 1)
    
    def update_commit_index(self):
        """
        Leader updates commit index based on majority replication
        """
        for n in range(self.commit_index + 1, len(self.log)):
            if self.log[n].term == self.current_term:
                replicated = sum(1 for idx in self.match_index.values() if idx >= n)
                replicated += 1
                
                if replicated >= self.majority():
                    self.commit_index = n
                    self.message_log.append(
                        f"Node {self.node_id}: Committed entry at index {n}"
                    )


class RaftCluster:
    """
    Simulates a cluster of Raft nodes
    """
    
    def __init__(self, num_nodes: int):
        self.nodes = [RaftNode(i, num_nodes) for i in range(num_nodes)]
        self.num_nodes = num_nodes
        self.current_leader: Optional[int] = None
    
    def run_election(self, candidate_id: int) -> Optional[int]:
        """
        Run leader election
        """
        candidate = self.nodes[candidate_id]
        
        vote_requests = candidate.start_election()
        
        for msg in vote_requests:
            target_node = self.nodes[msg.to_node]
            response = target_node.handle_request_vote(msg)
            
            if candidate.handle_vote_response(response):
                self.current_leader = candidate_id
                return candidate_id
        
        return None
    
    def replicate_log(self, command: Any) -> bool:
        """
        Leader replicates log entry to followers
        """
        if self.current_leader is None:
            print("No leader elected")
            return False
        
        leader = self.nodes[self.current_leader]
        
        entry = leader.append_entry(command)
        
        for node_id in range(self.num_nodes):
            if node_id != self.current_leader:
                append_msg = leader.create_append_entries(node_id)
                follower = self.nodes[node_id]
                
                response = follower.handle_append_entries(append_msg)
                leader.handle_append_response(response)
        
        return leader.commit_index >= entry.index
    
    def print_logs(self):
        """Print all node logs"""
        print("\n=== Raft Execution Log ===")
        for node in self.nodes:
            for log in node.message_log:
                print(log)
    
    def print_state(self):
        """Print current cluster state"""
        print("\n=== Cluster State ===")
        for node in self.nodes:
            print(f"Node {node.node_id}: {node.state.value} | Term: {node.current_term} | "
                  f"Log size: {len(node.log)} | Commit: {node.commit_index}")


def demo_raft():
    """
    Demonstrate Raft consensus
    """
    print("=" * 60)
    print("RAFT CONSENSUS ALGORITHM DEMONSTRATION")
    print("=" * 60)
    
    num_nodes = 5
    cluster = RaftCluster(num_nodes)
    
    print(f"\nInitializing cluster with {num_nodes} nodes")
    print(f"Majority required: {cluster.nodes[0].majority()} nodes\n")
    
    print("Scenario 1: Leader Election")
    print("-" * 40)
    
    leader_id = cluster.run_election(candidate_id=0)
    
    if leader_id is not None:
        print(f"\n[SUCCESS] Leader elected: Node {leader_id}")
    else:
        print("\n[FAILED] Election failed")
    
    cluster.print_logs()
    cluster.print_state()
    
    print("\n" + "=" * 60)
    print("Scenario 2: Log Replication")
    print("-" * 40)
    
    if leader_id is not None:
        commands = ["SET x=1", "SET y=2", "SET z=3"]
        
        for cmd in commands:
            success = cluster.replicate_log(cmd)
            if success:
                print(f"[SUCCESS] Command '{cmd}' replicated and committed")
            else:
                print(f"[FAILED] Command '{cmd}' failed to commit")
        
        cluster.print_logs()
        cluster.print_state()
    
    print("\n" + "=" * 60)
    print("Scenario 3: New Election After Leader Failure")
    print("-" * 40)
    
    cluster2 = RaftCluster(num_nodes)
    
    first_leader = cluster2.run_election(candidate_id=0)
    print(f"First leader: Node {first_leader}")
    
    cluster2.nodes[first_leader].state = NodeState.FOLLOWER
    
    new_leader = cluster2.run_election(candidate_id=1)
    
    if new_leader is not None:
        print(f"\n[SUCCESS] New leader elected after failure: Node {new_leader}")
    else:
        print("\n[FAILED] New election failed")
    
    cluster2.print_logs()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_raft()
