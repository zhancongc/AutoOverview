#!/usr/bin/env python3
"""测试 filter_service.get_statistics 返回的结构"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.paper_filter import PaperFilterService

# 创建一些测试数据
test_papers = [
    {'id': '1', 'title': 'Test Paper 1', 'is_english': True, 'year': 2023, 'cited_by_count': 10},
    {'id': '2', 'title': 'Test Paper 2', 'is_english': False, 'year': 2022, 'cited_by_count': 5},
    {'id': '3', 'title': 'Test Paper 3', 'is_english': True, 'year': 2021, 'cited_by_count': 15},
]

filter_service = PaperFilterService()
stats = filter_service.get_statistics(test_papers)

print("filter_service.get_statistics 返回:")
print(stats)
print()
print("键列表:")
print(list(stats.keys()))
print()
print("尝试访问 'english_count':")
try:
    print(f"english_count = {stats['english_count']}")
except KeyError as e:
    print(f"KeyError: {e}")
    print(f"可用的键: {list(stats.keys())}")