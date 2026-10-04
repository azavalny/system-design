# Consistency and Consensus

* System model requirements:

| Problem | Must wait for communication | Requires synchrony |
| ------- | --------------------------- | ------------------ |
| Atomic commit | All participating nodes | Partially synchronous |
| Consensus, total order broadcast, linearizable CAS | Quorum | Partially synchronous |
| Linearizable get/set | Quorum | Asynchronous |
| Eventual consistency, causal broadcast, FIFO broadcast | Local replica only | Asynchronous |

Strength of assumptions increases from bottom to top

How replicated nodes agree on data and operation order, the consistency models that emerge from those choices, and the algorithms that make agreement possible.

* Consistency - all replica nodes display the same data at the same time
* Consensus - algorithm for getting all nodes to agree
* Eventual consistency - property that eventually all reads will return the same with inconsistencies self resolving
  * Violations of timeliness/availability

* Linearizability - strong consistency property ensuring operations are instant, atomic, and appear as if one copy of the data exists on all nodes
  * Or whether timings of requests & responses can be arrange in a valid sequential order
    * One read should have the same data after another read
    * Once new value is written then all reads following must return that same value
  * Use when you need hard uniqueness constraints, control when you read your own writes to avoid stale reads, and single leader replication with a lock. Multi leader and leaderless don't need linearizability
  * Not guaranteed with strict quorum `w + r > n`
  * If an app requires linearizability and some replicas get disconnected and can't process requests then the app is unavailable
    * If an app dosen't, then each replica can process requests independently making app available with network defaults
    * If success of an app needs ordering of operations then you need strict consistency and linearizability
  * Biggest tradeoff of being slow and less available

* Causal Consistency - weak consistency property where cause and effect order is preserved across all replicas where operations with no causal relationships can appear in different orders
  * If operation B could have been influenced by operation A, then every node must see A before B
  * Unlike linearizability & strong consistency, available during network delays and failures
  * Done with a sequence number or Lamport timestamps (counter, transaction id) to order events based on causal dependencies

* Split brain - when we don't know who the leader is
* Total order - all operations arrange in single global sequence

* CAP Theorem - when network failures (partitions) occur, systems must choose between strict/strong consistency or availability

* PACELC - Extension of CAP theorem - during partitions choose between availability and consistency, otherwise choose between latency and consistency. 

* Total order broadcast - all messages are broadcasted/delivered to all nodes in the same order
  * No messages lost for any node
  * Messages delivered in the same order to each node
  * Use to implement linearizable compare and set operations

* 2 Phase Commit (2PC) - atomic commits for distributed database
  * Phase 1 Coordinator asks all nodes if they're ready and if all say yes (ensures atomicity)
  * Phase 2 Coordinator sends a commit request to all nodes. Otherwise, Coordinator sends an abort request to all ndoes

  * Coordinator must retry forever once decision is made and one of the nodes go down. If Coordinator goes down all nodes have to wait.

  * In doubt transaction - if coordinator crashes then transactions must wait and use their locks to hold up the database to block other transactions until the Coordinator goes back up
  * Transaction Coordinator acts as its own database of logs and is a single point of failure unless replicated


* Fault tolerance - ability of a system to operate correctly when nodes fail


* Consensus algorithms handle mutually incompatible operations and ensure:
  * Uniform Agreement among all the nodes
  * Integrity where no node decides twice
  * Validity where node takes responsibility over the value it proposed
  * Termination where every available node decides value assuming at least half the nodes are still alive

  * E.g. Raft, Paxos, Zab, VSR are all total order broadcast algorithms that do repeated rounds of consensus using an epoch number to cast ballot
    * Every time a current leader dies, a new vote is started to elect new leader with incremented epoch
    * Total order broadcast implements linearizable atomic operations in a fault tolerant way
    * Require strict majority over `n//2 + 1` of the nodes must agree
      * 3 nodes minimum to tolerate 1 failure, 5 nodes for 2 failures
    * Assume fixed set of nodes
    * Timeouts used to detect failed nodes

