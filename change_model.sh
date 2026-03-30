#!/bin/bash

# Claude 配置根目录
CLAUDE_DIR="$HOME/.claude"
MODELS_DIR="${CLAUDE_DIR}/models"
CLAUDE_BIN="$HOME/.local/bin/claude"

# 显示用法
usage() {
    echo "用法: $0 {aliyun|glm|doubao}"
    exit 1
}

# 检查参数个数
if [ $# -ne 1 ]; then
    usage
fi

MODEL="$1"
SOURCE_FILE="${MODELS_DIR}/settings.json.${MODEL}"
TARGET_FILE="${CLAUDE_DIR}/settings.json"

# 检查模型配置文件是否存在
if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ 错误: 找不到模型配置文件 $SOURCE_FILE"
    exit 1
fi

# 可选：备份当前 settings.json（如果存在）
if [ -f "$TARGET_FILE" ]; then
    BACKUP_FILE="${TARGET_FILE}.backup.$(date +%Y%m%d%H%M%S)"
    cp "$TARGET_FILE" "$BACKUP_FILE"
    echo "📦 已备份当前配置为 $(basename $BACKUP_FILE)"
fi

# 复制模型配置文件到目标位置
cp "$SOURCE_FILE" "$TARGET_FILE"
echo "✅ 已切换到模型: $MODEL (配置文件: settings.json.${MODEL})"

# 启动 Claude
exec "$CLAUDE_BIN"
