import os
import sys as system_api  # 测试别名
import datetime
import pandas as pd  # 测试别名
from collections import defaultdict, Counter


def test():
    # 只使用 os 和 defaultdict
    print(os.name)
    d = defaultdict(int)
