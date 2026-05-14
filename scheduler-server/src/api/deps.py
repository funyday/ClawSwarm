"""API 依赖定义，集中提供路由层复用的依赖项。"""

from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import decode_access_token
from src.core.config import settings
from src.models.app_user import AppUser


DbSession = Session


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[AppUser]:
    """获取当前登录用户"""
    cookie_name = settings.auth_cookie_name or "clawswarm_token"
    token = request.cookies.get(cookie_name)
    
    if not token:
        return None
    
    user_id = decode_access_token(token)
    if not user_id:
        return None
    
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    return user


async def get_current_user_required(
    request: Request,
    db: Session = Depends(get_db),
) -> AppUser:
    """获取当前登录用户 (必须登录)"""
    user = await get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return user


async def get_current_admin_user(
    request: Request,
    db: Session = Depends(get_db),
) -> AppUser:
    """获取当前登录的管理员用户"""
    user = await get_current_user_required(request, db)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
