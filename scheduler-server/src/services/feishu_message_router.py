"""飞书消息路由服务。"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.models.feishu_bot import FeishuBot
from src.models.feishu_group import FeishuGroup
from src.models.feishu_group_bot import FeishuGroupBot
from src.models.feishu_message_log import FeishuMessageLog
from src.services.feishu_message_parser import FeishuMessage, FeishuMention


@dataclass
class RouteResult:
    """路由结果"""
    success: bool
    bot: Optional[FeishuBot] = None
    agent_id: Optional[int] = None
    error: Optional[str] = None


class FeishuMessageRouter:
    """飞书消息路由器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def route(self, message: FeishuMessage, group: FeishuGroup) -> list[RouteResult]:
        """
        根据群组配置路由消息
        
        Args:
            message: 解析后的消息
            group: 群组配置
            
        Returns:
            路由结果列表
        """
        # 获取群组关联的所有 Bot
        bots = self._get_group_bots(group.id)
        if not bots:
            return [RouteResult(success=False, error="群组未配置 Bot")]
        
        # 根据消息模式路由
        if group.message_mode == "at_mode":
            return await self._route_at_mode(message, bots)
        elif group.message_mode == "broadcast":
            return await self._route_broadcast(message, bots)
        elif group.message_mode == "round_robin":
            return await self._route_round_robin(message, bots, group)
        else:
            return [RouteResult(success=False, error=f"未知消息模式: {group.message_mode}")]
    
    def _get_group_bots(self, group_id: int) -> list[FeishuBot]:
        """获取群组关联的所有 Bot"""
        query = (
            select(FeishuBot)
            .join(FeishuGroupBot, FeishuGroupBot.bot_id == FeishuBot.id)
            .where(
                FeishuGroupBot.group_id == group_id,
                FeishuGroupBot.enabled == True,
                FeishuBot.status == "active",
            )
            .order_by(FeishuGroupBot.priority)
        )
        return list(self.db.execute(query).scalars().all())
    
    async def _route_at_mode(
        self, message: FeishuMessage, bots: list[FeishuBot]
    ) -> list[RouteResult]:
        """
        @Bot 模式：只响应被 @ 的 Bot 对应的 Agent
        
        如果消息中没有 @ 任何 Bot，返回成功但不分发
        """
        if not message.has_bot_mention:
            # 没有 @ Bot，静默忽略
            return [RouteResult(success=True)]
        
        results = []
        mentioned_bot_names = set(message.mentioned_bot_names)
        
        for bot in bots:
            if bot.name in mentioned_bot_names:
                results.append(RouteResult(
                    success=True,
                    bot=bot,
                    agent_id=bot.agent_id,
                ))
            else:
                # Bot 未被 @，跳过
                results.append(RouteResult(success=True))
        
        return results
    
    async def _route_broadcast(
        self, message: FeishuMessage, bots: list[FeishuBot]
    ) -> list[RouteResult]:
        """
        广播模式：所有 Bot 对应的 Agent 都响应
        """
        results = []
        for bot in bots:
            results.append(RouteResult(
                success=True,
                bot=bot,
                agent_id=bot.agent_id,
            ))
        
        return results
    
    async def _route_round_robin(
        self,
        message: FeishuMessage,
        bots: list[FeishuBot],
        group: FeishuGroup,
    ) -> list[RouteResult]:
        """
        轮询模式：按优先级轮流响应
        """
        if not bots:
            return [RouteResult(success=False, error="群组无有效 Bot")]
        
        # 计算当前应该响应的 Bot 索引
        current_index = group.round_robin_index % len(bots)
        bot = bots[current_index]
        
        # 更新轮询索引
        group.round_robin_index = (current_index + 1) % len(bots)
        group.updated_at = datetime.utcnow()
        self.db.commit()
        
        return [RouteResult(
            success=True,
            bot=bot,
            agent_id=bot.agent_id,
        )]
    
    def find_group_by_chat_id(self, chat_id: str) -> Optional[FeishuGroup]:
        """根据飞书群 ID 查找群组配置"""
        query = select(FeishuGroup).where(
            FeishuGroup.feishu_chat_id == chat_id,
            FeishuGroup.status == "active",
        )
        return self.db.execute(query).scalar_one_or_none()
    
    def find_bot_by_name(self, name: str) -> Optional[FeishuBot]:
        """根据 Bot 名称查找 Bot"""
        query = select(FeishuBot).where(
            FeishuBot.name == name,
            FeishuBot.status == "active",
        )
        return self.db.execute(query).scalar_one_or_none()
    
    def log_message(
        self,
        group_id: int,
        bot_id: Optional[int],
        message: FeishuMessage,
        message_mode: str,
        dispatch_result: str,
        dispatch_error: Optional[str] = None,
        agent_response: Optional[str] = None,
    ) -> FeishuMessageLog:
        """记录消息日志"""
        log = FeishuMessageLog(
            group_id=group_id,
            bot_id=bot_id,
            sender_id=message.sender_id,
            sender_name=message.sender_name,
            feishu_message_id=message.message_id,
            content=message.content,
            message_mode=message_mode,
            dispatch_result=dispatch_result,
            dispatch_error=dispatch_error,
            agent_response=agent_response,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
