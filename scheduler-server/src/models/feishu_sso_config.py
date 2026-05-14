"""飞书 SSO 配置模型。"""

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base
from src.models.base_mixins import TimestampMixin


class FeishuSSOConfig(Base, TimestampMixin):
    """飞书 SSO 全局配置"""
    __tablename__ = "feishu_sso_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 飞书应用配置
    app_id: Mapped[str] = mapped_column(
        String(64), 
        comment="飞书 App ID"
    )
    app_secret: Mapped[str] = mapped_column(
        String(256), 
        comment="飞书 App Secret (加密存储)"
    )
    redirect_uri: Mapped[str] = mapped_column(
        String(500), 
        comment="OAuth 回调地址"
    )
    
    # 安全配置
    state_secret: Mapped[str] = mapped_column(
        String(128), 
        comment="生成 state 的密钥"
    )
    
    # 权限范围
    scopes: Mapped[str] = mapped_column(
        String(500), 
        default="contact:user.base:readonly",
        comment="OAuth 权限范围"
    )
    
    # 访问控制
    allowed_departments: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        comment="允许的部门 JSON 数组"
    )
    allowed_emails: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        comment="允许的邮箱后缀 JSON 数组"
    )
    auto_create_user: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="未匹配用户是否自动创建"
    )
    
    # 状态
    enabled: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否启用"
    )
    
    def __repr__(self) -> str:
        return f"<FeishuSSOConfig(id={self.id}, app_id='{self.app_id}', enabled={self.enabled})>"
