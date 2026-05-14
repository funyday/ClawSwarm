# ClawSwarm 项目规范

## 项目概述

ClawSwarm 是一个开源的编排系统，将群体智能引入 OpenClaw 中的 Agent。它打破了传统 AI 交互的"一对一"限制，允许多个专业 Agent 加入统一的群聊。

## 技术栈

- **前端**: Vue 3, Vite, TypeScript, Element Plus, Pinia, Vue Router, Vue I18n
- **后端**: Python 3.10+, FastAPI, SQLAlchemy, Uvicorn
- **插件**: TypeScript, tsup, Vitest, Zod, Undici
- **运行时**: Docker, Docker Compose
- **包管理器**: Node.js 使用 `pnpm`，Python 使用 `uv`

## 目录结构

```
/workspace/projects/              # 工作区根目录 & 技术项目根目录
├── .coze                         # 根 .coze（与子项目 .coze 合一）
├── scripts/                      # 预览脚本
│   ├── coze-preview-build.sh    # 预览构建（pnpm install）
│   └── coze-preview-run.sh      # 预览运行（vite dev server）
├── web-client/                  # 前端 Web 项目
│   ├── .coze                    # 子项目 .coze
│   ├── scripts/
│   │   ├── coze-deploy-build.sh # 部署构建（pnpm build）
│   │   └── coze-deploy-run.sh   # 部署运行（vite preview）
│   └── ...
├── channel/                     # OpenClaw 插件
└── scheduler-server/            # Python FastAPI 后端
```

## 关键入口

- **前端预览**: `bash scripts/coze-preview-run.sh` → 5000 端口
- **前端构建**: `bash scripts/coze-preview-build.sh` → pnpm install
- **部署构建**: `bash web-client/scripts/coze-deploy-build.sh` → 静态产物
- **部署运行**: `bash web-client/scripts/coze-deploy-run.sh` → vite preview
- **后端服务**: `cd scheduler-server && python3 run_dev.py` → 18080 端口

## 运行与预览

### 开发预览
```bash
# 安装前端依赖
bash scripts/coze-preview-build.sh

# 启动后端服务（需要先安装依赖：pip install -r requirements.txt）
cd scheduler-server && python3 run_dev.py &

# 启动前端预览服务
bash scripts/coze-preview-run.sh
# 访问 http://localhost:5000
```

### 注意事项
- 预览服务绑定 `0.0.0.0:5000`，使用 `pnpm` 管理依赖
- 前端独立可预览，但 API 请求需要后端服务运行在 `18080` 端口
- 幂等性：run 脚本会先清理 5000 端口再启动

## 用户偏好与长期约束

1. **包管理器**: Node.js 项目必须使用 `pnpm`，禁止 npm/yarn
2. **端口约定**: 
   - 预览服务使用 `5000` 端口
   - 禁止使用 `9000` 端口
3. **脚本位置**: 所有脚本基于自身位置定位项目目录，使用 `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` 推导

## 预览链路处理记录

### 判断依据
- 项目包含 `web-client` 前端，使用 Vite + Vue 3
- 有明确的前端开发服务器和构建命令
- 判定为 **Web 预览型项目**

### 最终方案
- 根 `.coze` 与子项目 `.coze` 合一（path = "."）
- `[dev].build` → `scripts/coze-preview-build.sh`（安装依赖）
- `[dev].run` → `scripts/coze-preview-run.sh`（启动 vite dev server）
- `[deploy]` → 指向 `web-client/scripts/` 中的部署脚本

### 验证结果
- `curl http://localhost:5000` → 200
- `ss -lptn 'sport = :5000'` → 0.0.0.0:5000 (LISTEN)

## 常见问题和预防

1. **API 代理错误**: 前端访问 `/api/*` 会代理到 `127.0.0.1:18080`，后端未启动时会出现 `ECONNREFUSED`，这是预期行为
2. **依赖安装**: 确保先执行 build 脚本安装依赖，再启动预览
3. **端口冲突**: run 脚本使用幂等设计，会自动清理旧进程

## Docker 部署

### 目录结构

```
/workspace/projects/              # 工作区根目录 & 技术项目根目录
├── .env                         # 环境变量配置
├── .env.example                 # 环境变量模板
├── Dockerfile                   # 后端构建文件
├── docker-compose.yml           # Docker Compose 配置
├── nginx.conf                   # Nginx 配置
├── init-scripts/                # 数据库初始化脚本
├── ssl/                         # SSL 证书目录
└── scripts/
    ├── deploy.sh               # 部署脚本
    ├── stop.sh                 # 停止脚本
    └── logs.sh                 # 日志查看脚本
```

### Docker 部署步骤

```bash
# 1. 克隆代码
git clone https://github.com/your/clawswarm.git
cd clawswarm

# 2. 复制并编辑环境变量
cp .env.example .env
vim .env

# 3. 一键部署
bash scripts/deploy.sh

# 4. 查看服务状态
docker compose ps

# 5. 查看日志
bash scripts/logs.sh -f
```

### Docker 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DB_PASSWORD` | 是 | PostgreSQL 数据库密码 |
| `CLAWSWARM_BASE_URL` | 是 | 应用基础 URL（用于飞书回调） |
| `SECRET_KEY` | 是 | 加密密钥（生产环境必须修改） |
| `HEADSCALE_URL` | 否 | Headscale 服务器地址 |
| `HEADSCALE_API_KEY` | 否 | Headscale API Key |
| `TAILSCALE_AUTH_KEY` | 否 | Tailscale 认证密钥 |
| `FEISHU_APP_ID` | 否 | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 否 | 飞书应用 App Secret |

### Tailscale 容器配置

1. 在 `docker-compose.yml` 中取消注释 tailscale 服务
2. 从 Tailscale 控制台获取认证密钥
3. 在 `.env` 中设置 `TAILSCALE_AUTH_KEY`
4. 重新部署

### 服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | HTTP 访问 |
| 443 | Nginx | HTTPS 访问（需配置证书） |
| 5432 | PostgreSQL | 数据库（仅容器内访问） |
| 18080 | Backend | API 服务（仅容器内访问） |
