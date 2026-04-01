# 异步API使用文档

## 概述

从 v4.0 开始，综述生成接口采用异步任务模式，避免长时间等待导致超时。

## API 接口

### 1. 提交任务

**接口**: `POST /api/smart-generate`

**请求参数**:
```json
{
  "topic": "基于FMEA法的Agent开发项目风险管理研究",
  "target_count": 50,
  "recent_years_ratio": 0.5,
  "english_ratio": 0.3,
  "search_years": 10,
  "max_search_queries": 8
}
```

**响应**:
```json
{
  "success": true,
  "message": "任务已提交，请使用任务ID查询进度",
  "data": {
    "task_id": "751bdaa7",
    "topic": "基于FMEA法的Agent开发项目风险管理研究",
    "status": "pending",
    "poll_url": "/api/tasks/751bdaa7"
  }
}
```

### 2. 查询任务状态

**接口**: `GET /api/tasks/{task_id}`

**响应（处理中）**:
```json
{
  "success": true,
  "data": {
    "task_id": "751bdaa7",
    "topic": "基于FMEA法的Agent开发项目风险管理研究",
    "status": "processing",
    "progress": {
      "step": "searching",
      "message": "正在搜索文献 (3/8)..."
    },
    "created_at": "2026-04-01T10:30:00",
    "started_at": "2026-04-01T10:30:01",
    "completed_at": null,
    "error": null,
    "has_result": false
  }
}
```

**响应（已完成）**:
```json
{
  "success": true,
  "data": {
    "task_id": "751bdaa7",
    "status": "completed",
    "progress": {},
    "result": {
      "id": 123,
      "topic": "...",
      "review": "综述内容...",
      "papers": [...],
      "statistics": {...},
      "cited_papers_count": 52
    }
  }
}
```

**响应（失败）**:
```json
{
  "success": true,
  "data": {
    "task_id": "751bdaa7",
    "status": "failed",
    "error": "未找到相关文献",
    "completed_at": "2026-04-01T10:32:00"
  }
}
```

## 任务状态

| 状态 | 说明 |
|------|------|
| `pending` | 等待执行 |
| `processing` | 执行中 |
| `completed` | 完成 |
| `failed` | 失败 |

## 进度信息

处理中的任务会返回 `progress` 对象：

```json
{
  "step": "searching",      // 当前步骤
  "message": "正在搜索文献..."  // 进度描述
}
```

**步骤说明**:
- `analyzing`: 正在分析题目
- `searching`: 正在搜索文献
- `filtering`: 正在筛选文献
- `generating`: 正在生成综述
- `validating`: 正在验证和修复引用

## 前端集成示例

### JavaScript/TypeScript

```typescript
// 1. 提交任务
async function submitReviewTask(params) {
  const response = await fetch('http://localhost:8000/api/smart-generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  const result = await response.json();
  return result.data.task_id;
}

// 2. 轮询任务状态
async function pollTaskStatus(taskId) {
  const response = await fetch(`http://localhost:8000/api/tasks/${taskId}`);
  const result = await response.json();
  return result.data;
}

// 3. 完整流程
async function generateReview(topic) {
  // 提交任务
  const taskId = await submitReviewTask({
    topic,
    target_count: 50,
    recent_years_ratio: 0.5,
    english_ratio: 0.3,
  });

  console.log('任务已提交:', taskId);

  // 轮询直到完成
  while (true) {
    const taskInfo = await pollTaskStatus(taskId);

    if (taskInfo.status === 'completed') {
      return taskInfo.result;
    }

    if (taskInfo.status === 'failed') {
      throw new Error(taskInfo.error);
    }

    // 显示进度
    console.log(taskInfo.progress?.message || taskInfo.status);

    // 等待1秒
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}
```

### React Hook

```typescript
function useReviewGeneration() {
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const submitTask = async (params) => {
    const response = await fetch('/api/smart-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    const data = await response.json();
    setTaskId(data.data.task_id);
    setStatus('polling');
  };

  useEffect(() => {
    if (status !== 'polling' || !taskId) return;

    const interval = setInterval(async () => {
      const response = await fetch(`/api/tasks/${taskId}`);
      const data = await response.json();
      const taskInfo = data.data;

      setProgress(taskInfo.progress || {});

      if (taskInfo.status === 'completed') {
        setStatus('completed');
        setResult(taskInfo.result);
        clearInterval(interval);
      } else if (taskInfo.status === 'failed') {
        setStatus('error');
        setError(taskInfo.error);
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [status, taskId]);

  return { status, progress, result, error, submitTask };
}
```

## 轮询建议

1. **轮询间隔**: 建议 1-2 秒
2. **超时时间**: 建议设置 2-5 分钟超时
3. **进度显示**: 显示 `progress.message` 给用户
4. **错误处理**: 处理 `failed` 状态和异常

## 兼容性

旧版同步接口仍然可用：`POST /api/smart-generate-sync`

但推荐使用新的异步接口以获得更好的用户体验。
