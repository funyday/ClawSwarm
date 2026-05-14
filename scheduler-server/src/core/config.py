"""
这个文件负责读取服务启动配置。
"""
from pydantic import BaseModel
import os
from pathlib import Path

DEFAULT_CONTAINER_DATABASE_URL = "sqlite:////opt/clawswarm/app.db"
DEFAULT_LOCAL_DATABASE_URL = "sqlite:///./data/app.db"
DEFAULT_CONTAINER_DATA_DIR = "/opt/clawswarm"
DEFAULT_LOCAL_DATA_DIR = "./data"
DEFAULT_WEB_DIST_DIR = "/opt/clawswarm-web"


def _default_database_url() -> str:
    if Path("/app").exists():
        return DEFAULT_CONTAINER_DATABASE_URL
    return DEFAULT_LOCAL_DATABASE_URL


def _default_data_dir() -> str:
    if Path("/app").exists():
        return DEFAULT_CONTAINER_DATA_DIR
    return DEFAULT_LOCAL_DATA_DIR


def _env_flag(name: str, default: bool) -> bool:
    """
    把环境变量解析成布尔值。
    这样 .env.dev 里既可以写 1/0，也可以写 true/false。
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    # 基础配置
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8080"))
    database_url: str = os.getenv("DATABASE_URL", _default_database_url())
    data_dir: str = os.getenv("DATA_DIR", _default_data_dir())
    web_dist_dir: str = os.getenv("WEB_DIST_DIR", DEFAULT_WEB_DIST_DIR)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # OpenClaw 配置
    default_channel_account_id: str = os.getenv("DEFAULT_CHANNEL_ACCOUNT_ID", "default")
    channel_allow_insecure_tls: bool = _env_flag("CHANNEL_ALLOW_INSECURE_TLS", False)
    local_agent_mock_enabled: bool = _env_flag("LOCAL_AGENT_MOCK_ENABLED", False)
    
    # 认证配置
    auth_secret: str = os.getenv("AUTH_SECRET", "clawswarm-dev-auth-secret")
    auth_cookie_name: str | None = os.getenv("AUTH_COOKIE_NAME")
    default_login_username: str = os.getenv("DEFAULT_LOGIN_USERNAME", "admin")
    default_login_password: str = os.getenv("DEFAULT_LOGIN_PASSWORD", "admin123456")
    
    # 飞书 SSO 配置
    feishu_sso_enabled: bool = _env_flag("FEISHU_SSO_ENABLED", True)
    feishu_sso_app_id: str = os.getenv("FEISHU_SSO_APP_ID", "")
    feishu_sso_app_secret: str = os.getenv("FEISHU_SSO_APP_SECRET", "")
    feishu_sso_redirect_uri: str = os.getenv("FEISHU_SSO_REDIRECT_URI", "")
    
    # 飞书 Bot Webhook 配置
    feishu_webhook_path: str = os.getenv("FEISHU_WEBHOOK_PATH", "/feishu/webhook")
    
    # Tailscale 配置
    tailscale_enabled: bool = _env_flag("TAILSCALE_ENABLED", False)
    tailscale_authkey: str = os.getenv("TAILSCALE_AUTHKEY", "")
    tailscale_hostname: str = os.getenv("TAILSCALE_HOSTNAME", "clawswarm-server")
    tailscale_proxy_url: str = os.getenv("TAILSCALE_PROXY_URL", "")
    
    # ClawSwarm API 基础 URL (用于回调)
    clawswarm_base_url: str = os.getenv("CLAWSWARM_BASE_URL", "http://localhost:18080")


settings = Settings()
