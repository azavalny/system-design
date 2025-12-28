# filename: distributed_sharding_batched.py

from bplustree import BPlusTree
import time
import random
from multiprocessing import Process, Queue

# ---------------------------------------------------------
# Worker process: maintains one shard
# ---------------------------------------------------------
def shard_worker(insert_queue: Queue, query_queue: Queue):
    tree = BPlusTree(order=4)

    # Process batched insert tasks
    while True:
        task = insert_queue.get() 
        if task == "DONE_INSERT":
            break
        # task is a list of (key, value) tuples
        for k, v in task:
            tree.insert(k, v)

    # Process batched query tasks
    while True:
        task = query_queue.get()
        if task == "DONE_QUERY":
            break
        # task is a list of keys to search
        results = [tree.search(k) for k in task]
     

# ---------------------------------------------------------
# Generate test data
# ---------------------------------------------------------
def generate_test_data(N=1000000):
    keys = list(range(1, N + 1))
    random.shuffle(keys)
    values = [str(k) for k in keys]
    return keys, values

# ---------------------------------------------------------
# Single-Tree Experiment
# ---------------------------------------------------------
def run_single_tree_experiment(keys, values, query_keys):
    tree = BPlusTree(order=4) #shard

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
# Distributed Sharded Experiment (batched)
# ---------------------------------------------------------
def run_distributed_sharded_experiment(keys, values, query_keys, num_shards=3):
    insert_queues = [Queue() for _ in range(num_shards)]
    query_queues = [Queue() for _ in range(num_shards)]


    # Launch shard processes
    processes = []
    for i in range(num_shards):
        p = Process(target=shard_worker, args=(insert_queues[i], query_queues[i]))
        p.start()
        processes.append(p)

    t1 = time.time()
    # Partition data into shards
    shard_kvs = [[] for _ in range(num_shards)]  #[[(key1, val1)], [(key2, val2)], []]
    for k, v in zip(keys, values):
        shard_kvs[k % num_shards].append((k, v))

    # ---------------- Batched Inserts ----------------
    
    for i in range(num_shards): #1
        insert_queues[i].put(shard_kvs[i])       # send entire shard as batch
        insert_queues[i].put("DONE_INSERT")

    # Partition query keys into shards
    shard_queries = [[] for _ in range(num_shards)] #[[5, 6, 7], [9, 10], []]
    for k in query_keys:
        shard_queries[k % num_shards].append(k) #5, shard 2
    #[1, 2, 3, 4, 5] keys
    #number of shards  = 3
    #shard 1 = [1, 4]
    #shard 2 = [2]
    #shard 3 = []

    #1 % 3 = 1
    #2 % 3 = 2
    #4%3= 1
    #[ [[1, 4] [] [] ] 

    # ---------------- Batched Queries ----------------
    for i in range(num_shards):
        query_queues[i].put(shard_queries[i])   # send all queries as batch
        query_queues[i].put("DONE_QUERY")
   
   

    # Join processes
    for p in processes:
        p.join()
    t4 = time.time()
    return {
        "total_time": t4 - t1,
    }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    N = 1000000  # total keys
    keys, values = generate_test_data(N)
    query_keys = random.sample(keys, 1000)

    # ---------------- Single-Tree ----------------
    print("Running single-tree experiment...")
    single = run_single_tree_experiment(keys, values, query_keys)
    print(f"Single-tree insert time: {single['insert_time']:.6f} sec")
    print(f"Single-tree search time: {single['search_time']:.6f} sec")

    # --------------- Distributed Sharded ----------------
    print("\nRunning distributed sharded experiment (batched)...")
    distributed = run_distributed_sharded_experiment(keys, values, query_keys, num_shards=3)
    print(f"Distributed sharded total time: {distributed['total_time']:.6f} sec")


