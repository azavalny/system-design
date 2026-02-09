import random
import threading
import time
import queue

HEARTBEAT_INTERVAL = 1
ELECTION_TIMEOUT = (3, 6)
HEARTBEAT = "HEARTBEAT"
ELECTION = "ELECTION"

REQUEST_VOTE = "REQUEST_VOTE"
VOTE = "VOTE"


class Node(threading.Thread):
    def __init__(self, node_id, all_queues):
        threading.Thread.__init__(self)
        self.node_id = node_id
        self.state = "follower" #default state
        self.current_term = 0 #default term
        self.voted_for = None
        self.running = True
        self.all_queues = all_queues #node_id -> queue
        self.my_queue = self.all_queues[node_id] #(msg_type, sender, term)
        self.leader_id = None
        self.election_timeout = random.randint(ELECTION_TIMEOUT[0], ELECTION_TIMEOUT[1])
        self.last_heartbeat_time = time.time()
        self.votes_received = set()


    def send_heartbeat(self):
        for nid, q in self.all_queues.items():
            if nid != self.node_id:
                q.put((HEARTBEAT, self.node_id, self.current_term))

    def ask_for_votes(self):
        for nid, q in self.all_queues.items():
            if nid != self.node_id:
                q.put((REQUEST_VOTE, self.node_id, self.current_term))

        
    def start_election(self):
        self.current_term += 1
        self.state = "candidate"
        self.voted_for = self.node_id #vote for itself
        self.votes_received = {self.node_id}
        self.last_heartbeat_time = time.time()

        print(f"[Node {self.node_id}] Became CANDIDATE for term {self.current_term}")

        self.ask_for_votes()


    def register_vote_from_candidates(self, sender, term):
        if self.state == "candidate" and term == self.current_term:
            self.votes_received.add(sender)

            if len(self.votes_received) > len(self.all_queues) // 2:
                self.become_leader()


    def become_leader(self):
        self.state = "leader"
        self.leader_id = self.node_id
        print(f"[Node {self.node_id}] Became LEADER for term {self.current_term}")


    def update_term_and_reset_vote(self, new_term):
        """Update to a new term and reset voting state."""
        self.current_term = new_term
        self.state = "follower"
        self.voted_for = None


    def cast_vote(self, candidate_id, term):
        if self.voted_for is None:  # not yet voted
            self.voted_for = candidate_id
            self.all_queues[candidate_id].put((VOTE, self.node_id, self.current_term))
            print(f"[Node {self.node_id}] Voted for Node {candidate_id} in term {term}")


    def leader_is_alive(self, sender, term, time):
        self.current_term = term
        self.state = "follower"
        self.voted_for = None
        self.leader_id = sender
        self.last_heartbeat_time = time
        print(f"[Node {self.node_id}] Accepted leader {sender} for term {term}")



    def run(self):
        while self.running:
            current_time = time.time()
            #leader sends heartbeats to followers
            if self.state == "leader":
                self.send_heartbeat()
                time.sleep(HEARTBEAT_INTERVAL+10)

            if self.state in ["follower", "candidate"]:
                if current_time - self.last_heartbeat_time > self.election_timeout:
                    self.start_election()

            try:
                msg_type, sender, term = self.my_queue.get(timeout=0.1)# wait 0.1 seconds for a message else declare queue is empty

                if msg_type == HEARTBEAT:
                    if term >= self.current_term: #ensures older leader is not able to send heartbeat 
                        if term > self.current_term:
                            print(f"[Node {self.node_id}] Stepping down due to higher term heartbeat from {sender}")
                        
                    self.leader_is_alive(sender, term, current_time)

                elif msg_type == REQUEST_VOTE:
                    if term > self.current_term: # new election
                        self.update_term_and_reset_vote(term)

                    if term == self.current_term: #current election
                       self.cast_vote(sender, term)

                elif msg_type == VOTE:
                    self.register_vote_from_candidates(sender, term)
                            
            except queue.Empty:

                pass
