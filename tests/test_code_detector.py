import unittest
import libcst as cst
from codeinsight.code_detector import (
    CodeDuplicateDetector,
    ASTBasedDuplicateDetector,
    format_duplicate_report,
    CodeBlock,
    DuplicatePair,
    DuplicateReport,
)


class TestCodeDuplicateDetector(unittest.TestCase):
    """测试代码块重复检测器"""

    def test_no_duplicates(self):
        """测试没有重复的代码"""
        code = """def func1():
    return 1

def func2():
    return 2

def func3():
    return 3
"""
        detector = CodeDuplicateDetector(min_block_size=3)
        report = detector.detect(code)

        self.assertGreaterEqual(report.exact_duplicates, 0)
        self.assertLessEqual(report.duplicate_percentage, 100)

    def test_exact_duplicates(self):
        """测试完全重复的代码"""
        code = """def func1():
    x = 1
    y = 2
    z = x + y
    return z

def func2():
    x = 1
    y = 2
    z = x + y
    return z
"""
        detector = CodeDuplicateDetector(min_block_size=3)
        report = detector.detect(code)

        self.assertGreater(report.exact_duplicates, 0)

    def test_similar_duplicates(self):
        """测试相似的代码"""
        code = """def func1():
    x = 1
    y = 2
    z = x + y
    return z

def func2():
    a = 1
    b = 2
    c = a + b
    return c
"""
        detector = CodeDuplicateDetector(min_block_size=3, similarity_threshold=0.5)
        report = detector.detect(code)

        self.assertGreater(report.similar_duplicates, 0)

    def test_ignore_comments(self):
        """测试忽略注释"""
        code = """def func1():
    # This is a comment
    x = 1
    y = 2
    return x + y

def func2():
    # Different comment
    x = 1
    y = 2
    return x + y
"""
        detector = CodeDuplicateDetector(min_block_size=3, ignore_comments=True)
        report = detector.detect(code)

        self.assertGreater(report.exact_duplicates, 0)

    def test_ignore_whitespace(self):
        """测试忽略空白字符"""
        code = """def func1():
    x = 1
    y = 2
    return x + y

def func2():
    x = 1
    y = 2
    return x + y
"""
        detector = CodeDuplicateDetector(min_block_size=3, ignore_whitespace=True)
        report = detector.detect(code)

        self.assertGreater(report.exact_duplicates, 0)

    def test_min_block_size(self):
        """测试最小代码块大小"""
        code = """def func1():
    return 1

def func2():
    return 2
"""
        detector = CodeDuplicateDetector(min_block_size=10)
        report = detector.detect(code)

        self.assertEqual(report.exact_duplicates, 0)


class TestASTBasedDuplicateDetector(unittest.TestCase):
    """测试基于AST的函数重复检测器"""

    def test_no_duplicate_functions(self):
        """测试没有重复的函数"""
        code = """def func1():
    return 1

def func2():
    return 2
"""
        tree = cst.parse_module(code)
        detector = ASTBasedDuplicateDetector(min_function_size=1)
        report = detector.detect(tree, code)

        self.assertEqual(report.exact_duplicates, 0)

    def test_exact_duplicate_functions(self):
        """测试完全重复的函数"""
        code = """def func1():
    x = 1
    y = 2
    return x + y

def func2():
    x = 1
    y = 2
    return x + y
"""
        tree = cst.parse_module(code)
        detector = ASTBasedDuplicateDetector(min_function_size=1)
        report = detector.detect(tree, code)

        self.assertGreater(report.similar_duplicates, 0)

    def test_similar_functions(self):
        """测试相似的函数"""
        code = """def func1():
    x = 1
    y = 2
    return x + y

def func2():
    a = 1
    b = 2
    return a + b
"""
        tree = cst.parse_module(code)
        detector = ASTBasedDuplicateDetector(min_function_size=1)
        report = detector.detect(tree, code)

        self.assertGreater(report.similar_duplicates, 0)

    def test_min_function_size(self):
        """测试最小函数大小"""
        code = """def func1():
    return 1

def func2():
    return 1
"""
        tree = cst.parse_module(code)
        detector = ASTBasedDuplicateDetector(min_function_size=5)
        report = detector.detect(tree, code)

        self.assertEqual(report.total_blocks, 0)

    def test_class_methods(self):
        """测试类方法重复检测"""
        code = """class MyClass:
    def method1(self):
        x = 1
        y = 2
        return x + y

    def method2(self):
        x = 1
        y = 2
        return x + y
"""
        tree = cst.parse_module(code)
        detector = ASTBasedDuplicateDetector(min_function_size=1)
        report = detector.detect(tree, code)

        self.assertGreater(report.similar_duplicates, 0)


