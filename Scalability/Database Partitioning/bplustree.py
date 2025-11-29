"""
bplustree.py
Minimal educational B+ Tree skeleton for integers (keys) and arbitrary values.
Designed to be implemented step-by-step:
  - Phase A: search & range_scan
  - Phase B: simple insert into leaf without splits
  - Phase C: implement leaf split + promotion
  - Phase D: implement internal node split + propagation
No deletion, no persistence, single-threaded.
"""
import math
from typing import List, Optional, Any, Tuple



class Node:
    def __init__(self, order: int, is_leaf: bool = False):
        self.order = order
        self.is_leaf = is_leaf
        self.keys: List[int] = [] # sorted list of keys
        # children: for internal nodes -> list of Node
        # for leaf nodes we use `values` instead of children
        self.children = []
        self.parent = None

    def __repr__(self):
        t = "Leaf" if self.is_leaf else "Internal"
        return f"<{t} keys={self.keys}>"


class LeafNode(Node):
    def __init__(self, order: int):
        super().__init__(order, is_leaf=True)
        self.values: List[Any] = []           # parallel to keys
        self.next_leaf: Optional["LeafNode"] = None  # linked list to next leaf

    def insert_into_leaf(self, key: int, value: Any):
        """Insert key,value into this leaf (no splitting here)."""
        # Find position to insert to keep keys sorted
        i = 0
        while i < len(self.keys) and self.keys[i] < key:
            i += 1
        if i < len(self.keys) and self.keys[i] == key:
            # Replace existing value for simplicity (no duplicates)
            self.values[i] = value
        else:
            self.keys.insert(i, key)
            self.values.insert(i, value)


class InternalNode(Node):
    def __init__(self, order: int):
        super().__init__(order, is_leaf=False)
        # internal node: keys separate child ranges, children length = len(keys)+1


