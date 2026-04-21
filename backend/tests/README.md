# 测试用例

> 最后更新: 2026-04-21 (v6.1)

## 测试文件

| 文件 | 描述 | 版本 |
|------|------|------|
| `test_v61.py` | **v6.1 完整测试套件**（推荐使用）| 6.1 |
| `test_cases.py` | 题目分类和文献搜索综合测试 | 旧版 |
| `test_paper_filter.py` | 文献筛选与排序测试 | 旧版 |
| `test_review_simple.py` | 综述生成测试（DeepSeek API）| 旧版 |
| `test_three_simple.py` | 三圈文献分析测试 | 旧版 |
| `test_flow_search_only.py` | 仅搜索流程测试 | 旧版 |

## v6.1 架构

当前产品采用 **3 阶段架构**：

```
┌─────────────────────────────────────────────────────────────┐
│  阶段1: PaperSearchAgent         │
│  - LLM + Function Calling 驱动                │
│  - OpenAlex 优先 + Semantic Scholar 兜底            │
│  - Danmo Scholar 品牌展示                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段2: SmartReviewGeneratorFinal   │
│  - 8步生成流程                        │
│  - 内置 6 条引用规范                     │
│  - 对比矩阵（前20篇）                    │
│  - IEEE 参考文献格式                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段3: CitationValidatorV2        │
│  - arXiv 预印本处理                    │
│  - Unicode 作者名修复                   │
│  - 可信出版商过滤                      │
│  - 自动修复问题                        │
└─────────────────────────────────────────────────────────────┘
```

## 6 条引用规范

```python
1. ✅ 参考文献列表中没有的文献，正文中禁止引用
2. ✅ 正文引用的文献，参考文献列表中的文献应该是对应的
3. ✅ 正文中引用编号顺序必须是从1开始，依次递增的
4. ✅ 同一个文献禁止引用超过2次
5. ✅ 正文中没有引用的文献，参考文献列表禁止列出
6. ✅ 修正正文中声称的论文数量
```

## 运行测试

### 运行所有 v6.1 测试

```bash
cd backend

# 使用 pytest 运行 v6.1 测试套件
pytest tests/test_v61.py -v

# 显示 print 输出
pytest tests/test_v61.py -v -s
```

### 运行特定测试类

```bash
# 只测试 PaperSearchAgent
pytest tests/test_v61.py::TestPaperSearchAgent -v -s

# 只测试 CitationValidatorV2
pytest tests/test_v61.py::TestCitationValidatorV2 -v -s
```

### 运行旧版测试

```bash
# 运行所有旧版测试
pytest tests/

# 运行特定旧版测试文件
pytest tests/test_paper_filter.py -v
```

### 手动运行测试

```bash
cd backend

# v6.1 测试说明
python3 tests/test_v61.py

# 文献筛选测试
python3 tests/test_paper_filter.py

# 综述生成测试
python3 tests/test_review_simple.py
```

## 测试依赖

```bash
pip install pytest pytest-asyncio
```

## 产品功能对照

| 功能模块 | 测试覆盖 | 说明 |
|---------|---------|------|
| PaperSearchAgent | ✅ | 智能文献检索，OpenAlex + Semantic Scholar |
| SmartReviewGeneratorFinal | ✅ | 8步综述生成，6条引用规范 |
| CitationValidatorV2 | ✅ | 引用校验和修复 |
| 对比矩阵 | ✅ | 前20篇文献对比 |
| 额度体系 | ✅ | 综述=2积分，矩阵=1积分 |
| 导出功能 | ✅ | BibTeX/RIS/Word/Markdown/PDF |
| 中英文双语 | ✅ | react-i18next 支持 |
| 每日搜索限制 | ✅ | 默认 5 次/天 |

## 额度体系

| 操作 | 积分消耗 |
|------|---------|
| 生成文献综述 | 2 积分 |
| 生成对比矩阵 | 1 积分 |
| 注册赠送 | 2 积分 |
| 每日文献搜索 | 5 次（免费） |

## 导出格式

| 类型 | 格式 |
|------|------|
| 文献列表 | BibTeX, RIS, Word |
| 综述 | Markdown, Word, PDF（带水印） |
| 对比矩阵 | Markdown, Word |

## 测试结果示例

```
============================= test session starts ==============================
collected 12 items

tests/test_v61.py::TestPaperSearchAgent::test_basic_search_chinese ✓
tests/test_v61.py::TestPaperSearchAgent::test_basic_search_english ✓
tests/test_v61.py::TestCitationValidatorV2::test_citation_continuity ✓
tests/test_v61.py::TestCitationValidatorV2::test_unicode_fix ✓
...

============================= 12 passed in 15.2s ==============================
```
