# Distributed Systems

Foundations from Martin Kleppmann's [Concurrent and Distributed Systems course notes](https://www.cl.cam.ac.uk/teaching/2122/ConcDisSys/dist-sys-notes.pdf): system models, time and clocks, ordering events, and broadcast.

In multithreading, threads share the same memory address space but in distributed systems the network addresses are different between nodes. There's no single shared address space, so you can't just pass pointers in shared memory

Distributed System - multiple computers communicating via a network

- "A distributed system is one in which the failure of a computer you didn't even know existed can render your own computer unusable" - Lamport
- Advantages:
  - If one node fails the system keeps functioning
  - Get data from a nearby node rather than one halfway around the world
  - Store and process large amounts of data that can't fit on one computer
- Disadvantages:
  - Communication over the network might fail
  - Processes might crash without knowing why
  - Nondeterministic issues (packet delays, timing)

If a program can run on a single computer, keep it that way and keep things as simple as you can

## Networking

- **Latency** - time until message arrives
  - same building/datacenter ~= 1 ms
  - intercontinental ~= 100 ms
- **Bandwidth** - data volume/time
  - 5G - 50-1000 Mbit/s

Messages are groups of network packets that get sent between two IP addresses

## Two Generals Problem

Network problem - two generals have to attack a city at the same time, so each only attacks if the other army attacks

1. General 1 always attacks even if no response is received from General 2 - risks attacking alone
2. General 1 waits to attack until a response is received from General 2 - General 2 is now uncertain whether that response arrived

> It's impossible to reach certainty by exchanging any finite number of messages over an unreliable network. There's no way for one node to have certainty about the state of another node except through communication

e.g. online shop should only ship goods if and only if a payment is made

- shop would rather charge customer and not ship physical goods than ship physical goods without customer making payment
  - faster to send refund than to ship back goods

## Byzantine Generals Problem

Node behavior problem - 3 or more generals have to agree to attack a city

- Assume messaging is reliable unlike the two generals problem
- Some generals are traitors that modify the messages they pass on to trick other generals
- Honest generals don't know who the lying ones are and lying generals can collude

> With f malicious generals, the problem can only be solved with **3f + 1** generals in total, so less than 1/3 of the generals can be malicious

Digital signatures help but the problem is still hard

## System Models

Capture network (message loss), node (crashes), and timing (latency) behavior. Assume bidirectional point to point communication between nodes

### Network Models (strongest to weakest)

1. **Reliable (perfect) links** - message is received if and only if it is sent. Messages may be reordered
2. **Fair-loss links** - messages may be lost, duplicated, reordered. If you keep retrying, message eventually gets through
3. **Arbitrary (active adversary) links** - malicious adversary interferes with messages (eavesdrop, modify, drop, spoof, replay packets)

**Network partition** - some links dropping/delaying all messages for an extended period of time

Can convert one of these assumptions into another:

- fair-loss link + retry + dedup -> reliable link
- arbitrary link + TLS -> fair-loss link (TLS stops tampering and spoofing but an adversary can still drop messages)

### Node Models

1. **Crash stop** - if node crashes, it's dead forever (e.g. hardware failures)
2. **Crash recovery** - nodes may crash and recover but lose their in memory state (data on disk survives)
3. **Byzantine** - faulty node deviates from the algorithm while possibly pretending to look honest

### Timing Models

1. **Synchronous** - message latency and node execution speed have a known upper bound
2. **Partially synchronous** - system is asynchronous for some finite (but unknown) periods of time, synchronous otherwise
3. **Asynchronous** - no timing assumptions at all

Network latency causes:

1. Message loss requiring retry
2. Congestion/contention causing queuing
3. Network/route reconfiguration

Node pauses:

- OS scheduling issues, priority inversion
- Garbage collection pauses (can be minutes for large heaps)
- Page faults, swaps, thrashing

## Time

Used for schedulers, timeouts, failure detectors, retry timers, profiling performance, logging events, cache TTL, order of events, certificate validity

- **Physical clock** - count seconds elapsed
- **Logical clock** - event counter

Computers use an oscillator circuit with a quartz crystal that resonates at a known frequency to count elapsed time

- Quartz clock error (drift) is measured in ppm (most computers < 50 ppm)
- Atomic clocks and GPS satellites provide much more accurate clocks

### UTC

UTC - coordinated universal time - atomic time with corrections to account for Earth's rotation

- **Leap seconds** - extra second added/removed on June 30th or December 31st at 23:59:59 UTC depending on the Earth's rotation speed
  - Negative leap second - clock skips 23:59:59 and goes from 23:59:58 straight to 00:00:00
  - No leap second - clock moves from 23:59:59 to 00:00:00 after one second
  - Positive leap second - clock moves to 23:59:60 after one second then to 00:00:00 after one further second
- Software finds it hard to deal with leap seconds, so some systems smear the leap second over the course of a day

Timestamps are either:

1. **UNIX time** - number of seconds since the epoch Jan 1, 1970 00:00:00 UTC, ignoring leap seconds
2. **ISO 8601** - date and time with an offset relative to UTC e.g. `2026-08-23T08:23:50+00:00`

Can convert between the two using the Gregorian calendar

### Clock Skew and NTP

- **Clock drift** - quartz clock error gradually increases over time
- **Clock skew** - difference between two clocks at a point in time
  - in async/partially sync networks it's impossible to reduce clock skew to 0

**NTP (network time protocol)** - clients query a server which has an accurate clock (atomic/GPS)

