#!/bin/bash
# ============================================
# AutoOverview 中文前端 + 后端 - 更新脚本
# 在上海服务器本地运行
# git pull → 构建前端 → 数据库迁移 → 更新服务配置 → 重启后端
# ============================================

set -e

APP_DIR="/app/AutoOverview"
BACKEND_PORT=8006
START_TIME=$(date +%s)

echo "=========================================="
echo " AutoOverview 中文版 - 更新"
echo " 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ---------- 1. 拉取代码 ----------
echo ""
echo "[1/5] 拉取最新代码..."
cd "$APP_DIR"
git pull
echo "✓ 代码已更新"

# ---------- 2. 构建中文前端 ----------
echo ""
echo "[2/5] 构建中文前端..."
cd frontend
npm install

# 清空旧构建产物，避免新旧文件混杂
rm -rf dist-zh
npm run build
echo "✓ 前端构建完成"

# ---------- 3. 数据库迁移 ----------
echo ""
echo "[3/5] 检查数据库迁移..."
cd "$APP_DIR/backend"
"$APP_DIR/backend/.venv/bin/python" "$APP_DIR/backend/migrations/base.py" migrate --dir "$APP_DIR/backend/migrations"
echo "✓ 数据库迁移完成"

# ---------- 4. 更新 systemd 服务配置 ----------
echo ""
echo "[4/5] 更新服务配置..."
if [ -f "$APP_DIR/autooverview.service" ]; then
    cp "$APP_DIR/autooverview.service" /etc/systemd/system/autooverview.service
    systemctl daemon-reload
    echo "✓ 服务配置已更新"
else
    echo "⚠ 未找到 autooverview.service，跳过"
fi

# ---------- 5. 重启后端 ----------
echo ""
echo "[5/5] 重启后端..."

# 安装新增依赖（使用 venv）
[ -f "requirements.txt" ] && "$APP_DIR/backend/.venv/bin/pip" install -q -r requirements.txt

systemctl restart autooverview
echo "✓ 后端已重启"

sleep 2
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/api/health)
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))
echo ""
echo "=========================================="
echo " 更新完成 (API: $API_CODE)"
echo " 耗时: ${MINUTES}分${SECONDS}秒"
echo "=========================================="
