"""飞书 OAuth SSO 服务。"""

import hashlib
import secrets
import json
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from src.models.app_user import AppUser
from src.models.feishu_sso_config import FeishuSSOConfig
from src.schemas.feishu import FeishuUserInfo


class SessionStateManager:
    """简单的内存状态管理器（生产环境建议使用 Redis）"""
    _states: dict = {}
    
    @classmethod
    def store_state(cls, state: str, redirect_url: str, expires_in: int = 600):
        """存储 state 和对应的重定向 URL"""
        cls._states[state] = {
            "redirect_url": redirect_url,
            "created_at": time.time(),
            "expires_in": expires_in,
        }
    
    @classmethod
    def get_and_delete_state(cls, state: str) -> Optional[str]:
        """获取并删除 state（一次性使用）"""
        if state not in cls._states:
            return None
        
        stored = cls._states[state]
        
        # 检查是否过期
        if time.time() - stored["created_at"] > stored["expires_in"]:
            del cls._states[state]
            return None
        
        redirect_url = stored["redirect_url"]
        del cls._states[state]
        return redirect_url


class FeishuOAuthService:
    """飞书 OAuth 2.0 服务"""
    
    AUTHORIZE_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"
    TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
    USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    APP_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    
    def __init__(self, db: Session):
        self.db = db
        self.config = self._get_config()
        self._app_access_token = None
        self._app_token_expires_at = None
    
    def _get_config(self) -> Optional[FeishuSSOConfig]:
        """获取 SSO 配置"""
        return self.db.query(FeishuSSOConfig).filter(
            FeishuSSOConfig.enabled == True
        ).first()
    
    def is_enabled(self) -> bool:
        """检查 SSO 是否启用"""
        return self.config is not None
    
    def get_authorize_url(self, redirect_uri: str, state: str) -> str:
        """生成飞书授权 URL"""
        if not self.config:
            raise ValueError("飞书 SSO 未配置")
        
        params = {
            "app_id": self.config.app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZE_URL}?{query}"
    
    @staticmethod
    def generate_state() -> str:
        """生成随机 state 参数"""
        return secrets.token_urlsafe(32)
    
    def verify_state(self, state: str, stored_state: str) -> bool:
        """验证 state 参数"""
        if not self.config:
            return False
        return secrets.compare_digest(state, stored_state)
    
    async def _get_app_access_token(self) -> str:
        """获取 app_access_token"""
        # 检查缓存
        if self._app_access_token and self._app_token_expires_at:
            if datetime.utcnow() < self._app_token_expires_at:
                return self._app_access_token
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.APP_TOKEN_URL,
                json={
                    "app_id": self.config.app_id,
                    "app_secret": self.config.app_secret,
                }
            )
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"获取 app_access_token 失败: {data.get('msg')}")
            
            self._app_access_token = data["app_access_token"]
            # 提前 5 分钟过期
            expires_in = data.get("expire", 7200) - 300
            self._app_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return self._app_access_token
    
    async def exchange_code_for_token(self, code: str) -> dict:
        """用授权码换取 access_token"""
        if not self.config:
            raise ValueError("飞书 SSO 未配置")
        
        app_token = await self._get_app_access_token()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {app_token}",
                }
            )
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"兑换 token 失败: {data.get('msg')}, code: {data.get('code')}")
            
            return {
                "access_token": data["data"]["access_token"],
                "token_type": data["data"]["token_type"],
                "expires_in": data["data"]["expires_in"],
                "refresh_token": data["data"].get("refresh_token"),
                "scope": data["data"].get("scope"),
            }
    
    async def get_user_info(self, access_token: str) -> FeishuUserInfo:
        """获取用户信息"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                }
            )
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"获取用户信息失败: {data.get('msg')}")
            
            user_data = data["data"]
            return FeishuUserInfo(
                union_id=user_data.get("union_id", ""),
                open_id=user_data.get("open_id", ""),
                name=user_data.get("name", ""),
                email=user_data.get("email", ""),
                avatar_url=user_data.get("avatar_url", ""),
                tenant_key=user_data.get("tenant_key", ""),
            )
    
    def create_or_update_user(self, user_info: FeishuUserInfo) -> AppUser:
        """创建或更新用户"""
        user = self.db.query(AppUser).filter(
            AppUser.feishu_union_id == user_info.union_id
        ).first()
        
        if not user:
            # 检查是否有相同 email 的用户
            user = self.db.query(AppUser).filter(
                AppUser.username == user_info.email
            ).first()
        
        if not user:
            # 创建新用户
            user = AppUser(
                username=user_info.email or user_info.union_id,
                display_name=user_info.name,
                feishu_union_id=user_info.union_id,
                feishu_open_id=user_info.open_id,
                feishu_name=user_info.name,
                feishu_avatar=user_info.avatar_url,
                feishu_email=user_info.email,
                sso_enabled=True,
                is_admin=False,
            )
            self.db.add(user)
        else:
            # 更新用户信息
            user.feishu_union_id = user_info.union_id
            user.feishu_open_id = user_info.open_id
            user.feishu_name = user_info.name
            user.feishu_avatar = user_info.avatar_url
            if not user.feishu_email:
                user.feishu_email = user_info.email
        
        user.last_login_at = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def check_user_access(self, user_info: FeishuUserInfo) -> bool:
        """检查用户是否有访问权限"""
        if not self.config:
            return True  # 没有配置则允许访问
        
        # 如果禁用了自动创建，则只允许已存在的用户
        if not self.config.auto_create_user:
            existing_user = self.db.query(AppUser).filter(
                AppUser.feishu_union_id == user_info.union_id
            ).first()
            return existing_user is not None
        
        return True  # 允许自动创建用户
