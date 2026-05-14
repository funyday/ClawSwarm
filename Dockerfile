# ClawSwarm Backend Dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY scheduler-server/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY scheduler-server/src ./src

# 复制启动脚本
COPY scheduler-server/run.py .
COPY scheduler-server/run_dev.py .

# 创建必要的目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 18080

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "run_dev.py"]
