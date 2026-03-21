"""
Complexity Analysis and Comparison: Paxos vs Raft

This script analyzes and compares the implementation complexity of Paxos and Raft
consensus algorithms to help determine which to use for cloud systems.
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Tuple


class CodeComplexityAnalyzer:
    """Analyze code complexity metrics"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'r') as f:
            self.content = f.read()
        self.tree = ast.parse(self.content)
    
    def count_lines(self) -> Dict[str, int]:
        """Count different types of lines"""
        lines = self.content.split('\n')
        
        total = len(lines)
        blank = sum(1 for line in lines if not line.strip())
        comments = sum(1 for line in lines if line.strip().startswith('#'))
        docstrings = self.content.count('"""') // 2 * 3
        
        code = total - blank - comments
        
        return {
            'total': total,
            'code': code,
            'blank': blank,
            'comments': comments,
            'documentation': docstrings
        }
    
    def count_classes(self) -> int:
        """Count number of classes"""
        return sum(1 for node in ast.walk(self.tree) if isinstance(node, ast.ClassDef))
    
    def count_functions(self) -> int:
        """Count number of functions/methods"""
        return sum(1 for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef))
    
    def count_methods_per_class(self) -> Dict[str, int]:
        """Count methods in each class"""
        methods = {}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for item in node.body if isinstance(item, ast.FunctionDef))
                methods[node.name] = method_count
        return methods
    
    def measure_cyclomatic_complexity(self) -> int:
        """Rough cyclomatic complexity (count decision points)"""
        complexity = 1
        
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def count_message_types(self) -> int:
        """Count number of message types defined"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and 'MessageType' in node.name:
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        return len(node.body)
        return 0
    
    def count_states(self) -> int:
        """Count number of node states"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and 'State' in node.name:
                return len([item for item in node.body if isinstance(item, ast.Assign)])
        return 0
    
    def analyze(self) -> Dict:
        """Run complete analysis"""
        lines = self.count_lines()
        methods = self.count_methods_per_class()
        
        return {
            'file': os.path.basename(self.filepath),
            'lines': lines,
            'classes': self.count_classes(),
            'functions': self.count_functions(),
            'methods_per_class': methods,
            'cyclomatic_complexity': self.measure_cyclomatic_complexity(),
            'message_types': self.count_message_types(),
            'states': self.count_states()
        }


