#!/bin/bash
# ClawSwarm 部署脚本

set -e

echo "=========================================="
echo "  ClawSwarm Docker 部署脚本"
echo "=========================================="

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装 Docker"
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "错误: 未安装 Docker Compose"
    exit 1
fi

# 获取 Docker Compose 命令
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo ""
    echo "创建 .env 配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置相关参数"
    echo "完成后重新运行此脚本"
    exit 1
fi

echo ""
echo "步骤 1: 构建前端..."
cd web-client
if [ ! -d "dist" ]; then
    echo "构建前端..."
    pnpm install
    pnpm build
else
    echo "前端已构建，跳过"
fi
cd ..

echo ""
echo "步骤 2: 构建并启动服务..."
$DOCKER_COMPOSE down 2>/dev/null || true
$DOCKER_COMPOSE build --no-cache
$DOCKER_COMPOSE up -d

echo ""
echo "步骤 3: 等待服务启动..."
sleep 5

echo ""
echo "步骤 4: 检查服务状态..."
$DOCKER_COMPOSE ps

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "访问地址: http://localhost"
echo ""
echo "查看日志: $DOCKER_COMPOSE logs -f"
echo "停止服务: $DOCKER_COMPOSE down"
echo ""
