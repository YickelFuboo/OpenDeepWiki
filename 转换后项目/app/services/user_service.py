import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from loguru import logger

from src.models.user import User
from src.dto.user_dto import CreateUserDto, UpdateUserDto, UserInfoDto, UpdateProfileDto, VerifyPasswordDto, ChangePasswordDto
from src.core.auth import get_password_hash, verify_password


class UserService:
    """用户管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_user_list(self, page: int = 1, page_size: int = 10, keyword: Optional[str] = None) -> tuple[List[User], int]:
        """获取用户列表"""
        query = select(User)
        
        # 如果有关键词，则按名称或邮箱搜索
        if keyword:
            query = query.where(
                User.name.contains(keyword) | User.email.contains(keyword)
            )
        
        # 按创建时间降序排序
        query = query.order_by(User.created_at.desc())
        
        # 计算总数
        count_result = await self.db.execute(
            select(User).where(query.whereclause) if query.whereclause else select(User)
        )
        total = len(count_result.scalars().all())
        
        # 获取分页数据
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return users, total
    
    async def create_user(self, create_user_dto: CreateUserDto) -> User:
        """创建用户"""
        # 检查邮箱是否已存在
        existing_user = await self.get_user_by_email(create_user_dto.email)
        if existing_user:
            raise ValueError("邮箱已存在")
        
        # 生成用户名（如果没有提供）
        username = create_user_dto.name.lower().replace(" ", "_")
        existing_username = await self.get_user_by_username(username)
        if existing_username:
            username = f"{username}_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            name=create_user_dto.name,
            email=create_user_dto.email,
            password=get_password_hash(create_user_dto.password),
            roles=[create_user_dto.role],
            avatar=create_user_dto.avatar or "",
            created_at=datetime.utcnow()
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Created user: {user.email}")
        return user
    
    async def update_user(self, user_id: str, update_user_dto: UpdateUserDto) -> Optional[User]:
        """更新用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # 检查邮箱是否已被其他用户使用
        if update_user_dto.email != user.email:
            existing_user = await self.get_user_by_email(update_user_dto.email)
            if existing_user:
                raise ValueError("邮箱已被其他用户使用")
        
        # 更新用户信息
        user.name = update_user_dto.name
        user.email = update_user_dto.email
        user.roles = [update_user_dto.role]
        user.avatar = update_user_dto.avatar or user.avatar
        user.updated_at = datetime.utcnow()
        
        # 如果提供了新密码，则更新密码
        if update_user_dto.password:
            user.password = get_password_hash(update_user_dto.password)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Updated user: {user.email}")
        return user
    
    async def update_profile(self, user_id: str, update_profile_dto: UpdateProfileDto) -> Optional[User]:
        """更新用户资料"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # 检查邮箱是否已被其他用户使用
        if update_profile_dto.email != user.email:
            existing_user = await self.get_user_by_email(update_profile_dto.email)
            if existing_user:
                raise ValueError("邮箱已被其他用户使用")
        
        # 更新用户信息
        user.name = update_profile_dto.name
        user.email = update_profile_dto.email
        user.avatar = update_profile_dto.avatar or user.avatar
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Updated profile for user: {user.email}")
        return user
    
    async def verify_password(self, user_id: str, verify_password_dto: VerifyPasswordDto) -> bool:
        """验证密码"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        return verify_password(verify_password_dto.password, user.password)
    
    async def change_password(self, user_id: str, change_password_dto: ChangePasswordDto) -> bool:
        """修改密码"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # 验证当前密码
        if not verify_password(change_password_dto.current_password, user.password):
            raise ValueError("当前密码不正确")
        
        # 更新密码
        user.password = get_password_hash(change_password_dto.new_password)
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"Changed password for user: {user.email}")
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()
        
        logger.info(f"Deleted user: {user.email}")
        return True
    
    async def update_last_login(self, user_id: str, ip_address: str) -> None:
        """更新最后登录信息"""
        user = await self.get_user_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            await self.db.commit()
    
    def user_to_dto(self, user: User) -> UserInfoDto:
        """将用户实体转换为DTO"""
        return UserInfoDto(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.roles[0] if user.roles else "user",
            avatar=user.avatar,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            last_login_ip=user.last_login_ip
        )
    
    async def get_user_info(self, user_id: str) -> Optional[UserInfoDto]:
        """获取用户信息DTO"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        return self.user_to_dto(user) 