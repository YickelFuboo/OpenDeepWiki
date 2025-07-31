"""
认证管理服务
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import JWTError, jwt

from db.models.user import User
from api.schemes.user import UserLogin, TokenResponse
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户登录"""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                return None
            
            if not user.verify_password(password):
                return None
            
            return user
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None
    
    def login(self, user_credentials: UserLogin) -> TokenResponse:
        """用户登录"""
        try:
            user = self.authenticate_user(user_credentials.username, user_credentials.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户账户已被禁用"
                )
            
            access_token_expires = timedelta(minutes=settings.jwt.access_token_expire_minutes)
            access_token = self.create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user.id,
                username=user.username
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登录失败"
            )
    
    def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""
        try:
            payload = self.verify_token(token)
            if payload is None:
                return None
            
            username: str = payload.get("sub")
            if username is None:
                return None
            
            user = self.db.query(User).filter(User.username == username).first()
            return user
        except Exception as e:
            logger.error(f"获取当前用户失败: {e}")
            return None 