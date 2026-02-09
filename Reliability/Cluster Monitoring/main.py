from RAFT import Node
import queue

NUM_NODES = 4

all_queues = {i: queue.Queue() for i in range(1, NUM_NODES + 1)}
all_nodes = [Node(i, all_queues) for i in range(1, NUM_NODES + 1)]

def declare_default_leader(all_nodes):
    all_nodes[0].state = "leader" #declar first node as default leader
    all_nodes[0].leader_id = all_nodes[0].node_id


def spin_up_servers(all_nodes):
    declare_default_leader(all_nodes)
    for node in all_nodes:
        node.start()
        
def wait_for_servers_to_finish(all_nodes):
    for node in all_nodes:
        node.join()

if __name__ == "__main__":
    spin_up_servers(all_nodes)

    wait_for_servers_to_finish(all_nodes)
    