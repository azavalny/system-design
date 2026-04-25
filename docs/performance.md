# Performance

How to think about responsiveness under load and where to optimize across network, memory, disk, and CPU.

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

![](../Performance/latency.png)

**Tail latency** is an important metric that measures 99th, 99.9th... response times to model how well your application handles peak load.

![](../Performance/amdahls_gunther_law.png)

**Amdahl's law** models concurrency speedup by using more threads. After an initial sharp speedup, you will notice diminishing returns because of the overhead of managing threads as well as CPU context switching.

**Gunther's law** extends Amdahl's law by taking into account coherence delay (caching of variables and syncing them across caches) and scaling dimension which gets slower to maintain as you add more threads.
