#!/bin/bash
# ============================================
# AutoOverview 英文版前端 - 首次部署脚本
# 在服务器本地运行
# 域名: autooverview.plainkit.top
# 证书: 复用 Cloudflare *.plainkit.top 通配符证书
# ============================================

set -e

# ---------- 配置 ----------
DOMAIN="autooverview.plainkit.top"
APP_DIR="/opt/autooverview-en"
DIST_DIR="$APP_DIR/frontend/dist-en"
# 上海后端服务器
BACKEND_HOST="14.103.210.88"
BACKEND_PORT=8006
SSL_CERT="/etc/ssl/cloudflare/plainkit.top.pem"
SSL_KEY="/etc/ssl/cloudflare/plainkit.top-key.pem"
CADDY_SITE_CONF="/etc/caddy/sites/autooverview.plainkit.top.conf"

echo "=========================================="
echo " AutoOverview 英文版 - 首次部署"
echo " 域名: $DOMAIN"
echo "=========================================="

# ---------- 0. 检查证书 ----------
echo ""
echo "[0/4] 检查 Cloudflare 证书..."
if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "✗ 证书不存在: $SSL_CERT 或 $SSL_KEY"
    echo "  请先部署 Cloudflare Origin 证书"
    exit 1
fi
echo "✓ 证书就绪"

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

mkdir -p /etc/caddy/sites

# 确保主 Caddyfile 使用 import 模式（不覆盖现有站点）
if ! grep -q "import sites" /etc/caddy/Caddyfile 2>/dev/null; then
    echo "初始化主 Caddyfile..."
    cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak
    cat > /etc/caddy/Caddyfile << 'MAINCONF'
{
    email zhancongc@icloud.com
}

import sites/*.conf
MAINCONF
fi

# 写入 Caddy 站点配置（与现有 plainkit.top.conf 同级）
cat > "$CADDY_SITE_CONF" << CADDYCONF
$DOMAIN {
    tls $SSL_CERT $SSL_KEY

    encode gzip

    # API 反向代理到上海后端
    handle /api/* {
        reverse_proxy $BACKEND_HOST:$BACKEND_PORT
    }

    # 静态文件服务 + SPA 路由
    handle {
        root * $DIST_DIR
        try_files {path} /index.html
        file_server

        # 静态资源缓存
        @static path *.js *.css *.png *.jpg *.svg *.woff *.woff2
        header @static Cache-Control "public, max-age=31536000, immutable"

        # HTML 不缓存
        @html path *.html /
        header @html Cache-Control "no-cache, no-store, must-revalidate"
    }

    # 安全头
    header X-Content-Type-Options "nosniff"
    header X-Frame-Options "DENY"
}
CADDYCONF

# 验证并重载
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
echo "✓ Caddy 配置完成"

# ---------- 4. 验证 ----------
echo ""
echo "[4/4] 验证部署..."
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ 部署成功！访问 https://$DOMAIN"
else
    echo "⚠ HTTP 状态码: $HTTP_CODE"
    echo "  检查: systemctl status caddy && journalctl -u caddy -n 20"
fi

echo ""
echo "=========================================="
echo " 部署完成"
echo " 网站: https://$DOMAIN"
echo " 文件: $DIST_DIR"
echo " Caddy: $CADDY_SITE_CONF"
echo "=========================================="
