# CodeInsight 快速参考指南

## 安装依赖

```bash
conda activate codeinsight
pip install -r requirements.txt
```

---

## 命令速查表

### 基础分析 - 单个文件

```bash
# 基础分析
python -m codeinsight.cli file.py

# 显示函数级详细分析
python -m codeinsight.cli file.py --show-functions

# 显示简化语法树
python -m codeinsight.cli file.py --show-cst

# 导出为JSON报告
python -m codeinsight.cli file.py --json report.json
```

### 项目分析 - 整个目录

```bash
# 分析整个项目（递归）
python -m codeinsight.cli ./src --directory

# 分析并导出JSON
python -m codeinsight.cli ./src --directory --json project.json
```

---

## 输出说明

### 代码质量评分

| 评分 | 等级 | 含义 |
|------|------|------|
| 80-100 | ⭐ 优秀 | 代码质量很好 |
| 60-79 | 👍 良好 | 代码质量可接受 |
| 40-59 | ⚠️ 需改进 | 存在一些问题 |
| 0-39 | ❌ 较差 | 需要重构 |


---

## 快速开始

```bash
# 1. 分析单个文件并显示函数详情
python -m codeinsight.cli examples/sample.py --show-functions

# 2. 分析整个目录
python -m codeinsight.cli ./src --directory

# 3. 生成JSON报告
python -m codeinsight.cli ./src --directory --json metrics.json

# 4. 修复未使用引入
python -m codeinsight.cli test_fix.py --fix
```