class BPlusTree:
    def __init__(self, order: int = 4):
        assert order >= 3, "order should be >= 3"
        self.order = order
        self.root: Node = LeafNode(order)

    # ----------------------
    # Search helpers
    # ----------------------
    def find_leaf(self, key: int) -> LeafNode:
        """Traverse from root to find leaf node that should contain `key`."""
        node = self.root
        while not node.is_leaf:
            internal: InternalNode = node  # type: ignore
            # choose child index
            i = 0
            while i < len(internal.keys) and key >= internal.keys[i]:
                i += 1
            node = internal.children[i]
        return node  # type: ignore

    def search(self, key: int) -> Optional[Any]:
        leaf = self.find_leaf(key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                return leaf.values[i]
        return None

    def range_query(self, lo: int, hi: int) -> List[Tuple[int, Any]]:
        """Return list of (key,value) for lo <= key <= hi."""
        results: List[Tuple[int, Any]] = []
        leaf = self.find_leaf(lo)
        # scan from found leaf, through linked leaves, until hi exceeded
        while leaf is not None:
            for k, v in zip(leaf.keys, leaf.values):
                if k < lo:
                    continue
                if k > hi:
                    return results
                results.append((k, v))
            leaf = leaf.next_leaf
        return results

    # ----------------------
    # Insertion (skeleton)
    # ----------------------
    def insert(self, key: int, value: Any):
        """
        High-level insert:
          1. find leaf
          2. insert into leaf (or replace)
          3. if leaf overflows -> split leaf and propagate up
        We'll implement split helpers below.
        """
        leaf = self.find_leaf(key)
        leaf.insert_into_leaf(key, value)

        if len(leaf.keys) > (self.order - 1):  # node capacity exceeded
            self._split_leaf(leaf)

    def _split_leaf(self, leaf: LeafNode):
        """
        Split a leaf node into two leaves.
        Steps:
          - create new_leaf
          - move half of keys+values to new_leaf
          - fix linked list pointers
          - if leaf has no parent -> create new root
          - otherwise insert promoted key into parent
        """
        # Steps to implement:
        # 1) Compute split point: mid = ceil(order/2)
        # 2) create new_leaf and move keys/values from mid onwards
        # 3) set new_leaf.next_leaf = leaf.next_leaf; leaf.next_leaf = new_leaf
        # 4) set parents
        # 5) promote first key of new_leaf up into parent (as separator)
        split = math.ceil(self.order/2)
        new_leaf = LeafNode(self.order)

        new_leaf.keys = leaf.keys[split:]
        new_leaf.values = leaf.values[split:]

        leaf.keys = leaf.keys[:split]
        leaf.values = leaf.values[:split]

        new_leaf.next_leaf = leaf.next_leaf
        leaf.next_leaf = new_leaf
        
        if leaf.parent is None:
            new_root = InternalNode(self.order)
            new_root.keys = [new_leaf.keys[0]]
            new_root.children = [leaf, new_leaf]
            leaf.parent = new_root
            new_leaf.parent = new_root
            self.root = new_root
        
        else:
            new_leaf.parent = leaf.parent
            self._insert_in_parent(leaf, new_leaf.keys[0], new_leaf)


    def _insert_in_parent(self, left: Node, key: int, right: Node):
        """
        Insert `key` and `right` child into parent of `left`.
        If parent overflows, perform internal split.
        """
        # insert key into parent.keys at correct position and insert right into children list
        # If parent is over capacity -> call _split_internal

        parent = left.parent

        # Case 1: left has no parent -> create new root
        if parent is None:
            new_root = InternalNode(self.order)
            new_root.keys = [key]
            new_root.children = [left, right]
            left.parent = new_root
            right.parent = new_root
            self.root = new_root
            return
        
        parent = left.parent
        index = 0
        while index < len(parent.keys) and parent.keys[index] < key:
            index += 1
        
        parent.keys.insert(index, key)

        parent.children.insert(index + 1, right)
        right.parent = parent
        if len(parent.keys) > (self.order-1):
            self._split_internal(parent)
    
        

    def _split_internal(self, internal: InternalNode):
        """
        Split an internal node.
        Steps:
        - choose mid key to promote
        - left keeps keys[:mid], children[:mid+1]
        - right gets keys[mid+1:], children[mid+1:]
        - promoted key is internal.keys[mid]
        - call _insert_in_parent on left, promoted_key, right
        """
        split = math.ceil(self.order/2)-1
        promoted_key = internal.keys[split]


        left = internal
        left.keys = left[:split]
        left.children = left.children[:split+1]

        right = InternalNode(self.order)
        right.keys = internal.keys[split+1:]
        right.children = internal.children[split+1:]

        for child in right.children:
            child.parent = right

        self._insert_in_parent(left, promoted_key, right)



    # ----------------------
    # Utility / Debug
    # ----------------------
    def print_tree(self):
        """Print tree level-by-level (BFS) for debugging."""
        q = [self.root]
        level = 0
        while q:
            next_q = []
            print(f"Level {level}:", end=" ")
            for n in q:
                print(n, end=" | ")
                if not n.is_leaf:
                    next_q.extend(n.children)
            print()
            q = next_q
            level += 1

    def debug_leaves(self):
        """Print all leaves via linked list (in-order)."""
        # find leftmost leaf
        node = self.root
        while not node.is_leaf:
            node = node.children[0]
        leaf: LeafNode = node  # type: ignore
        idx = 0
        while leaf is not None:
            print(f"Leaf {idx}: keys={leaf.keys}")
            leaf = leaf.next_leaf
            idx += 1

    


# -------------------------
# Quick demo (minimal)
# -------------------------
if __name__ == "__main__":
    tree = BPlusTree(order=4)
    items = [(5, "a"), (15, "b"), (25, "c"), (35, "d"), (45, "e"), (55, "f")]
    for k, v in items:
        tree.insert(k, v)

    print("Tree structure:")
    tree.print_tree()
    print("\nLeaves:")
    tree.debug_leaves()
    print("\nSearch 25 ->", tree.search(25))
    print("Range 10..40 ->", tree.range_query(10, 40))




