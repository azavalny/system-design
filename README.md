# System Design

System design, architecture, and databases explained from the _Software Architecture & Technology of Large-Scale Systems_ Udemy Course and _Designing Data Intensive Applications_ book for leveling up your software engineering skills and preparing for interviews

## Key Vocabulary

- **Throughput** - # of requests processed / time
- **Latency** - how long a request takes to be handled
  - Combination of wait/idle time for other resources and processing time of your programs
  - **Response time** is what the client sees: latency + network delay to transport the result to the user
- **Idempotence** - send same request twice, get same result with no side effects
- **Eventual consistency** - A change in the data in one location will eventually be updated in every other location, but reads from other locations may not yet have the updated value

---

## Organizing Software

It's best to organize software into:

- **Client** - part of backend where the request is handled
- **Services** - process request
- **Resources** - databases that services query from

That way the client doesn't have to directly access resources and everything can be independent.

---

## Performance

Performance is defined as the responsiveness of your software under load with the goal of minimizing latency and maximizing throughput.

Performance reductions are the result of a queue buildup of requests or jobs caused by:

- Slow processing
- Limited resource capacity
- Synchronous processes that can be made concurrent

### Improve Latency

1. Vertically scale by improving your hardware (CPU, network, memory, disk size)
2. Cache data that is frequently read and rarely modified (server has cache controls)

### Improve Throughput

1. Improve concurrency mechanisms of concurrent requests/jobs
2. Make serial aspects concurrent to process more requests/jobs simultaneously
   1. Reduce how many lines of code locks cover through **lock splitting** for objects and **lock striping** for data structures inside objects
   2. Design around **optimistic locking** (use a version number column) over pessimistic locking to avoid locking the database

---

## Latency

Latency acts as a bottleneck for throughput which is why you should improve it first.

### Network

- Use compression via binary encoding (Protobufs) to reduce data size and cache data
- Reuse application sessions and database connections

### Memory

- Use proper memory allocation techniques to reduce memory leaks, and cache data properly
- Normalize your data to avoid duplication and wasted space
- Choose good garbage collectors for cleaning weak/soft references to objects

### Disk

- Use indexes to speed queries and denormalize distributed data
- Use SSDs and RAID configurations for hardware
- Use zero-copy to reduce copying data between memory buffers (from disk straight to network)

### CPU

- Use batch and asynchronous processing

Higher throughput means you can support more users greater than the peak.

![](performance/latency.png)

**Tail latency** is an important metric that measures 99th, 99.9th... response times to model how well your application handles peak load.

![](performance/amdahls_gunther_law.png)

**Amdahl's law** models concurrency speedup by using more threads. After an initial sharp speedup, you will notice diminishing returns because of the overhead of managing threads as well as CPU context switching.

**Gunther's law** extends Amdahl's law by taking into account coherence delay (caching of variables and syncing them across caches) and scaling dimension which gets slower to maintain as you add more threads.

---

## Scalability

- **Horizontal scaling** - more of the same machine to handle more load
  - Cost grows linearly
  - Software has to support multi-machine instances and coordinate data between them
- **Vertical scaling** - upgrading hardware
  - Cost grows nonlinearly
  - Committing to the machine you buy

To scale a system you need:

1. **Decentralization** - specialized workers
2. **Independence** - of workers to take advantage of concurrency

Monoliths by definition are anti-patterns for scalability.

### Modularity

**Modularity** is breaking business logic down into specialized functions/services with loosely coupled modules and decoupled services.

To make a system scalable, you have to make it decentralized with independent components:

- Cache frequently read and rarely modified data to reduce load on the backend
- Use asynchronous and event-driven processing for distributing load over time
- Vertically partition systems into independent, stateless, replicated services
- Shard and replicate data
- Use load balancers to distribute load evenly
  - Discovery service to offload tracking healthy IP addresses away from load balancer
- DNS as a load balancer at a global scale

---

## Microservices

Microservices are vertically partitioned services and databases that make your software highly scalable, typically leading to eventual consistency.

- Services developed and deployed independently (for each business vertical) with separate database and schema for each service
  - Allows frequent deployment of new features for users
- Tradeoff exists between independence and reusability of components:
  - Prefer separate schemas and services for each business vertical
  - Avoid reusable libraries except utilities to reduce coupling

