import os
import sys
from math import sqrt

unused_module = __import__('json')

def calculate(a, b):
    if a > 0:
        for i in range(10):
            if i % 2 == 0:
                while a < 100:
                    a += 1
    return a + b

def greet(name: str):
    print(f"Hello, {name}")

class Calculator:
    def add(self, x, y):
        return x + y

def no_annotation_func(x, y):
    return x * y