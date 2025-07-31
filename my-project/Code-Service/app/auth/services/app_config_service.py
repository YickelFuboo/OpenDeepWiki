"""
应用配置管理服务

提供应用配置的CRUD和域名验证功能
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session


from app.db.models.app_config import AppConfig, AppConfigMcp
from app.db.models.warehouse import Warehouse
from app.schemas.app_config import (
    AppConfigInput, AppConfigOutput, DomainValidationRequest, DomainValidationResponse
)
from app.utils.auth import get_current_user_id


logger = logging.getLogger(__name__)


class AppConfigService:
    """应用配置管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_app_config(self, config_data: AppConfigInput, user_id: str) -> AppConfigOutput:
        """创建应用配置"""
        try:
            # 检查AppId是否已存在
            existing_app = self.db.query(AppConfig).filter(
                AppConfig.app_id == config_data.app_id
            ).first()
            
            if existing_app:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="应用ID已存在"
                )
            
            # 检查用户是否有权限访问该组织和仓库
            warehouse = self.db.query(Warehouse).filter(
                Warehouse.organization_name.ilike(config_data.organization_name),
                Warehouse.name.ilike(config_data.repository_name)
            ).first()
            
            if not warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的组织或仓库不存在"
                )
            
            # 创建应用配置
            app_config = AppConfig(
                id=self._generate_id(),
                app_id=config_data.app_id,
                name=config_data.name,
                organization_name=config_data.organization_name,
                repository_name=config_data.repository_name,
                allowed_domains_json=json.dumps(config_data.allowed_domains),
                enable_domain_validation=config_data.enable_domain_validation,
                description=config_data.description,
                prompt=config_data.prompt,
                introduction=config_data.introduction,
                model=config_data.model,
                recommended_questions_json=json.dumps(config_data.recommended_questions),
                user_id=user_id,
                is_enabled=True
            )
            
            self.db.add(app_config)
            self.db.commit()
            self.db.refresh(app_config)
            
            # 创建MCP配置
            for mcp_data in config_data.mcps:
                mcp_config = AppConfigMcp(
                    id=self._generate_id(),
                    app_config_id=app_config.id,
                    url=mcp_data.url,
                    headers_json=json.dumps(mcp_data.headers)
                )
                self.db.add(mcp_config)
            
            self.db.commit()
            
            return self._map_to_output(app_config)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建应用配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建应用配置失败: {str(e)}"
            )
    
    def get_app_configs(self, user_id: str) -> List[AppConfigOutput]:
        """获取应用配置列表"""
        try:
            app_configs = self.db.query(AppConfig).filter(
                AppConfig.user_id == user_id
            ).order_by(AppConfig.created_at.desc()).all()
            
            return [self._map_to_output(config) for config in app_configs]
            
        except Exception as e:
            logger.error(f"获取应用配置列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取应用配置列表失败: {str(e)}"
            )
    
    def get_app_config_by_app_id(self, app_id: str, user_id: str) -> AppConfigOutput:
        """根据AppId获取应用配置"""
        try:
            app_config = self.db.query(AppConfig).filter(
                AppConfig.app_id == app_id,
                AppConfig.user_id == user_id
            ).first()
            
            if not app_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="应用配置不存在"
                )
            
            return self._map_to_output(app_config)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取应用配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取应用配置失败: {str(e)}"
            )
    
    def update_app_config(self, app_id: str, config_data: AppConfigInput, user_id: str) -> AppConfigOutput:
        """更新应用配置"""
        try:
            app_config = self.db.query(AppConfig).filter(
                AppConfig.app_id == app_id,
                AppConfig.user_id == user_id
            ).first()
            
            if not app_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="应用配置不存在"
                )
            
            # 检查新的组织和仓库是否存在（如果有变更）
            if (app_config.organization_name != config_data.organization_name or
                app_config.repository_name != config_data.repository_name):
                warehouse = self.db.query(Warehouse).filter(
                    Warehouse.organization_name.ilike(config_data.organization_name),
                    Warehouse.name.ilike(config_data.repository_name)
                ).first()
                
                if not warehouse:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="指定的组织或仓库不存在"
                    )
            
            # 更新字段
            app_config.name = config_data.name
            app_config.organization_name = config_data.organization_name
            app_config.repository_name = config_data.repository_name
            app_config.allowed_domains_json = json.dumps(config_data.allowed_domains)
            app_config.enable_domain_validation = config_data.enable_domain_validation
            app_config.description = config_data.description
            app_config.prompt = config_data.prompt
            app_config.introduction = config_data.introduction
            app_config.model = config_data.model
            app_config.recommended_questions_json = json.dumps(config_data.recommended_questions)
            app_config.updated_at = datetime.utcnow()
            
            # 更新MCP配置
            # 删除旧的MCP配置
            self.db.query(AppConfigMcp).filter(
                AppConfigMcp.app_config_id == app_config.id
            ).delete()
            
            # 创建新的MCP配置
            for mcp_data in config_data.mcps:
                mcp_config = AppConfigMcp(
                    id=self._generate_id(),
                    app_config_id=app_config.id,
                    url=mcp_data.url,
                    headers_json=json.dumps(mcp_data.headers)
                )
                self.db.add(mcp_config)
            
            self.db.commit()
            self.db.refresh(app_config)
            
            return self._map_to_output(app_config)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新应用配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新应用配置失败: {str(e)}"
            )
    
    def delete_app_config(self, app_id: str, user_id: str):
        """删除应用配置"""
        try:
            app_config = self.db.query(AppConfig).filter(
                AppConfig.app_id == app_id,
                AppConfig.user_id == user_id
            ).first()
            
            if not app_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="应用配置不存在"
                )
            
            self.db.delete(app_config)
            self.db.commit()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除应用配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除应用配置失败: {str(e)}"
            )
    
    def toggle_app_config_enabled(self, app_id: str, user_id: str) -> AppConfigOutput:
        """启用/禁用应用"""
        try:
            app_config = self.db.query(AppConfig).filter(
                AppConfig.app_id == app_id,
                AppConfig.user_id == user_id
            ).first()
            
            if not app_config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="应用配置不存在"
                )
            
            app_config.is_enabled = not app_config.is_enabled
            app_config.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(app_config)
            
            return self._map_to_output(app_config)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"切换应用状态失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"切换应用状态失败: {str(e)}"
            )
    
    def validate_domain(self, request: DomainValidationRequest) -> DomainValidationResponse:
        """域名验证（公开接口，不需要登录）"""
        try:
            app_config = self.db.query(AppConfig).filter(
                AppConfig.app_id == request.app_id,
                AppConfig.is_enabled == True
            ).first()
            
            if not app_config:
                return DomainValidationResponse(
                    is_valid=False,
                    reason="应用配置不存在或已禁用"
                )
            
            # 如果未启用域名验证，直接通过
            if not app_config.enable_domain_validation:
                # 更新最后使用时间
                await self._update_last_used_time(app_config.id)
                
                return DomainValidationResponse(
                    is_valid=True,
                    app_config=self._map_to_output(app_config)
                )
            
            # 解析允许的域名列表
            allowed_domains = app_config.allowed_domains
            
            if not allowed_domains:
                return DomainValidationResponse(
                    is_valid=False,
                    reason="未配置允许的域名"
                )
            
            # 验证域名
            is_valid_domain = any(
                request.domain.lower() == domain.lower() or
                request.domain.lower().endswith("." + domain.lower())
                for domain in allowed_domains
            )
            
            if not is_valid_domain:
                return DomainValidationResponse(
                    is_valid=False,
                    reason=f"域名 {request.domain} 未被授权"
                )
            
            # 更新最后使用时间
            await self._update_last_used_time(app_config.id)
            
            return DomainValidationResponse(
                is_valid=True,
                app_config=self._map_to_output(app_config)
            )
            
        except Exception as e:
            logger.error(f"域名验证失败: {e}")
            return DomainValidationResponse(
                is_valid=False,
                reason=f"域名验证失败: {str(e)}"
            )
    
    def get_public_app_config(self, app_id: str) -> Optional[AppConfigOutput]:
        """获取应用配置（公开接口，用于第三方脚本）"""
        try:
            app_config = self.db.query(AppConfig).filter(
                AppConfig.app_id == app_id,
                AppConfig.is_enabled == True
            ).first()
            
            if not app_config:
                return None
            
            # 更新最后使用时间
            await self._update_last_used_time(app_config.id)
            
            return self._map_to_output(app_config)
            
        except Exception as e:
            logger.error(f"获取公开应用配置失败: {e}")
            return None
    
    async def _update_last_used_time(self, app_config_id: str):
        """更新最后使用时间"""
        try:
            app_config = self.db.query(AppConfig).filter(
                AppConfig.id == app_config_id
            ).first()
            
            if app_config:
                app_config.last_used_at = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            logger.error(f"更新最后使用时间失败: {e}")
    
    def _map_to_output(self, app_config: AppConfig) -> AppConfigOutput:
        """将实体映射为输出DTO"""
        return AppConfigOutput(
            app_id=app_config.app_id,
            name=app_config.name,
            is_enabled=app_config.is_enabled,
            organization_name=app_config.organization_name,
            repository_name=app_config.repository_name,
            allowed_domains=app_config.allowed_domains,
            enable_domain_validation=app_config.enable_domain_validation,
            description=app_config.description,
            prompt=app_config.prompt,
            introduction=app_config.introduction,
            model=app_config.model,
            recommended_questions=app_config.recommended_questions,
            mcps=[
                {
                    "url": mcp.url,
                    "headers": mcp.headers
                }
                for mcp in app_config.mcps
            ],
            created_at=app_config.created_at,
            updated_at=app_config.updated_at
        )
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4()) 