### Microservice Distributed Transactions

- Don't reuse libraries except utilities to avoid inter-service dependencies
- **Compensating transactions / saga pattern** means you roll back the entire workflow if any part fails
- Older approach is **2-phase commit (2PC)**:
  - Commit requires all services to vote
  - Poor fit for microservices compared to compensating transactions

### Sync vs Async

- Use **synchronous** processing for immediate responses and read queries
- Use **asynchronous** processing for write queries and where deferred responses are okay

---

## Event-Driven Architecture

Event-driven architecture: producers publish events to a router/broker/message queue and consumers consume them.

- Producer and consumer services being decoupled allows them to scale, be developed, and deployed independently
- Transactions are done async and the database may be polled regularly in case services go down
- If a transaction step as part of an event fails, new undo events are created to revert changes to the database

---

## Stateful vs Stateless Web Apps

- **Stateful** web applications have data in-memory and require low latency
- **Stateless** web applications store data in caches leading to higher scalability than stateful at the expense of higher latency
  - Store session data in caches like Redis and/or client-side cookies, or server shared cache

---

# Scaling Databases

**A database is the hardest part of software to scale** because you have to maintain transaction order and data consistency.

Data is either replicated or sharded/partitioned across multiple nodes.

Duplicating databases or components in general results in redundancy to increase fault tolerance and availability.

---

## Replication Strategies

Each of these are usually done asynchronously to avoid slowing writes by waiting for confirmation from followers.

### 1. Leader Replication

Choose 1 database to be the leader who accepts all writes (and can process reads). The rest are followers that accept reads.

- Increases read throughput
- Increases durability by copying data
- Leader sends replication logs (Write-Ahead Log) of ordered changes to followers to keep them synchronized
- Writes might not reach all followers in time for a client read (stale reads)

### 2. Multi-Leader Replication

Leaders act as followers to other leaders.

