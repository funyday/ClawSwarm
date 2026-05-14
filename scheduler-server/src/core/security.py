"""
这里放 channel 对接相关的签名和校验辅助函数。
"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings


# JWT 配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def now_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hmac_sha256_hex(secret: str, message: str) -> str:
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def build_channel_canonical_string(*, timestamp_ms: int, nonce: str, method: str, path: str, body_sha256_hex: str) -> str:
    return f"{timestamp_ms}\n{nonce}\n{method.upper()}\n{path}\n{body_sha256_hex}\n"


def new_nonce() -> str:
    return uuid.uuid4().hex


def verify_callback_signature(*, token: str, timestamp: str, body: bytes, signature: str) -> bool:
    raw = hmac_sha256_hex(token, f"{timestamp}.{body.decode('utf-8')}")
    expected = f"sha256={raw}"
    return hmac.compare_digest(expected, signature)


# ============== 密码和 JWT 工具 ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(to_encode, settings.auth_secret, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """解码 JWT token，返回 user_id"""
    try:
        payload = jwt.decode(token, settings.auth_secret, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
