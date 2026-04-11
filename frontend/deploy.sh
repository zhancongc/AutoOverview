#!/bin/bash

# AutoOverview 双版本前端部署脚本
# 支持中文版和英文版的独立部署

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AutoOverview 双版本前端部署脚本 ===${NC}"
echo ""

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}用法: ./deploy.sh [版本] [环境]${NC}"
    echo ""
    echo "版本选项："
    echo "  zh          - 中文版"
    echo "  en          - 英文版"
    echo "  both        - 同时构建两个版本"
    echo ""
    echo "环境选项（可选）："
    echo "  shanghai    - 部署到上海服务器（默认）"
    echo "  newyork     - 部署到纽约服务器"
    echo "  local       - 本地构建，不部署"
    echo ""
    echo "示例："
    echo "  ./deploy.sh zh shanghai    # 构建并部署中文版到上海"
    echo "  ./deploy.sh en newyork     # 构建并部署英文版到纽约"
    echo "  ./deploy.sh both local     # 构建两个版本，不部署"
    echo ""
    exit 1
fi

VERSION=$1
ENVIRONMENT=${2:-local}

echo -e "${BLUE}版本: ${VERSION}${NC}"
echo -e "${BLUE}环境: ${ENVIRONMENT}${NC}"
echo ""

# 安装依赖
echo -e "${GREEN}步骤 1: 安装依赖${NC}"
npm install

# 构建指定版本
echo -e "${GREEN}步骤 2: 构建前端${NC}"

case $VERSION in
    zh)
        echo "构建中文版..."
        npm run build
        BUILD_DIR="dist-zh"
        ;;

    en)
        echo "构建英文版..."
        npm run build:en
        BUILD_DIR="dist-en"
        ;;

    both)
        echo "构建中文版和英文版..."
        npm run build:both
        BUILD_DIR="dist-zh 和 dist-en"
        ;;

    *)
        echo -e "${RED}错误: 未知的版本 '${VERSION}'${NC}"
        echo "请使用 'zh' 或 'en' 或 'both'"
        exit 1
        ;;
esac

# 部署
echo -e "${GREEN}步骤 3: 部署${NC}"

if [ "$ENVIRONMENT" = "local" ]; then
    echo "本地构建完成，不部署"
    echo "构建产物在 ${BUILD_DIR} 目录"
else
    case $ENVIRONMENT in
        shanghai)
            echo "部署到上海服务器..."
            if [ "$VERSION" = "zh" ] || [ "$VERSION" = "both" ]; then
                echo "  - 部署中文版到 https://autooverview.snappicker.com"
                # rsync -avz dist-zh/ user@autooverview.snappicker.com:/var/www/html/
                echo -e "${YELLOW}请配置 rsync 命令${NC}"
            fi
            if [ "$VERSION" = "en" ] || [ "$VERSION" = "both" ]; then
                echo "  - 部署英文版到 https://autooverview.snappicker.com/en"
                # rsync -avz dist-en/ user@autooverview.snappicker.com:/var/www/html/en/
                echo -e "${YELLOW}请配置 rsync 命令${NC}"
            fi
            ;;

        newyork)
            echo "部署到纽约服务器..."
            if [ "$VERSION" = "en" ] || [ "$VERSION" = "both" ]; then
                echo "  - 部署英文版到 https://autooverview.plainkit.top"
                # rsync -avz dist-en/ user@autooverview.plainkit.top:/var/www/html/
                echo -e "${YELLOW}请配置 rsync 命令${NC}"
            fi
            if [ "$VERSION" = "zh" ]; then
                echo -e "${RED}警告: 纽约服务器通常只需要英文版${NC}"
            fi
            ;;

        *)
            echo -e "${RED}错误: 未知的环境 '${ENVIRONMENT}'${NC}"
            exit 1
            ;;
    esac
fi

echo ""
echo -e "${GREEN}部署完成！${NC}"
echo ""
echo -e "${BLUE}验证部署：${NC}"
echo "中文版: https://autooverview.snappicker.com"
echo "英文版: https://autooverview.plainkit.top"
echo ""
echo "检查清单："
echo "1. 网站是否可以访问"
echo "2. 浏览器控制台检查 API 请求"
echo "3. 测试登录/注册功能"
echo "4. 测试支付功能（中文版支付宝，英文版 Paddle）"
echo "5. 检查默认语言是否正确"
