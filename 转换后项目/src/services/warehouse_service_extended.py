import uuid
import os
import zipfile
import shutil
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from fastapi import UploadFile, HTTPException
from loguru import logger

from src.models.warehouse import Warehouse
from src.models.document_commit_record import DocumentCommitRecord
from src.infrastructure.permission_middleware import PermissionMiddleware


class WarehouseServiceExtended:
    """扩展的知识仓库管理服务 - 包含复杂功能"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.permission_middleware = PermissionMiddleware(db)
    
    async def check_warehouse_access(self, warehouse_id: str, user_id: Optional[str] = None) -> bool:
        """检查用户对指定仓库的访问权限"""
        return await self.permission_middleware.check_warehouse_access(warehouse_id, user_id)
    
    async def check_warehouse_manage_access(self, warehouse_id: str, user_id: Optional[str] = None) -> bool:
        """检查用户对指定仓库的管理权限"""
        return await self.permission_middleware.check_warehouse_manage_access(warehouse_id, user_id)
    
    async def update_warehouse_status(self, warehouse_id: str, user_id: str) -> bool:
        """更新仓库状态"""
        if not await self.check_warehouse_manage_access(warehouse_id, user_id):
            raise HTTPException(status_code=403, detail="您没有权限管理此仓库")
        
        await self.db.execute(
            update(Warehouse)
            .where(Warehouse.id == warehouse_id)
            .values(status="pending")
        )
        await self.db.commit()
        
        logger.info(f"Updated warehouse status: {warehouse_id}")
        return True
    
    async def get_last_warehouse(self, address: str) -> Dict[str, Any]:
        """查询上次提交的仓库"""
        address = address.strip().rstrip('/').lower()
        
        if not address.endswith(".git"):
            address += ".git"
        
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.address == address)
        )
        warehouse = result.scalar_one_or_none()
        
        if not warehouse:
            raise HTTPException(status_code=404, detail="仓库不存在")
        
        return {
            "name": warehouse.name,
            "address": warehouse.address,
            "description": warehouse.description,
            "version": warehouse.version,
            "status": warehouse.status,
            "error": warehouse.error
        }
    
    async def get_change_log(self, owner: str, name: str) -> Optional[DocumentCommitRecord]:
        """获取变更日志"""
        owner = owner.strip().lower()
        name = name.strip().lower()
        
        result = await self.db.execute(
            select(Warehouse).where(
                Warehouse.name == name,
                Warehouse.organization_name == owner,
                Warehouse.status.in_(["completed", "processing"])
            )
        )
        warehouse = result.scalar_one_or_none()
        
        if not warehouse:
            raise HTTPException(
                status_code=404, 
                detail=f"仓库不存在，请检查仓库名称和组织名称: {owner} {name}"
            )
        
        commit_result = await self.db.execute(
            select(DocumentCommitRecord).where(DocumentCommitRecord.warehouse_id == warehouse.id)
        )
        commits = commit_result.scalars().all()
        
        change_log = []
        for commit in commits:
            change_log.append(f"## {commit.last_update} {commit.title}")
            change_log.append(f" {commit.commit_message}")
        
        return DocumentCommitRecord(
            commit_id="",
            commit_message="\n".join(change_log),
            created_at=datetime.utcnow()
        )
    
    async def download_file_from_url(self, file_url: str, organization: str, repository_name: str) -> str:
        """从URL下载文件到本地"""
        try:
            os.makedirs(f"uploads/{organization}", exist_ok=True)
            
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            
            file_path = f"uploads/{organization}/{repository_name}.zip"
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return file_path
            
        except Exception as e:
            logger.error(f"下载文件失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"下载文件失败: {str(e)}")
    
    async def upload_and_submit_warehouse(
        self,
        organization: str,
        repository_name: str,
        file: Optional[UploadFile] = None,
        file_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """上传并且提交仓库"""
        try:
            if not organization or not repository_name:
                raise HTTPException(status_code=400, detail="组织名称和仓库名称不能为空")
            
            file_path = None
            
            if file_url:
                file_path = await self.download_file_from_url(file_url, organization, repository_name)
            elif file:
                if not file.filename.endswith(('.zip', '.gz', '.tar', '.br')):
                    raise HTTPException(status_code=400, detail="只支持zip，gz，tar，br格式的文件")
                
                os.makedirs(f"uploads/{organization}", exist_ok=True)
                file_path = f"uploads/{organization}/{file.filename}"
                
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(file.file, f)
            else:
                raise HTTPException(status_code=400, detail="没有文件上传")
            
            extract_path = await self._extract_file(file_path, organization, repository_name)
            await self._process_extracted_directory(extract_path)
            
            warehouse = await self._create_warehouse_from_upload(
                organization, repository_name, extract_path
            )
            
            return {
                "success": True,
                "warehouse_id": warehouse.id,
                "message": "仓库上传成功"
            }
            
        except Exception as e:
            logger.error(f"上传仓库失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"上传仓库失败: {str(e)}")
    
    async def _extract_file(self, file_path: str, organization: str, repository_name: str) -> str:
        """解压文件"""
        extract_path = f"uploads/{organization}/{repository_name}"
        
        if file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        else:
            # 其他格式的处理可以后续添加
            raise HTTPException(status_code=400, detail="暂只支持zip格式")
        
        return extract_path
    
    async def _process_extracted_directory(self, extract_path: str):
        """处理解压后的目录结构"""
        if os.path.exists(extract_path) and os.path.isdir(extract_path):
            subdirs = [d for d in os.listdir(extract_path) 
                      if os.path.isdir(os.path.join(extract_path, d))]
            
            if len(subdirs) == 1:
                subdir_path = os.path.join(extract_path, subdirs[0])
                for item in os.listdir(subdir_path):
                    src = os.path.join(subdir_path, item)
                    dst = os.path.join(extract_path, item)
                    shutil.move(src, dst)
                os.rmdir(subdir_path)
    
    async def _create_warehouse_from_upload(self, organization: str, repository_name: str, path: str) -> Warehouse:
        """从上传创建仓库"""
        warehouse = Warehouse(
            id=str(uuid.uuid4()),
            user_id="system",
            name=repository_name,
            description=f"从 {organization}/{repository_name} 上传的仓库",
            type="upload",
            organization_name=organization,
            git_path=path,
            is_public=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(warehouse)
        await self.db.commit()
        await self.db.refresh(warehouse)
        
        return warehouse
    
    async def get_file_content(self, warehouse_id: str, path: str) -> str:
        """获取指定仓库代码文件"""
        try:
            result = await self.db.execute(
                select(Warehouse).where(Warehouse.id == warehouse_id)
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            file_path = os.path.join(warehouse.git_path or "", path)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="文件不存在")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            logger.error(f"获取文件内容失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文件内容失败: {str(e)}")
    
    async def export_markdown_zip(self, warehouse_id: str) -> bytes:
        """导出Markdown压缩包"""
        try:
            result = await self.db.execute(
                select(Warehouse).where(Warehouse.id == warehouse_id)
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                readme_content = f"# {warehouse.name}\n\n{warehouse.description or ''}"
                zip_file.writestr("README.md", readme_content)
            
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"导出Markdown压缩包失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"导出Markdown压缩包失败: {str(e)}") 