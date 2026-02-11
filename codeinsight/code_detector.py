import libcst as cst
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import difflib


@dataclass
class CodeBlock:
    """代码块信息"""
    start_line: int
    end_line: int
    content: str
    hash_value: str

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass
class DuplicatePair:
    """重复代码对"""
    block1: CodeBlock
    block2: CodeBlock
    similarity: float
    type: str  # 'exact' or 'similar'


@dataclass
class DuplicateReport:
    """重复检测报告"""
    total_blocks: int
    exact_duplicates: int
    similar_duplicates: int
    duplicate_pairs: List[DuplicatePair]
    duplicate_lines: int
    total_lines: int
    duplicate_percentage: float


class CodeDuplicateDetector:
    """代码重复检测器"""

    def __init__(
        self,
        min_block_size: int = 5,
        similarity_threshold: float = 0.85,
        ignore_comments: bool = True,
        ignore_whitespace: bool = True
    ):
        self.min_block_size = min_block_size
        self.similarity_threshold = similarity_threshold
        self.ignore_comments = ignore_comments
        self.ignore_whitespace = ignore_whitespace

    def detect(self, source: str) -> DuplicateReport:
        """检测代码重复"""
        lines = source.split('\n')
        total_lines = len(lines)

        if self.ignore_comments:
            lines = self._remove_comments(lines)

        if self.ignore_whitespace:
            lines = [line.strip() for line in lines]

        blocks = self._extract_blocks(lines)
        exact_duplicates, similar_duplicates = self._find_duplicates(blocks)

        duplicate_lines = self._calculate_duplicate_lines(exact_duplicates, similar_duplicates)

        return DuplicateReport(
            total_blocks=len(blocks),
            exact_duplicates=len(exact_duplicates),
            similar_duplicates=len(similar_duplicates),
            duplicate_pairs=exact_duplicates + similar_duplicates,
            duplicate_lines=duplicate_lines,
            total_lines=total_lines,
            duplicate_percentage=(duplicate_lines / total_lines * 100) if total_lines > 0 else 0
        )

    def _remove_comments(self, lines: List[str]) -> List[str]:
        """移除注释行"""
        result = []
        in_multiline_comment = False
        for line in lines:
            stripped = line.strip()
            if '"""' in stripped or "'''" in stripped:
                in_multiline_comment = not in_multiline_comment
                continue
            if in_multiline_comment:
                continue
            if stripped.startswith('#'):
                continue
            result.append(line)
        return result

    def _extract_blocks(self, lines: List[str]) -> List[CodeBlock]:
        """提取代码块"""
        blocks = []
        n = len(lines)

        for start in range(n - self.min_block_size + 1):
            for end in range(start + self.min_block_size, min(start + 30, n + 1)):
                block_lines = lines[start:end]
                content = '\n'.join(block_lines)
                hash_value = self._compute_hash(content)
                blocks.append(CodeBlock(
                    start_line=start + 1,
                    end_line=end,
                    content=content,
                    hash_value=hash_value
                ))

        return blocks

    def _compute_hash(self, content: str) -> str:
        """计算内容的哈希值"""
        import hashlib
        normalized = '\n'.join(line.strip() for line in content.strip().split('\n') if line.strip())
        return hashlib.md5(normalized.encode()).hexdigest()

    def _find_duplicates(self, blocks: List[CodeBlock]) -> Tuple[List[DuplicatePair], List[DuplicatePair]]:
        """查找重复代码块"""
        exact_duplicates = []
        similar_duplicates = []

        hash_to_blocks = defaultdict(list)
        for block in blocks:
            hash_to_blocks[block.hash_value].append(block)

        for hash_value, matching_blocks in hash_to_blocks.items():
            if len(matching_blocks) > 1:
                for i in range(len(matching_blocks)):
                    for j in range(i + 1, len(matching_blocks)):
                        exact_duplicates.append(DuplicatePair(
                            block1=matching_blocks[i],
                            block2=matching_blocks[j],
                            similarity=1.0,
                            type='exact'
                        ))

        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                if blocks[i].hash_value != blocks[j].hash_value:
                    similarity = self._calculate_similarity(blocks[i].content, blocks[j].content)
                    if similarity >= self.similarity_threshold:
                        similar_duplicates.append(DuplicatePair(
                            block1=blocks[i],
                            block2=blocks[j],
                            similarity=similarity,
                            type='similar'
                        ))

        similar_duplicates = self._deduplicate_similar(similar_duplicates)

        return exact_duplicates, similar_duplicates

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """计算两个代码块的相似度"""
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')

        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        return matcher.ratio()

    def _deduplicate_similar(self, similar_duplicates: List[DuplicatePair]) -> List[DuplicatePair]:
        """去重相似的重复对"""
        seen = set()
        result = []

        for pair in similar_duplicates:
            key = (pair.block1.start_line, pair.block1.end_line,
                   pair.block2.start_line, pair.block2.end_line)
            if key not in seen:
                seen.add(key)
                result.append(pair)

        return result

    def _calculate_duplicate_lines(
        self,
        exact_duplicates: List[DuplicatePair],
        similar_duplicates: List[DuplicatePair]
    ) -> int:
        """计算重复行数"""
        covered_lines = set()

        for pair in exact_duplicates + similar_duplicates:
            for line in range(pair.block1.start_line, pair.block1.end_line + 1):
                covered_lines.add(line)

        return len(covered_lines)


