# codeinsight/refactor.py
import libcst as cst
from typing import Union


class UnusedImportRemover(cst.CSTTransformer):
    def __init__(self, unused_imports: set):
        # 确保传入的是集合，并去掉两端空格
        self.unused_imports = {name.strip() for name in unused_imports}

    def _should_remove(self, alias: cst.ImportAlias) -> bool:
        """
        核心判断逻辑：
        对于 'import pandas as pd'：
        - alias.name.value 是 'pandas'
        - alias.asname.name.value 是 'pd'
        分析器在检测未使用变量时，记录的是 'pd'。
        """
        # 1. 如果有 'as' 别名，我们必须检查别名的名字
        if alias.asname:
            name_to_check = alias.asname.name.value
        else:
            # 2. 如果没有别名，检查原始包名
            name_to_check = alias.name.value

        return name_to_check in self.unused_imports

    def leave_Import(
        self, original_node: cst.Import, updated_node: cst.Import
    ) -> Union[cst.Import, cst.RemovalSentinel]:
        # 过滤掉所有被判定为“未使用”的子节点
        new_names = [n for n in updated_node.names if not self._should_remove(n)]

        # 如果这一行一个名字都不剩了，删除整行
        if not new_names:
            return cst.RemoveFromParent()

        # 重新整理逗号（确保最后一个元素后面没有逗号）
        return updated_node.with_changes(names=self._clean_commas(new_names))

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> Union[cst.ImportFrom, cst.RemovalSentinel]:
        if isinstance(updated_node.names, cst.ImportStar):
            return updated_node

        new_names = [n for n in updated_node.names if not self._should_remove(n)]

        if not new_names:
            return cst.RemoveFromParent()

        return updated_node.with_changes(names=self._clean_commas(new_names))

    def _clean_commas(self, names_list):
        """辅助工具：修复导入列表中的逗号逻辑"""
        if not names_list:
            return names_list
        new_list = list(names_list)
        # 关键：LibCST 的最后一个 ImportAlias 节点的 comma 必须为 None 或默认值
        new_list[-1] = new_list[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return new_list
