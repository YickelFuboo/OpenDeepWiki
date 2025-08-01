from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .config import settings
from .database import get_db
from src.models.user import User
from src.services.user_service import UserService

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt.expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt.secret, 
        algorithm="HS256",
        issuer=settings.jwt.issuer,
        audience=settings.jwt.audience
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt.refresh_expire_minutes)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt.secret, 
        algorithm="HS256",
        issuer=settings.jwt.issuer,
        audience=settings.jwt.audience
    )
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt.secret, 
            algorithms=["HS256"],
            issuer=settings.jwt.issuer,
            audience=settings.jwt.audience
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_from_cookie_or_header(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """从Cookie或Header获取当前用户"""
    token = None
    
    # 首先检查Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # 如果Authorization header中没有token，则检查cookie
    if not token:
        token = request.cookies.get("token")
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt.secret, 
            algorithms=["HS256"],
            issuer=settings.jwt.issuer,
            audience=settings.jwt.audience
        )
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    return user if user and user.is_active else None


# 权限检查装饰器
def require_roles(*roles: str):
    """要求特定角色的装饰器"""
    def decorator(func):
        async def wrapper(current_user: User = Depends(get_current_active_user), *args, **kwargs):
            if not any(role in current_user.roles for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            return await func(current_user, *args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """要求管理员权限"""
    return require_roles("admin")


def require_user():
    """要求用户权限"""
    return require_roles("user", "admin") 