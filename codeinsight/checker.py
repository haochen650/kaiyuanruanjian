# codeinsight/checker.py
import libcst as cst
from typing import List

class BugPatternScanner(cst.CSTVisitor):
    """扫描代码中的逻辑风险和潜在 Bug"""
    def __init__(self):
        self.findings = []

    def visit_Param(self, node: cst.Param) -> None:
        # 检测可变默认参数 (如 def func(a=[]))
        if isinstance(node.default, (cst.List, cst.Dict)):
            self.findings.append(f"⚠️ 潜在 Bug: 参数 '{node.name.value}' 使用了可变默认对象。")

    def visit_Call(self, node: cst.Call) -> None:
        # 检测危险函数 eval() 或 exec()
        if isinstance(node.func, cst.Name) and node.func.value in ['eval', 'exec']:
            self.findings.append(f"❌ 安全漏洞: 发现 '{node.func.value}' 调用，存在代码注入风险。")
        
        # 检测 subprocess 的 shell=True 风险
        if isinstance(node.func, cst.Attribute) and node.func.attr.value == 'run':
            for arg in node.args:
                if arg.keyword and arg.keyword.value == 'shell':
                    if isinstance(arg.value, cst.Name) and arg.value.value == 'True':
                        self.findings.append("❌ 安全风险: subprocess 开启了 shell=True。")

def check_logic_bugs(tree: cst.Module) -> List[str]:
    scanner = BugPatternScanner()
    tree.visit(scanner)
    return scanner.findings