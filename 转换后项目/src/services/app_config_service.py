from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from loguru import logger
from datetime import datetime

from src.models.app_config import AppConfig, AppConfigMcp
from src.models.warehouse import Warehouse
from src.dto.app_config_dto import (
    AppConfigInput, AppConfigOutput, AppConfigMcpDto,
    DomainValidationRequest, DomainValidationResponse
)


class AppConfigService:
    """应用配置管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_app_config(self, user_id: str, app_config_data: AppConfigInput) -> AppConfigOutput:
        """创建应用配置"""
        try:
            # 检查AppId是否已存在
            existing_app = await self.db.execute(
                select(AppConfig).where(AppConfig.app_id == app_config_data.app_id)
            )
            if existing_app.scalar_one_or_none():
                raise ValueError("应用ID已存在")
            
            # 检查用户是否有权限访问该组织和仓库
            warehouse = await self.db.execute(
                select(Warehouse).where(
                    and_(
                        Warehouse.organization_name.ilike(app_config_data.organization_name),
                        Warehouse.name.ilike(app_config_data.repository_name)
                    )
                )
            )
            warehouse = warehouse.scalar_one_or_none()
            
            if not warehouse:
                raise ValueError("指定的组织或仓库不存在")
            
            # 创建应用配置
            app_config = AppConfig(
                app_id=app_config_data.app_id,
                name=app_config_data.name,
                organization_name=app_config_data.organization_name,
                repository_name=app_config_data.repository_name,
                enable_domain_validation=app_config_data.enable_domain_validation,
                description=app_config_data.description,
                prompt=app_config_data.prompt,
                introduction=app_config_data.introduction,
                model=app_config_data.model,
                user_id=user_id,
                is_enabled=True
            )
            
            # 设置允许的域名
            app_config.set_allowed_domains(app_config_data.allowed_domains)
            
            # 设置推荐提问
            if app_config_data.recommended_questions:
                app_config.set_recommended_questions(app_config_data.recommended_questions)
            
            self.db.add(app_config)
            await self.db.commit()
            await self.db.refresh(app_config)
            
            # 创建MCP配置
            for mcp_data in app_config_data.mcps:
                mcp = AppConfigMcp(
                    app_config_id=app_config.id,
                    url=mcp_data.url
                )
                mcp.set_headers(mcp_data.headers)
                self.db.add(mcp)
            
            await self.db.commit()
            
            return await self._map_to_output(app_config)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建应用配置失败: {e}")
            raise
    
    async def get_app_configs(self, user_id: str) -> List[AppConfigOutput]:
        """获取应用配置列表"""
        try:
            result = await self.db.execute(
                select(AppConfig)
                .options(selectinload(AppConfig.mcps))
                .where(AppConfig.user_id == user_id)
                .order_by(AppConfig.created_at.desc())
            )
            app_configs = result.scalars().all()
            
            outputs = []
            for app_config in app_configs:
                output = await self._map_to_output(app_config)
                outputs.append(output)
            
            return outputs
            
        except Exception as e:
            logger.error(f"获取应用配置列表失败: {e}")
            raise
    
    async def get_app_config_by_id(self, user_id: str, app_id: str) -> Optional[AppConfigOutput]:
        """根据AppId获取应用配置"""
        try:
            result = await self.db.execute(
                select(AppConfig)
                .options(selectinload(AppConfig.mcps))
                .where(
                    and_(
                        AppConfig.app_id == app_id,
                        AppConfig.user_id == user_id
                    )
                )
            )
            app_config = result.scalar_one_or_none()
            
            if not app_config:
                return None
            
            return await self._map_to_output(app_config)
            
        except Exception as e:
            logger.error(f"获取应用配置失败: {e}")
            raise
    
    async def update_app_config(self, user_id: str, app_id: str, 
                               app_config_data: AppConfigInput) -> Optional[AppConfigOutput]:
        """更新应用配置"""
        try:
            # 获取现有配置
            result = await self.db.execute(
                select(AppConfig)
                .options(selectinload(AppConfig.mcps))
                .where(
                    and_(
                        AppConfig.app_id == app_id,
                        AppConfig.user_id == user_id
                    )
                )
            )
            app_config = result.scalar_one_or_none()
            
            if not app_config:
                return None
            
            # 检查组织仓库是否存在
            warehouse = await self.db.execute(
                select(Warehouse).where(
                    and_(
                        Warehouse.organization_name.ilike(app_config_data.organization_name),
                        Warehouse.name.ilike(app_config_data.repository_name)
                    )
                )
            )
            warehouse = warehouse.scalar_one_or_none()
            
            if not warehouse:
                raise ValueError("指定的组织或仓库不存在")
            
            # 更新配置
            app_config.name = app_config_data.name
            app_config.organization_name = app_config_data.organization_name
            app_config.repository_name = app_config_data.repository_name
            app_config.enable_domain_validation = app_config_data.enable_domain_validation
            app_config.description = app_config_data.description
            app_config.prompt = app_config_data.prompt
            app_config.introduction = app_config_data.introduction
            app_config.model = app_config_data.model
            
            # 更新允许的域名
            app_config.set_allowed_domains(app_config_data.allowed_domains)
            
            # 更新推荐提问
            if app_config_data.recommended_questions:
                app_config.set_recommended_questions(app_config_data.recommended_questions)
            
            # 删除现有MCP配置
            for mcp in app_config.mcps:
                await self.db.delete(mcp)
            
            # 创建新的MCP配置
            for mcp_data in app_config_data.mcps:
                mcp = AppConfigMcp(
                    app_config_id=app_config.id,
                    url=mcp_data.url
                )
                mcp.set_headers(mcp_data.headers)
                self.db.add(mcp)
            
            await self.db.commit()
            
            return await self._map_to_output(app_config)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新应用配置失败: {e}")
            raise
    
    async def delete_app_config(self, user_id: str, app_id: str) -> bool:
        """删除应用配置"""
        try:
            result = await self.db.execute(
                select(AppConfig).where(
                    and_(
                        AppConfig.app_id == app_id,
                        AppConfig.user_id == user_id
                    )
                )
            )
            app_config = result.scalar_one_or_none()
            
            if not app_config:
                return False
            
            await self.db.delete(app_config)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除应用配置失败: {e}")
            raise
    
    async def toggle_app_config_enabled(self, user_id: str, app_id: str) -> Optional[AppConfigOutput]:
        """切换应用配置启用状态"""
        try:
            result = await self.db.execute(
                select(AppConfig).where(
                    and_(
                        AppConfig.app_id == app_id,
                        AppConfig.user_id == user_id
                    )
                )
            )
            app_config = result.scalar_one_or_none()
            
            if not app_config:
                return None
            
            app_config.is_enabled = not app_config.is_enabled
            await self.db.commit()
            
            return await self._map_to_output(app_config)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"切换应用配置状态失败: {e}")
            raise
    
    async def validate_domain(self, request: DomainValidationRequest) -> DomainValidationResponse:
        """验证域名"""
        try:
            # 获取应用配置
            result = await self.db.execute(
                select(AppConfig).where(AppConfig.app_id == request.app_id)
            )
            app_config = result.scalar_one_or_none()
            
            if not app_config:
                return DomainValidationResponse(
                    is_valid=False,
                    reason="应用配置不存在"
                )
            
            if not app_config.is_enabled:
                return DomainValidationResponse(
                    is_valid=False,
                    reason="应用配置已禁用"
                )
            
            # 检查域名验证
            if app_config.enable_domain_validation:
                allowed_domains = app_config.get_allowed_domains()
                if not allowed_domains:
                    return DomainValidationResponse(
                        is_valid=False,
                        reason="未配置允许的域名"
                    )
                
                if request.domain not in allowed_domains:
                    return DomainValidationResponse(
                        is_valid=False,
                        reason="域名不在允许列表中"
                    )
            
            # 更新最后使用时间
            app_config.last_used_at = datetime.utcnow()
            await self.db.commit()
            
            return DomainValidationResponse(
                is_valid=True,
                reason="验证通过",
                app_config=await self._map_to_output(app_config)
            )
            
        except Exception as e:
            logger.error(f"验证域名失败: {e}")
            return DomainValidationResponse(
                is_valid=False,
                reason=f"验证失败: {str(e)}"
            )
    
    async def get_public_config(self, app_id: str) -> Optional[AppConfigOutput]:
        """获取公开的应用配置"""
        try:
            result = await self.db.execute(
                select(AppConfig)
                .options(selectinload(AppConfig.mcps))
                .where(
                    and_(
                        AppConfig.app_id == app_id,
                        AppConfig.is_enabled == True
                    )
                )
            )
            app_config = result.scalar_one_or_none()
            
            if not app_config:
                return None
            
            return await self._map_to_output(app_config)
            
        except Exception as e:
            logger.error(f"获取公开应用配置失败: {e}")
            raise
    
    async def _map_to_output(self, app_config: AppConfig) -> AppConfigOutput:
        """映射到输出DTO"""
        mcps = []
        for mcp in app_config.mcps:
            mcps.append(AppConfigMcpDto(
                url=mcp.url,
                headers=mcp.get_headers()
            ))
        
        return AppConfigOutput(
            app_id=app_config.app_id,
            name=app_config.name,
            is_enabled=app_config.is_enabled,
            organization_name=app_config.organization_name,
            repository_name=app_config.repository_name,
            allowed_domains=app_config.get_allowed_domains(),
            enable_domain_validation=app_config.enable_domain_validation,
            description=app_config.description,
            created_at=app_config.created_at,
            updated_at=app_config.updated_at,
            prompt=app_config.prompt,
            introduction=app_config.introduction,
            model=app_config.model,
            recommended_questions=app_config.get_recommended_questions(),
            mcps=mcps
        ) 