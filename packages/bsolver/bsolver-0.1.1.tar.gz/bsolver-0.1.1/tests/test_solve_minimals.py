import unittest
from bsolver.arbre import Var, TRUE, FALSE

# Helper to normalize results from solve() into set of frozensets for comparison

def implicant_set(node):
    return {frozenset(s) for s in node.solve()}

class TestSolveMinimal(unittest.TestCase):
    def setUp(self):
        self.A = Var("A")
        self.B = Var("B")
        self.C = Var("C")
        self.D = Var("D")
        self.E = Var("E")
        self.F = Var("F")

    def test_terminal_true_false(self):
        self.assertEqual(TRUE.solutions, {frozenset()})
        self.assertEqual(FALSE.solutions, set())

    def test_single_variable(self):
        self.assertEqual(self.A.solutions, {frozenset({("A", True)})})

    def test_tautology(self):
        # A | ~A should yield empty implicant set meaning always true
        expr = self.A | ~self.A
        self.assertEqual(expr.solutions, {frozenset()})

    def test_simple_or(self):
        expr = self.A | self.B
        expected = {frozenset({("A", True)}), frozenset({("B", True)})}
        self.assertEqual(expr.solutions, expected)

    def test_disjoint_conjunctions(self):
        expr = (self.A & self.B) | (self.C & self.D)
        expected = {frozenset({("A", True), ("B", True)}),
                    frozenset({("C", True), ("D", True)})}
        self.assertEqual(expr.solutions, expected)

    def test_absorption_union(self):
        # (A&B)|(~A&C) should also produce (B&C) implicant where A indifferent
        expr = (self.A & self.B) | (~self.A & self.C)
        expected = {frozenset({("A", True), ("B", True)}),
                    frozenset({("A", False), ("C", True)}),
                    frozenset({("B", True), ("C", True)})}
        self.assertEqual(expr.solutions, expected)

    def test_complex(self):
        # (A&B)|(A&C)|(~A&D&E)|(~A&D&F)|(B&C)|(E&F)
        expr = (self.A & self.B) | (self.A & self.C) | (~self.A & self.D & self.E) | (~self.A & self.D & self.F) | (self.B & self.C) | (self.E & self.F)
        expected = {
            frozenset({("A", True), ("B", True)}),
            frozenset({("A", True), ("C", True)}),
            frozenset({("B", True), ("C", True)}),
            frozenset({("E", True), ("F", True)}),
            frozenset({("A", False), ("D", True), ("E", True)}),
            frozenset({("A", False), ("D", True), ("F", True)}),
            frozenset({("B", True), ("D", True), ("E", True)}),
            frozenset({("B", True), ("D", True), ("F", True)}),
            frozenset({("C", True), ("D", True), ("E", True)}),
            frozenset({("C", True), ("D", True), ("F", True)}),
        }
        self.assertEqual(expr.solutions, expected)

if __name__ == '__main__':
    unittest.main()
