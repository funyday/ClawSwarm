"""API 依赖定义，集中提供路由层复用的依赖项。"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.security import decode_access_token
from src.core.config import settings
from src.models.app_user import AppUser

logger = logging.getLogger(__name__)


DbSession = Session


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


def extract_token(request: Request, authorization: Optional[str] = Header(None)) -> Optional[str]:
    """从 Cookie 或 Authorization 头中提取 token"""
    # 首先尝试从 Authorization 头获取 (Bearer token)
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    
    # 其次从 Cookie 获取
    cookie_name = settings.auth_cookie_name or "clawswarm_token"
    return request.cookies.get(cookie_name)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> Optional[AppUser]:
    """获取当前登录用户"""
    logger.info(f"get_current_user called, authorization header: {authorization}")
    
    token = extract_token(request, authorization)
    logger.info(f"Extracted token: {token[:50] if token else None}...")
    
    if not token:
        logger.info("No token found")
        return None
    
    user_id = decode_access_token(token)
    logger.info(f"Decoded user_id: {user_id}")
    
    if not user_id:
        logger.info("Token decode failed")
        return None
    
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    logger.info(f"Found user: {user.username if user else None}")
    return user


async def get_current_user_required(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> AppUser:
    """获取当前登录用户 (必须登录)"""
    user = await get_current_user(request, db, authorization)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return user


async def get_current_admin_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> AppUser:
    """获取当前登录的管理员用户"""
    user = await get_current_user_required(request, db, authorization)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
