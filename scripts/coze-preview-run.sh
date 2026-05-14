#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录（scripts/ 的上一级）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# 进入 web-client 子目录执行预览
cd web-client

# 显式声明关键环境变量，不依赖平台执行环境继承
export PORT=5000

# 清理 5000 端口残留进程（绝不碰 9000）
fuser -k 5000/tcp 2>/dev/null || true
sleep 1

# 使用 Vite 启动开发服务器，绑定 0.0.0.0 暴露 5000 端口
exec pnpm exec vite --host 0.0.0.0 --port 5000