class TestCodeBlock(unittest.TestCase):
    """测试代码块数据类"""

    def test_line_count(self):
        """测试行数计算"""
        block = CodeBlock(start_line=1, end_line=5, content="test", hash_value="abc")
        self.assertEqual(block.line_count, 5)

    def test_line_count_single_line(self):
        """测试单行代码块"""
        block = CodeBlock(start_line=1, end_line=1, content="test", hash_value="abc")
        self.assertEqual(block.line_count, 1)


class TestDuplicatePair(unittest.TestCase):
    """测试重复代码对数据类"""

    def test_exact_duplicate_type(self):
        """测试完全重复类型"""
        block1 = CodeBlock(start_line=1, end_line=5, content="test", hash_value="abc")
        block2 = CodeBlock(start_line=10, end_line=14, content="test", hash_value="abc")
        pair = DuplicatePair(block1, block2, 1.0, "exact")

        self.assertEqual(pair.type, "exact")
        self.assertEqual(pair.similarity, 1.0)

    def test_similar_duplicate_type(self):
        """测试相似重复类型"""
        block1 = CodeBlock(start_line=1, end_line=5, content="test1", hash_value="abc")
        block2 = CodeBlock(
            start_line=10, end_line=14, content="test2", hash_value="def"
        )
        pair = DuplicatePair(block1, block2, 0.9, "similar")

        self.assertEqual(pair.type, "similar")
        self.assertEqual(pair.similarity, 0.9)


class TestDuplicateReport(unittest.TestCase):
    """测试重复检测报告数据类"""

    def test_duplicate_percentage(self):
        """测试重复百分比计算"""
        report = DuplicateReport(
            total_blocks=10,
            exact_duplicates=2,
            similar_duplicates=1,
            duplicate_pairs=[],
            duplicate_lines=20,
            total_lines=100,
            duplicate_percentage=20.0,
        )

        self.assertEqual(report.duplicate_percentage, 20.0)

    def test_total_blocks(self):
        """测试总代码块数"""
        report = DuplicateReport(
            total_blocks=10,
            exact_duplicates=2,
            similar_duplicates=1,
            duplicate_pairs=[],
            duplicate_lines=20,
            total_lines=100,
            duplicate_percentage=20.0,
        )

        self.assertEqual(report.total_blocks, 10)


class TestFormatDuplicateReport(unittest.TestCase):
    """测试报告格式化"""

    def test_format_empty_report(self):
        """测试空报告格式化"""
        report = DuplicateReport(
            total_blocks=0,
            exact_duplicates=0,
            similar_duplicates=0,
            duplicate_pairs=[],
            duplicate_lines=0,
            total_lines=100,
            duplicate_percentage=0.0,
        )

        formatted = format_duplicate_report(report)
        self.assertIn("代码重复检测报告", formatted)
        self.assertIn("0%", formatted)

    def test_format_report_with_duplicates(self):
        """测试有重复的报告格式化"""
        block1 = CodeBlock(start_line=1, end_line=5, content="test", hash_value="abc")
        block2 = CodeBlock(start_line=10, end_line=14, content="test", hash_value="abc")
        pair = DuplicatePair(block1, block2, 1.0, "exact")

        report = DuplicateReport(
            total_blocks=2,
            exact_duplicates=1,
            similar_duplicates=0,
            duplicate_pairs=[pair],
            duplicate_lines=5,
            total_lines=100,
            duplicate_percentage=5.0,
        )

        formatted = format_duplicate_report(report)
        self.assertIn("1 对", formatted)
        self.assertIn("5.0%", formatted)

    def test_format_report_with_high_duplication(self):
        """测试高重复率报告格式化"""
        report = DuplicateReport(
            total_blocks=10,
            exact_duplicates=5,
            similar_duplicates=2,
            duplicate_pairs=[],
            duplicate_lines=50,
            total_lines=100,
            duplicate_percentage=50.0,
        )

        formatted = format_duplicate_report(report)
        self.assertIn("警告", formatted)


if __name__ == "__main__":
    unittest.main()
