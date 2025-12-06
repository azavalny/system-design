from bplustree import BPlusTree

#create shards
shard1 = BPlusTree(order=4)
shard2 =  BPlusTree(order=4)
shard3 =  BPlusTree(order=4)
shards = [shard1, shard2, shard3]

#find shard and insert in btree of shard
def insert_sharded(key, value):
    shard_index = key % len(shards)
    shards[shard_index].insert(key, value)

def search_sharded(key):
    shard_index = key % len(shards)
    return shards[shard_index].search(key)
    


def range_query_sharded(start, end):
    results = []
    for shard in shards:
        results.extend(shard.range_query(start, end)) #[(key, val)]
    
    results.sort(key=lambda x:x[0])
    return results


items = [(5, "a"), (15, "b"), (25, "c"), (35, "d"),
         (45, "e"), (55, "f"), (65, "g"), (75, "h")]

for k, v in items:
    insert_sharded(k, v)


print("Point query 25 ->", search_sharded(25))
print("Point query 55 ->", search_sharded(55))

print("Range query 10..60 ->", range_query_sharded(10, 60))

# -----------------------
# Optional: Inspect shards
# -----------------------
for i, shard in enumerate(shards):
    print(f"\nShard {i} structure:")
    shard.print_tree()
    print(f"Shard {i} leaves:")
    shard.debug_leaves()