import os
import time
import tracemalloc
import unittest
from warnings import warn
from bsolver.arbre import Node, Var, TRUE, FALSE


# Helper builders, copied/adapted from test_perf_arbre.py
def build_deep_tree(depth: int) -> Node:
    node = TRUE
    for i in range(depth, 0, -1):
        node = node & Var(f"x{i}")
    return node


def build_wide_tree(width: int) -> Node:
    node = FALSE
    for i in range(1, width + 1):
        node = node | Var(f"y{i}")
    return node


def build_balanced_tree(depth: int) -> Node:
    def rec(level, idx):
        if level == 0:
            return Var(f"z{idx}")
        left = rec(level - 1, idx * 2)
        right = rec(level - 1, idx * 2 + 1)
        return left.and_(right)

    return rec(depth, 1)


def measure_memory(func):
    tracemalloc.start()
    t0 = time.perf_counter()
    func()
    t1 = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return (t1 - t0), current / 1024.0, peak / 1024.0


TEST_LEVEL = int(os.getenv("TEST_LEVEL", "1"))  # 1=basic, 2=extra, 3=extreme

class TestPerformance(unittest.TestCase):
    # Soft tolerance factors and hard limits
    SOFT_TIME_FACTOR = 2.5  # warn if > predicted * factor
    HARD_TIME_FACTOR = 6.0  # fail if > predicted * factor
    SOFT_MEM_FACTOR = 2.5
    HARD_MEM_FACTOR = 6.0
    MIN_TIME_BASELINE = 5e-4  # 0.5ms baseline to cover Python overhead

    def tearDown(self) -> None:
        # Clear cache
        Node.solutions.clear_cache()
        Node.hash.clear_cache()
        Node.fingerprint.clear_cache()
        return super().tearDown()

    def assert_perf(self, label: str, predicted_s: float, measured_s: float):
        # Clamp predicted to a minimal baseline to avoid negative/near-zero formula artifacts
        if predicted_s <= self.MIN_TIME_BASELINE:
            predicted_s = self.MIN_TIME_BASELINE
        msg = f"{label}: measured {measured_s:.6f}s vs predicted {predicted_s:.6f}s"
        if measured_s > predicted_s * self.HARD_TIME_FACTOR:
            self.fail("EXTREME slow: " + msg)
        elif measured_s > predicted_s * self.SOFT_TIME_FACTOR:
            warn("WARNING slow: " + msg)

    def assert_mem(self, label: str, predicted_kb: float, measured_kb: float):
        if predicted_kb <= 0:
            predicted_kb = 0.1
        msg = f"{label}: measured {measured_kb:.2f}KB vs predicted {predicted_kb:.2f}KB"
        if measured_kb > predicted_kb * self.HARD_MEM_FACTOR:
            self.fail("EXTREME memory: " + msg)
        elif measured_kb > predicted_kb * self.SOFT_MEM_FACTOR:
            warn("WARNING memory: " + msg)

    @unittest.skipUnless(TEST_LEVEL > 0, "Tests de performance désactivés")
    def test_simplify_time_linear_nodes(self):
        # Nouveau modèle (bench 2025-09):
        # T_simplify_deep(d) ≈ 1.93e-5 · d + 2.17e-4 (secondes)
        cases = [5, 10, 20, 40, 80, 160]
        if TEST_LEVEL < 2:
            cases = cases[:3]
        elif TEST_LEVEL < 3:
            cases = cases[:5]
        results = []
        for depth in cases:
            tree = build_deep_tree(depth)
            # approx node count (pour info seulement)
            n_nodes = 2 * depth + 1
            # prédiction (fonction du depth directement)
            predicted = 1.93e-5 * depth + 2.17e-4

            def op():
                _ = tree.simplify()

            t, curr_kb, peak_kb = measure_memory(op)
            self.assert_perf(f"simplify(deep d={depth})", predicted, t)
            results.append((depth, n_nodes, t, predicted, peak_kb))
        print("\n[Recap Simplify Deep]")
        print("Depth | Nodes | Time (s) | Pred (s) | Peak Mem (KB)")
        for depth, n_nodes, t, predicted, peak_kb in results:
            print(f"{depth:5d} | {n_nodes:5d} | {t:8.6f} | {predicted:8.6f} | {peak_kb:10.2f}")

    @unittest.skipUnless(TEST_LEVEL > 0, "Tests de performance désactivés")
    def test_solve_deep(self):
    # Nouveau modèle (bench 2025-09):
    # T_solve_deep(n) ≈ 1.85e-4·n + 8.8e-4 ; M_peak_deep(n) ≈ 2.2·n + 1.0 (KB)
        cases = [5, 10, 15, 20, 25, 50]
        if TEST_LEVEL < 2:
            cases = cases[:3]
        elif TEST_LEVEL < 3:
            cases = cases[:5]
        results = []
        for n in cases:
            tree = build_deep_tree(n).simplify()
            def count_nodes(node, seen=None):
                if seen is None:
                    seen = set()
                if node in seen:
                    return 0
                seen.add(node)
                if hasattr(node, 'true') and hasattr(node, 'false'):
                    return 1 + count_nodes(node.true, seen) + count_nodes(node.false, seen)
                return 1
            n_nodes = count_nodes(tree)
            n_vars = len(tree.vars())
            solutions = []
            def op():
                nonlocal solutions
                solutions = tree.solutions
            t, curr_kb, peak_kb = measure_memory(op)
            n_solutions = len(solutions)
            pred_t = 1.85e-4 * n + 8.8e-4
            pred_m = 2.2 * n + 1.0
            self.assert_perf(f"solve(deep n={n})", pred_t, t)
            self.assert_mem(f"solve(deep n={n})", pred_m, peak_kb)
            results.append((n, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m))
        print("\n[Recap Solve Deep]")
        print("n | Nodes | Vars | Sols | Time (s) | Pred (s) | Peak Mem (KB) | Pred Mem (KB)")
        for n, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m in results:
            print(f"{n:2d} | {n_nodes:5d} | {n_vars:4d} | {n_solutions:4d} | {t:8.6f} | {pred_t:8.6f} | {peak_kb:13.2f} | {pred_m:13.2f}")

    @unittest.skipUnless(TEST_LEVEL > 0, "Tests de performance désactivés")
    def test_solve_wide(self):
    # Nouveau modèle (bench 2025-09):
    # T_solve_wide(n) ≈ 1.05e-4·n + 2.9e-4 ; M_peak_wide(n) ≈ 2.05·n + 1.0 (KB)
        test_cases = [5, 10, 20, 40, 80, 160]
        if TEST_LEVEL < 2:
            test_cases = test_cases[:3]
        elif TEST_LEVEL < 3:
            test_cases = test_cases[:5]
        results = []
        for n in test_cases:
            tree = build_wide_tree(n).simplify()
            def count_nodes(node, seen=None):
                if seen is None:
                    seen = set()
                if node in seen:
                    return 0
                seen.add(node)
                if hasattr(node, 'true') and hasattr(node, 'false'):
                    return 1 + count_nodes(node.true, seen) + count_nodes(node.false, seen)
                return 1
            n_nodes = count_nodes(tree)
            n_vars = len(tree.vars())
            solutions = []
            def op():
                nonlocal solutions
                solutions = tree.solutions
            t, curr_kb, peak_kb = measure_memory(op)
            n_solutions = len(solutions)
            pred_t = 1.05e-4 * n + 2.9e-4
            pred_m = 2.05 * n + 1.0
            self.assert_perf(f"solve(wide n={n})", pred_t, t)
            self.assert_mem(f"solve(wide n={n})", pred_m, peak_kb)
            results.append((n, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m))
        print("\n[Recap Solve Wide]")
        print("n | Nodes | Vars | Sols | Time (s) | Pred (s) | Peak Mem (KB) | Pred Mem (KB)")
        for n, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m in results:
            print(f"{n:3d} | {n_nodes:5d} | {n_vars:4d} | {n_solutions:4d} | {t:8.6f} | {pred_t:8.6f} | {peak_kb:13.2f} | {pred_m:13.2f}")

    @unittest.skipUnless(TEST_LEVEL > 0, "Tests de performance désactivés")
    def test_solve_balanced(self):
    # Nouveau modèle (bench 2025-09):
    # T_solve_balanced(d) ≈ 1.50e-4·(2^d) + 3.9e-4 ; M_peak ≈ 6.2·(2^d) + 10.0 (KB)
        test_cases = list(range(3, 10))
        if TEST_LEVEL < 2:
            test_cases = test_cases[:3]
        elif TEST_LEVEL < 3:
            test_cases = test_cases[:5]
        results = []
        for d in test_cases:
            tree = build_balanced_tree(d).simplify()
            L = 2 ** d
            def count_nodes(node, seen=None):
                if seen is None:
                    seen = set()
                if node in seen:
                    return 0
                seen.add(node)
                if hasattr(node, 'true') and hasattr(node, 'false'):
                    return 1 + count_nodes(node.true, seen) + count_nodes(node.false, seen)
                return 1
            n_nodes = count_nodes(tree)
            n_vars = len(tree.vars())
            solutions = []
            def op():
                nonlocal solutions
                solutions = tree.solutions
            t, curr_kb, peak_kb = measure_memory(op)
            n_solutions = len(solutions)
            pred_t = 1.50e-4 * L + 3.9e-4
            pred_m = 6.2 * L + 10.0
            self.assert_perf(f"solve(balanced d={d})", pred_t, t)
            self.assert_mem(f"solve(balanced d={d})", pred_m, peak_kb)
            results.append((d, L, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m))
        print("\n[Recap Solve Balanced]")
        print("d | Leaves | Nodes | Vars | Sols | Time (s) | Pred (s) | Peak Mem (KB) | Pred Mem (KB)")
        for d, L, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m in results:
            print(f"{d:2d} | {L:6d} | {n_nodes:5d} | {n_vars:4d} | {n_solutions:4d} | {t:8.6f} | {pred_t:8.6f} | {peak_kb:13.2f} | {pred_m:13.2f}")

    @unittest.skipUnless(TEST_LEVEL > 0, "Tests de performance désactivés")
    def test_solve_combined(self):
        # Nouveau modèle (bench 2025-09):
        # Soit L = 2^b et G = width + L
        # T ≈ 4.425e-4 · G − 1.322e-3 (borné par baseline)
        # M ≈ 14.0 · G (KB)
        test_cases = [(5, 5, 3), (8, 8, 3), (10, 10, 3), (12, 12, 4), (15, 15, 4), (20, 20, 5)]
        
        if TEST_LEVEL < 2:
            test_cases = test_cases[:3]
        elif TEST_LEVEL < 3:
            test_cases = test_cases[:5]
        results = []
        for (d, w, b) in test_cases:
            tree = build_deep_tree(d).or_(build_wide_tree(w)).and_(build_balanced_tree(b)).simplify()
            L = 2 ** b
            G = w + L
            def count_nodes(node, seen=None):
                if seen is None:
                    seen = set()
                if node in seen:
                    return 0
                seen.add(node)
                if hasattr(node, 'true') and hasattr(node, 'false'):
                    return 1 + count_nodes(node.true, seen) + count_nodes(node.false, seen)
                return 1
            n_nodes = count_nodes(tree)
            n_vars = len(tree.vars())
            solutions = []
            def op():
                nonlocal solutions
                solutions = tree.solutions
            t, curr_kb, peak_kb = measure_memory(op)
            n_solutions = len(solutions)
            # Prédictions basées sur G (w + 2^b)
            pred_t = max(4.425e-4 * G - 1.322e-3, self.MIN_TIME_BASELINE)
            pred_m = 14.0 * G
            self.assert_perf(f"solve(combined d={d},w={w},b={b})", pred_t, t)
            self.assert_mem(f"solve(combined d={d},w={w},b={b})", pred_m, peak_kb)
            results.append((d, w, b, G, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m))
        print("\n[Recap Solve Combined]")
        print("d | w | b | G | Nodes | Vars | Sols | Time (s) | Pred (s) | Peak Mem (KB) | Pred Mem (KB)")
        for d, w, b, G, n_nodes, n_vars, n_solutions, t, pred_t, peak_kb, pred_m in results:
            print(f"{d:2d} | {w:2d} | {b:2d} | {G:4d} | {n_nodes:5d} | {n_vars:4d} | {n_solutions:4d} | {t:8.6f} | {pred_t:8.6f} | {peak_kb:13.2f} | {pred_m:13.2f}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
