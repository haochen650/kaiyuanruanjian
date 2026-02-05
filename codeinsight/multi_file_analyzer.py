"""多文件分析和报告导出"""

import json
from pathlib import Path
from typing import List, Dict, Any
from .analyzer import CodeMetrics
import libcst as cst


class MultiFileAnalyzer:
    """分析多个Python文件"""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}

    def analyze_directory(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """分析目录下的所有Python文件

        Args:
            directory: 目录路径
            recursive: 是否递归分析子目录

        Returns:
            包含所有文件分析结果的字典
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ValueError(f"{directory} 不是有效的目录")

        # 查找所有Python文件
        if recursive:
            py_files = list(dir_path.rglob("*.py"))
        else:
            py_files = list(dir_path.glob("*.py"))

        # 排除常见的非源代码文件夹
        excluded_dirs = {".git", "__pycache__", ".venv", "venv", ".idea", "node_modules"}
        py_files = [f for f in py_files if not any(part in f.parts for part in excluded_dirs)]

        results = {}
        total_score = 0
        file_count = 0

        for py_file in sorted(py_files):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = cst.parse_module(source)
                metrics = CodeMetrics()
                result = metrics.analyze(tree, source)

                results[str(py_file)] = result
                total_score += result['quality_score']
                file_count += 1
            except Exception as e:
                results[str(py_file)] = {"error": str(e)}

        # 计算项目级汇总
        summary = self._calculate_summary(results, file_count)

        return {
            "directory": str(dir_path),
            "total_files": len(py_files),
            "analyzed_files": file_count,
            "summary": summary,
            "files": results,
        }

    def _calculate_summary(self, results: Dict, file_count: int) -> Dict[str, Any]:
        """计算项目级汇总指标"""
        if file_count == 0:
            return {}

        avg_score = 0
        total_functions = 0
        total_classes = 0
        total_lines = 0
        worst_score = 100
        worst_file = None
        best_score = 0
        best_file = None

        for file_path, result in results.items():
            if "error" in result:
                continue

            score = result.get('quality_score', 0)
            avg_score += score
            total_functions += result.get('function_count', 0)
            total_classes += result.get('class_count', 0)
            total_lines += result.get('line_count', 0)

            if score < worst_score:
                worst_score = score
                worst_file = file_path
            if score > best_score:
                best_score = score
                best_file = file_path

        return {
            "average_quality_score": round(avg_score / file_count, 2),
            "best_file": best_file,
            "best_file_score": best_score,
            "worst_file": worst_file,
            "worst_file_score": worst_score,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_lines": total_lines,
        }


class ReportExporter:
    """导出分析报告"""

    @staticmethod
    def export_json(result: Dict[str, Any], output_file: str) -> None:
        """导出为JSON格式

        Args:
            result: 分析结果字典
            output_file: 输出文件路径
        """
        # 处理不可序列化的对象
        json_result = ReportExporter._make_serializable(result)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _make_serializable(obj: Any) -> Any:
        """将对象转换为JSON可序列化的形式"""
        if hasattr(obj, '__dataclass_fields__'):
            # 处理dataclass对象
            return {k: ReportExporter._make_serializable(v)
                    for k, v in obj.__dict__.items()}
        elif isinstance(obj, (list, tuple)):
            return [ReportExporter._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: ReportExporter._make_serializable(v) for k, v in obj.items()}
        else:
            return obj
