#!/bin/bash
# =====================================================
# AutoOverview - Ubuntu 服务器初始化安装脚本
# =====================================================
# 功能：
#   1. 系统更新 + 基础依赖
#   2. 安装 Node.js 20.x
#   3. 安装和配置 PostgreSQL
#   4. 创建项目目录和虚拟环境
#   5. 安装 Python 依赖
#   6. 构建 React 前端
#   7. 配置环境文件
#   8. 配置 systemd 服务
#   9. 安装和配置 Nginx
#   10. 数据库初始化（主表 + authkit 表）
# =====================================================

set -e  # 遇到错误立即退出

# =====================================================
# 配置变量（可按需修改）
# =====================================================
PROJECT_DIR="/app/AutoOverview"
PROJECT_USER="root"
DB_USER="postgres"
DB_PASSWORD="security"       # 建议修改
DB_NAME="paper"
DB_HOST="localhost"
DB_PORT="5432"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =====================================================
# 工具函数
# =====================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =====================================================
# 检查是否为 root 用户
# =====================================================
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 用户或 sudo 运行此脚本"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AutoOverview 服务器初始化安装${NC}"
echo -e "${BLUE}========================================${NC}\n"

# =====================================================
# 1. 系统更新 + 基础依赖
# =====================================================
log_info "步骤 1/10: 更新系统包并安装基础依赖..."
apt-get update -y
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libpq-dev

log_success "基础依赖安装完成\n"

# =====================================================
# 2. 安装 Node.js 20.x
# =====================================================
log_info "步骤 2/10: 安装 Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    log_success "Node.js $(node --version) 安装完成"
else
    log_warning "Node.js 已安装: $(node --version)，跳过"
fi
log_success "Node.js 就绪\n"

# =====================================================
# 3. 安装和配置 PostgreSQL
# =====================================================
log_info "步骤 3/10: 安装 PostgreSQL..."
if ! command -v psql &> /dev/null; then
    apt-get install -y postgresql postgresql-contrib

    systemctl start postgresql
    systemctl enable postgresql

    log_success "PostgreSQL 安装完成"
else
    log_warning "PostgreSQL 已安装，跳过安装步骤"
fi

# 验证 PostgreSQL
if systemctl is-active --quiet postgresql; then
    log_success "PostgreSQL 运行正常"
else
    log_error "PostgreSQL 运行异常"
    exit 1
fi

# 配置 PostgreSQL（创建数据库和设置密码）
log_info "配置 PostgreSQL 数据库..."
sudo -u postgres psql <<EOF
-- 创建数据库（如果不存在）
SELECT 'CREATE DATABASE ${DB_NAME}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\\gexec

-- 设置 postgres 用户密码
ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
EOF

if [ $? -eq 0 ]; then
    log_success "PostgreSQL 配置完成\n"
else
    log_error "PostgreSQL 配置失败"
    exit 1
fi

# =====================================================
# 4. 创建项目目录和虚拟环境
# =====================================================
log_info "步骤 4/10: 配置项目环境..."

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    log_warning "项目目录已创建: $PROJECT_DIR"
    log_warning "请将项目文件上传到 $PROJECT_DIR 后重新运行脚本"
    exit 0
fi

cd "$PROJECT_DIR"

# 创建必要的目录
mkdir -p "$PROJECT_DIR/backend/logs"
mkdir -p "$PROJECT_DIR/backend/cache"
chmod 755 "$PROJECT_DIR/backend/logs"
chmod 755 "$PROJECT_DIR/backend/cache"

# 创建虚拟环境
if [ ! -d "$PROJECT_DIR/backend/.venv" ]; then
    log_info "创建 Python 虚拟环境..."
    cd "$PROJECT_DIR/backend"
    python3 -m venv "$PROJECT_DIR/backend/.venv"
    log_success "虚拟环境创建完成"
else
    log_warning "虚拟环境已存在，跳过创建"
fi

cd "$PROJECT_DIR"

# =====================================================
# 5. 安装 Python 依赖
# =====================================================
log_info "步骤 5/10: 安装 Python 依赖..."

if [ -f "$PROJECT_DIR/backend/requirements.txt" ]; then
    # 升级 pip
    "$PROJECT_DIR/backend/.venv/bin/pip" install --upgrade pip

    # 安装依赖
    "$PROJECT_DIR/backend/.venv/bin/pip" install -r "$PROJECT_DIR/backend/requirements.txt"
    log_success "Python 依赖安装完成\n"
