from bplustree import BPlusTree
import time
import random
from multiprocessing import Process, Queue

# ---------------------------------------------------------
# Worker process: maintains one shard
# ---------------------------------------------------------
def shard_worker(insert_queue: Queue, query_queue: Queue):
    tree = BPlusTree(order=4)
    
    # Process insert tasks
    while True:
        task = insert_queue.get()
        if task == "DONE_INSERT":
            break
        key, value = task
        tree.insert(key, value)
    
    # Process search tasks
    while True:
        query = query_queue.get()
        if query == "DONE_QUERY":
            break
        results = []
        for key in query:
            results.append(tree.search(key))
    
    


# ---------------------------------------------------------
# Generate test data
# ---------------------------------------------------------
def generate_test_data(N=1000000):
    keys = list(range(1, N + 1))
    random.shuffle(keys)
    values = [str(k) for k in keys]
    return keys, values

# ---------------------------------------------------------
# Single-Tree Experiment (one B+ tree)
# ---------------------------------------------------------
def run_single_tree_experiment(keys, values, query_keys):
    tree = BPlusTree(order=4)

    # Insert timing
    t1 = time.time()
    for k, v in zip(keys, values):
        tree.insert(k, v)
    t2 = time.time()

    # Search timing
    t3 = time.time()
    for k in query_keys:
        tree.search(k)
    t4 = time.time()

    return {
        "insert_time": t2 - t1,
        "search_time": t4 - t3,
    }

# ---------------------------------------------------------
# Distributed Sharded Experiment
# ---------------------------------------------------------
def run_distributed_sharded_experiment(keys, values, query_keys, num_shards=3):
    insert_queues = [Queue() for _ in range(num_shards)] #keys to insert
    query_queues = [Queue() for _ in range(num_shards)] #keys to search


    # Launch shard processes with EMPTY queues. each shard gets an empty queuue
    processes = []
    for i in range(num_shards):
        p = Process(target=shard_worker, args=(insert_queues[i], query_queues[i]))
        p.start()
        processes.append(p)


    
    # Partition data for each shard
    t1 = time.time()
    shard_kvs = [[] for _ in range(num_shards)]
    for k, v in zip(keys, values):
        shard_kvs[k % num_shards].append((k, v))

    # Send inserts
    
    for i in range(num_shards): #we pass inserts of each shard in shard queue
        for kv in shard_kvs[i]:
            insert_queues[i].put(kv)
        insert_queues[i].put("DONE_INSERT")
    t2 = time.time()

    t3 = time.time()
    # Partition query keys for each shard
    shard_queries = [[] for _ in range(num_shards)]
    for k in query_keys:
        shard_queries[k % num_shards].append(k)

    # Send queries
    for i in range(num_shards):
        query_queues[i].put(shard_queries[i])
        query_queues[i].put("DONE_QUERY")
    

    t4 = time.time()

    # Join processes
    for p in processes:
        p.join()

    return {
        "insert_time": t2 - t1,
        "search_time": t4 - t3,
    }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    N = 1000000  # number of keys
    keys, values = generate_test_data(N)
    query_keys = random.sample(keys, 1000)

    # ---------------- Single-Tree ----------------
    print("Running single-tree experiment...")
    single = run_single_tree_experiment(keys, values, query_keys)
    print(f"Single-tree insert time: {single['insert_time']:.6f} sec")
    print(f"Single-tree search time: {single['search_time']:.6f} sec")

    # --------------- Distributed Sharded ----------------
    print("\nRunning distributed sharded experiment...")
    distributed = run_distributed_sharded_experiment(keys, values, query_keys, num_shards=3)
    print(f"Distributed sharded insert time: {distributed['insert_time']:.6f} sec")
    print(f"Distributed sharded search time: {distributed['search_time']:.6f} sec")


