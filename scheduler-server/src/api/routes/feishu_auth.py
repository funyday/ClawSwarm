"""飞书 SSO 认证路由。"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request
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
        allowed, message = oauth_service.check_access_control(user_info)
        if not allowed:
            raise HTTPException(status_code=403, detail=message)
        
        # 获取或创建用户
        user = oauth_service.get_or_create_user(user_info)
        
        # 设置认证 Cookie
        from src.core.security import create_access_token
        
        access_token_jwt = create_access_token(user.id)
        cookie_name = settings.auth_cookie_name or "clawswarm_token"
        response.set_cookie(
            key=cookie_name,
            value=access_token_jwt,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,  # 7 天
        )
        
        # 返回用户信息
        return LoginResponse(
            success=True,
            user=AppUserResponse.model_validate(user),
            redirect_url=stored_redirect,
        )
        
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


@router.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    获取当前用户信息
    """
    from src.api.deps import get_current_user
    from src.models.app_user import AppUser
    
    try:
        user = await get_current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="未登录")
        return AppUserResponse.model_validate(user)
    except Exception:
        raise HTTPException(status_code=401, detail="未登录")
