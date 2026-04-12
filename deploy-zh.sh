#!/bin/bash
# ============================================
# AutoOverview 中文前端 + 后端 - 首次部署
# 在上海服务器本地运行 (14.103.210.88)
# 使用 Nginx + systemd
# ============================================

set -e

APP_DIR="/app/AutoOverview"
BACKEND_PORT=8006

echo "=========================================="
echo " AutoOverview 中文版 - 首次部署"
echo "=========================================="

# ---------- 1. 拉取代码 ----------
echo ""
echo "[1/4] 拉取代码..."
if [ ! -d "$APP_DIR" ]; then
    git clone git@github.com:zhancongc/AutoOverview.git "$APP_DIR"
    cd "$APP_DIR"
else
    cd "$APP_DIR"
    git pull
fi
echo "✓ 代码已更新"

# ---------- 2. 构建中文前端 ----------
echo ""
echo "[2/4] 构建中文前端..."
cd frontend
npm install
npm run build
echo "✓ 构建完成: $APP_DIR/frontend/dist/"

# ---------- 3. 配置后端 ----------
echo ""
echo "[3/4] 配置后端..."
cd "$APP_DIR/backend"

# Python 依赖
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
fi

# systemd 服务
cat > /etc/systemd/system/autooverview.service << SERVICE
[Unit]
Description=AutoOverview Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
Restart=always
RestartSec=5
Environment=IS_DEV=false

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable autooverview
systemctl restart autooverview
echo "✓ 后端已启动 (端口 $BACKEND_PORT)"

# ---------- 4. 配置 Nginx ----------
echo ""
echo "[4/4] 配置 Nginx..."

if ! command -v nginx &> /dev/null; then
    echo "安装 Nginx..."
    apt-get update -qq && apt-get install -y nginx
fi

# 写入 Nginx 站点配置
cat > /etc/nginx/sites-available/autooverview << 'NGINXCONF'
upstream autooverview_backend {
    server 127.0.0.1:8006;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;

    client_max_body_size 10M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 1000;
    gzip_comp_level 6;

    # Backend API proxy
    location /api {
        proxy_pass http://autooverview_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /docs { proxy_pass http://autooverview_backend; }
    location /openapi.json { proxy_pass http://autooverview_backend; }
    location /redoc { proxy_pass http://autooverview_backend; }

    # Frontend static files
    root /app/AutoOverview/frontend/dist;
    index index.html;

    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public";
        try_files $uri =404;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security
    location ~ /\.ht { deny all; return 404; }
    location ~ /\.git { deny all; return 404; }
    location ~ /\.env { deny all; return 404; }
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
NGINXCONF

ln -sf /etc/nginx/sites-available/autooverview /etc/nginx/sites-enabled/autooverview
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl reload nginx
echo "✓ Nginx 配置完成"

# ---------- 验证 ----------
echo ""
sleep 2
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/api/paddle/plans)
WEB_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1)
echo "  API: $API_CODE | 前端: $WEB_CODE"

echo ""
echo "=========================================="
echo " 部署完成"
echo " 前端: http://$(curl -s ifconfig.me)"
echo " API:  http://127.0.0.1:$BACKEND_PORT"
echo "=========================================="
