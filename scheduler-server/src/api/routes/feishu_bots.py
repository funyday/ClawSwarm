"""飞书 Bot 管理路由。"""

from typing import Optional
import httpx

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_current_user_required
from src.core.db import SessionLocal
from src.models.app_user import AppUser
from src.models.feishu_bot import FeishuBot
from src.models.feishu_group_bot import FeishuGroupBot
from src.schemas.feishu import (
    FeishuBotCreate,
    FeishuBotUpdate,
    FeishuBotResponse,
    FeishuBotDetailResponse,
    FeishuBotTestRequest,
    FeishuBotTestResponse,
)


router = APIRouter(prefix="/feishu/bots", tags=["飞书 Bot"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[FeishuBotDetailResponse])
async def list_bots(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """获取 Bot 列表"""
    bots = db.query(FeishuBot).all()
    result = []
    for bot in bots:
        bot_dict = {
            "id": bot.id,
            "name": bot.name,
            "app_id": bot.app_id,
            "instance_id": bot.instance_id,
            "agent_id": bot.agent_id,
            "status": bot.status,
            "created_at": bot.created_at,
            "updated_at": bot.updated_at,
            "instance_name": bot.instance.name if bot.instance else None,
            "agent_key": bot.agent.agent_key if bot.agent else None,
            "agent_display_name": bot.agent.display_name if bot.agent else None,
        }
        result.append(FeishuBotDetailResponse(**bot_dict))
    return result


@router.post("", response_model=FeishuBotResponse)
async def create_bot(
    bot_data: FeishuBotCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """创建 Bot"""
    # 检查 app_id 是否已存在
    existing = db.query(FeishuBot).filter(FeishuBot.app_id == bot_data.app_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该 App ID 已存在")
    
    bot = FeishuBot(
        name=bot_data.name,
        app_id=bot_data.app_id,
        app_secret=bot_data.app_secret,
        webhook_secret=bot_data.webhook_secret,
        instance_id=bot_data.instance_id,
        agent_id=bot_data.agent_id,
        status=bot_data.status,
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


@router.get("/{bot_id}", response_model=FeishuBotDetailResponse)
async def get_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """获取 Bot 详情"""
    bot = db.query(FeishuBot).filter(FeishuBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot 不存在")
    
    return FeishuBotDetailResponse(
        id=bot.id,
        name=bot.name,
        app_id=bot.app_id,
        instance_id=bot.instance_id,
        agent_id=bot.agent_id,
        status=bot.status,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
        instance_name=bot.instance.name if bot.instance else None,
        agent_key=bot.agent.agent_key if bot.agent else None,
        agent_display_name=bot.agent.display_name if bot.agent else None,
    )


@router.put("/{bot_id}", response_model=FeishuBotResponse)
async def update_bot(
    bot_id: int,
    bot_data: FeishuBotUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """更新 Bot"""
    bot = db.query(FeishuBot).filter(FeishuBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot 不存在")
    
    update_data = bot_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bot, key, value)
    
    db.commit()
    db.refresh(bot)
    return bot


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """删除 Bot"""
    bot = db.query(FeishuBot).filter(FeishuBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot 不存在")
    
    # 删除关联的群组 Bot
    db.query(FeishuGroupBot).filter(FeishuGroupBot.bot_id == bot_id).delete()
    
    db.delete(bot)
    db.commit()
    return {"success": True}


@router.post("/{bot_id}/test", response_model=FeishuBotTestResponse)
async def test_bot(
    bot_id: int,
    test_data: FeishuBotTestRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """测试 Bot 连接"""
    bot = db.query(FeishuBot).filter(FeishuBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot 不存在")
    
    try:
        # 获取 tenant_access_token
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": bot.app_id,
                    "app_secret": bot.app_secret,
                }
            )
            
            if token_response.status_code != 200:
                return FeishuBotTestResponse(
                    success=False,
                    message=f"获取 access_token 失败: {token_response.text}"
                )
            
            token_data = token_response.json()
            if token_data.get("code") != 0:
                return FeishuBotTestResponse(
                    success=False,
                    message=f"飞书 API 错误: {token_data.get('msg')}"
                )
            
            access_token = token_data.get("tenant_access_token")
            
            # 发送测试消息
            message_response = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages",
                params={"receive_id_type": "chat_id"},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "receive_id": test_data.chat_id,
                    "msg_type": "text",
                    "content": {"text": f"[测试消息] {test_data.message}"},
                }
            )
            
            if message_response.status_code == 200:
                return FeishuBotTestResponse(success=True, message="测试消息发送成功")
            else:
                return FeishuBotTestResponse(
                    success=False,
                    message=f"发送消息失败: {message_response.text}"
                )
    except Exception as e:
        return FeishuBotTestResponse(success=False, message=f"连接异常: {str(e)}")
