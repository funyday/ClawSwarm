"""应用登录用户模型。"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base
from src.models.base_mixins import TimestampMixin


class AppUser(Base, TimestampMixin):
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(120), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(500), nullable=True)  # SSO 模式下可为空
    
    # 飞书关联
    feishu_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    feishu_open_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    feishu_union_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    feishu_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feishu_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    feishu_department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feishu_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # SSO 状态
    sso_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    login_count: Mapped[int] = mapped_column(default=0)
    
    def __repr__(self) -> str:
        return f"<AppUser(id='{self.id}', username='{self.username}')>"
