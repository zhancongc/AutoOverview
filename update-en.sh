#!/bin/bash
# ============================================
# AutoOverview 英文版前端 - 更新脚本
# 在服务器本地运行
# git pull → 构建 → 直接生效
# ============================================

set -e

APP_DIR="/app/AutoOverview"
DIST_DIR="$APP_DIR/frontend/dist-en"

echo "=========================================="
echo " AutoOverview 英文版 - 更新"
echo "=========================================="

# ---------- 1. 拉取最新代码 ----------
echo ""
echo "[1/2] 拉取最新代码..."
cd "$APP_DIR"
git pull origin main 
echo "✓ 代码已更新"

# ---------- 2. 构建英文版 ----------
echo ""
echo "[2/2] 构建英文版前端..."
cd frontend
npm install
npm run build:en
echo "✓ 构建完成"

# Caddy 直接读 dist-en 目录，静态文件更新后自动生效
echo "✓ 已更新，访问 https://autooverview.plainkit.top"
echo ""
echo "=========================================="
echo " 更新完成"
echo "=========================================="