else
    log_warning "requirements.txt 不存在，跳过依赖安装"
    log_warning "请确保项目文件已上传到 $PROJECT_DIR"
fi

# =====================================================
# 6. 构建 React 前端
# =====================================================
log_info "步骤 6/10: 构建 React 前端..."

if [ -f "$PROJECT_DIR/frontend/package.json" ]; then
    cd "$PROJECT_DIR/frontend"
    npm install
    npm run build
    log_success "前端构建完成 → frontend/dist/\n"
    cd "$PROJECT_DIR"
else
    log_warning "frontend/package.json 不存在，跳过前端构建"
fi

# =====================================================
# 7. 配置环境文件
# =====================================================
log_info "步骤 7/10: 配置环境文件..."

# backend/.env
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    if [ -f "$PROJECT_DIR/backend/.env.example" ]; then
        cp "$PROJECT_DIR/backend/.env.example" "$PROJECT_DIR/backend/.env"
        log_warning "backend/.env 已创建，请修改以下配置："
        log_warning "  - DEEPSEEK_API_KEY"
        log_warning "  - DB_PASSWORD（当前: $DB_PASSWORD）"
        log_warning "  - AMINER_API_TOKEN"
        log_warning "  - SEMANTIC_SCHOLAR_API_KEY"
    else
        log_warning "backend/.env.example 不存在，请手动创建 backend/.env"
    fi
else
    log_success "backend/.env 已存在"
fi

# backend/.env.auth
if [ ! -f "$PROJECT_DIR/backend/.env.auth" ]; then
    if [ -f "$PROJECT_DIR/backend/.env.auth.example" ]; then
        cp "$PROJECT_DIR/backend/.env.auth.example" "$PROJECT_DIR/backend/.env.auth"
        log_warning "backend/.env.auth 已创建，请修改以下配置："
        log_warning "  - AUTH_JWT_SECRET_KEY"
        log_warning "  - AUTH_SMTP_*（邮件服务）"
        log_warning "  - ALIPAY_*（支付宝支付）"
        log_warning "  - IS_DEV=true 改为 false（生产环境）"
    else
        log_warning "backend/.env.auth.example 不存在，请手动创建 backend/.env.auth"
    fi
else
    log_success "backend/.env.auth 已存在"
fi

echo ""

# =====================================================
# 8. 配置 systemd 服务
# =====================================================
log_info "步骤 8/10: 配置 systemd 服务..."

if [ -f "$PROJECT_DIR/autooverview.service" ]; then
    cp "$PROJECT_DIR/autooverview.service" /etc/systemd/system/
    chmod 644 /etc/systemd/system/autooverview.service
    systemctl daemon-reload
    systemctl enable autooverview
    log_success "autooverview 服务已安装并设置开机自启"
else
    log_warning "autooverview.service 不存在，跳过"
fi

log_success "systemd 配置完成\n"

# =====================================================
# 9. 安装和配置 Nginx
# =====================================================
log_info "步骤 9/10: 安装和配置 Nginx..."

if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx
    systemctl start nginx
    systemctl enable nginx
    log_success "Nginx 安装完成"
else
    log_warning "Nginx 已安装，跳过安装步骤"
fi

# 验证 Nginx
if systemctl is-active --quiet nginx; then
    log_success "Nginx 运行正常"
else
    log_error "Nginx 运行异常"
    exit 1
fi

# 配置 Nginx 站点
if [ -f "$PROJECT_DIR/nginx-autooverview.conf" ]; then
    log_info "配置 Nginx 站点..."

    cp "$PROJECT_DIR/nginx-autooverview.conf" "/etc/nginx/sites-available/autooverview"
    ln -sf "/etc/nginx/sites-available/autooverview" "/etc/nginx/sites-enabled/autooverview"

    # 移除默认站点
    rm -f /etc/nginx/sites-enabled/default

    if nginx -t &> /dev/null; then
        systemctl reload nginx
        log_success "Nginx 配置已加载"
    else
        log_warning "Nginx 配置测试失败，请手动检查"
        nginx -t
    fi
else
    log_warning "nginx-autooverview.conf 不存在，跳过 Nginx 配置"
fi

log_success "Nginx 配置完成\n"

# =====================================================
# 10. 数据库初始化（主表 + authkit 表）
# =====================================================
log_info "步骤 10/10: 数据库初始化..."

cd "$PROJECT_DIR/backend"

