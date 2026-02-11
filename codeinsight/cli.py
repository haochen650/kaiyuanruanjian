import argparse
import sys
from pathlib import Path
import libcst as cst

# 核心模块导入
from codeinsight.refactor import UnusedImportRemover  # 确保你已经创建了这个文件
from .analyzer import CodeMetrics
from .cst_printer import print_cst_tree
from .multi_file_analyzer import MultiFileAnalyzer, ReportExporter
from .code_detector import CodeDuplicateDetector, ASTBasedDuplicateDetector, format_duplicate_report
from .evolution import EvolutionAnalyzer
from .checker import check_logic_bugs

def main():
    parser = argparse.ArgumentParser(description="CodeInsight: 多维度 Python 代码质量分析工具")
    parser.add_argument("file", help="Python 源文件或目录路径")
    parser.add_argument("--fix", action="store_true", help="自动修复可安全修复的问题（目前支持：移除未使用导入）")
    parser.add_argument("--show-cst", action="store_true", help="显示简化语法树")
    parser.add_argument("--show-functions", action="store_true", help="显示详细的函数分析")
    parser.add_argument("--detect-duplicates", action="store_true", help="检测代码重复")
    parser.add_argument("--duplicate-mode", choices=["block", "function"], default="block", help="重复检测模式: block(代码块) 或 function(函数)")
    parser.add_argument("--directory", "-d", action="store_true", help="分析目录下的所有Python文件")
    parser.add_argument("--json", "-j", metavar="OUTPUT_FILE", help="导出为JSON格式")
    parser.add_argument("--recursive", "-r", action="store_true", default=True, help="递归分析子目录")
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

    if args.check_bugs:
        bug_findings = check_logic_bugs(tree)
        print("\n🐛 深度 Bug 扫描结果:")
        if not bug_findings:
            print("  ✅ 未发现常见逻辑缺陷")
        for bug in bug_findings:
            print(f"  {bug}")

    if args.evolution:
        print("\n⏳ 历史演化轨迹 (过去10个版本):")
        ea = EvolutionAnalyzer(".")
        history = ea.analyze_history(str(filepath))
        for entry in history:
            print(f"  [{entry['date']}] {entry['commit']} | 评分: {entry['score']} | 复杂度: {entry['complexity']}")

    # --- 1. 执行分析指标 ---
    metrics = CodeMetrics()
    result = metrics.analyze(tree, source)

    # --- 2. 自动化修复逻辑 ---
    if args.fix and result['unused_imports']:
        print(f"\n🛠️  正在执行自动修复: {filepath.name}")
        
        # 实例化重构器
        fixer = UnusedImportRemover(set(result['unused_imports']))
        
        # 转换语法树
        modified_tree = tree.visit(fixer)
        new_code = modified_tree.code
        
        # 如果代码有变化，写回文件
        if new_code != source:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_code)
            print(f"✅ 已自动移除未使用的导入: {', '.join(result['unused_imports'])}")
            
            # 修复后重新分析一次，以保证后续输出的报告是基于最新代码的
            source = new_code
            tree = modified_tree
            result = metrics.analyze(tree, source)
        else:
            print("💡 未发现可自动修复的变更。")

    # --- 3. 输出报告 ---
    print(f"\n🔍 代码质量分析报告: {filepath}")
    print("-" * 40)

    # 质量评分
    quality_score = result['quality_score']
    if quality_score >= 80:
        score_emoji = "⭐"
    elif quality_score >= 60:
        score_emoji = "👍"
    elif quality_score >= 40:
        score_emoji = "⚠️"
    else:
        score_emoji = "❌"
    print(f"{score_emoji} 代码质量评分: {quality_score}/100")

    # 代码规模统计
    print(f"\n📈 代码规模:")
    print(f"  📝 总行数: {result['line_count']}")
    print(f"  💬 注释行数: {result['comment_count']}")
    if result['line_count'] > 0:
        code_lines = result['line_count'] - result['comment_count']
        density = (code_lines / result['line_count'] * 100)
        print(f"  📊 代码密度: {density:.1f}%")

    # 复杂度指标
    print(f"\n⚙️  复杂度指标:")
    print(f"  📊 圈复杂度: {result['cyclomatic_complexity']}")
    print(f"  🧮 函数数量: {result['function_count']}")
    print(f"  🏛️  类数量: {result['class_count']}")
    print(f"  📦 最大嵌套深度: {result['max_nesting_depth']}")

    # 类型注解覆盖率
    print(f"\n🏷️  类型注解覆盖率:")
    annotation_coverage = result['annotation_coverage']
    coverage_bar = "█" * int(annotation_coverage // 10) + "░" * (10 - int(annotation_coverage // 10))
    print(f"  {coverage_bar} {annotation_coverage:.1f}% ({result['total_functions']} 个函数)")
    print(f"  ❌ 缺少返回类型注解: {result['functions_missing_return_annotation']}")
    print(f"  ❌ 缺少参数类型注解: {result['functions_missing_param_annotation']}")

    # 导入管理
    print(f"\n📦 导入管理:")
    unused = result['unused_imports']
    if args.fix and not unused:
        print(f"  ✨ 所有未使用导入已清理完毕")
    else:
        print(f"  🗑️  未使用导入 ({len(unused)}): {', '.join(unused) if unused else '无'}")

    # 函数级别详细分析
    if args.show_functions and result['functions']:
        print(f"\n🔬 函数级别分析 ({len(result['functions'])} 个函数):")
        for func in result['functions']:
            print(f"  📌 {func.name}()")
            print(f"     参数: {func.params_count} 个", end="")
            if func.params_without_annotation > 0:
                print(f" (缺少注解: {func.params_without_annotation})", end="")
            print()
            print(f"     行数: {func.lines_count} 行", end="")
            if func.lines_count > 50:
                print(" ⚠️ (长函数)", end="")
            print()
            print(f"     返回注解: {'✓' if func.has_return_annotation else '✗'}", end="")
            print(f"  文档字符串: {'✓' if func.has_docstring else '✗'}")

    # 评估建议
    print("\n💡 优化建议:")
    suggestions_count = 0

    if quality_score < 60:
        print("  🚨 代码质量需要改进，以下是优先级建议:")

    if result['cyclomatic_complexity'] > 10:
        print("  ⚠️  圈复杂度过高 (> 10)，建议拆分逻辑")
        suggestions_count += 1
    if result['max_nesting_depth'] > 4:
        print("  ⚠️  嵌套过深 (> 4)，考虑提前 return 或提取函数")
        suggestions_count += 1
    if unused:
        print(f"  ⚠️  存在 {len(unused)} 个未使用导入，建议运行 --fix 自动清理")
        suggestions_count += 1
    if result['annotation_coverage'] < 50:
        print(f"  🏷️   类型注解覆盖率较低 ({annotation_coverage:.1f}%)，建议为关键函数添加类型注解")
        suggestions_count += 1
    
    # 长函数提示
    long_functions = [f for f in result['functions'] if f.lines_count > 50]
    if long_functions:
        print(f"  📏 发现 {len(long_functions)} 个长函数 (>50行):")
        for func in long_functions[:3]:
            print(f"     - {func.name}(): {func.lines_count} 行")
        suggestions_count += 1

    if suggestions_count == 0:
        print("  ✅ 代码质量良好，保持当前编码标准")

    if args.show_cst:
        print("\n🌳 简化语法树 (前3层):")
        print_cst_tree(tree, max_depth=3)

    # 代码重复检测
    if args.detect_duplicates:
        print("\n" + "=" * 50)
        if args.duplicate_mode == "block":
            detector = CodeDuplicateDetector(
                min_block_size=5,
                similarity_threshold=0.85,
                ignore_comments=True,
                ignore_whitespace=True
            )
            report = detector.detect(source)
        else:
            detector = ASTBasedDuplicateDetector(min_function_size=5)
            report = detector.detect(tree, source)
        print(format_duplicate_report(report))

    # JSON导出
    if args.json:
        ReportExporter.export_json(result, args.json)
        print(f"\n✅ 报告已导出到: {args.json}")


def _analyze_directory(directory: Path, args):
    """分析目录下的所有Python文件"""
    analyzer = MultiFileAnalyzer()
    
    # 如果开启了 --fix，我们需要在扫描目录时对每个文件进行处理
    #为了简单起见，这里假设 MultiFileAnalyzer 尚未集成修复功能
    # 如果要在目录扫描中也支持 --fix，建议在 MultiFileAnalyzer.analyze_directory 中实现逻辑
    result = analyzer.analyze_directory(str(directory), recursive=args.recursive)

    print(f"📂 目录分析报告: {result['directory']}\n")
    print(f"📊 扫描结果:")
    print(f"  总文件数: {result['total_files']}")
    print(f"  已分析: {result['analyzed_files']}")

    summary = result['summary']
    if summary:
        print(f"\n📈 项目级汇总:")
        print(f"  平均评分: {summary.get('average_quality_score', 0)}/100")
        print(f"  最佳文件: {Path(summary.get('best_file', '')).name} ({summary.get('best_file_score', 0)})")
        print(f"  最差文件: {Path(summary.get('worst_file', '')).name} ({summary.get('worst_file_score', 0)})")
        print(f"  总函数数: {summary.get('total_functions', 0)}")
        print(f"  总类数: {summary.get('total_classes', 0)}")
        print(f"  总行数: {summary.get('total_lines', 0)}")

    # 按评分排序并显示
    print(f"\n📋 文件质量排序:")
    files_with_scores = [
        (f, r['quality_score']) for f, r in result['files'].items()
        if isinstance(r, dict) and 'quality_score' in r
    ]
    files_with_scores.sort(key=lambda x: x[1], reverse=True)

    for file_path, score in files_with_scores[:10]:
        emoji = "⭐" if score >= 80 else "👍" if score >= 60 else "⚠️" if score >= 40 else "❌"
        print(f"  {emoji} {Path(file_path).name}: {score}/100")

    if args.json:
        ReportExporter.export_json(result, args.json)
        print(f"\n✅ 报告已导出到: {args.json}")


if __name__ == "__main__":
    main()
