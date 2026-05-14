"""飞书群组-Bot 关联模型。"""

from sqlalchemy import ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.base_mixins import TimestampMixin


class FeishuGroupBot(Base, TimestampMixin):
    """飞书群组与 Bot 的关联关系"""
    __tablename__ = "feishu_group_bots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联的群组
    group_id: Mapped[int] = mapped_column(
        ForeignKey("feishu_groups.id", ondelete="CASCADE"),
        comment="飞书群组 ID"
    )
    
    # 关联的 Bot
    bot_id: Mapped[int] = mapped_column(
        ForeignKey("feishu_bots.id", ondelete="CASCADE"),
        comment="飞书 Bot ID"
    )
    
    # 在该群中的优先级 (轮询模式使用)
    priority: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="优先级 (数字越小优先级越高)"
    )
    
    # 是否启用
    enabled: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否启用"
    )
    
    # 关系
    group: Mapped["FeishuGroup"] = relationship(
        "FeishuGroup",
        back_populates="bots"
    )
    bot: Mapped["FeishuBot"] = relationship(
        "FeishuBot",
        back_populates="group_associations"
    )
    
    def __repr__(self) -> str:
        return f"<FeishuGroupBot(group_id={self.group_id}, bot_id={self.bot_id}, priority={self.priority})>"