- Increases write availability (failure of one leader doesn't disrupt writes)
- If one leader fails, promote a follower to leader and reroute write requests
  - Old leader becomes a follower when it comes back
- Must handle write conflicts with multiple leaders

### 3. Leaderless Replication (Quorum)

Use quorum voting among nodes to validate read/write operations.

- Balances high availability with data accuracy
- Quorum condition:
  - quorum = **W + R > N**
    - where **N** is number of nodes
    - **W** is write quorum
    - **R** is read quorum

---

## Database Sharding / Partitioning

Sharding/partitioning splits data across multiple databases to increase throughput without overloading a single database.

### 1. Key Range

Give partitions a sorted order of ranges based on key.

- Do this if you plan to do a lot of range queries

### 2. Hashed Key Range

Hash keys to keep distribution uniform and avoid skew.

- Do this if you plan to make a lot of queries based on IDs

---

## Scalability Tools

### Load Balancer

Routes requests to available IP addresses of nodes to handle them.

- Example: DNS acts as a load balancer mapping domain name to an IP address

### Discovery Service

Keeps track of healthy node IP addresses separate from the load balancer.

### Reverse Proxy

Program guides requests from client to server.

- Can be a type of load balancer mapping requests to server IP addresses
- Handles security, routing, caching

### Sticky Sessions

All requests from a specific user routed to the same server node using a cookie from the session id so you can cache user login info.

### Message Queue

Producers add messages to a queue called the broker that consumers process.

- Decouples services as producers don't have to wait for consumer to process messages
- Independently scales producers and consumers
- Handles load spikes by offloading work to be processed asynchronously later to increase peak load handling

### Auto Scaler

Creates/deletes new app instances automatically to match load.

- Registers new instances with load balancer and deregisters old ones
- New instances assigned VM/container image + new IP address
- Configure min/max thresholds on cloud and monitor app health via pinging and HTTP health checks as well as resource monitoring

---

# Reliability

**Reliability** - system continues to function correctly and remain available for operations in the presence of partial failures. Can be measured as:

- \( P(\text{system working} \mid \text{time interval}) \)

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
---

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

---

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

---

## Component Recovery

- Stateless components can be restarted by having active replicas on hot standby or bringing up new replicas on warm standby and terminating unhealthy instances
- Stateful components need an automatic failover mechanism:
  - Floating IP address assigned to primary replica is assigned to a new replica when primary fails using a consensus algorithm for agreeing which node is primary
    - Load balancer can use floating IP to serve load and reassign it to secondary replica when primary goes down
    - Since floating IP isn't tied to an instance, it doesn't need to update a registry every time an instance fails
  - Use DNS router to keep registry of healthy instances that send heartbeats so the client never stores replica IPs and entries expire based on TTL

---

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

---

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

---

# Databases

## Relational vs Document

| Relational (SQL)                             | Document (NoSQL)                                |
| -------------------------------------------- | ----------------------------------------------- |
| Support for joins                            | More flexible schemas and faster reading        |
| Better for many:1 or many:many relationships | Better for one:many relationships like in trees |

Graph is better for modeling many:many common and complex relationships with edges as well as storing different object types in vertices.

- **Index** - lookup reference to find rows
- **Secondary index** - lookup reference to find rows based on other column values
- **Primary key** - uniquely identifies a row
- **Foreign key** - points to a row in another table

---

## B-Trees

**B-Tree** - generalized binary search tree that stores keys and data/pointers to data making them fast for individual key queries.

- Middle key is made parent when new key is added that exceeds capacity (keeps tree balanced and all leaf nodes at same depth)

**B+ Tree** - stores data only in leaf nodes linking them together in a linked list making them fast for range queries.

---

## OLTP vs OLAP

- **OLTP (Online transaction processing)** - fast, real-time transactions on small number of records
- **OLAP (Online analytical processing)** - analysis and reporting of the history of all records

**Data warehouse** - low latency storage of large volumes of data for analytical processing requiring high availability.

**Column-oriented storage** stores values from each column together in separate files so you only read columns used in a query instead of all the values in the row.

- More efficient for analytical queries over large datasets

---

## Compatibility

- **Backward compatible** - new code can read data generated by older code
- **Forward compatible** - older code can read data generated by newer code

---

## Protobuf vs Avro

**Protobuf**

- Serialize objects in binary format with field tags/aliases instead of key/values like in JSON with datatypes clearly specified
- Forward compatible when incrementing a new field tag for new fields
- Backward compatible since new fields are optional and tags have the same meaning

**Avro**

- Encode entire object and refer to schema for types of each field
- Reader and writer schema compatibility ensures backward compatibility

---

## RPC

**RPC (remote procedure call)** - running code on another computer using a local function call

**gRPC** - RPC with Protobufs for encoding objects and supporting streams

---

## Transactions

Transaction - group multiple reads and writes into a single logical unit.

- **Commit** - succeed
- **Abort / rollback** - fail (avoid partial failures)

ACID:

- **Atomicity** - all or nothing
- **Consistency** - invariants remain true
- **Isolation** - concurrent transactions don't interfere
- **Durability** - committed data persists (WAL on single node or replication across nodes)

### Isolation Level

Isolation level - how a transaction's changes are visible to other transactions during concurrent execution.

Standard SQL isolation levels:

- **Read Uncommitted** - allows reading uncommitted data (dirty reads)
- **Read Committed** - read only committed data but risks non-repeatable reads
- **Snapshot Isolation / Repeatable Read** - stable snapshot for whole transaction but risks phantom reads
- **Serializable** - transactions behave as if executed serially (no anomalies)

### 3 Ways to Implement Serializable Transactions

1. Execute transactions in serial order (no concurrency) through making fast transactions
2. **2-phase locking**
   - Reads acquire shared locks, writes acquire exclusive locks
   - Locks released at end
3. **Serializable Snapshot Isolation (SSI)**
   - Abort transaction when serializability violation detected using optimistic conflict detection
   - Works great for low contention, commutative, atomic operations

---

## Race Conditions

A race condition is an unpredictable outcome of multiple threads modifying and reading shared resources.

1. **Dirty reads** - one client reads another client's writes before they have been committed
2. **Dirty writes** - one client overwrites data another client has written before it fully commits
3. **Read skew** - one transaction reads multiple rows which are partially modified by another transaction midway through
4. **Non-repeatable read** - read same row twice within a transaction and get different results (single-row form of read skew)
5. **Lost updates** - two threads concurrently read then write where one overwrites the other's write
6. **Write skew** - transaction reads, decides based on the value, then writes but the original value changed by the time the write is made
7. **Phantom read** - transaction executes the same query twice and gets a different set of rows because another transaction modified rows in the meantime
