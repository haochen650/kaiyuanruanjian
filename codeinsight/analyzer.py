import libcst as cst
from typing import Dict, Set, List
from dataclasses import dataclass, field, asdict


@dataclass
class FunctionMetrics:
    """单个函数的指标"""

    name: str
    line_start: int
    line_end: int
    complexity: int
    params_count: int
    params_without_annotation: int
    has_return_annotation: bool
    has_docstring: bool
    local_vars_count: int = 0

    @property
    def lines_count(self) -> int:
        """函数的代码行数"""
        return self.line_end - self.line_start + 1

    @property
    def is_long_function(self, max_lines: int = 50) -> bool:
        """是否为长函数"""
        return self.lines_count > max_lines

    @property
    def has_many_params(self, max_params: int = 4) -> bool:
        """是否参数过多"""
        return self.params_count > max_params


@dataclass
class ClassMetrics:
    """单个类的指标"""

    name: str
    line_start: int
    line_end: int
    methods_count: int
    complexity: int
    has_docstring: bool
    functions: List[FunctionMetrics] = field(default_factory=list)

    @property
    def lines_count(self) -> int:
        """类的代码行数"""
        return self.line_end - self.line_start + 1


class CodeMetrics:
    def __init__(self):
        self.cyclomatic_complexity = 1  # 起始为1
        self.function_count = 0
        self.class_count = 0
        self.max_nesting_depth = 0
        self.current_nesting = 0
        self.imports: Set[str] = set()
        self.used_names: Set[str] = set()
        self.functions_missing_return_annotation = 0
        self.functions_missing_param_annotation = 0
        self.total_functions = 0
        self.annotated_functions = 0
        self.line_count = 0
        self.comment_count = 0
        self.functions_list: List[FunctionMetrics] = []
        self.classes_list: List[ClassMetrics] = []
        self.current_function: FunctionMetrics = None
        self.current_class: ClassMetrics = None

    def analyze(self, tree: cst.Module, source: str = "") -> Dict[str, any]:
        tree.visit(MetricsVisitor(self))

        # 计算代码统计
        if source:
            lines = source.split("\n")
            self.line_count = len(lines)
            self.comment_count = sum(
                1 for line in lines if line.strip().startswith("#")
            )

        # 计算类型注解覆盖率
        if self.total_functions > 0:
            annotation_coverage = (
                self.annotated_functions / self.total_functions
            ) * 100
        else:
            annotation_coverage = 0

        unused_imports = list(self.imports - self.used_names)

        # 计算综合评分
        score = self._calculate_score(unused_imports, annotation_coverage)

        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "max_nesting_depth": self.max_nesting_depth,
            "unused_imports": unused_imports,
            "functions_missing_return_annotation": self.functions_missing_return_annotation,
            "functions_missing_param_annotation": self.functions_missing_param_annotation,
            "total_functions": self.total_functions,
            "annotation_coverage": annotation_coverage,
            "line_count": self.line_count,
            "comment_count": self.comment_count,
            "quality_score": score,
            "functions": self.functions_list,
            "classes": self.classes_list,
        }

    def _calculate_score(
        self, unused_imports: List[str], annotation_coverage: float
    ) -> int:
        """计算代码质量评分 (0-100)"""
        score = 100

        # 圈复杂度扣分 (每超过1点扣5分，最多扣30分)
        if self.cyclomatic_complexity > 10:
            complexity_penalty = min((self.cyclomatic_complexity - 10) * 2, 30)
            score -= complexity_penalty

        # 嵌套深度扣分 (每超过1层扣3分，最多扣15分)
        if self.max_nesting_depth > 4:
            nesting_penalty = min((self.max_nesting_depth - 4) * 3, 15)
            score -= nesting_penalty

        # 未使用导入扣分 (每个扣2分，最多扣10分)
        import_penalty = min(len(unused_imports) * 2, 10)
        score -= import_penalty

        # 类型注解扣分 (覆盖率低于50%扣分)
        if annotation_coverage < 50:
            annotation_penalty = int((50 - annotation_coverage) * 0.3)
            score -= annotation_penalty

        return max(0, score)


