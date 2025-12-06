# filename: range_sharding_batched.py

from bplustree import BPlusTree
import time
import random
from multiprocessing import Process, Queue

# ---------------------------------------------------------
# Worker process: maintains one shard
# ---------------------------------------------------------
def shard_worker(insert_queue: Queue, query_queue: Queue):
    tree = BPlusTree(order=4)

    # Process batched inserts
    while True:
        task = insert_queue.get()
        if task == "DONE_INSERT":
            break
        # task is a list of (key, value) tuples
        for k, v in task:
            tree.insert(k, v)

    # Process batched range queries
    while True:
        task = query_queue.get()
        if task == "DONE_QUERY":
            break
        # task is a list of (lo, hi) tuples for this shard
        for lo, hi in task:
            tree.range_query(lo, hi)

# ---------------------------------------------------------
# Generate test data
# ---------------------------------------------------------
def generate_test_data(N=1000000):
    keys = list(range(1, N + 1))
    random.shuffle(keys)
    values = [str(k) for k in keys]
    return keys, values

# ---------------------------------------------------------
# Single-Tree Experiment with Range Queries
# ---------------------------------------------------------
def run_single_tree_range(keys, values, query_ranges):
    tree = BPlusTree(order=4)

    t1 = time.time()
    for k, v in zip(keys, values):
        tree.insert(k, v)
    t2 = time.time()

    t3 = time.time()
    for lo, hi in query_ranges:
        tree.range_query(lo, hi)
    t4 = time.time()

    return {"insert_time": t2 - t1, "range_query_time": t4 - t3}

# ---------------------------------------------------------
# Multi-Shard Experiment with Batched Range-Based Sharding
# ---------------------------------------------------------
def run_range_sharded_experiment(keys, values, query_ranges, num_shards=3):
    insert_queues = [Queue() for _ in range(num_shards)]
    query_queues = [Queue() for _ in range(num_shards)]

    # Launch shard processes
    processes = []
    for i in range(num_shards):
        p = Process(target=shard_worker, args=(insert_queues[i], query_queues[i]))
        p.start()
        processes.append(p)

    # Determine shard ranges
    sorted_keys = sorted(keys)
    shard_ranges = []
    shard_size = len(keys) // num_shards
    for i in range(num_shards):
        lo = sorted_keys[i * shard_size]
        hi = sorted_keys[(i + 1) * shard_size - 1] if i < num_shards - 1 else sorted_keys[-1]
        shard_ranges.append((lo, hi))

    t1 = time.time()
    # Partition keys into shards
    shard_kvs = [[] for _ in range(num_shards)]
    for k, v in zip(keys, values):
        for i, (lo, hi) in enumerate(shard_ranges):
            if lo <= k <= hi:
                shard_kvs[i].append((k, v))
                break

    
    # Send batched inserts
    for i in range(num_shards):
        insert_queues[i].put(shard_kvs[i])
        insert_queues[i].put("DONE_INSERT")

    # Partition range queries per shard
    shard_query_batches = [[] for _ in range(num_shards)]
    for lo, hi in query_ranges:
        for i, (s_lo, s_hi) in enumerate(shard_ranges):
            if hi < s_lo or lo > s_hi:
                continue  # no overlap
            # clip query to shard range
            shard_query_batches[i].append((max(lo, s_lo), min(hi, s_hi)))

    # Send batched queries
    for i in range(num_shards):
        query_queues[i].put(shard_query_batches[i])
        query_queues[i].put("DONE_QUERY")

    # Join processes
    for p in processes:
        p.join()
    t2 = time.time()

    return {"total_time": t2 - t1, "shard_ranges": shard_ranges}

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    N = 1000000
    keys, values = generate_test_data(N)

    # Example: 100 random range queries of length ~1000 keys each
    query_ranges = []
    for _ in range(100):
        lo = random.randint(1, N - 1000)
        hi = lo + 1000
        query_ranges.append((lo, hi))

    # ---------------- Single-Tree ----------------
    print("Running single-tree range experiment...")
    single = run_single_tree_range(keys, values, query_ranges)
    print(f"Single-tree insert time: {single['insert_time']:.6f} sec")
    print(f"Single-tree range query time: {single['range_query_time']:.6f} sec")

    # ---------------- Range-Based Sharded ----------------
    print("\nRunning batched range-sharded experiment...")
    sharded = run_range_sharded_experiment(keys, values, query_ranges, num_shards=3)
    print(f"Batched range-sharded total time: {sharded['total_time']:.6f} sec")
    print("Shard key ranges:", sharded["shard_ranges"])
