# CodeInsight 使用指南

完整的使用说明和常见场景

## 基础使用

### 分析单个文件

```bash
python -m codeinsight.cli myfile.py
```

### 显示函数级分析

```bash
python -m codeinsight.cli myfile.py --show-functions
```

### 分析整个项目

```bash
python -m codeinsight.cli ./src --directory
```

### 导出 JSON 报告

```bash
python -m codeinsight.cli ./src --directory --json report.json
```

---

## 常用场景

### 找出最差的文件

```bash
python -m codeinsight.cli ./src --directory --json metrics.json

python - <<'EOF'
import json
with open('metrics.json') as f:
    data = json.load(f)

# 获取所有低于60分的文件
poor_files = [
    (f, r['quality_score'])
    for f, r in data['files'].items()
    if isinstance(r, dict) and r.get('quality_score', 0) < 60
]

poor_files.sort(key=lambda x: x[1])
print(f"Found {len(poor_files)} files with quality < 60:")
for file_path, score in poor_files:
    print(f"  {file_path}: {score}/100")
EOF
```

### 找出所有长函数

```bash
python -m codeinsight.cli ./src --directory --json metrics.json

python - <<'EOF'
import json
with open('metrics.json') as f:
    data = json.load(f)

long_funcs = []
for file_path, result in data['files'].items():
    if isinstance(result, dict) and 'functions' in result:
        for func in result['functions']:
            if func['lines_count'] > 50:
                long_funcs.append({
                    'file': file_path,
                    'name': func['name'],
                    'lines': func['lines_count']
                })

long_funcs.sort(key=lambda x: x['lines'], reverse=True)
print(f"Found {len(long_funcs)} long functions:")
for item in long_funcs[:10]:
    print(f"  {item['file']}::{item['name']}() - {item['lines']} lines")
EOF
```

---

## API 使用

在 Python 脚本中使用：

```python
from codeinsight.analyzer import CodeMetrics
import libcst as cst

# 读取文件
with open('file.py', 'r') as f:
    source = f.read()

# 分析
tree = cst.parse_module(source)
metrics = CodeMetrics()
result = metrics.analyze(tree, source)

# 获取结果
print(f"Quality Score: {result['quality_score']}/100")
print(f"Functions: {result['function_count']}")

# 遍历函数
for func in result['functions']:
    print(f"  {func.name}: {func.lines_count} lines")
```

---

## 质量指标

### 代码质量评分

| 分数 | 等级 | 含义 |
|------|------|------|
| 80-100 | ⭐ 优秀 | 代码质量很好 |
| 60-79 | 👍 良好 | 代码质量可接受 |
| 40-59 | ⚠️ 需改进 | 存在较多问题 |
| 0-39 | ❌ 较差 | 质量严重不足 |

### 关键指标

- **圈复杂度** - 代码路径数，建议 < 10
- **嵌套深度** - 最大嵌套层级，建议 < 4
- **类型注解** - 覆盖率，建议 > 80%

---

## 故障排查

### 文件编码错误

如果遇到编码错误，在 Python 脚本中指定编码：

```python
with open('file.py', 'r', encoding='gbk') as f:
    source = f.read()
```

### 找不到模块

确保在项目根目录运行：

```bash
cd /path/to/codeinsight
python -m codeinsight.cli file.py
```

---

**更多信息查看 README.md 和 QUICK_REFERENCE.md**
