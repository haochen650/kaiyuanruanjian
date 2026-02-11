# codeinsight/evolution.py
import git
from pathlib import Path
from .analyzer import CodeMetrics
import libcst as cst
from typing import List, Dict


class EvolutionAnalyzer:
    """分析代码质量随提交历史的演化趋势"""

    def __init__(self, repo_path: str):
        self.repo = git.Repo(repo_path)
        self.metrics_history = []

    def analyze_history(self, file_path: str, limit: int = 10) -> List[Dict]:
        """分析指定文件在过去 N 个版本中的复杂度演化"""
        history = []
        # 获取该文件的提交记录
        commits = list(self.repo.iter_commits(paths=file_path, max_count=limit))

        for commit in reversed(commits):
            try:
                # 获取该提交时的文件内容
                blob = commit.tree / file_path
                content = blob.data_stream.read().decode("utf-8")

                # 执行静态分析
                tree = cst.parse_module(content)
                metrics = CodeMetrics()
                result = metrics.analyze(tree, content)

                history.append(
                    {
                        "commit": commit.hexsha[:7],
                        "date": commit.authored_datetime.strftime("%Y-%m-%d"),
                        "complexity": result["cyclomatic_complexity"],
                        "score": result["quality_score"],
                    }
                )
            except Exception:
                continue
        return history
