# 综述生成流程文档

## 概述

本文档描述了论文综述生成器API的智能生成综述流程（`/api/smart-generate`）。该流程采用混合分类器、多数据源搜索、LLM生成和质量验证反馈循环，确保生成的综述质量。

## 架构组件

### Service 类职责

| Service 类 | 文件 | 职责 |
|-----------|------|------|
| `FrameworkGenerator` | `services/hybrid_classifier.py` | 题目分析、关键词提取、搜索查询生成 |
| `ScholarFlux` | `services/scholarflux_wrapper.py` | 统一文献搜索API（多数据源聚合） |
| `PaperFilterService` | `services/paper_filter.py` | 文献筛选、相关性评分、统计计算 |
| `ReviewGeneratorService` | `services/review_generator.py` | 综述生成、引用处理、编号管理 |
| `ReferenceValidator` | `services/reference_validator.py` | 参考文献质量验证 |
| `ReviewRecordService` | `services/review_record_service.py` | 综述记录数据库操作 |

## 完整流程

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. 智能分析题目（FrameworkGenerator）                              │
│     - 混合分类器：规则提取 + LLM验证优化                            │
│     - 识别题目类型：应用型/评价型/理论型/实证型                     │
│     - 生成搜索查询（search_queries）                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. 初始文献搜索（ScholarFlux）                                     │
│     - 使用智能分析的搜索查询（最多5个）                              │
│     - 每个查询搜索100篇，years_ago=10                               │
│     - 补充搜索（确保至少150篇文献）                                 │
│     - 去重（基于标题）                                              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. 提取主题关键词（FrameworkGenerator.extract_relevance_keywords）│
│     - 从 key_elements 中提取                                        │
│     - 从 variables 中提取（实证型）                                 │
│     - 处理缩写（QFD、FMEA、DMAIC、AHP）                             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. 筛选文献（PaperFilterService.filter_and_sort）                  │
│     - 按相关性评分排序（关键词匹配度）                               │
│     - 按时间分布筛选（近5年占比）                                    │
│     - 按语言筛选（英文文献占比）                                     │
│     → 输出：候选池（100+篇）                                        │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5-7. 生成综述 + 验证被引用文献（带重试循环）【核心改进】           │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  Loop (最多2次):                                         │      │
│   │                                                          │      │
│   │  5. 生成综述 (ReviewGeneratorService)                   │      │
│   │     - LLM从候选池中选择50篇文献引用                       │      │
│   │     - 按文中首次出现顺序重新编号                          │      │
│   │     - 限制每篇文献最多引用2次                             │      │
│   │                                                          │      │
│   │  6. 验证被引用文献质量（关键！）                          │      │
│   │     - validate_citation_count(): 引用数量 >= target_count?│      │
│   │     - validate_recent_ratio(): 近5年占比 >= 用户要求?     │      │
│   │     - validate_english_ratio(): 英文占比 >= 用户要求?     │      │
│   │                                                          │      │
│   │  7. 决策：                                                │      │
│   │     - 全部通过 → 退出循环                                 │      │
│   │     - 任何项不通过 + 未达到最大重试次数 →                 │      │
│   │       • 扩大候选池（years_ago: 10→15，搜索更多文献）      │      │
│   │       • 重新筛选                                           │      │
│   │       • 重新生成综述                                       │      │
│   │     - 任何项不通过 + 达到最大重试次数 →                   │      │
│   │       • 标记 validation_passed = False                    │      │
│   │       • 继续保存结果                                       │      │
│   │                                                          │      │
│   └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  8. 验证并修正引用顺序                                              │
│     - validate_citation_order(): 检查引用是否从[1]开始连续          │
│     - 不正确则调用 _renumber_citations_by_appearance 修正           │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  9. 计算统计信息（PaperFilterService.get_statistics）               │
│     - 基于最终被引用的文献计算（不是候选池）                         │
│     - 总数、近5年占比、英文占比、平均被引量                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  10. 最终验证 + 保存记录                                            │
│      - validate_review(): 完整验证（包括引用顺序）                  │
│      - ReviewRecordService.update_success(): 保存到数据库          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  返回结果                                                            │
│  {                                                                   │
│    id, topic, review, papers (候选池),                              │
│    statistics, analysis, search_queries_results,                    │
│    cited_papers_count, validation_passed, validation                │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## 核心设计决策

### 1. 验证时机：生成后验证

**问题**：为什么不在筛选后验证候选池？

**答案**：
- 候选池（100+篇）只是供LLM选择的范围
- LLM最终可能只引用其中50篇
- 验证候选池无法保证LLM选择的文献达标

**解决方案**：在LLM生成综述后，验证其**实际引用**的文献质量。

### 2. 反馈循环：扩大候选池重新生成

当验证失败时：
- **扩大搜索范围**：`years_ago` 从 10 增加到 15
- **重新筛选**：获取更大的候选池
- **重新生成**：让LLM从更大的候选池中重新选择

### 3. 引用顺序修正

- `ReviewGeneratorService.generate_review()` 内部已经处理了引用编号
- 额外的验证确保引用从[1]开始连续编号
- 如果发现问题，调用 `_renumber_citations_by_appearance` 修正

## API 请求/响应

### 请求

```json
POST /api/smart-generate
{
  "topic": "基于QFD和PFMEA的螺纹钢质量管理研究",
  "target_count": 50,
  "recent_years_ratio": 0.5,
  "english_ratio": 0.3
}
```

### 响应

```json
{
  "success": true,
  "message": "文献综述生成成功",
  "data": {
    "id": 1,
    "topic": "基于QFD和PFMEA的螺纹钢质量管理研究",
    "review": "综述内容...",
    "papers": [...],           // 最终使用的候选池
    "statistics": {
      "total": 52,
      "recent_count": 30,
      "recent_ratio": 0.58,
      "english_count": 18,
      "english_ratio": 0.35
    },
    "analysis": {
      "type": "application",
      "key_elements": {...},
      "search_queries": [...]
    },
    "search_queries_results": [...],
    "cited_papers_count": 52,
    "validation_passed": true,
    "validation": {
      "passed": true,
      "warnings": [],
      "details": {...}
    },
    "created_at": "2026-03-31T10:30:00"
  }
}
```

## 验证标准

| 验证项 | 默认要求 | 说明 |
|--------|----------|------|
| 引用数量 | >= 50 | 可通过 `target_count` 参数调整 |
| 近5年占比 | >= 50% | 可通过 `recent_years_ratio` 参数调整 |
| 英文文献占比 | >= 30% | 可通过 `english_ratio` 参数调整 |
| 引用顺序 | 从[1]开始连续 | 固定要求 |

## 文件位置

- API接口：`backend/main.py` - `/api/smart-generate`
- Service类：`backend/services/`
  - `hybrid_classifier.py` - FrameworkGenerator
  - `scholarflux_wrapper.py` - ScholarFlux
  - `paper_filter.py` - PaperFilterService
  - `review_generator.py` - ReviewGeneratorService
  - `reference_validator.py` - ReferenceValidator
  - `review_record_service.py` - ReviewRecordService

## 更新历史

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-03-31 | 2.1 | 增加初始文献搜索数量：每个查询100篇，补充搜索200篇，确保至少150篇 |
| 2026-03-31 | 2.0 | 重构验证流程：验证被引用文献而非候选池 |
| 2026-03-30 | 1.0 | 初始版本 |
