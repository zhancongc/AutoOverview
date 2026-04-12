#!/bin/bash
# ============================================
# AutoOverview 中文前端 + 后端 - 更新脚本
# 在上海服务器本地运行
# git pull → 构建前端 → 重启后端
# ============================================

set -e

APP_DIR="/app/AutoOverview"
BACKEND_PORT=8006

echo "=========================================="
echo " AutoOverview 中文版 - 更新"
echo "=========================================="

# ---------- 1. 拉取代码 ----------
echo ""
echo "[1/3] 拉取最新代码..."
cd "$APP_DIR"
git pull
echo "✓ 代码已更新"

# ---------- 2. 构建中文前端 ----------
echo ""
echo "[2/3] 构建中文前端..."
cd frontend
npm install
npm run build
echo "✓ 前端构建完成"

# ---------- 3. 重启后端 ----------
echo ""
echo "[3/3] 重启后端..."
cd "$APP_DIR/backend"

# 安装新增依赖
[ -f "requirements.txt" ] && pip3 install -q -r requirements.txt

systemctl restart autooverview
echo "✓ 后端已重启"

sleep 2
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/api/paddle/plans)
echo ""
echo "=========================================="
echo " 更新完成 (API: $API_CODE)"
echo "=========================================="
