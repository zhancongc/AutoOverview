"""
进度消息国际化
提供中英文进度消息
"""

# 进度消息翻译表
PROGRESS_MESSAGES = {
    "waiting": {
        "zh": "系统繁忙，排队中…前面还有 {queue_pos} 个任务（约需等待 {queue_pos * 3} 分钟）",
        "en": "System busy, queuing... {queue_pos} tasks ahead (approx. {queue_pos * 3} min wait)"
    },
    "preparing": {
        "zh": "正在准备...",
        "en": "Preparing..."
    },
    "searching": {
        "zh": "正在搜索文献...",
        "en": "Searching papers..."
    },
    "papers_found": {
        "zh": "已找到 {papers_count} 篇相关文献，正在生成综述...",
        "en": "Found {papers_count} related papers, generating review..."
    },
    "generating": {
        "zh": "正在生成综述...",
        "en": "Generating review..."
    },
    "generating_matrix": {
        "zh": "正在生成对比矩阵...",
        "en": "Generating comparison matrix..."
    }
}


def get_progress_message(step: str, language: str = "zh", **kwargs) -> str:
    """
    获取对应语言的进度消息

    Args:
        step: 步骤名称 (waiting/preparing/searching/generating/generating_matrix)
        language: 语言代码 (zh/en)
        **kwargs: 模板参数 (如 queue_pos)

    Returns:
        本地化的进度消息
    """
    if language not in ["zh", "en"]:
        language = "zh"

    messages = PROGRESS_MESSAGES.get(step, {})
    message_template = messages.get(language, messages.get("zh", ""))

    try:
        return message_template.format(**kwargs)
    except (KeyError, IndexError):
        return message_template


def get_progress(step: str, language: str = "zh", **kwargs) -> dict:
    """
    获取进度对象（包含 step 和 message）

    Args:
        step: 步骤名称
        language: 语言代码
        **kwargs: 模板参数

    Returns:
        {"step": str, "message": str}
    """
    return {
        "step": step,
        "message": get_progress_message(step, language, **kwargs)
    }
