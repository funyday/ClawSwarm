"""飞书群组管理路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_current_user_required
from src.core.db import SessionLocal
from src.models.app_user import AppUser
from src.models.feishu_group import FeishuGroup
from src.models.feishu_group_bot import FeishuGroupBot
from src.models.feishu_bot import FeishuBot
from src.models.feishu_message_log import FeishuMessageLog
from src.schemas.feishu import (
    FeishuGroupCreate,
    FeishuGroupUpdate,
    FeishuGroupResponse,
    FeishuGroupBotCreate,
    FeishuGroupBotResponse,
    FeishuGroupBotWithDetailResponse,
    FeishuMessageLogResponse,
)


router = APIRouter(prefix="/feishu/groups", tags=["飞书群组"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[FeishuGroupResponse])
async def list_groups(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """获取群组列表"""
    groups = db.query(FeishuGroup).all()
    return groups


@router.post("", response_model=FeishuGroupResponse)
async def create_group(
    group_data: FeishuGroupCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """创建群组绑定"""
    # 检查飞书群是否已绑定
    existing = db.query(FeishuGroup).filter(
        FeishuGroup.feishu_chat_id == group_data.feishu_chat_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该飞书群已绑定")
    
    group = FeishuGroup(
        feishu_chat_id=group_data.feishu_chat_id,
        name=group_data.name,
        bound_group_id=group_data.bound_group_id,
        message_mode=group_data.message_mode,
        round_robin_timeout=group_data.round_robin_timeout,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get("/{group_id}", response_model=FeishuGroupResponse)
async def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """获取群组详情"""
    group = db.query(FeishuGroup).filter(FeishuGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    return group


@router.put("/{group_id}", response_model=FeishuGroupResponse)
async def update_group(
    group_id: int,
    group_data: FeishuGroupUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """更新群组配置"""
    group = db.query(FeishuGroup).filter(FeishuGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    update_data = group_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    
    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """删除群组绑定"""
    group = db.query(FeishuGroup).filter(FeishuGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    # 删除关联的 Bot
    db.query(FeishuGroupBot).filter(FeishuGroupBot.group_id == group_id).delete()
    
    db.delete(group)
    db.commit()
    return {"success": True}


# ============== 群组 Bot 管理 ==============

@router.get("/{group_id}/bots", response_model=list[FeishuGroupBotWithDetailResponse])
async def list_group_bots(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """获取群组关联的 Bots"""
    group = db.query(FeishuGroup).filter(FeishuGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    bots = db.query(FeishuGroupBot).filter(
        FeishuGroupBot.group_id == group_id
    ).order_by(FeishuGroupBot.priority).all()
    
    result = []
    for gb in bots:
        bot = db.query(FeishuBot).filter(FeishuBot.id == gb.bot_id).first()
        result.append(FeishuGroupBotWithDetailResponse(
            id=gb.id,
            group_id=gb.group_id,
            bot_id=gb.bot_id,
            priority=gb.priority,
            enabled=gb.enabled,
            created_at=gb.created_at,
            bot_name=bot.name if bot else None,
            bot_app_id=bot.app_id if bot else None,
            instance_name=bot.instance.name if bot and bot.instance else None,
            agent_key=bot.agent.agent_key if bot and bot.agent else None,
        ))
    return result


@router.post("/{group_id}/bots", response_model=FeishuGroupBotResponse)
async def add_bot_to_group(
    group_id: int,
    bot_data: FeishuGroupBotCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """添加 Bot 到群组"""
    # 检查群组
    group = db.query(FeishuGroup).filter(FeishuGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    # 检查 Bot
    bot = db.query(FeishuBot).filter(FeishuBot.id == bot_data.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot 不存在")
    
    # 检查是否已关联
    existing = db.query(FeishuGroupBot).filter(
        FeishuGroupBot.group_id == group_id,
        FeishuGroupBot.bot_id == bot_data.bot_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该 Bot 已关联到此群组")
    
    group_bot = FeishuGroupBot(
        group_id=group_id,
        bot_id=bot_data.bot_id,
        priority=bot_data.priority,
        enabled=bot_data.enabled,
    )
    db.add(group_bot)
    db.commit()
    db.refresh(group_bot)
    return group_bot


@router.delete("/{group_id}/bots/{bot_id}")
async def remove_bot_from_group(
    group_id: int,
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """从群组移除 Bot"""
    group_bot = db.query(FeishuGroupBot).filter(
        FeishuGroupBot.group_id == group_id,
        FeishuGroupBot.bot_id == bot_id
    ).first()
    if not group_bot:
        raise HTTPException(status_code=404, detail="关联不存在")
    
    db.delete(group_bot)
    db.commit()
    return {"success": True}


# ============== 消息日志 ==============

@router.get("/{group_id}/messages", response_model=list[FeishuMessageLogResponse])
async def get_group_messages(
    group_id: int,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user_required),
):
    """获取群组消息历史"""
    group = db.query(FeishuGroup).filter(FeishuGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    
    messages = db.query(FeishuMessageLog).filter(
        FeishuMessageLog.group_id == group_id
    ).order_by(
        FeishuMessageLog.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return messages
