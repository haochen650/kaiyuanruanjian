import argparse
import sys
from pathlib import Path
import libcst as cst

# 核心模块导入
from codeinsight.refactor import UnusedImportRemover
from .analyzer import CodeMetrics
from .cst_printer import print_cst_tree
from .multi_file_analyzer import MultiFileAnalyzer, ReportExporter
from .code_detector import (
    CodeDuplicateDetector,
    ASTBasedDuplicateDetector,
    format_duplicate_report,
)
from .evolution import EvolutionAnalyzer
from .checker import check_logic_bugs

def main():
    parser = argparse.ArgumentParser(
        description="CodeInsight: 多维度 Python 代码 quality 分析工具"
    )
    parser.add_argument("file", help="Python 源文件或目录路径")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复可安全修复的问题（目前支持：移除未使用导入）",
    )
    parser.add_argument("--show-cst", action="store_true", help="显示简化语法树")
    parser.add_argument(
        "--show-functions", action="store_true", help="显示详细的函数分析"
    )
    parser.add_argument("--detect-duplicates", action="store_true", help="检测代码重复")
    parser.add_argument(
        "--duplicate-mode",
        choices=["block", "function"],
        default="block",
        help="重复检测模式: block(代码块) 或 function(函数)",
    )
    parser.add_argument(
        "--directory", "-d", action="store_true", help="分析目录下的所有Python文件"
    )
    parser.add_argument("--json", "-j", metavar="OUTPUT_FILE", help="导出为JSON格式")
    parser.add_argument(
        "--recursive", "-r", action="store_true", default=True, help="递归分析子目录"
    )
    parser.add_argument("--evolution", action="store_true", help="分析文件的历史演化趋势")
    parser.add_argument("--check-bugs", action="store_true", help="执行深度逻辑 Bug 扫描")
    
    args = parser.parse_args()

    filepath = Path(args.file)

    # 处理目录分析
    if args.directory or filepath.is_dir():
        _analyze_directory(filepath, args)
        return

    # 处理单文件分析
    if not filepath.exists() or filepath.suffix != ".py":
        print("错误: 请提供有效的 .py 文件", file=sys.stderr)
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = cst.parse_module(source)
    except Exception as e:
        print(f"解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 执行 Bug 检查
    if args.check_bugs:
        bug_findings = check_logic_bugs(tree)
        print("\n🐛 深度 Bug 扫描结果:")
        if not bug_findings:
            print("   ✅ 未发现常见逻辑缺陷")
        for bug in bug_findings:
            print(f"   {bug}")

    # 执行演化分析
    if args.evolution:
        print("\n⏳ 历史演化轨迹 (过去10个版本):")
        ea = EvolutionAnalyzer(".")
        history = ea.analyze_history(str(filepath))
        for entry in history:
            print(f"   [{entry['date']}] {entry['commit']} | 评分: {entry['score']} | 复杂度: {entry['complexity']}")

    # --- 1. 执行分析指标 ---
    metrics = CodeMetrics()
    result = metrics.analyze(tree, source)

    # --- 2. 自动化修复逻辑 ---
    if args.fix and result["unused_imports"]:
        print(f"\n🛠️  正在执行自动修复: {filepath.name}")
        fixer = UnusedImportRemover(set(result["unused_imports"]))
        modified_tree = tree.visit(fixer)
        new_code = modified_tree.code

        if new_code != source:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_code)
            print(f"✅ 已自动移除未使用的导入: {', '.join(result['unused_imports'])}")
            source = new_code
            tree = modified_tree
            result = metrics.analyze(tree, source)
        else:
            print("💡 未发现可自动修复的变更。")

    # --- 3. 输出报告 ---
    print(f"\n🔍 代码质量分析报告: {filepath}")
    print("-" * 40)

    quality_score = result["quality_score"]
    score_emoji = "⭐" if quality_score >= 80 else "👍" if quality_score >= 60 else "⚠️" if quality_score >= 40 else "❌"
    print(f"{score_emoji} 代码质量评分: {quality_score}/100")

    # (中间的统计输出逻辑保持不变...)
    # ... [篇幅原因，此处省略你代码中已有的 Print 逻辑] ...

    # 代码重复检测
    if args.detect_duplicates:
        print("\n" + "=" * 50)
        if args.duplicate_mode == "block":
            detector = CodeDuplicateDetector(min_block_size=5)
            report = detector.detect(source)
        else:
            detector = ASTBasedDuplicateDetector(min_function_size=5)
            report = detector.detect(tree, source)
        print(format_duplicate_report(report))

    if args.json:
        ReportExporter.export_json(result, args.json)
        print(f"\n✅ 报告已导出到: {args.json}")

# _analyze_directory 函数也按此逻辑保留...
# TODO: Add explicit error handling for file not found exceptions
if __name__ == "__main__":
    print("Starting CodeInsight module directly...")
    # 这里可以调用你的主函数，例如: main()