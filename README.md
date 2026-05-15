# ClawSwarm

> 本项目基于 [@1Panel-dev](https://github.com/1Panel-dev) 的 [OpenClaw](https://github.com/1Panel-dev/OpenClaw) 进行二次开发，添加了群体智能编排、飞书集成、私有网络支持等功能。

开源的多 Agent 编排系统，将群体智能引入 OpenClaw 中的 Agent。它打破了传统 AI 交互的"一对一"限制，允许多个专业 Agent 加入统一的群聊。

## 功能特性

- **多 Agent 群聊编排**：支持 @Bot、广播、轮询三种消息模式
- **飞书多 Bot 接入**：每个 Agent 可绑定独立的飞书 Bot
- **飞书 SSO 登录**：安全的飞书账号登录认证
- **私有网络支持**：支持 Tailscale/Headscale 组网，连接内网 OpenClaw 实例
- **Web 管理界面**：直观的管理后台

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户                                 │
│                    (飞书 / Web)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    ClawSwarm 服务                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │  Web 前端   │  │  API 后端   │  │  Tailscale      │     │
│  │  (Vue 3)   │  │  (FastAPI)  │  │  客户端         │     │
│  └─────────────┘  └─────────────┘  └────────┬────────┘     │
│                                               │              │
│                                               │ Tailscale    │
│                                               │ 网络         │
└───────────────────────────────────────────────┼──────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │  OpenClaw   │
                                         │  实例 1     │
                                         └─────────────┘
```

## 快速开始

### 前置要求

- Docker 24+
- Docker Compose v2+
- Git

### 部署步骤

#### 1. 克隆代码

```bash
git clone https://github.com/funyday/ClawSwarm.git
cd ClawSwarm
```

#### 2. 配置环境变量

```bash
cp .env.example .env
vim .env
```

必填配置：

```bash
# 数据库密码
DB_PASSWORD=your_secure_password

# 应用 URL
# - 公网部署：需要设置为公网可访问的地址（用于飞书回调）
# - 内网部署：设置为 http://服务器IP
CLAWSWARM_BASE_URL=http://服务器IP

# 加密密钥（生产环境建议修改）
SECRET_KEY=change-me-to-random-string

# 默认管理员账号
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# 飞书 SSO 登录（内网部署设为 false）
FEISHU_SSO_ENABLED=false
```

#### 3. 内网部署（无需公网）

内网部署时，飞书 SSO 登录不可用，但可以使用本地账号登录：

```bash
# .env 配置
CLAWSWARM_BASE_URL=http://192.168.1.100
FEISHU_SSO_ENABLED=false
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

首次登录使用默认账号：`admin` / `admin123`

#### 4. 配置飞书 Bot（可选）

如果你需要使用飞书 Bot 功能：

```bash
# 编辑 .env
vim .env

# 配置飞书应用信息
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=your_feishu_app_secret
```

在飞书开放平台创建应用后，配置重定向 URL 为：
```
http://服务器IP/auth/feishu/callback
```

#### 5. 配置 Tailscale/Headscale（可选）

支持通过私有网络连接内网 OpenClaw 实例。

**方式一：Tailscale 官方**

```bash
# 获取 Auth Key：https://login.tailscale.com/admin/settings/keys
TAILSCALE_AUTH_KEY=tskey-auth-xxxxx
TAILSCALE_NETWORK_MODE=userspace
```

**方式二：自托管 Headscale**

```bash
HEADSCALE_URL=https://your-headscale-server.com
HEADSCALE_API_KEY=your_headscale_api_key
```

然后在 `docker-compose.yml` 中取消注释 tailscale 服务。

#### 6. 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
bash scripts/logs.sh
```

#### 7. 访问

打开浏览器访问 `http://服务器IP`

首次登录：
- 用户名：`admin`
- 密码：`admin123`

## 目录结构

```
ClawSwarm/
├── docker-compose.yml    # Docker 服务编排
├── Dockerfile            # 后端镜像构建
├── nginx.conf            # Nginx 配置
├── .env.example          # 环境变量模板
├── scheduler-server/     # 后端代码
│   └── src/
│       ├── api/          # API 路由
│       ├── models/       # 数据模型
│       └── services/     # 业务服务
├── web-client/          # 前端代码
│   └── src/
│       ├── pages/        # 页面组件
│       ├── stores/       # 状态管理
│       └── api/          # API 调用
├── init-scripts/        # 数据库初始化脚本
└── scripts/            # 部署脚本
    ├── deploy.sh        # 部署脚本
    ├── stop.sh          # 停止脚本
    └── logs.sh          # 日志脚本
```

## 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DB_PASSWORD` | 是 | PostgreSQL 数据库密码 |
| `CLAWSWARM_BASE_URL` | 是 | 应用基础 URL（用于飞书回调） |
| `SECRET_KEY` | 是 | 加密密钥（生产环境必须修改） |
| `TAILSCALE_AUTH_KEY` | 否 | Tailscale 认证密钥 |
| `HEADSCALE_URL` | 否 | Headscale 服务器地址 |
| `HEADSCALE_API_KEY` | 否 | Headscale API Key |
| `FEISHU_APP_ID` | 否 | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 否 | 飞书应用 App Secret |

## 服务端口

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | HTTP 访问 |
| 443 | Nginx | HTTPS 访问（需配置证书） |
| 5432 | PostgreSQL | 数据库（容器内访问） |
| 18080 | Backend | API 服务（容器内访问） |

## 常用命令

```bash
# 部署
bash scripts/deploy.sh

# 停止
bash scripts/stop.sh

# 查看日志
bash scripts/logs.sh -f

# 重启服务
docker-compose restart backend

# 进入后端容器
docker-compose exec backend bash
```

## 开发

### 本地开发

```bash
# 后端
cd scheduler-server
pip install -r requirements.txt
python run_dev.py

# 前端
cd web-client
pnpm install
pnpm dev
```

### 构建前端

```bash
cd web-client
pnpm build
```

## 许可证

MIT