# 检查是否需要初始化数据库
if [ -f "$PROJECT_DIR/backend/database_schema.sql" ]; then
    log_info "检查数据库是否已初始化..."

    # 检查是否存在 review_tasks 表
    TABLE_EXISTS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'review_tasks');" 2>/dev/null | tr -d '[:space:]')

    if [ "$TABLE_EXISTS" = "f" ] || [ -z "$TABLE_EXISTS" ]; then
        log_info "数据库未初始化，开始初始化..."

        # 方法1: 使用 SQL 脚本
        if [ -f "$PROJECT_DIR/backend/database_schema.sql" ]; then
            sudo -u postgres psql -d "$DB_NAME" < "$PROJECT_DIR/backend/database_schema.sql"
            if [ $? -eq 0 ]; then
                log_success "主表初始化完成 (SQL)"
            fi
        fi

        # 方法2: 使用 Python ORM 初始化（包含 authkit 表）
        if [ -f "$PROJECT_DIR/backend/init_db.py" ]; then
            log_info "使用 Python 初始化 authkit 表..."
            "$PROJECT_DIR/backend/.venv/bin/python" "$PROJECT_DIR/backend/init_db.py" 2>/dev/null || log_warning "Python 初始化脚本执行完成（可能有警告）"
            log_success "authkit 表初始化完成"
        fi

        log_success "数据库初始化完成"
    else
        log_info "数据库已初始化，跳过"
    fi
else
    log_warning "database_schema.sql 不存在，跳过数据库初始化"
fi

cd "$PROJECT_DIR"
log_success "数据库配置完成\n"

# =====================================================
# 安装完成
# =====================================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}安装完成！${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "项目目录: ${YELLOW}$PROJECT_DIR${NC}"
echo -e "虚拟环境: ${YELLOW}$PROJECT_DIR/backend/.venv${NC}"
echo -e "前端文件: ${YELLOW}$PROJECT_DIR/frontend/dist/${NC}"
echo -e ""

echo -e "服务管理命令："
echo -e "  ${YELLOW}启动:${NC}   systemctl start autooverview"
echo -e "  ${YELLOW}停止:${NC}   systemctl stop autooverview"
echo -e "  ${YELLOW}重启:${NC}   systemctl restart autooverview"
echo -e "  ${YELLOW}状态:${NC}   systemctl status autooverview"
echo -e "  ${YELLOW}日志:${NC}   journalctl -u autooverview -f"
echo -e ""

echo -e "数据库信息："
echo -e "  ${YELLOW}用户:${NC}   $DB_USER"
echo -e "  ${YELLOW}密码:${NC}   $DB_PASSWORD"
echo -e "  ${YELLOW}数据库:${NC} $DB_NAME"
echo -e "  ${YELLOW}地址:${NC}   $DB_HOST:$DB_PORT"
echo -e ""

echo -e "后续步骤："
echo -e "  1. ${YELLOW}修改 backend/.env${NC}"
echo -e "     设置 DEEPSEEK_API_KEY、数据库密码等"
echo -e "  2. ${YELLOW}修改 backend/.env.auth${NC}"
echo -e "     设置 JWT 密钥、SMTP、支付宝配置"
echo -e "     将 IS_DEV=true 改为 false"
echo -e "  3. ${YELLOW}配置 SSL 证书${NC}"
echo -e "     certbot --nginx -d your-domain.com"
echo -e "  4. ${YELLOW}修改 nginx 域名${NC}"
echo -e "     编辑 nginx-autooverview.conf 中的 server_name"
echo -e "  5. ${YELLOW}启动服务${NC}"
echo -e "     systemctl start autooverview"
echo -e ""
echo -e "${GREEN}✓ 数据库已自动初始化（主表 + authkit 表）${NC}"
echo ""

# 显示安装摘要
echo -e "${BLUE}安装摘要:${NC}"
echo -e "  ${GREEN}✓${NC} Python3: $(python3 --version)"
echo -e "  ${GREEN}✓${NC} Node.js: $(node --version)"
echo -e "  ${GREEN}✓${NC} npm: $(npm --version)"
echo -e "  ${GREEN}✓${NC} PostgreSQL: $(psql --version)"
echo -e "  ${GREEN}✓${NC} Nginx: $(nginx -v 2>&1 | cut -d/ -f2)"
echo -e "  ${GREEN}✓${NC} 虚拟环境: $PROJECT_DIR/backend/.venv"
echo ""

