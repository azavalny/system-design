# Reliability

How systems stay available and correct in the presence of partial failures, with patterns for fault tolerance, recovery, and stability under load.

**Reliability** - system continues to function correctly and remain available for operations in the presence of partial failures. Can be measured as:

Probability of a system working given a time interval

**Availability** - probability of system working correctly and available for operations at a given time.

- uptime / (uptime + downtime)
- number of successful requests / total requests

**High availability comes at the cost of new features and expensive operations and mechanisms to add, and has large tradeoffs against scalability of a system.**

Distributed systems are hard because they generally don't have shared memory where communication between nodes is passed through messages over an unreliable network with variable delays, as well as partial failures, unreliable clocks, and processing pauses causing issues. 

A **partial failure** is where parts of a distributed system become broken in unpredictable ways:

1. Sent packets or replies being lost or delayed (use timeouts or UDP for low latency systems)
2. A node's clock may be out of sync with other nodes (use last write wins to fix clock skew + confidence intervals for clock reads)
3. A process may pause for a substantial amount of time (e.g. garbage collector) and make the node declared dead by other nodes and restart (use fencing tokens)

In distributed systems, nodes must communicate over a sometimes unreliable network, and major decisions cannot be made by a single node

## Fault Tolerance

Fault tolerance - automatically detect and recover from failures.

### Automatic Fault Detection Signals

- Response - server fails to receive or respond to client
- Timeout - server response duration takes longer than timeout duration (could be network or node failure we don't know)
- Incorrect response - server's response incorrect
- Crash - server dies
- Arbitrary response - server response influenced by cybersecurity attack

Byzantine Fault - a node tricks and deceives other nodes about the information it received for a malicious attack. Can be prevented with a 2/3 supermajority vote

Safety - correctness of a system
Liveness - eventual correctness of a system

Safety should always hold in a distributed system and liveness should eventually happen

### Failover

Failover - automatic redundant backup that takes over when the primary system fails ensuring minimal downtime and should be tested regularly in production.

## Fault Tolerant Design

### 1. Redundancy

Replicate/duplicate critical components to increase availability with backups.

- **Active** - all replicas available and running but most expensive
- **Passive / warm** - primary replica running with rest on standby
- **Cold** - spare replicas only started on failure with lowest availability but cheapest option

### 2. Stateless Components

Components with no memory that can scale by horizontal replication.

- **Active-active redundancy**: multiple components work in parallel sharing workload simultaneously providing load balancing and instant failover if one component fails
- Load balancers are stateless by default unless they store user's session data

### 3. Stateful Components

Components with memory (databases, load balancers with user session data, message/event queues, cache, static content like images)

- Active-active redundancy achieved with **synchronous replication** so all components have same state
- Passive redundancy allows delays with data updates through **asynchronous replication** providing high write availability
  - Issue: outstanding (not-yet-replicated) updates are lost if the primary fails
- Load balancers also replicated to avoid them becoming a single point of failure

### 4. Caches

If cache fails/misses then data is read from the database causing load spikes.

- Memcached typically uses active-active redundancy
- Redis typically uses active-passive replication

### 5. Datacenters

Multiple datacenters provide independent infrastructure to isolate faults.

- **Zonal** - datacenters nearby each other in the same city so they can communicate in active-active setups with fast synchronous replication
- **Regional** - datacenters far away from each other in case something bad happens in a zone of datacenters
  - Disaster recovery against forces of nature, war
  - Active-passive setup with asynchronous replication

Datacenters can also use DNS to distribute load to different zones & regions.

- **Synchronous replication between zones and asynchronous replication between regions** providing high availability at component and zonal level
- In external regions you can keep components cold but databases warm

### 6. External Monitoring Service

Health checks.

- Health checks as HTTP or TCP requests generate alerts for recovery and events for scaling
- Done periodically and respond with response code, time, and number of retries usually on `/health` route

### 7. Internal Cluster Service

Inter-replica heartbeat checks for self monitoring.

- Provides higher availability compared to an external monitoring service
- Replica nodes exchange heartbeats so if one goes down the other becomes the primary node and gets the downed node's data
- Useful for stateful cluster components (databases, load balancers with IPs, etc) to keep consensus with each other on primary and secondary

## Component Recovery

- Stateless components can be restarted by having active replicas on hot standby or bringing up new replicas on warm standby and terminating unhealthy instances
- Stateful components need an automatic failover mechanism:
  - Floating IP address assigned to primary replica is assigned to a new replica when primary fails using a consensus algorithm for agreeing which node is primary
    - Load balancer can use floating IP to serve load and reassign it to secondary replica when primary goes down
    - Since floating IP isn't tied to an instance, it doesn't need to update a registry every time an instance fails
  - Use DNS router to keep registry of healthy instances that send heartbeats so the client never stores replica IPs and entries expire based on TTL

## Database Recovery

### 1. Hot Standby (Same Zone)

Synchronous replication in same zone.

- Almost no downtime
- Needs network proximity
- Slow writes because the same transaction must be copied to all database replicas

### 2. Warm Standby (Cross-Region)

Asynchronous replication across regions.

- Used for disaster recovery and faster performance
- Replication log from primary instance tracking transactions transferred to secondary
- Issue: new primary replica might lose updates due to **replication lag** between async writes
- Slow failover because regions have larger distances between them

### 3. Cold Backups

- Cost effective since you don't need live database replicas
- Causes significant downtime when backup is restored
- Cold backups can also be corrupted if the primary database is corrupted
- Use log updates, backup checkpoints, import, and apply updates as the recovery process

## System Stability Patterns

Make sure system is stable under peak loads.

### Client-Side Patterns

1. **Timeouts**
   - Prevent blocked threads and cascading failures
   - Have timeouts for all client calls
2. **Retries**
   - Prevent transient errors (glitches, race conditions) from affecting availability
   - Exponential backoff + random wait times so requests don't get re-routed to the same instance
   - Use idempotency tokens (based on request id) so failed requests only happen once
3. **Circuit breaker**
   - Track successes and failures
   - When failures cross a threshold, fall back to default/cached values and error messages

### Server-Side Patterns

- **Fail fast** - default values for invalid parameters or immediately error
- **Shed load** - after failed request, reject other requests
- **Back pressure** - slow down clients by rejecting requests within the system boundary and encourage exponential backoff (especially for calls to external services)