* Apache Zookeeper - tool for automatically providing consensus, failure detection, and membership service that distributed applications can use
  * Replicates data across all nodes using fault tolerant total order broadcast algorithm to apply the same writes in the same order to keep replicas consistent
  * Provides Compare and Set with a distributed lock or a lease with expiry time
  * Provides total order of operations using a fencing token with a transaction ID and version number
  * Uses heartbeats for failure detection and session timeout between clients and Zookeeper servers
  * Uses change notifications to have clients subscribe to cluster changes
  * Runs on a fixed number of nodes supporting a large number of clients

* Linearizable compare and set, atomic transactions, total order broadcast, locks and leases, membership coordination services, and uniquess reduce to Consensus 

* State machine replication - replicas use FIFO total order broadcast to deliver every write to all replicas
  * Ensures each replica receives updates in same order
  * Applying an update is deterministic so every replica ends up identical, but you have to wait for delivery through broadcast and can't update state immediately
  * E.g. blockchains, smart contracts, serializable transactions
  * Can use weaker broadcast if updates allow it:
    * Causal broadcast if concurrent updates are commutative
    * Reliable broadcast if all updates are commutative
    * Best effort broadcast if all updates are commutative, idempotent, and message loss is tolerated

* Consensus vs total order broadcast
  * Consensus - several nodes agree on a single value
  * Total order broadcast - all nodes agree on what the next message to deliver is
  * An algorithm for one can be converted into the other
  * Consensus decides the order of the replication log, the log feeds the state machine, and determinism makes every replica identical
  * E.g. Paxos - single value consensus, Multi-Paxos - generalization to total order broadcast, Raft - total order broadcast
  * A single leader that sequences all writes gives total order broadcast, but it's only fault tolerant if a new leader can be chosen safely when it fails, which itself needs consensus
    * Manual failover - human operator chooses a new node as leader if it fails (e.g. planned outages)
  * Assume partially synchronous, crash recovery system
  * FLP result - there's no deterministic consensus algorithm that is guaranteed to terminate in an asynchronous crash-stop system, even if only one node can crash

* Automatic leader election in consensus algorithms
  * Failure detector (based on timeout) suspects the leader crashed or is unavailable
  * Must prevent two leaders at the same time
  * Term is incremented every time a leader election is started
    * Guarantee <= 1 leader per term
    * Each node can only vote once per term
    * Requires a quorum of nodes to elect a new leader in a term
  * Even after being elected, a leader can't assume it's still the leader (a newer term may exist), so it needs a quorum to acknowledge each message before deciding on it

* Raft - every node is either a follower, candidate, or leader
  * Each node is a follower on startup or after recovering from a crash
  * When the current leader is unresponsive, a follower becomes a candidate in a new term:
    * If it gets votes from a quorum, it becomes the new leader
    * If it discovers a current leader or a node with a higher term number, it steps down to a follower (higher terms take precedence)
    * If the election times out, it starts a new election with a higher term number
  * If a leader discovers a higher term, it becomes a follower

* Linearizability in practice
  * Quorum reads and writes alone are not enough to ensure linearizability, because a later read could still hit a quorum that doesn't have the newest value yet
  * ABD algorithm - quorum writes and reads with read repair
    * Reader gets responses from a quorum and picks the value with the latest timestamp
    * Before returning, the reader resends that value to replicas that didn't have it and waits until a quorum acknowledges
    * Every subsequent quorum read will then see the new value
  * Compare and swap - set x to new value only if its current value equals the expected old value
    * Can't be made linearizable with quorums, you have to use total order broadcast and wait for delivery
  * Linearizable compare and swap is equivalent to consensus and total order broadcast

* Why eventual consistency
  * Linearizability is very expensive to implement in practice with lots of messages and waiting for responses
  * Leader can be a bottleneck limiting scalability
  * If you can't contact a quorum of nodes, you can't process read/write operations limiting availability
  * Eventual consistency - replicas process operations based on their local state. Eventually, all replicas will be in the same state but there's no guarantee how long it might take
  * Strong eventual consistency:
    1. every update to one replica will eventually be made to other replicas
    2. any two replicas that processed the same set of updates are in the same state, even if they processed them in different orders
    * No need to wait for network communication before processing an operation
    * Causal broadcast can disseminate updates
    * Concurrent update conflicts need to be resolved
  * CRDT (conflict free replicated data type) - lets multiple users update concurrently without central coordination
    * Merges changes automatically, guaranteeing all replicas eventually converge to the exact same state
    * Don't require total order broadcast