class ASTBasedDuplicateDetector:
    """基于AST的代码重复检测器"""

    def __init__(self, min_function_size: int = 5):
        self.min_function_size = min_function_size

    def detect(self, tree: cst.Module, source: str) -> DuplicateReport:
        """基于AST检测重复函数"""
        functions = self._extract_functions(tree, source)
        exact_duplicates, similar_duplicates = self._find_function_duplicates(functions)

        total_lines = len(source.split('\n'))
        duplicate_lines = self._calculate_duplicate_lines(exact_duplicates, similar_duplicates)

        return DuplicateReport(
            total_blocks=len(functions),
            exact_duplicates=len(exact_duplicates),
            similar_duplicates=len(similar_duplicates),
            duplicate_pairs=exact_duplicates + similar_duplicates,
            duplicate_lines=duplicate_lines,
            total_lines=total_lines,
            duplicate_percentage=(duplicate_lines / total_lines * 100) if total_lines > 0 else 0
        )

    def _extract_functions(self, tree: cst.Module, source: str) -> List[CodeBlock]:
        """提取所有函数"""
        functions = []
        lines = source.split('\n')

        wrapper = cst.metadata.MetadataWrapper(tree)
        positions = wrapper.resolve(cst.metadata.PositionProvider)

        class FunctionExtractor(cst.CSTVisitor):
            def __init__(self, outer):
                self.outer = outer
                self.functions = []

            def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
                pos = positions[node]
                start_line = pos.start.line
                end_line = pos.end.line

                if end_line - start_line + 1 >= self.outer.min_function_size:
                    content = '\n'.join(lines[start_line - 1:end_line])
                    hash_value = self.outer._compute_hash(content)
                    self.functions.append(CodeBlock(
                        start_line=start_line,
                        end_line=end_line,
                        content=content,
                        hash_value=hash_value
                    ))
                return True

        extractor = FunctionExtractor(self)
        wrapper.visit(extractor)
        return extractor.functions

    def _compute_hash(self, content: str) -> str:
        """计算内容的哈希值"""
        import hashlib
        import re
        
        lines = content.split('\n')
        result = []
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                result.append(stripped)
        
        normalized = '\n'.join(result)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _find_function_duplicates(
        self,
        functions: List[CodeBlock]
    ) -> Tuple[List[DuplicatePair], List[DuplicatePair]]:
        """查找重复函数"""
        exact_duplicates = []
        similar_duplicates = []

        hash_to_functions = defaultdict(list)
        for func in functions:
            hash_to_functions[func.hash_value].append(func)

        for hash_value, matching_functions in hash_to_functions.items():
            if len(matching_functions) > 1:
                for i in range(len(matching_functions)):
                    for j in range(i + 1, len(matching_functions)):
                        exact_duplicates.append(DuplicatePair(
                            block1=matching_functions[i],
                            block2=matching_functions[j],
                            similarity=1.0,
                            type='exact'
                        ))

        for i in range(len(functions)):
            for j in range(i + 1, len(functions)):
                if functions[i].hash_value != functions[j].hash_value:
                    similarity = self._calculate_similarity(functions[i].content, functions[j].content)
                    if similarity >= 0.85:
                        similar_duplicates.append(DuplicatePair(
                            block1=functions[i],
                            block2=functions[j],
                            similarity=similarity,
                            type='similar'
                        ))

        return exact_duplicates, similar_duplicates

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """计算两个函数的相似度"""
        matcher = difflib.SequenceMatcher(None, content1, content2)
        return matcher.ratio()

    def _calculate_duplicate_lines(
        self,
        exact_duplicates: List[DuplicatePair],
        similar_duplicates: List[DuplicatePair]
    ) -> int:
        """计算重复行数"""
        covered_lines = set()

        for pair in exact_duplicates + similar_duplicates:
            for line in range(pair.block1.start_line, pair.block1.end_line + 1):
                covered_lines.add(line)

        return len(covered_lines)


def format_duplicate_report(report: DuplicateReport, max_pairs: int = 10) -> str:
    """格式化重复检测报告"""
    lines = []
    lines.append("\n🔍 代码重复检测报告")
    lines.append("-" * 40)

    lines.append(f"\n📊 统计信息:")
    lines.append(f"  总代码块数: {report.total_blocks}")
    lines.append(f"  完全重复: {report.exact_duplicates} 对")
    lines.append(f"  相似重复: {report.similar_duplicates} 对")
    lines.append(f"  重复行数: {report.duplicate_lines} / {report.total_lines}")
    lines.append(f"  重复比例: {report.duplicate_percentage:.1f}%")

    if report.duplicate_pairs:
        lines.append(f"\n📋 重复详情 (显示前 {min(max_pairs, len(report.duplicate_pairs))} 对):")

        for i, pair in enumerate(report.duplicate_pairs[:max_pairs], 1):
            emoji = "🔴" if pair.type == 'exact' else "🟡"
            lines.append(f"\n  {emoji} 重复 #{i} ({pair.type}, 相似度: {pair.similarity:.1%})")
            lines.append(f"     位置 1: 第 {pair.block1.start_line}-{pair.block1.end_line} 行 ({pair.block1.line_count} 行)")
            lines.append(f"     位置 2: 第 {pair.block2.start_line}-{pair.block2.end_line} 行 ({pair.block2.line_count} 行)")

            if pair.block1.line_count <= 10:
                lines.append(f"     代码片段:")
                for line in pair.block1.content.split('\n')[:5]:
                    lines.append(f"       {line}")

    if report.duplicate_percentage > 10:
        lines.append(f"\n⚠️  警告: 代码重复率较高 ({report.duplicate_percentage:.1f}%)，建议进行重构")
    elif report.duplicate_percentage > 5:
        lines.append(f"\n💡 提示: 代码重复率适中 ({report.duplicate_percentage:.1f}%)，可考虑优化")
    else:
        lines.append(f"\n✅ 代码重复率较低 ({report.duplicate_percentage:.1f}%)，保持良好")

    return '\n'.join(lines)
