import unittest
from bsolver.arbre import Var, TRUE, FALSE


class TestArbreBasics(unittest.TestCase):
    def test_repr(self):
        A = Var("A")
        self.assertEqual(repr(TRUE), "TRUE")
        self.assertEqual(repr(FALSE), "FALSE")
        self.assertEqual(repr(A), "Var('A')")
        self.assertEqual(repr(~A), "~Var('A')")
        expr = Var("X", TRUE, ~A)
        self.assertIn("X", repr(expr))

    def test_eval(self):
        A = Var("A")
        self.assertFalse(A.eval({}))  # missing var defaults to False
        self.assertTrue(A.eval({"A": True}))
        self.assertFalse(A.eval({"A": False}))

    def test_logic_terminals(self):
        A = Var("A")
        self.assertIs((TRUE & A), A)
        self.assertIs((FALSE & A), FALSE)
        self.assertIs((TRUE | A), TRUE)
        self.assertIs((FALSE | A), A)

    def test_logic_equivalences(self):
        A = Var("A")
        self.assertEqual(A & A, A)
        self.assertEqual(A | ~A, TRUE)  # tautology

    def test_simplify(self):
        A = Var("A")
        expr = Var("X", TRUE, TRUE)
        self.assertIs(expr.simplify(), TRUE)
        expr2 = Var("Y", FALSE, FALSE)
        self.assertIs(expr2.simplify(), FALSE)
        expr3 = Var("Z", A, A)
        self.assertEqual(expr3.simplify(), A)
        # idempotence
        simple = (A & TRUE).simplify()
        self.assertEqual(simple, simple.simplify())

    def test_vars(self):
        A, B, C = Var("A"), Var("B"), Var("C")
        expr = (A & B) | ~C
        self.assertEqual(expr.vars(), {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
