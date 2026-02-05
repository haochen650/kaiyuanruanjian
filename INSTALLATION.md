# CodeInsight 安装指南

## 系统要求

- **Python**: 3.10 或更高版本
- **操作系统**: Windows / macOS / Linux
- **包管理器**: pip 或 conda

## 方式一：使用 Conda（推荐）

### 步骤 1: 创建 Conda 环境

```bash
# 创建名为 codeinsight 的 Python 3.10 环境
conda create -n codeinsight python=3.10

# 激活环境
conda activate codeinsight
```

### 步骤 2: 进入项目目录

```bash
cd D:\Developing\Workspace\python\Pycharm\codeinsight
# 或
cd /path/to/codeinsight
```

### 步骤 3: 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install libcst>=0.4.0
```

### 步骤 4: 验证安装

```bash
# 查看版本和帮助
python -m codeinsight.cli --help
```

---

## 方式二：使用 Pip（全局安装）

### 步骤 1: 安装依赖

```bash
pip install libcst>=0.4.0
```

### 步骤 2: 进入项目目录

```bash
cd /path/to/codeinsight
```

### 步骤 3: 验证安装

```bash
python -m codeinsight.cli --help
```

---

## 方式三：编辑模式安装（开发）

如果需要修改代码并测试，使用编辑模式：

```bash
# 在项目根目录
pip install -e .
```

---

## 快速测试

安装完成后，测试基础功能：

### 测试 1: 分析示例文件

```bash
python -m codeinsight.cli examples/sample.py
```

**预期输出：** 显示代码质量分析报告

### 测试 2: 显示函数分析

```bash
python -m codeinsight.cli examples/sample.py --show-functions
```

**预期输出：** 包含函数级别的详细分析

### 测试 3: 导出为 JSON

```bash
python -m codeinsight.cli examples/sample.py --json test_report.json
```

**预期输出：** 生成 `test_report.json` 文件

---

## 依赖说明

### libcst >= 0.4.0

**LibCST** (Concrete Syntax Tree) 是 Meta 开源的 Python 代码解析库。

- 用于准确解析 Python 代码结构
- 不执行代码，只分析语法
- 支持 Python 3.8+

**安装：**

```bash
pip install libcst>=0.4.0
```

---

## 常见问题

### Q: ModuleNotFoundError: No module named 'libcst'

**原因：** libcst 未安装

**解决方案：**

```bash
pip install libcst
```

### Q: 使用 conda 环境时提示找不到模块

**原因：** 未激活环境或安装到了错误的环境

**解决方案：**

```bash
# 确认激活了正确的环境
conda activate codeinsight

# 查看当前环境
conda info --envs

# 重新安装依赖
pip install -r requirements.txt
```

### Q: 在 Windows 上权限不足

**症状：** `PermissionError` 或 `Access is denied`

**解决方案：**

- 使用管理员模式运行 CMD/PowerShell
- 或指定用户安装：`pip install --user libcst`

### Q: 不同 Python 版本冲突

**症状：** 调用旧版本的 Python 或包

**解决方案：**

```bash
# 明确指定 Python 版本
python3.10 -m pip install libcst

# 或使用虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## 卸载

### 卸载工具

```bash
# 移除项目文件
rm -rf codeinsight/

# 或直接删除目录
```

### 删除 Conda 环境

```bash
# 删除环境
conda remove -n codeinsight --all

# 验证删除
conda env list
```

### 卸载依赖

```bash
pip uninstall libcst
```

---

## 高级配置

### 使用虚拟环境

对于全局 pip 用户，建议使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv codeinsight_env

# 激活环境
source codeinsight_env/bin/activate  # macOS/Linux
# 或
codeinsight_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 使用 Poetry（可选）

如果项目使用 Poetry 管理依赖：

```bash
# 创建 pyproject.toml（如果不存在）
poetry init

# 添加依赖
poetry add libcst

# 安装
poetry install

# 运行
poetry run python -m codeinsight.cli file.py
```

---

## 验证所有依赖

创建以下脚本 `check_env.py` 来验证环境：

```python
#!/usr/bin/env python
"""Check if all dependencies are properly installed"""

import sys

print("Environment Check")
print("-" * 50)

# Check Python version
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
print(f"[OK] Python {python_version}")

# Check libcst
try:
    import libcst
    print(f"[OK] libcst {libcst.__version__}")
except ImportError:
    print("[ERROR] libcst not found")
    sys.exit(1)

# Check codeinsight modules
try:
    from codeinsight.analyzer import CodeMetrics
    print("[OK] codeinsight.analyzer")
except ImportError as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

try:
    from codeinsight.cli import main
    print("[OK] codeinsight.cli")
except ImportError as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

try:
    from codeinsight.multi_file_analyzer import MultiFileAnalyzer
    print("[OK] codeinsight.multi_file_analyzer")
except ImportError as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

print("-" * 50)
print("[SUCCESS] All dependencies are properly installed!")
print("\nYou can now run:")
print("  python -m codeinsight.cli examples/sample.py")
```

运行验证：

```bash
python check_env.py
```

---

## 下一步

安装完成后，查看以下文档：

1. **README.md** - 功能概述和快速开始
2. **QUICK_REFERENCE.md** - 命令速查表
3. **FEATURE_EXPANSION.md** - 功能详细说明

---

## 获取帮助

### 查看帮助信息

```bash
python -m codeinsight.cli --help
```

### 查看详细文档

```bash
# 查看 README
cat README.md

# 查看快速参考
cat QUICK_REFERENCE.md
```

---

**安装完成后，祝你使用愉快！** 🚀
