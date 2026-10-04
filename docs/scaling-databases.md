# Scaling Databases

**A database is the hardest part of software to scale** because you have to maintain transaction order and data consistency.

Data is either replicated or sharded/partitioned across multiple nodes.

Duplicating databases or components in general results in redundancy to increase fault tolerance and availability.

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
  - Write successful if acknowledged by w replicas, and we read from r replicas, so there's an overlap of at least 1 node that received the write and that we read from
  - Reads can tolerate n - r unavailable replicas, writes n - w
- **Majority quorum** - r = w = (n + 1) / 2 for odd n, so read and write quorums are both greater than half
- If every write had to reach all replicas, one unavailable replica would stop the system. With a quorum, as long as enough nodes respond we're okay and return the value with the latest timestamp
- Assuming replicas fail independently with probability p (real faults are often correlated):
  - P(all n faulty) = p^n
  - P(at least 1 faulty) = 1 - (1 - p)^n (complement of none failing)

**Read after write consistency** - client can immediately read data it wrote itself

Deduplicating retries requires the database to track requests it has already seen, otherwise a retried write after a lost acknowledgement gets applied twice

- **Idempotence** - function that can be retried without deduplication
  - e.g. incrementing a counter is not idempotent since the counter changes again
  - e.g. adding an element to a set is idempotent as adding it a second time doesn't change the set
- Have clients generate logical timestamps for their writes
- **Tombstone** - marker for a removed element to remember it was deleted instead of erasing it

Reconciling replicas:

- **Read repair** - client sends the latest value back to replicas that returned an older timestamp
- **Anti-entropy** - background process where replicas compare data and keep the records with the latest timestamp for each key
- **Last writer wins** - use timestamps with a total order **(Lamport clock)** and keep the latest
  - Data loss since concurrent writes with older timestamps get discarded
- **Multi value register** - use timestamps with a partial order **(Vector clock)**
  - Keep all concurrent updates as conflicting values for the application to resolve

## Database Sharding / Partitioning

Sharding/partitioning splits data across multiple databases to increase throughput without overloading a single database.

### 1. Key Range

Give partitions a sorted order of ranges based on key.

- Do this if you plan to do a lot of range queries

### 2. Hashed Key Range

Hash keys to keep distribution uniform and avoid skew.

- Do this if you plan to make a lot of queries based on IDs

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



# Data Engineering:
**Lambda Architecture** - stream processor  consumes events which later get corrected by batch processor
  * Exactly once semantics for stream processors to discard partial output of failed messages
  * Windowing by event time (processing time meaningless)
  * Data enters in as hot to the stream processor (fast) and cold to the batch processor (accurate) which gets merged for serving

**Kappa Architecture** - just stream processor + storing outputs of events to database

**Delta Architecture** - "Medallion Architecture" using streaming and batch processing like Lambda and combining data at 3 stages:
  * Bronze for raw data
  * Silver for filtered and cleaned data
  * Gold for business ready data
  * Stored in a data lake or data warehouse for final result