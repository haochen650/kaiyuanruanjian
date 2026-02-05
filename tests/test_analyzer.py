import unittest
import libcst as cst
from codeinsight.analyzer import CodeMetrics

class TestAnalyzer(unittest.TestCase):
    def test_simple_function(self):
        code = "def f(): pass"
        tree = cst.parse_module(code)
        metrics = CodeMetrics()
        result = metrics.analyze(tree)
        self.assertEqual(result["function_count"], 1)
        self.assertEqual(result["cyclomatic_complexity"], 1)

    def test_if_statement(self):
        code = "if True: pass"
        tree = cst.parse_module(code)
        metrics = CodeMetrics()
        result = metrics.analyze(tree)
        self.assertEqual(result["cyclomatic_complexity"], 2)

if __name__ == "__main__":
    unittest.main()