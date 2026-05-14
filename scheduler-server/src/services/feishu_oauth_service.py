"""飞书 OAuth SSO 服务。"""

import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from src.models.app_user import AppUser
from src.models.feishu_sso_config import FeishuSSOConfig
from src.schemas.feishu import FeishuUserInfo


class FeishuOAuthService:
    """飞书 OAuth 2.0 服务"""
    
    AUTHORIZE_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"
    TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
    USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    
    def __init__(self, db: Session):
        self.db = db
        self.config = self._get_config()
    
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
    
    async def exchange_code_for_token(self, code: str) -> dict:
        """用授权码换取 access_token"""
        if not self.config:
            raise ValueError("飞书 SSO 未配置")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                },
                headers={
                    "Content-Type": "application/json",
                },
                params={
                    "app_id": self.config.app_id,
                    "app_secret": self.config.app_secret,
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"获取 access_token 失败: {response.text}")
            
            data = response.json()
            if data.get("code") != 0:
                raise ValueError(f"飞书 API 错误: {data.get('msg')}")
            
            return data.get("data", {})
    
    async def get_user_info(self, access_token: str) -> FeishuUserInfo:
        """获取用户信息"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise ValueError(f"获取用户信息失败: {response.text}")
            
            data = response.json()
            if data.get("code") != 0:
                raise ValueError(f"飞书 API 错误: {data.get('msg')}")
            
            user_data = data.get("data", {})
            return FeishuUserInfo(
                union_id=user_data.get("union_id", ""),
                open_id=user_data.get("open_id", ""),
                name=user_data.get("name", ""),
                email=user_data.get("email", ""),
                avatar_url=user_data.get("avatar_url", ""),
                department=user_data.get("department", ""),
            )
    
    def check_access_control(self, user_info: FeishuUserInfo) -> tuple[bool, str]:
        """检查用户访问权限"""
        if not self.config:
            return False, "SSO 未配置"
        
        # 检查部门
        if self.config.allowed_departments:
            departments = json.loads(self.config.allowed_departments)
            if user_info.department and user_info.department not in departments:
                return False, f"不在允许的部门范围内"
        
        # 检查邮箱
        if self.config.allowed_emails and user_info.email:
            email_suffixes = json.loads(self.config.allowed_emails)
            email_lower = user_info.email.lower()
            if not any(email_lower.endswith(suffix.lower()) for suffix in email_suffixes):
                return False, f"邮箱不在允许范围内"
        
        return True, "允许访问"
    
    def get_or_create_user(self, user_info: FeishuUserInfo) -> AppUser:
        """获取或创建用户"""
        # 查找现有用户
        user = self.db.query(AppUser).filter(
            AppUser.feishu_union_id == user_info.union_id
        ).first()
        
        if user:
            # 更新用户信息
            user.feishu_open_id = user_info.open_id
            user.feishu_name = user_info.name
            user.feishu_avatar = user_info.avatar_url
            user.feishu_department = user_info.department
            user.feishu_email = user_info.email
            user.last_login_at = datetime.utcnow()
            user.login_count += 1
            self.db.commit()
            return user
        
        # 自动创建新用户
        if not self.config or not self.config.auto_create_user:
            raise ValueError("用户不存在且未开启自动创建")
        
        from uuid import uuid4
        user = AppUser(
            id=str(uuid4()),
            username=user_info.union_id,  # 使用 union_id 作为用户名
            display_name=user_info.name,
            password_hash=None,  # SSO 用户无密码
            feishu_user_id=user_info.union_id,
            feishu_open_id=user_info.open_id,
            feishu_union_id=user_info.union_id,
            feishu_name=user_info.name,
            feishu_avatar=user_info.avatar_url,
            feishu_department=user_info.department,
            feishu_email=user_info.email,
            sso_enabled=True,
            last_login_at=datetime.utcnow(),
            login_count=1,
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


# 会话状态存储 (生产环境应使用 Redis)
_session_states: dict[str, dict] = {}


class SessionStateManager:
    """会话状态管理器"""
    
    @staticmethod
    def store_state(state: str, redirect_uri: str, expires_in: int = 600) -> None:
        """存储 state"""
        _session_states[state] = {
            "redirect_uri": redirect_uri,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in),
        }
    
    @staticmethod
    def get_and_delete_state(state: str) -> Optional[str]:
        """获取并删除 state (一次性)"""
        if state not in _session_states:
            return None
        
        session_data = _session_states.pop(state)
        if datetime.utcnow() > session_data["expires_at"]:
            return None
        
        return session_data["redirect_uri"]
    
    @staticmethod
    def cleanup_expired() -> None:
        """清理过期 state"""
        now = datetime.utcnow()
        expired = [s for s, d in _session_states.items() if now > d["expires_at"]]
        for s in expired:
            _session_states.pop(s, None)
