"""飞书群组配置模型。"""

from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.base_mixins import TimestampMixin


class FeishuGroup(Base, TimestampMixin):
    """飞书群组配置"""
    __tablename__ = "feishu_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 飞书群信息
    feishu_chat_id: Mapped[str] = mapped_column(
        String(64), 
        unique=True, 
        comment="飞书群 ID"
    )
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=True,
        comment="飞书群名称 (可选同步)"
    )
    
    # 绑定到 ClawSwarm 群组
    bound_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("chat_groups.id", ondelete="SET NULL"),
        nullable=True,
        comment="绑定的 ClawSwarm 群组 ID"
    )
    
    # 消息模式配置
    message_mode: Mapped[str] = mapped_column(
        String(32), 
        default="at_mode",
        comment="at_mode / broadcast / round_robin"
    )
    round_robin_timeout: Mapped[int] = mapped_column(
        Integer, 
        default=30,
        comment="轮询超时时间 (秒)"
    )
    round_robin_index: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="当前轮询位置"
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(32), 
        default="active",
        comment="active / inactive"
    )
    
    # 关系
    bound_group: Mapped["ChatGroup | None"] = relationship(
        "ChatGroup",
        back_populates="feishu_groups"
    )
    bots: Mapped[list["FeishuGroupBot"]] = relationship(
        "FeishuGroupBot",
        back_populates="group",
        cascade="all, delete-orphan"
    )
    message_logs: Mapped[list["FeishuMessageLog"]] = relationship(
        "FeishuMessageLog",
        back_populates="group",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<FeishuGroup(id={self.id}, chat_id='{self.feishu_chat_id}', mode='{self.message_mode}')>"
