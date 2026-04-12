#!/bin/bash
# ============================================
# AutoOverview 英文版前端 - 首次部署脚本
# 在服务器本地运行 (14.103.210.88)
# 域名: autooverview.plainkit.top
# ============================================

set -e

# ---------- 配置 ----------
DOMAIN="autooverview.plainkit.top"
EMAIL="zhancongc@icloud.com"
APP_DIR="/opt/autooverview-en"
DIST_DIR="$APP_DIR/dist"
BACKEND_PORT=8006

echo "=========================================="
echo " AutoOverview 英文版 - 首次部署"
echo " 域名: $DOMAIN"
echo "=========================================="

# ---------- 1. 拉取代码 ----------
echo ""
echo "[1/4] 拉取最新代码..."
if [ ! -d "$APP_DIR" ]; then
    git clone git@github.com:zhancongc/AutoOverview.git "$APP_DIR"
    cd "$APP_DIR"
else
    cd "$APP_DIR"
    git pull
fi
echo "✓ 代码已更新"

# ---------- 2. 构建 ----------
echo ""
echo "[2/4] 构建英文版前端..."
cd frontend
npm install
npm run build:en
echo "✓ 构建完成: $DIST_DIR"

# ---------- 3. 配置 Caddy ----------
echo ""
echo "[3/4] 配置 Caddy..."

# 安装 Caddy（如果未安装）
if ! command -v caddy &> /dev/null; then
    echo "安装 Caddy..."
    yum install -y yum-utils
    yum-config-manager --add-repo https://caddyserver.com/api/download?dist=el&arch=amd64
    yum install -y caddy
fi

# 写入 Caddy 配置
cat > /etc/caddy/Caddyfile << CADDYCONF
$DOMAIN {
    root * $DIST_DIR
    file_server
    encode gzip

    # SPA 路由：非文件请求返回 index.html
    try_files {path} /index.html

    # API 反向代理到后端
    reverse_proxy /api/* 127.0.0.1:$BACKEND_PORT

    # 静态资源缓存
    @static path *.js *.css *.png *.jpg *.svg *.woff *.woff2
    header @static Cache-Control "public, max-age=31536000, immutable"

    # HTML 不缓存
    @html path *.html /
    header @html Cache-Control "no-cache, no-store, must-revalidate"

    # 安全头
    header X-Content-Type-Options "nosniff"
    header X-Frame-Options "DENY"

    tls $EMAIL
}
CADDYCONF

# 验证并启动
caddy validate --config /etc/caddy/Caddyfile
systemctl enable caddy
systemctl restart caddy
echo "✓ Caddy 配置完成"

# ---------- 4. 验证 ----------
echo ""
echo "[4/4] 验证部署..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ 部署成功！访问 https://$DOMAIN"
else
    echo "⚠ HTTP 状态码: $HTTP_CODE，请检查 Caddy 和 DNS 配置"
    echo "  - 确保 DNS 已将 $DOMAIN 指向本机"
    echo "  - 检查防火墙是否开放 80/443 端口"
fi

echo ""
echo "=========================================="
echo " 部署完成"
echo " 网站: https://$DOMAIN"
echo " 文件: $DIST_DIR"
echo "=========================================="
