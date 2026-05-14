#!/bin/bash
# ClawSwarm 停止脚本

set -e

DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

echo "停止 ClawSwarm 服务..."
$DOCKER_COMPOSE down

echo "服务已停止"
