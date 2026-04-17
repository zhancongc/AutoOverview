#!/bin/bash
# =====================================================
# AutoOverview - 域名迁移脚本
# =====================================================
# 功能：将域名从 autooverview.snappicker.com 迁移到 autooverview.danmo.tech
# =====================================================

set -e

OLD_DOMAIN="autooverview.snappicker.com"
NEW_DOMAIN="autooverview.danmo.tech"
NGINX_CONF="/etc/nginx/sites-available/autooverview"
NGINX_CONF_SOURCE="nginx-autooverview.conf"
CERTBOT_EMAIL="service@danmo.tech"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 root
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 用户运行此脚本"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AutoOverview 域名迁移${NC}"
echo -e "${BLUE}旧域名: ${OLD_DOMAIN}${NC}"
echo -e "${BLUE}新域名: ${NEW_DOMAIN}${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 确认
read -p "确认继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "已取消"
    exit 0
fi

# 1. 检查 certbot
log_info "检查 certbot..."
if ! command -v certbot &> /dev/null; then
    log_info "安装 certbot..."
    apt-get update -y
    apt-get install -y certbot python3-certbot-nginx
    log_success "certbot 安装完成"
else
    log_success "certbot 已安装: $(certbot --version 2>&1)"
fi

# 2. 创建 certbot challenge 目录
mkdir -p /var/www/certbot
log_success "certbot challenge 目录就绪"

# 3. 备份旧的 nginx 配置
if [ -f "$NGINX_CONF" ]; then
    log_info "备份旧 nginx 配置..."
    cp "$NGINX_CONF" "${NGINX_CONF}.bak.$(date +%Y%m%d_%H%M%S)"
    log_success "旧配置已备份"
fi

# 4. 更新 nginx 配置文件
log_info "更新 nginx 配置..."
if [ -f "$NGINX_CONF_SOURCE" ]; then
    # 使用项目中的配置文件进行替换
    cp "$NGINX_CONF_SOURCE" "$NGINX_CONF"
    log_success "已复制项目配置到 $NGINX_CONF"
else
    log_warning "本地配置文件不存在，直接修改现有配置"
fi

# 替换所有旧域名为新域名
log_info "将域名从 $OLD_DOMAIN 更新为 $NEW_DOMAIN..."
sed -i "s/${OLD_DOMAIN}/${NEW_DOMAIN}/g" "$NGINX_CONF"
log_success "域名已更新"

# 5. 临时启用 HTTP 用于证书申请
log_info "配置临时 HTTP 服务用于证书申请..."

# 确保配置中有 http server 配置
if ! grep -q "listen 80;" "$NGINX_CONF"; then
    log_error "nginx 配置中缺少 HTTP server 配置"
    exit 1
fi

# 6. 测试 nginx 配置
log_info "测试 nginx 配置..."
if nginx -t; then
    log_success "nginx 配置语法正确"
else
    log_error "nginx 配置有误，请先修复"
    exit 1
fi

# 7. 重载 nginx
log_info "重载 nginx..."
systemctl reload nginx
log_success "nginx 已重载"

# 8. 申请证书
echo ""
log_info "开始申请新域名 SSL 证书..."
echo ""

CERTBOT_CMD="certbot --nginx -d ${NEW_DOMAIN} --non-interactive --agree-tos"
if [ -n "$CERTBOT_EMAIL" ]; then
    CERTBOT_CMD="$CERTBOT_CMD --email $CERTBOT_EMAIL"
fi

if eval "$CERTBOT_CMD"; then
    log_success "SSL 证书申请成功!"
else
    log_error "SSL 证书申请失败"
    log_error "请确认："
    log_error "  1. 域名 ${NEW_DOMAIN} 已解析到本服务器 IP"
    log_error "  2. 80 端口可从外网访问"
    log_error ""
    log_error "正在恢复旧配置..."
    if [ -f "${NGINX_CONF}.bak" ]; then
        cp "${NGINX_CONF}.bak" "$NGINX_CONF"
        systemctl reload nginx
        log_success "已恢复旧配置"
    fi
    exit 1
fi

# 9. 验证自动续期
echo ""
log_info "验证证书自动续期..."
if certbot renew --dry-run &> /dev/null; then
    log_success "证书自动续期配置正常"
else
    log_warning "自动续期验证未通过，可手动测试: certbot renew --dry-run"
fi

# 10. 显示结果
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}域名迁移完成！${NC}"
echo -e "${GREEN}========================================${NC}\n"

certbot certificates 2>/dev/null

echo ""
echo -e "旧域名: ${YELLOW}https://${OLD_DOMAIN}${NC}"
echo -e "新域名: ${YELLOW}https://${NEW_DOMAIN}${NC}"
echo -e ""
echo -e "证书管理命令："
echo -e "  ${YELLOW}查看证书:${NC}   certbot certificates"
echo -e "  ${YELLOW}手动续期:${NC}   certbot renew"
echo -e "  ${YELLOW}撤销旧证书:${NC} certbot revoke --cert-name ${OLD_DOMAIN}"
echo -e "  ${YELLOW}删除旧证书:${NC} certbot delete --cert-name ${OLD_DOMAIN}"
echo ""
echo -e "新证书会在到期前自动续期（certbot timer）"
