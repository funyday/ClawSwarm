#!/bin/bash
# ClawSwarm 日志查看脚本

DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

if [ "$1" == "--follow" ] || [ "$1" == "-f" ]; then
    echo "跟踪日志 (Ctrl+C 退出)..."
    $DOCKER_COMPOSE logs -f
else
    $DOCKER_COMPOSE logs --tail=100
fi
