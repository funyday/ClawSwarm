"""飞书 SSO 配置管理路由 (管理员)。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from src.api.deps import get_current_admin_user
from src.core.db import SessionLocal
from src.models.app_user import AppUser
from src.models.feishu_sso_config import FeishuSSOConfig
from src.schemas.feishu import (
    FeishuSSOConfigCreate,
    FeishuSSOConfigUpdate,
    FeishuSSOConfigResponse,
)
from src.core.security import get_password_hash


router = APIRouter(prefix="/admin/auth", tags=["管理员-认证配置"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/config", response_model=FeishuSSOConfigResponse | None)
async def get_sso_config(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """获取 SSO 配置"""
    config = db.query(FeishuSSOConfig).first()
    return config


@router.post("/config", response_model=FeishuSSOConfigResponse)
async def create_or_update_sso_config(
    config_data: FeishuSSOConfigCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """创建或更新 SSO 配置"""
    config = db.query(FeishuSSOConfig).first()
    
    if config:
        # 更新
        config.app_id = config_data.app_id
        config.app_secret = config_data.app_secret
        config.redirect_uri = config_data.redirect_uri
        config.state_secret = config_data.state_secret
        config.scopes = config_data.scopes
        config.allowed_departments = str(config_data.allowed_departments) if config_data.allowed_departments else None
        config.allowed_emails = str(config_data.allowed_emails) if config_data.allowed_emails else None
        config.auto_create_user = config_data.auto_create_user
        config.enabled = config_data.enabled
    else:
        # 创建
        config = FeishuSSOConfig(
            app_id=config_data.app_id,
            app_secret=config_data.app_secret,
            redirect_uri=config_data.redirect_uri,
            state_secret=config_data.state_secret,
            scopes=config_data.scopes,
            allowed_departments=str(config_data.allowed_departments) if config_data.allowed_departments else None,
            allowed_emails=str(config_data.allowed_emails) if config_data.allowed_emails else None,
            auto_create_user=config_data.auto_create_user,
            enabled=config_data.enabled,
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    return config


@router.post("/config/test")
async def test_sso_connection(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """测试 SSO 连接"""
    config = db.query(FeishuSSOConfig).first()
    
    if not config:
        return {"success": False, "message": "SSO 未配置"}
    
    try:
        # 测试获取 access_token
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token",
                json={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/json"},
                params={
                    "app_id": config.app_id,
                    "app_secret": config.app_secret,
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "连接成功"}
            else:
                return {"success": False, "message": f"连接失败: {response.text}"}
    except Exception as e:
        return {"success": False, "message": f"连接异常: {str(e)}"}
