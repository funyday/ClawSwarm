# Tailscale 部署指南

## 概述

ClawSwarm 支持通过 Tailscale 实现跨公网组网，让内网的 OpenClaw 实例可以被公网的 ClawSwarm 服务访问。

## 网络架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Tailscale 私有网络                                    │
│                                                                             │
│  100.64.1.1   ClawSwarm Server (公网 IP + Tailscale)                      │
│  100.64.1.10  OpenClaw-Dev Instance (内网)                                │
│  100.64.1.11  OpenClaw-QA Instance (内网)                                 │
│  100.64.1.12  OpenClaw-Review Instance (内网)                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 前置准备

### 1. 创建 Tailscale 网络

1. 注册 [Tailscale](https://tailscale.com/) 账号
2. 创建一个新的 Tailscale 网络
3. 获取 Auth Key:
   - 进入管理后台: https://login.tailscale.com/admin/settings/keys
   - 点击 "Generate auth key"
   - 勾选 "Reusable" (可选，便于批量部署)
   - 复制生成的 key

### 2. 在 OpenClaw 实例上安装 Tailscale

在每个内网 OpenClaw 实例服务器上执行:

```bash
# 安装 Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 加入网络 (使用预共享密钥)
sudo tailscale up --authkey=tskey-auth-xxxxx --hostname=openclaw-dev
```

重复以上步骤，为每个 OpenClaw 实例分配唯一的主机名。

## 部署方式

### 方式 A: Docker Compose 部署 (推荐)

1. 创建 `.env` 文件:

```bash
# 数据库
COZE_DB_PASSWORD=your_db_password
COZE_DB_HOST=your-db-host

# 认证
AUTH_SECRET=your-secure-secret

# 飞书 SSO
FEISHU_SSO_APP_ID=cli_xxxxx
FEISHU_SSO_APP_SECRET=your-app-secret
FEISHU_SSO_REDIRECT_URI=https://clawswarm.example.com/auth/feishu/callback

# Tailscale
TAILSCALE_AUTHKEY=tskey-auth-xxxxx
```

2. 启动服务:

```bash
docker-compose up -d
```

### 方式 B: Kubernetes 部署

1. 创建 Secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: clawswarm-secrets
type: Opaque
stringData:
  tailscale-authkey: tskey-auth-xxxxx
  feishu-app-secret: your-secret
```

2. 配置 Pod:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clawswarm
spec:
  template:
    spec:
      containers:
        - name: clawswarm
          env:
            - name: TAILSCALE_ENABLED
              value: "true"
            - name: TAILSCALE_AUTHKEY
              valueFrom:
                secretKeyRef:
                  name: clawswarm-secrets
                  key: tailscale-authkey
            - name: TAILSCALE_HOSTNAME
              value: "clawswarm-server"
          securityContext:
            capabilities:
              add:
                - NET_ADMIN
          volumeMounts:
            - name: dev-net-tun
              mountPath: /dev/net/tun
      volumes:
        - name: dev-net-tun
          hostPath:
            path: /dev/net/tun
```

## OpenClaw 实例配置

在 ClawSwarm Web UI 中添加 OpenClaw 实例时:

1. **连接方式**: 选择 "Tailscale"
2. **主机名**: 输入 OpenClaw 实例的 Tailscale 主机名 (如 `openclaw-dev`)
3. **端口**: 默认 `18789`
4. **完整地址**: 将自动生成为 `http://100.64.x.x:18789`

## Tailscale 节点管理

### 查看节点状态

```bash
# 在 ClawSwarm 服务器上
tailscale status
```

### 添加新节点

```bash
# 在新服务器上
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --authkey=tskey-auth-xxxxx --hostname=openclaw-new
```

### 移除节点

```bash
# 在 ClawSwarm 服务器上
tailscale logout --hostname openclaw-old
```

## 故障排除

### 节点无法连接

1. 检查 Tailscale 服务状态:
   ```bash
   systemctl status tailscaled
   ```

2. 检查网络连通性:
   ```bash
   ping 100.64.1.10
   ```

3. 检查端口是否开放:
   ```bash
   nc -zv 100.64.1.10 18789
   ```

### Tailscale 启动失败

确保容器有正确的权限:
- `NET_ADMIN` capability
- `/dev/net/tun` 设备访问

## 安全建议

1. **使用 Auth Key**: 不要使用 OAuth 进行自动化部署
2. **限制 Key 权限**: 为每个节点创建专用 Key
3. **启用 HTTPS**: 生产环境建议使用 Tailscale Funnel 提供 HTTPS
4. **网络隔离**: 使用 Tailscale ACL 控制节点间访问

## 参考链接

- [Tailscale 官方文档](https://tailscale.com/kb/)
- [Tailscale API](https://tailscale.com/api/)
- [Headscale (自建控制平面)](https://github.com/juanfont/headscale)
