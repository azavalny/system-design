# Consistency and Consensus

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
