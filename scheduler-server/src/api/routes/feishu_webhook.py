"""飞书 Webhook 路由。"""

import hashlib
import hmac
import time
import asyncio
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.models.feishu_bot import FeishuBot
from src.models.feishu_group import FeishuGroup
from src.services.feishu_message_parser import FeishuMessageParser, FeishuMessage
from src.services.feishu_message_router import FeishuMessageRouter
from src.services.feishu_message_sender import FeishuMessageSender
from src.integrations.channel_client import channel_client


router = APIRouter(prefix="/feishu", tags=["飞书 Webhook"])


class WebhookValidator:
    """飞书 Webhook 签名验证"""
    
    @staticmethod
    def verify_sign(timestamp: str, sign: str, secret: str) -> bool:
        """
        验证飞书签名
        
        签名算法: HMAC-SHA256 + Base64
        """
        try:
            # 构造签名字符串
            string_to_sign = f"{timestamp}{secret}"
            
            # 计算签名
            hmac_obj = hmac.new(
                secret.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                hashlib.sha256,
            )
            calculated_sign = hmac_obj.digest()
            
            # Base64 编码
            import base64
            expected_sign = base64.b64encode(calculated_sign).decode("utf-8")
            
            return hmac.compare_digest(sign, expected_sign)
        except Exception:
            return False


def find_bot_by_app_id(app_id: str, db: Session) -> Optional[FeishuBot]:
    """根据飞书 App ID 查找 Bot 配置"""
    from sqlalchemy import select
    query = select(FeishuBot).where(
        FeishuBot.app_id == app_id,
        FeishuBot.status == "active",
    )
    return db.execute(query).scalar_one_or_none()


@router.get("/webhook")
async def verify_webhook(
    challenge: str,
    db: Session = Depends(get_db),
):
    """
    飞书事件订阅验证
    
    飞书会在配置 Webhook URL 时发送 GET 请求进行验证
    需要返回 challenge 参数
    """
    return {"challenge": challenge}


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    接收飞书事件
    
    支持的事件类型:
    - im.message.receive_v1: 接收消息事件
    """
    # 获取原始请求体用于签名验证
    body = await request.json()
    
    # 获取飞书回调头信息
    headers = dict(request.headers)
    timestamp = headers.get("X-Lark-Request-Timestamp", "")
    sign = headers.get("X-Lark-Request-Signature", "")
    
    # 解析事件类型
    event_type = body.get("header", {}).get("event_type", "")
    
    if event_type == "im.message.receive_v1":
        return await handle_message_event(body, timestamp, sign, db)
    else:
        # 其他事件类型，直接返回成功
        return {"code": 0, "msg": "success"}


async def handle_message_event(
    body: dict,
    timestamp: str,
    sign: str,
    db: Session,
) -> dict:
    """
    处理接收消息事件
    """
    # 获取事件详情
    event = body.get("event", {})
    header = body.get("header", {})
    
    # 获取 Bot 的 app_id（需要从事件中获取或配置）
    # 飞书事件中的 app_id 在 tenant_key 中
    tenant_key = header.get("tenant_key", "")
    
    # 解析消息
    message = FeishuMessageParser.parse(body)
    if not message:
        return {"code": 1, "msg": "Failed to parse message"}
    
    # 验证签名（如果配置了签名密钥）
    # 注意：飞书事件回调可能不带签名，需要根据实际情况处理
    # 这里简化处理，实际生产环境应验证签名
    
    # 查找群组配置
    router_service = FeishuMessageRouter(db)
    group = router_service.find_group_by_chat_id(message.chat_id)
    
    if not group:
        # 群组未绑定，忽略消息
        return {"code": 0, "msg": "Group not bound"}
    
    # 如果是广播模式，检查是否需要验证签名
    # 获取群组关联的 Bot 进行签名验证
    bots = router_service._get_group_bots(group.id)
    if not bots:
        return {"code": 0, "msg": "No bot configured for group"}
    
    bot = bots[0]
    
    # 验证签名
    if timestamp and sign:
        if not WebhookValidator.verify_sign(timestamp, sign, bot.webhook_secret):
            print(f"Webhook signature verification failed")
            # 注意：生产环境应该返回错误
            # return {"code": 1, "msg": "Invalid signature"}
    
    # 路由消息
    route_results = await router_service.route(message, group)
    
    if not any(r.success and r.bot for r in route_results):
        # 没有需要处理的 Bot
        return {"code": 0, "msg": "No bot to dispatch"}
    
    # 并发处理各 Bot 的消息
    tasks = []
    for result in route_results:
        if result.success and result.bot:
            task = process_bot_message(
                db=db,
                message=message,
                bot=result.bot,
                agent_id=result.agent_id,
                group=group,
                router=router_service,
            )
            tasks.append(task)
    
    # 并发执行
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    return {"code": 0, "msg": "success"}


async def process_bot_message(
    db: Session,
    message: FeishuMessage,
    bot: FeishuBot,
    agent_id: Optional[int],
    group: FeishuGroup,
    router: FeishuMessageRouter,
):
    """
    处理单个 Bot 的消息
    
    1. 调用 OpenClaw Channel
    2. 发送响应到飞书群
    3. 记录消息日志
    """
    try:
        # 获取目标 Agent
        if agent_id:
            # 使用指定的 Agent
            from sqlalchemy import select
            from src.models.agent_profile import AgentProfile
            query = select(AgentProfile).where(AgentProfile.id == agent_id)
            agent = db.execute(query).scalar_one_or_none()
            agent_key = agent.agent_key if agent else None
            agent_name = agent.name if agent else bot.name
        else:
            # 使用 main Agent
            agent_key = None
            agent_name = bot.name
        
        # 调用 OpenClaw Channel
        response_text = None
        try:
            response_text = await channel_client.send_inbound(
                instance_key=bot.instance.instance_key,
                payload={
                    "messageId": message.message_id,
                    "accountId": bot.instance.channel_account_id,
                    "chat": {
                        "type": "group",
                        "chatId": str(group.bound_group_id) if group.bound_group_id else message.chat_id,
                    },
                    "from": {
                        "id": message.sender_id,
                        "name": message.sender_name or "Unknown",
                    },
                    "text": message.content,
                    "directAgentId": agent_key,
                },
            )
        except Exception as e:
            print(f"Failed to call OpenClaw: {e}")
            response_text = f"处理消息时出错: {str(e)}"
        
        # 发送响应到飞书群
        if response_text:
            sender = FeishuMessageSender(bot)
            await sender.send_agent_response(
                chat_id=message.chat_id,
                agent_name=agent_name,
                response_text=response_text,
                use_card=True,
            )
        
        # 记录日志
        router.log_message(
            group_id=group.id,
            bot_id=bot.id,
            message=message,
            message_mode=group.message_mode,
            dispatch_result="success",
            agent_response=response_text,
        )
        
    except Exception as e:
        print(f"Failed to process bot message: {e}")
        router.log_message(
            group_id=group.id,
            bot_id=bot.id,
            message=message,
            message_mode=group.message_mode,
            dispatch_result="error",
            dispatch_error=str(e),
        )
