import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.user import User
from src.dto.auth_dto import LoginDto, RegisterDto, TokenDto
from src.core.auth import verify_password, create_access_token, create_refresh_token
from .user_service import UserService


class AuthService:
    """认证服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
    
    async def login(self, login_dto: LoginDto, ip_address: str) -> Optional[TokenDto]:
        """用户登录"""
        # 根据邮箱查找用户
        user = await self.user_service.get_user_by_email(login_dto.email)
        if not user:
            logger.warning(f"Login failed: email {login_dto.email} not found")
            return None
        
        # 验证密码
        if not verify_password(login_dto.password, user.password):
            logger.warning(f"Login failed: invalid password for email {login_dto.email}")
            return None
        
        # 检查用户是否被禁用
        if not user.is_active:
            logger.warning(f"Login failed: user {login_dto.email} is disabled")
            return None
        
        # 更新最后登录信息
        await self.user_service.update_last_login(user.id, ip_address)
        
        # 生成令牌
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        logger.info(f"User logged in: {user.email}")
        
        return TokenDto(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=24 * 60 * 60  # 24小时
        )
    
    async def register(self, register_dto: RegisterDto) -> Optional[User]:
        """用户注册"""
        # 检查邮箱是否已存在
        existing_user = await self.user_service.get_user_by_email(register_dto.email)
        if existing_user:
            raise ValueError("邮箱已被注册")
        
        # 创建用户DTO
        from src.dto.user_dto import CreateUserDto
        create_user_dto = CreateUserDto(
            name=register_dto.name,
            email=register_dto.email,
            password=register_dto.password,
            role="user"
        )
        
        # 创建用户
        user = await self.user_service.create_user(create_user_dto)
        
        logger.info(f"User registered: {user.email}")
        return user
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenDto]:
        """刷新令牌"""
        try:
            from jose import jwt, JWTError
            from src.core.config import settings
            
            # 验证刷新令牌
            payload = jwt.decode(
                refresh_token,
                settings.jwt.secret,
                algorithms=["HS256"],
                issuer=settings.jwt.issuer,
                audience=settings.jwt.audience
            )
            
            # 检查令牌类型
            if payload.get("type") != "refresh":
                return None
            
            username = payload.get("sub")
            if not username:
                return None
            
            # 查找用户
            user = await self.user_service.get_user_by_username(username)
            if not user or not user.is_active:
                return None
            
            # 生成新令牌
            access_token = create_access_token(data={"sub": user.username})
            new_refresh_token = create_refresh_token(data={"sub": user.username})
            
            return TokenDto(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=24 * 60 * 60  # 24小时
            )
            
        except JWTError:
            return None
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""
        try:
            from jose import jwt, JWTError
            from src.core.config import settings
            
            # 验证令牌
            payload = jwt.decode(
                token,
                settings.jwt.secret,
                algorithms=["HS256"],
                issuer=settings.jwt.issuer,
                audience=settings.jwt.audience
            )
            
            username = payload.get("sub")
            if not username:
                return None
            
            # 查找用户
            user = await self.user_service.get_user_by_username(username)
            if not user or not user.is_active:
                return None
            
            return user
            
        except JWTError:
            return None 