def compare_algorithms():
    """
    Compare Paxos and Raft implementations
    """
    print("=" * 80)
    print("PAXOS vs RAFT: COMPLEXITY COMPARISON ANALYSIS")
    print("=" * 80)
    
    base_path = Path(__file__).parent
    paxos_path = base_path / 'paxos' / 'paxos_basic.py'
    raft_path = base_path / 'raft' / 'raft_basic.py'
    
    paxos_analyzer = CodeComplexityAnalyzer(str(paxos_path))
    raft_analyzer = CodeComplexityAnalyzer(str(raft_path))
    
    paxos_metrics = paxos_analyzer.analyze()
    raft_metrics = raft_analyzer.analyze()
    
    print("\n" + "=" * 80)
    print("1. CODE SIZE COMPARISON")
    print("=" * 80)
    
    print("\n{:<30} {:>20} {:>20}".format("Metric", "Paxos", "Raft"))
    print("-" * 80)
    print("{:<30} {:>20} {:>20}".format(
        "Total Lines",
        paxos_metrics['lines']['total'],
        raft_metrics['lines']['total']
    ))
    print("{:<30} {:>20} {:>20}".format(
        "Code Lines (excl. blank/doc)",
        paxos_metrics['lines']['code'],
        raft_metrics['lines']['code']
    ))
    print("{:<30} {:>20} {:>20}".format(
        "Documentation Lines",
        paxos_metrics['lines']['documentation'],
        raft_metrics['lines']['documentation']
    ))
    print("{:<30} {:>20} {:>20}".format(
        "Blank Lines",
        paxos_metrics['lines']['blank'],
        raft_metrics['lines']['blank']
    ))
    
    print("\n" + "=" * 80)
    print("2. STRUCTURAL COMPLEXITY")
    print("=" * 80)
    
    print("\n{:<30} {:>20} {:>20}".format("Metric", "Paxos", "Raft"))
    print("-" * 80)
    print("{:<30} {:>20} {:>20}".format(
        "Number of Classes",
        paxos_metrics['classes'],
        raft_metrics['classes']
    ))
    print("{:<30} {:>20} {:>20}".format(
        "Number of Functions/Methods",
        paxos_metrics['functions'],
        raft_metrics['functions']
    ))
    print("{:<30} {:>20} {:>20}".format(
        "Message Types",
        paxos_metrics['message_types'],
        raft_metrics['message_types']
    ))
    print("{:<30} {:>20} {:>20}".format(
        "Node States",
        paxos_metrics['states'],
        raft_metrics['states']
    ))
    
    print("\n" + "=" * 80)
    print("3. METHODS PER CLASS")
    print("=" * 80)
    
    print("\nPaxos Classes:")
    for cls, count in paxos_metrics['methods_per_class'].items():
        print(f"  {cls:<30} {count:>3} methods")
    
    print("\nRaft Classes:")
    for cls, count in raft_metrics['methods_per_class'].items():
        print(f"  {cls:<30} {count:>3} methods")
    
    print("\n" + "=" * 80)
    print("4. CYCLOMATIC COMPLEXITY")
    print("=" * 80)
    
    print("\n{:<30} {:>20} {:>20}".format("Metric", "Paxos", "Raft"))
    print("-" * 80)
    print("{:<30} {:>20} {:>20}".format(
        "Decision Points",
        paxos_metrics['cyclomatic_complexity'],
        raft_metrics['cyclomatic_complexity']
    ))
    
    complexity_ratio = raft_metrics['cyclomatic_complexity'] / paxos_metrics['cyclomatic_complexity']
    print(f"\nRaft has {complexity_ratio:.2f}x more decision points than Paxos")
    
    print("\n" + "=" * 80)
    print("5. KEY DIFFERENCES ANALYSIS")
    print("=" * 80)
    
    print("""
PAXOS:
------
[+] Simpler conceptual model (propose-promise-accept)
[+] Fewer states to manage (no explicit leader state)
[+] More flexible (no strong leader requirement)
[-] Harder to understand in practice
[-] Requires additional mechanisms for multi-decree consensus
[-] No built-in log structure
[-] More complex to implement correctly in production

RAFT:
-----
[+] Easier to understand (clear leader election, log replication)
[+] Built-in log structure and state machine replication
[+] Better defined membership changes
[+] More practical for real-world systems
[+] Clearer separation of concerns (election, replication, safety)
[-] More code due to comprehensive features
[-] More states to manage
[-] Slightly higher message overhead
    """)
    
    print("\n" + "=" * 80)
    print("6. PROTOCOL PHASES COMPARISON")
    print("=" * 80)
    
    print("""
PAXOS PHASES:
1. Phase 1a: Proposer sends PREPARE(n)
2. Phase 1b: Acceptors respond with PROMISE
3. Phase 2a: Proposer sends ACCEPT(n, value)
4. Phase 2b: Acceptors respond with ACCEPTED
Total: 4 message types, 2 phases

RAFT PHASES:
1. Leader Election: RequestVote + VoteResponse
2. Log Replication: AppendEntries + AppendResponse
3. Commitment: Implicit through majority replication
Total: 4 message types, but clearer purpose for each
    """)
    
    print("\n" + "=" * 80)
    print("7. RECOMMENDATION FOR CLOUD SYSTEMS")
    print("=" * 80)
    
    print("""
RECOMMENDATION: RAFT

Reasons:
--------
1. UNDERSTANDABILITY
   - Raft was explicitly designed to be understandable
   - Easier for team members to learn and maintain
   - Better documentation and learning resources
   
2. PRACTICAL FEATURES
   - Built-in log replication (essential for state machines)
   - Clear leader election with timeouts
   - Better handling of membership changes
   - Snapshot support for log compaction
   
3. INDUSTRY ADOPTION
   - Used in production systems: etcd, Consul, CockroachDB
   - More examples and libraries available
   - Better tooling and debugging support
   
4. IMPLEMENTATION COMPLEXITY
   - While Raft has more code, it's more structured
   - Clearer error handling and edge cases
   - Better defined correctness properties
   
5. PERFORMANCE
   - Similar performance to Multi-Paxos
   - More efficient log replication
   - Better batching opportunities

When to consider Paxos:
-----------------------
- Academic research projects
- When you need extreme flexibility in consensus
- When implementing custom variants (Fast Paxos, EPaxos)
- When you have deep expertise in Paxos already

For cloud systems, distributed databases, and production use:
Choose RAFT for better maintainability and team productivity.
    """)
    
    print("\n" + "=" * 80)
    print("8. NEXT STEPS")
    print("=" * 80)
    
    print("""
To implement Raft in your cloud system:

1. Use existing libraries:
   - Go: hashicorp/raft (most mature)
   - Python: pysyncobj, rafter
   - Java: Apache Ratis, Atomix
   - Rust: tikv/raft-rs

2. Consider managed services:
   - etcd (Raft-based key-value store)
   - Consul (service mesh with Raft)
   - CockroachDB (Raft-based SQL)

3. Key implementation considerations:
   - Proper election timeout tuning
   - Network partition handling
   - Log compaction strategy
   - Membership change procedures
   - Monitoring and observability
    """)
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    compare_algorithms()
