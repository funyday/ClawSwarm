# ClawSwarm Dockerfile
# 支持 Tailscale 集成的多阶段构建

FROM python:3.11-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制依赖文件
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# 下载 Tailscale
RUN curl -fsSL https://tailscale.com/install.sh | sh

# 生产镜像
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 应用
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY src/ ./src/

# Tailscale 二进制文件 (可选，如果需要容器内运行 Tailscale)
COPY --from=builder /usr/sbin/tailscaled /usr/sbin/tailscaled
COPY --from=builder /usr/sbin/tailscale /usr/sbin/tailscale

# 创建数据目录
RUN mkdir -p /opt/clawswarm

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 8080 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
