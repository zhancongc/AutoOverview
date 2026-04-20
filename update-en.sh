#!/bin/bash
# ============================================
# AutoOverview 英文版前端 - 更新脚本
# 在服务器本地运行
# git pull → 构建 → 直接生效
# ============================================

set -e

APP_DIR="/app/AutoOverview"
DIST_DIR="$APP_DIR/frontend/dist-en"
START_TIME=$(date +%s)

echo "=========================================="
echo " AutoOverview 英文版 - 更新"
echo " 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
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

# 清空旧构建产物，避免新旧文件混杂
rm -rf dist-en
npm run build:en
echo "✓ 构建完成"

# Caddy 直接读 dist-en 目录，静态文件更新后自动生效
echo "✓ 已更新，访问 https://autooverview.plainkit.top"
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))
echo ""
echo "=========================================="
echo " 更新完成"
echo " 耗时: ${MINUTES}分${SECONDS}秒"
echo "=========================================="
