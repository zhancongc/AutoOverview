# 测试用例

## 测试文件

| 文件 | 描述 |
|------|------|
| `test_cases.py` | 题目分类和文献搜索综合测试 |
| `test_paper_filter.py` | 文献筛选与排序测试（50篇、近5年50%、英文30%） |
| `test_review_simple.py` | 综述生成测试（DeepSeek API） |
| `test_three_simple.py` | 三圈文献分析测试（题目解析、文献检索、缺口分析） |

## 运行测试

### 运行所有测试

```bash
cd backend

# 使用 pytest 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_paper_filter.py

# 显示详细输出
pytest tests/ -v

# 显示 print 输出
pytest tests/ -s
```

### 手动运行测试

```bash
cd backend

# 文献筛选测试
python3 tests/test_paper_filter.py

# 综述生成测试
python3 tests/test_review_simple.py

# 三圈分析测试
python3 tests/test_three_simple.py

# 综合测试
python3 tests/test_cases.py
```

## 测试依赖

```bash
pip install pytest pytest-asyncio
```

## 测试结果示例

```
✓ 文献筛选与排序测试通过
  总数: 50 篇
  近5年: 31 篇 (62.0%)
  英文: 49 篇 (98.0%)

✓ 综述生成测试通过
  长度: 4959 字符
  使用文献: 5 篇

✓ 三圈文献分析测试通过
  圈A: 人工智能研究现状 (50篇)
  圈B: 制造业现状与痛点 (6篇)
  圈C: 优化方法应用 (20篇)
```
