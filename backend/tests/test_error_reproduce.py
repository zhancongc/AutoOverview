#!/usr/bin/env python3
"""尝试重现错误"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 读取文件，找到 _filter_papers_by_quality 方法中所有使用 stats 的地方
with open('services/review_task_executor.py', 'r') as f:
    lines = f.readlines()

# 找到 _filter_papers_by_quality 方法的开始
start_line = None
end_line = None
for i, line in enumerate(lines, 1):
    if 'async def _filter_papers_by_quality' in line:
        start_line = i
    elif start_line and i > start_line and line.strip() == '}' and lines[i-2].strip() == '}':
        end_line = i
        break

print(f"_filter_papers_by_quality 方法: 行 {start_line} - {end_line}")
print()

# 打印这个方法中所有使用 stats 的地方
print("方法中所有使用 'stats' 的地方:")
for i, line in enumerate(lines[start_line-1:end_line], start_line):
    if 'stats' in line:
        print(f"  行 {i}: {line.rstrip()}")