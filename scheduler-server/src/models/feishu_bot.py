"""飞书 Bot 配置模型。"""

from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.base_mixins import TimestampMixin


class FeishuBot(Base, TimestampMixin):
    """飞书 Bot 配置"""
    __tablename__ = "feishu_bots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Bot 基本信息
    name: Mapped[str] = mapped_column(String(120), comment="Bot 显示名称")
    app_id: Mapped[str] = mapped_column(String(64), unique=True, comment="飞书 App ID")
    app_secret: Mapped[str] = mapped_column(String(256), comment="飞书 App Secret (加密存储)")
    webhook_secret: Mapped[str] = mapped_column(String(128), comment="Webhook 加密密钥")
    
    # 关联的 OpenClaw Instance
    instance_id: Mapped[int] = mapped_column(
        ForeignKey("openclaw_instances.id", ondelete="CASCADE"),
        comment="关联的 OpenClaw Instance ID"
    )
    
    # 关联的 Agent (可选，为空则使用 main Agent)
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_profiles.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联的 Agent ID (可选)"
    )
    
    # Bot 状态
    status: Mapped[str] = mapped_column(String(32), default="active", comment="active / inactive")
    
    # 关系
    instance: Mapped["OpenClawInstance"] = relationship(
        "OpenClawInstance",
        back_populates="feishu_bots"
    )
    agent: Mapped["AgentProfile | None"] = relationship(
        "AgentProfile",
        back_populates="feishu_bots"
    )
    group_associations: Mapped[list["FeishuGroupBot"]] = relationship(
        "FeishuGroupBot",
        back_populates="bot",
        cascade="all, delete-orphan"
    )
    message_logs: Mapped[list["FeishuMessageLog"]] = relationship(
        "FeishuMessageLog",
        back_populates="bot",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<FeishuBot(id={self.id}, name='{self.name}', app_id='{self.app_id}')>"
