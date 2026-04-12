#!/bin/bash
# ============================================
# AutoOverview 英文版前端 - 更新脚本
# 拉取最新代码 → 构建 → 上传 → 生效
# ============================================

set -e

DOMAIN="autooverview.plainkit.top"
REMOTE_USER="root"
REMOTE_HOST="14.103.210.88"
REMOTE_DIR="/opt/autooverview-en"

echo "=========================================="
echo " AutoOverview 英文版 - 更新"
echo "=========================================="

# ---------- 1. 拉取最新代码 ----------
echo ""
echo "[1/3] 拉取最新代码..."
cd "$(dirname "$0")"
git pull
echo "✓ 代码已更新"

# ---------- 2. 构建英文版 ----------
echo ""
echo "[2/3] 构建英文版前端..."
cd frontend
npm install
npm run build:en
echo "✓ 构建完成"

# ---------- 3. 上传并生效 ----------
echo ""
echo "[3/3] 上传到服务器..."
rsync -avz --delete dist-en/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/dist/

# Caddy 静态文件无需重启，直接生效
echo "✓ 已更新，访问 https://$DOMAIN"
echo ""
echo "=========================================="
echo " 更新完成"
echo "=========================================="