- Stratum 0: atomic clock or GPS receiver
- Stratum 1: synced with Stratum 0
- Stratum 2: syncs with Stratum 1

Estimating skew from one request/response:

- Round trip time = total time client waited minus the server's processing time
- Estimated server time when client gets the response = time server sent the response + half the round trip time (assumes request and response latency are the same)
- Estimated clock skew = estimated server time - time client got the response

After estimating the skew:

- if skew < 125 ms, client slightly speeds up or slows down its clock rate until it matches the server via **slewing**
- if 125 ms <= skew < 1000 s, reset client clock to server timestamp via **stepping**
- if skew >= 1000 s, NTP does nothing and leaves it for a human operator to fix

Time of day clocks can be moved backward by stepping, so subtracting start from end time could result in negative elapsed time

> Use monotonic clocks to measure elapsed time so NTP stepping doesn't affect it (slewing is okay). Monotonic clock values are meaningless across nodes, so use time of day clocks for timestamps that are compared between nodes

e.g. Python uses monotonic clocks for `time.monotonic()` / `time.monotonic_ns()`

## Ordering Events

Delays can mess up the ordering of messages, and physical timestamps may be inconsistent with causality

**Happens-before relation** - a happens before b: `a -> b`

- **Event** - something happening at one node (sending, receiving, local execution step)
- Each node has a strict total order of the events that happened on it (each thread is a separate node)
- Messages are unique
- `a -> b` if a happened before b on the same node, a is the send and b is the receive of the same message, or transitively through another event
- Partial order - concurrent events `a || b` where neither happened before the other

**Causality** - a might have caused b if `a -> b`, but a can't have caused b if `a || b`

### Lamport Clocks

Attach timestamps to events in the system to capture the order of events

- Each node has its own counter t initialized to 0
- For every local event on a node, increment t
- Pair each sent message with the current timestamp t
- On receiving a message with timestamp t', set **t = max(t, t') + 1**

Guarantees if `a -> b` then a's timestamp is smaller than b's, but the inverse isn't necessarily true (because they could have been concurrent)

Events can have the same timestamp, so to make timestamps unique you pair the timestamp with the node name

> Lamport timestamps define a total order (any event can be ordered one after the other) consistent with causality in a cheap way, but you can't tell from them whether two events were concurrent

### Vector Clocks

Can also tell which events are concurrent

- Track a vector of the number of events that have occurred on each node
  - e.g. `<2, 0, 2>` represents first 2 events on Node A, no events on Node B, first 2 events on Node C
- Every node's vector initialized to 0's
- On each local event, increment the node's own entry
- On each sent message, attach the vector timestamp T
- On receiving a message, merge the message's vector into the local vector by picking the largest element of each entry, then increment the node's own entry

Vector timestamps exactly reflect causality in both directions: `T(a) < T(b)` if and only if `a -> b`, and if neither vector is less than or equal to the other then `a || b`

**Comparison:**

> Use Lamport clocks when you need to order logs, break ties, or timestamp events with a total order
>
> Use vector clocks when you need to detect conflicting, concurrent writes to the same data
>
> Vector clocks cost O(n) memory per timestamp for n nodes instead of O(1) for Lamport clocks

**Hybrid logical clocks (HLC)** - modern databases use a hybrid **(physical time, logical counter)** timestamp to avoid the memory overhead of vector clocks while still keeping Lamport clock causality

- If the sender's message has a later timestamp, the receiver adopts that physical time into its HLC timestamp and bumps the logical counter instead of changing its actual system clock
- e.g. CockroachDB uses HLC timestamps to decide transaction ordering across nodes, so causally related transactions (one reads what the other wrote) are ordered correctly without paying vector clocks' O(n) metadata tax. It still relies on clocks staying within a configured max offset (500 ms by default) to handle transactions that aren't causally connected

## Broadcast

Broadcasting is one node sending a message to all nodes in a group. If one node is faulty, the remaining nodes carry on

Reliable broadcast ordering guarantees:

1. **FIFO broadcast** - if 2 messages are broadcast by the same node, they're delivered in the order they were sent to every node including the sender. Messages sent by different nodes can be delivered in any order
   - attach a per-sender sequence number to each message and buffer messages that arrive early until the earlier ones are delivered
2. **Causal broadcast** - if one broadcast message happened before another, every node delivers it first. Concurrent messages can be delivered in any order
   - same as FIFO but attach a vector of how many messages from each node the sender had delivered, and wait until those dependencies are delivered
3. **Total order broadcast** - if one message is delivered before another on one node, it must also be delivered before it on all nodes
   - Single leader (sequencer) - send every message to a leader which broadcasts them via FIFO broadcast
     - If leader crashes, system stops delivering messages
   - Attach a Lamport clock to each message and deliver messages in total order of timestamps
     - Must wait until you've received a message with a higher timestamp from every node, so if one node crashes, system stops
4. **FIFO total order broadcast** - FIFO + total order broadcast
   - Equivalent to consensus
   - Use it to build a replication log where each replica rebuilds its state by replaying the log

Broadcast algorithms:

1. Broadcasting node sends the message directly to every other node with retries
   - node may crash before all messages are delivered
2. **Eager reliable broadcast** - when a node receives a broadcast for the first time, it re-broadcasts it to every other n-1 nodes
   - Ensures if a node crashes, every node still gets the message
   - Expensive O(n^2) messages for n nodes since a message is sent for every pair
3. **Gossip protocols** - when a node receives a message for the first time, it forwards it to a small fixed number of random nodes (e.g. 3)
   - Eventually reaches all nodes with high probability
