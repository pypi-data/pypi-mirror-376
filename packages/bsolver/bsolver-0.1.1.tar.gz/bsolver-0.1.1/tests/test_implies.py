import unittest
from bsolver.arbre import Node, TerminalNode, Var

class TestImplies(unittest.TestCase):
    def setUp(self):
        # Création de quelques nœuds de base pour les tests
        self.true_node = TerminalNode(True)
        self.false_node = TerminalNode(False)
        self.var_a = Var('A')
        self.var_b = Var('B')
        self.var_c = Var('C')

    def test_basic_cases(self):
        # Cas de base
        self.assertTrue(self.true_node.implies(self.true_node))
        self.assertTrue(self.false_node.implies(self.true_node))
        self.assertFalse(self.true_node.implies(self.false_node))
        self.assertTrue(self.false_node.implies(self.false_node))

    def test_simple_variables(self):
        # Cas simples avec des variables
        self.assertTrue(self.var_a.implies(self.var_a))
        self.assertFalse(self.var_a.implies(~self.var_a))
        self.assertFalse((self.var_a | self.var_b).implies(self.var_a))
        self.assertTrue((self.var_a & self.var_b).implies(self.var_a))
        self.assertFalse(self.var_a.implies(self.var_a & self.var_b))

    def test_complex_cases(self):
        # Cas complexes
        expr1 = (self.var_a & self.var_b) | (~self.var_a & self.var_c)
        expr2 = self.var_b | self.var_c
        self.assertTrue(expr1.implies(expr2))

        expr3 = (self.var_a & ~self.var_b) | (~self.var_a & self.var_b)
        expr4 = self.var_a | self.var_b
        self.assertTrue(expr3.implies(expr4))

        expr5 = (self.var_a & self.var_b & self.var_c)
        expr6 = self.var_a & self.var_b
        self.assertTrue(expr5.implies(expr6))
        self.assertFalse(expr6.implies(expr5))

if __name__ == '__main__':
    unittest.main()