import libcst as cst

def print_cst_tree(module: cst.Module, max_depth: int = 3):
    """简化打印 CST 结构，避免过深"""
    def _print_node(node, depth=0):
        if depth > max_depth:
            return
        indent = "  " * depth
        node_name = type(node).__name__
        print(f"{indent}{node_name}")
        for field in node._fields:
            value = getattr(node, field)
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, cst.CSTNode):
                        _print_node(item, depth + 1)
            elif isinstance(value, cst.CSTNode):
                _print_node(value, depth + 1)
    _print_node(module)