class MetricsVisitor(cst.CSTVisitor):
    def __init__(self, metrics: CodeMetrics):
        self.metrics = metrics

    def visit_If(self, node: cst.If) -> bool:
        self.metrics.cyclomatic_complexity += 1
        self._enter_block()
        return True

    def visit_For(self, node: cst.For) -> bool:
        self.metrics.cyclomatic_complexity += 1
        self._enter_block()
        return True

    def visit_While(self, node: cst.While) -> bool:
        self.metrics.cyclomatic_complexity += 1
        self._enter_block()
        return True

    def visit_Try(self, node: cst.Try) -> bool:
        self._enter_block()
        return True

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.metrics.function_count += 1
        self.metrics.total_functions += 1

        # 获取函数位置信息（简化处理）
        line_start = 1
        line_end = 1

        # 检查返回类型注解
        has_return_annotation = node.returns is not None
        if not has_return_annotation:
            self.metrics.functions_missing_return_annotation += 1

        # 检查参数注解
        params = node.params.params
        missing_params = 0
        for param in params:
            if param.annotation is None and param.name.value != "self":
                missing_params += 1
        if missing_params > 0:
            self.metrics.functions_missing_param_annotation += 1

        # 检查文档字符串
        has_docstring = self._has_docstring(node.body)

        # 创建函数指标对象
        func_metrics = FunctionMetrics(
            name=node.name.value,
            line_start=line_start,
            line_end=line_end,
            complexity=1,  # 会在访问控制流时更新
            params_count=len(params),
            params_without_annotation=missing_params,
            has_return_annotation=has_return_annotation,
            has_docstring=has_docstring,
        )

        # 只有当同时有返回类型和所有参数都有类型注解时，才认为这个函数是有注解的
        has_params = len([p for p in params if p.name.value != "self"]) > 0
        is_annotated = has_return_annotation and (
            missing_params == 0 if has_params else True
        )
        if is_annotated:
            self.metrics.annotated_functions += 1

        # 保存到列表
        self.metrics.functions_list.append(func_metrics)
        self.metrics.current_function = func_metrics

        self._enter_block()
        return True

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        self.metrics.class_count += 1

        # 获取类位置信息（简化处理）
        line_start = 1
        line_end = 1

        # 检查文档字符串
        has_docstring = self._has_docstring(node.body)

        # 创建类指标对象
        class_metrics = ClassMetrics(
            name=node.name.value,
            line_start=line_start,
            line_end=line_end,
            methods_count=0,
            complexity=1,
            has_docstring=has_docstring,
        )

        self.metrics.classes_list.append(class_metrics)
        self.metrics.current_class = class_metrics

        self._enter_block()
        return True

    def visit_Import(self, node: cst.Import) -> bool:
        for name in node.names:
            if isinstance(name.name, cst.Name):
                self.metrics.imports.add(name.name.value)
            elif isinstance(name.name, cst.Attribute):
                # 简化：取顶层模块名
                top = name.name
                while isinstance(top, cst.Attribute):
                    top = top.value
                if isinstance(top, cst.Name):
                    self.metrics.imports.add(top.value)
        return False  # 不继续访问子节点

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        # 记录具体导入的名字 (from ... import X)
        if not isinstance(node.names, cst.ImportStar):
            # node.names 是 Sequence[ImportAlias]，直接迭代
            for import_alias in node.names:
                if isinstance(import_alias.name, cst.Name):
                    self.metrics.imports.add(import_alias.name.value)
                elif isinstance(import_alias.name, cst.Attribute):
                    # 处理 from x import y.z 的情况，取最后一个名字
                    attr = import_alias.name
                    while isinstance(attr.value, cst.Attribute):
                        attr = attr.value
                    if isinstance(attr.value, cst.Name):
                        self.metrics.imports.add(attr.attr.value)
        return False  # 不继续访问子节点，防止Name被visit_Name重复记录

    def visit_Name(self, node: cst.Name) -> None:
        self.metrics.used_names.add(node.value)

    def _enter_block(self):
        self.metrics.current_nesting += 1
        if self.metrics.current_nesting > self.metrics.max_nesting_depth:
            self.metrics.max_nesting_depth = self.metrics.current_nesting

    def leave_If(self, node: cst.If) -> None:
        self.metrics.current_nesting -= 1

    def leave_For(self, node: cst.For) -> None:
        self.metrics.current_nesting -= 1

    def leave_While(self, node: cst.While) -> None:
        self.metrics.current_nesting -= 1

    def leave_Try(self, node: cst.Try) -> None:
        self.metrics.current_nesting -= 1

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.metrics.current_nesting -= 1
        self.metrics.current_function = None

    def _has_docstring(self, body: cst.IndentedBlock) -> bool:
        """检查函数/类是否有docstring"""
        if not body.body:
            return False
        first_stmt = body.body[0]
        if isinstance(first_stmt, cst.SimpleStatementLine):
            if first_stmt.body and isinstance(first_stmt.body[0], cst.Expr):
                if isinstance(
                    first_stmt.body[0].value, (cst.SimpleString, cst.ConcatenatedString)
                ):
                    return True
        return False

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.metrics.current_nesting -= 1
        self.metrics.current_class = None
