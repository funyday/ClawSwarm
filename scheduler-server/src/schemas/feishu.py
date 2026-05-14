"""飞书相关 Schema。"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ============== SSO 配置 Schema ==============

class FeishuSSOConfigBase(BaseModel):
    app_id: str
    redirect_uri: str
    scopes: str = "contact:user.base:readonly"
    allowed_departments: Optional[list[str]] = None
    allowed_emails: Optional[list[str]] = None
    auto_create_user: bool = True
    enabled: bool = True


class FeishuSSOConfigCreate(FeishuSSOConfigBase):
    app_secret: str
    state_secret: str


class FeishuSSOConfigUpdate(BaseModel):
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    state_secret: Optional[str] = None
    scopes: Optional[str] = None
    allowed_departments: Optional[list[str]] = None
    allowed_emails: Optional[list[str]] = None
    auto_create_user: Optional[bool] = None
    enabled: Optional[bool] = None


class FeishuSSOConfigResponse(FeishuSSOConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 飞书用户信息 Schema ==============

class FeishuUserInfo(BaseModel):
    """飞书用户信息 (OAuth 回调返回)"""
    union_id: str
    open_id: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    department: Optional[str] = None


# ============== 用户 Schema ==============

class AppUserBase(BaseModel):
    username: str
    display_name: str


class AppUserCreate(AppUserBase):
    password: Optional[str] = None


class AppUserResponse(AppUserBase):
    id: str
    feishu_user_id: Optional[str] = None
    feishu_name: Optional[str] = None
    feishu_avatar: Optional[str] = None
    feishu_department: Optional[str] = None
    sso_enabled: bool
    is_admin: bool
    last_login_at: Optional[datetime] = None
    login_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 登录响应 Schema ==============

class LoginResponse(BaseModel):
    success: bool
    user: Optional[AppUserResponse] = None
    message: Optional[str] = None
    redirect_url: Optional[str] = None


# ============== Feishu Bot Schema ==============

class FeishuBotBase(BaseModel):
    name: str
    instance_id: int
    agent_id: Optional[int] = None
    status: str = "active"


class FeishuBotCreate(FeishuBotBase):
    app_id: str
    app_secret: str
    webhook_secret: str


class FeishuBotUpdate(BaseModel):
    name: Optional[str] = None
    instance_id: Optional[int] = None
    agent_id: Optional[int] = None
    status: Optional[str] = None


class FeishuBotResponse(FeishuBotBase):
    id: int
    app_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeishuBotDetailResponse(FeishuBotResponse):
    instance_name: Optional[str] = None
    agent_key: Optional[str] = None
    agent_display_name: Optional[str] = None


# ============== Feishu Group Schema ==============

class FeishuGroupBase(BaseModel):
    feishu_chat_id: str
    name: Optional[str] = None
    bound_group_id: Optional[int] = None
    message_mode: str = "at_mode"
    round_robin_timeout: int = 30
    status: str = "active"


class FeishuGroupCreate(BaseModel):
    feishu_chat_id: str
    name: Optional[str] = None
    bound_group_id: Optional[int] = None
    message_mode: str = "at_mode"
    round_robin_timeout: int = 30


class FeishuGroupUpdate(BaseModel):
    name: Optional[str] = None
    bound_group_id: Optional[int] = None
    message_mode: Optional[str] = None
    round_robin_timeout: Optional[int] = None
    status: Optional[str] = None


class FeishuGroupResponse(FeishuGroupBase):
    id: int
    round_robin_index: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Feishu Group Bot Schema ==============

class FeishuGroupBotBase(BaseModel):
    bot_id: int
    priority: int = 0
    enabled: bool = True


class FeishuGroupBotCreate(FeishuGroupBotBase):
    pass


class FeishuGroupBotResponse(FeishuGroupBotBase):
    id: int
    group_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FeishuGroupBotWithDetailResponse(FeishuGroupBotResponse):
    bot_name: Optional[str] = None
    bot_app_id: Optional[str] = None
    instance_name: Optional[str] = None
    agent_key: Optional[str] = None


# ============== Feishu Message Log Schema ==============

class FeishuMessageLogResponse(BaseModel):
    id: int
    group_id: Optional[int] = None
    bot_id: Optional[int] = None
    sender_id: str
    sender_name: Optional[str] = None
    feishu_message_id: str
    content: str
    message_mode: str
    dispatch_result: str
    dispatch_error: Optional[str] = None
    agent_response: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 测试连接 Schema ==============

class FeishuBotTestRequest(BaseModel):
    chat_id: str
    message: str = "这是一条测试消息"


class FeishuBotTestResponse(BaseModel):
    success: bool
    message: Optional[str] = None

