# 搜索页论文相关性评分方案（待开发）

> 暂未实施，token 成本原因暂缓。当前已屏蔽"相关性"排序按钮。

## 背景

`/search-papers` 页面的"相关性"排序和"引用数"排序结果完全一样。原因是后端 `PaperSearchAgent.search()` 最终按引用量排序返回，前端 `default` 模式不做排序直接展示，导致两种排序无区别。

## 方案：LLM 批量打分

在 `PaperSearchAgent.search()` 收集完所有论文后、返回前，增加一个 **LLM 批量打分** 步骤。

### 涉及文件

- `backend/services/paper_search_agent.py` — 新增 `_score_relevance()` 方法，修改 `search()` 排序逻辑
- `frontend/src/components/SearchPapersPage.tsx` — `Paper` 接口加 `relevance_score`，`sortPapers` 的 `default` 模式按 `relevance_score` 降序

### 不修改的文件

- `paper_filter.py` 的 `_calculate_relevance_score` — 基于关键词匹配，只在综述生成流程中使用
- `review_task_executor.py` — 只透传 papers
- 翻译文件 — 按钮文案"相关性"已存在

### 打分 Prompt

```
你是一位学术文献相关性评估专家。请评估以下论文与研究主题的相关性。

研究主题: {topic}

对每篇论文，根据标题和摘要判断其与主题的相关程度，打 1-10 分：
- 10: 直接相关，是该主题的核心研究
- 7-9: 高度相关，涉及主题的关键技术或方法
- 4-6: 中度相关，与主题有交叉但侧重点不同
- 1-3: 低相关，仅边缘相关或几乎无关

返回 JSON: {"paper_0": 分数, "paper_1": 分数, ...}

论文列表:
[0] 标题: xxx | 摘要: xxx（截断200字）
[1] 标题: xxx | 摘要: xxx
...
```

### 性能预估

- 30 篇论文，分 2 批（15+15）
- 每批 ~1500 input tokens + ~50 output tokens
- 额外耗时约 2-4 秒
- 搜索总耗时从 ~30-60s 增加到 ~35-65s

### 恢复步骤

恢复时需要：
1. 后端添加打分逻辑
2. 前端恢复"相关性"排序按钮（还原 `SortMode` 和按钮列表）
