from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import JWTConfig
from database import get_db
from models.user import User

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWTConfig.get_access_token_expire_minutes())
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWTConfig.get_secret_key(), algorithm=JWTConfig.get_algorithm())
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWTConfig.get_refresh_token_expire_minutes())
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWTConfig.get_secret_key(), algorithm=JWTConfig.get_algorithm())
    return encoded_jwt


def verify_token(token: str) -> dict:
    """验证令牌"""
    try:
        payload = jwt.decode(token, JWTConfig.get_secret_key(), algorithms=[JWTConfig.get_algorithm()])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def get_user_roles(user: User, db: Session) -> list:
    """获取用户角色"""
    from models.user import UserInRole, Role
    
    user_roles = db.query(UserInRole).filter(UserInRole.user_id == user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    return [role.name for role in roles]


def check_user_permission(user: User, required_roles: list, db: Session) -> bool:
    """检查用户权限"""
    user_roles = get_user_roles(user, db)
    return any(role in user_roles for role in required_roles) 