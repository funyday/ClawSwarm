"""飞书 SSO 认证路由。"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from src.core.db import SessionLocal
from src.core.config import settings
from src.services.feishu_oauth_service import FeishuOAuthService, SessionStateManager
from src.schemas.feishu import LoginResponse, AppUserResponse


router = APIRouter(prefix="/auth", tags=["认证"])


def get_db():
    """数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/feishu")
async def feishu_login(
    request: Request,
    redirect_url: str = "/",
    db: Session = Depends(get_db),
):
    """
    跳转飞书授权页
    """
    oauth_service = FeishuOAuthService(db)
    
    if not oauth_service.is_enabled():
        raise HTTPException(status_code=400, detail="飞书 SSO 未配置")
    
    # 生成 state
    state = FeishuOAuthService.generate_state()
    SessionStateManager.store_state(state, redirect_url)
    
    # 从数据库获取回调 URL
    callback_uri = oauth_service.config.redirect_uri if oauth_service.config else None
    
    # 如果数据库没有配置，使用 settings 中的默认值
    if not callback_uri:
        callback_base = settings.clawswarm_base_url.rstrip("/")
        callback_uri = f"{callback_base}/auth/feishu/callback"
    
    # 生成授权 URL
    authorize_url = oauth_service.get_authorize_url(callback_uri, state)
    
    return RedirectResponse(url=authorize_url)


@router.get("/feishu/callback")
async def feishu_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    飞书 OAuth 回调
    """
    oauth_service = FeishuOAuthService(db)
    
    if not oauth_service.is_enabled():
        raise HTTPException(status_code=400, detail="飞书 SSO 未配置")
    
    # 验证 state
    stored_redirect = SessionStateManager.get_and_delete_state(state)
    if not stored_redirect:
        raise HTTPException(status_code=400, detail="无效的 state")
    
    try:
        # 交换 token
        token_data = await oauth_service.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        
        # 获取用户信息
        user_info = await oauth_service.get_user_info(access_token)
        
        # 检查访问权限
        if not oauth_service.check_user_access(user_info):
            raise HTTPException(status_code=403, detail="您没有访问权限")
        
        # 获取或创建用户
        user = oauth_service.create_or_update_user(user_info)
        
        # 创建访问 token
        from src.core.security import create_access_token
        
        access_token_jwt = create_access_token(user.id)
        
        # 返回重定向到前端页面，带上 token
        # 前端会读取 token 并初始化登录状态
        frontend_base = settings.clawswarm_base_url.rstrip("/")
        redirect_url = f"{frontend_base}/?login_token={access_token_jwt}"
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
):
    """
    登出
    """
    cookie_name = settings.auth_cookie_name or "clawswarm_token"
    response.delete_cookie(key=cookie_name)
    return {"success": True}


import logging
import sys
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

@router.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
):
    """
    获取当前用户信息
    """
    print(f"[DEBUG] /me called, authorization: {authorization}", flush=True)
    
    from src.api.deps import get_current_user
    from src.models.app_user import AppUser
    
    try:
        user = await get_current_user(request, db, authorization)
        print(f"[DEBUG] user from deps: {user}", flush=True)
        if not user:
            raise HTTPException(status_code=401, detail="未登录")
        return AppUserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] error: {e}", flush=True)
        raise HTTPException(status_code=401, detail="未登录")
