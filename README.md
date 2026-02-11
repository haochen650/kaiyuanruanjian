# CodeInsight: Python 代码质量分析工具

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

一个全面的Python代码质量分析工具，提供多维度的代码指标分析、智能建议和项目级汇总。

## 特性

### 📊 代码质量分析
- **圈复杂度** - 衡量代码分支复杂度
- **嵌套深度** - 识别过度嵌套的代码
- **类型注解覆盖率** - 统计类型提示的覆盖程度
- **代码规模** - 行数、注释密度、代码密度
- **综合评分** - 0-100分的代码质量评分

### 🔬 函数级详细分析
- 自动检测**长函数**（>50行）
- 识别**参数过多**的函数（>4个参数）
- 检测**缺少文档字符串**的函数
- 统计**未使用导入**

### 🔍 代码重复检测
- **代码块重复检测** - 识别完全重复或相似的代码块
- **函数重复检测** - 检测重复或相似的函数
- **重复率统计** - 计算代码重复比例
- **智能去重** - 支持忽略注释和空白字符
- **相似度分析** - 基于哈希和序列匹配算法

### 📁 项目级分析
- 递归扫描整个项目的Python文件
- 生成**项目汇总报告**
- 按质量评分**排序所有文件**
- 自动排除非源代码文件夹
- 基于 LibCST Transformer 的自动修复引擎
- 精准移除未使用导入，支持别名对齐与逗号清理

### 📄 报告导出
- 导出为**JSON格式**
- 便于与其他工具集成
- 支持数据分析和趋势追踪

### 💡 智能建议
根据检测结果自动提供优化建议

---

## 快速开始

### 安装

```bash
# 激活 conda 环境
conda activate codeinsight

# 安装依赖
pip install -r requirements.txt
```

### 基础使用

```bash
# 分析单个文件
python -m codeinsight.cli file.py

# 显示函数级详细分析
python -m codeinsight.cli file.py --show-functions

# 检测代码重复（代码块模式）
python -m codeinsight.cli file.py --detect-duplicates

# 检测代码重复（函数模式）
python -m codeinsight.cli file.py --detect-duplicates --duplicate-mode function

# 分析整个项目
python -m codeinsight.cli ./src --directory

# 导出为 JSON
python -m codeinsight.cli ./src --directory --json report.json

# 精准移除未使用导入
python -m codeinsight.cli test_fix.py --fix
```

---

## 命令参考

```bash
python -m codeinsight.cli <path> [options]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--show-functions` | 显示函数级详细分析 |
| `--show-cst` | 显示简化的语法树 |
| `--detect-duplicates` | 检测代码重复 |
| `--duplicate-mode` | 重复检测模式：block(代码块) 或 function(函数) |
| `--directory` | 分析目录下的所有Python文件 |
| `--recursive` | 递归分析子目录（默认true） |
| `--json <file>` | 导出为JSON格式 |

---

## 质量指标说明

### 代码质量评分

| 评分 | 等级 | 含义 |
|------|------|------|
| 80-100 | ⭐ 优秀 | 代码质量很好 |
| 60-79 | 👍 良好 | 代码质量可接受 |
| 40-59 | ⚠️ 需改进 | 存在较多问题 |
| 0-39 | ❌ 较差 | 质量严重不足 |

### 关键指标

- **圈复杂度** - 代码路径复杂度，建议值 < 10
- **嵌套深度** - 最大嵌套层级，建议值 < 4
- **类型注解覆盖率** - 有完整注解的函数占比，建议值 > 80%
- **代码密度** - 有效代码行数占比，建议值 80%-95%
- **代码重复率** - 重复代码占总代码的比例，建议值 < 10%

### 代码重复检测

代码重复检测功能提供两种模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `block` | 检测代码块级别的重复 | 发现任意代码段的重复 |
| `function` | 检测函数级别的重复 | 识别重复或相似的函数 |

**重复类型：**
- 🔴 **完全重复** - 代码完全相同（相似度 100%）
- 🟡 **相似重复** - 代码结构相似（相似度 ≥ 85%）

**建议：**
- 重复率 > 10%：需要重构，提取公共代码
- 重复率 5-10%：可考虑优化
- 重复率 < 5%：代码质量良好

---

## 常见问题

### Q: 如何处理圈复杂度过高？

分解复杂函数为多个子函数：

```python
# 改进前
def process(a, b, c):
    if a:
        if b:
            # ...
        else:
            # ...
    else:
        if c:
            # ...

# 改进后
def process(a, b, c):
    if a and b:
        return _case1()
    elif a:
        return _case2()
    elif c:
        return _case3()
    return _default()
```

### Q: 如何完整注解函数？

```python
# 完整的函数注解
def calculate(a: int, b: int) -> int:
    """计算两数之和"""
    return a + b
```

### Q: 如何集成到 CI/CD？

```yaml
# GitHub Actions 示例
- name: Code Quality Check
  run: |
    python -m codeinsight.cli ./src --directory --json metrics.json
```

---

## 在 Python 脚本中使用

```python
from codeinsight.analyzer import CodeMetrics
from codeinsight.code_detector import CodeDuplicateDetector, ASTBasedDuplicateDetector
import libcst as cst

# 读取文件
with open('file.py', 'r') as f:
    source = f.read()

# 分析代码质量
tree = cst.parse_module(source)
metrics = CodeMetrics()
result = metrics.analyze(tree, source)

# 获取结果
print(f"Quality Score: {result['quality_score']}")
for func in result['functions']:
    print(f"{func.name}: {func.lines_count} lines")

# 检测代码重复（代码块模式）
detector = CodeDuplicateDetector(min_block_size=5, similarity_threshold=0.85)
report = detector.detect(source)
print(f"Duplicate Rate: {report.duplicate_percentage:.1f}%")

# 检测代码重复（函数模式）
ast_detector = ASTBasedDuplicateDetector(min_function_size=5)
report = ast_detector.detect(tree, source)
print(f"Duplicate Functions: {report.exact_duplicates}")
```

---

## 项目结构

```
codeinsight/
├── codeinsight/
│   ├── analyzer.py              # 核心分析引擎
│   ├── cli.py                   # 命令行接口
│   ├── code_detector.py         # 代码重复检测
│   ├── multi_file_analyzer.py   # 多文件分析
│   ├── refactor.py              # 未使用引入修复
│   └── cst_printer.py           # 工具函数
├── examples/
│   └── sample.py                # 示例代码
├── tests/
│   ├── test_fix.py              # 修复测试
│   ├── test_analyzer.py         # 单元测试
│   └── test_code_detector.py    # 重复检测测试
├── README.md                    # 使用文档
├── QUICK_REFERENCE.md          # 快速参考
├── FEATURE_EXPANSION.md        # 功能详细说明
└── requirements.txt            # 依赖配置
```

---

## 依赖

- Python >= 3.10
- libcst >= 0.4.0

---

## 许可证

MIT License

---

