"""飞书消息日志模型。"""

from sqlalchemy import String, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.base_mixins import TimestampMixin


class FeishuMessageLog(Base, TimestampMixin):
    """飞书消息日志 (用于审计和历史查询)"""
    __tablename__ = "feishu_message_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联的群组
    group_id: Mapped[int] = mapped_column(
        ForeignKey("feishu_groups.id", ondelete="SET NULL"),
        nullable=True,
        comment="飞书群组 ID"
    )
    
    # 关联的 Bot
    bot_id: Mapped[int] = mapped_column(
        ForeignKey("feishu_bots.id", ondelete="SET NULL"),
        nullable=True,
        comment="飞书 Bot ID"
    )
    
    # 发送者信息
    sender_id: Mapped[str] = mapped_column(
        String(64),
        comment="飞书用户 ID"
    )
    sender_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="飞书用户名称"
    )
    
    # 消息信息
    feishu_message_id: Mapped[str] = mapped_column(
        String(64),
        comment="飞书消息 ID"
    )
    content: Mapped[str] = mapped_column(
        Text,
        comment="消息内容"
    )
    
    # 路由信息
    message_mode: Mapped[str] = mapped_column(
        String(32),
        comment="匹配到的消息模式"
    )
    dispatch_result: Mapped[str] = mapped_column(
        String(32),
        comment="分发结果: success / failed / pending"
    )
    dispatch_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="分发错误信息"
    )
    
    # Agent 响应
    agent_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Agent 响应内容"
    )
    
    # 关系
    group: Mapped["FeishuGroup | None"] = relationship(
        "FeishuGroup",
        back_populates="message_logs"
    )
    bot: Mapped["FeishuBot | None"] = relationship(
        "FeishuBot",
        back_populates="message_logs"
    )
    
    def __repr__(self) -> str:
        return f"<FeishuMessageLog(id={self.id}, message_id='{self.feishu_message_id}')>"
