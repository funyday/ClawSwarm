#!/usr/bin/env bash
set -euo pipefail

# 基于脚本位置定位项目根目录（scripts/ 的上一级）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# 进入 web-client 子目录执行依赖安装
cd web-client

# 使用 pnpm 安装依赖
pnpm install
