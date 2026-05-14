# ClawSwarm

开源的多 Agent 编排系统，将群体智能引入 OpenClaw 中的 Agent。

## 快速开始

### Docker 部署（推荐）

```bash
# 1. 克隆代码
git clone https://github.com/your/clawswarm.git
cd clawswarm

# 2. 配置环境变量
cp .env.example .env
vim .env  # 编辑必要的配置

# 3. 部署
bash scripts/deploy.sh

# 4. 访问
# 打开浏览器访问 http://localhost
```

### 配置说明

编辑 `.env` 文件：

```bash
# 数据库密码
DB_PASSWORD=your_secure_password

# 应用 URL（用于飞书回调等）
CLAWSWARM_BASE_URL=https://your-domain.com

# 加密密钥（生产环境必须修改）
SECRET_KEY=change-me-to-random-key
```

## 功能特性

- 多 Agent 群聊编排
- 飞书 Bot 接入
- 飞书 SSO 登录
- Headscale/Tailscale 网络支持

## 文档

- [项目规范](./AGENTS.md)
- [飞书配置](./docs/feishu-setup.md) (待完成)
- [网络配置](./docs/network-setup.md) (待完成)

## 许可证

MIT
