import uuid
import os
import zipfile
import gzip
import tarfile
import shutil
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException
from loguru import logger

from src.models.warehouse import Warehouse
from src.models.document import Document


class WarehouseUploadService:
    """仓库上传服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def download_file_from_url(self, file_url: str, organization: str, repository_name: str) -> str:
        """从URL下载文件到本地"""
        try:
            # 创建目录
            os.makedirs(f"uploads/{organization}", exist_ok=True)
            
            # 下载文件
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            
            # 保存文件
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
        user_id: str,
        file: Optional[UploadFile] = None,
        file_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """上传并且提交仓库"""
        try:
            if not organization or not repository_name:
                raise HTTPException(status_code=400, detail="组织名称和仓库名称不能为空")
            
            file_path = None
            
            if file_url:
                # 从URL下载文件
                file_path = await self.download_file_from_url(file_url, organization, repository_name)
            elif file:
                # 检查文件格式
                if not file.filename.endswith(('.zip', '.gz', '.tar', '.br')):
                    raise HTTPException(status_code=400, detail="只支持zip，gz，tar，br格式的文件")
                
                # 保存上传的文件
                os.makedirs(f"uploads/{organization}", exist_ok=True)
                file_path = f"uploads/{organization}/{file.filename}"
                
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(file.file, f)
            else:
                raise HTTPException(status_code=400, detail="没有文件上传")
            
            # 解压文件
            extract_path = await self._extract_file(file_path, organization, repository_name)
            
            # 处理解压后的目录结构
            await self._process_extracted_directory(extract_path)
            
            # 创建仓库记录
            warehouse = await self._create_warehouse_from_upload(
                organization, repository_name, extract_path, user_id
            )
            
            # 创建文档记录
            document = await self._create_document_for_warehouse(warehouse.id, user_id)
            
            return {
                "success": True,
                "warehouse_id": warehouse.id,
                "document_id": document.id,
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
        elif file_path.endswith('.gz'):
            with gzip.open(file_path, 'rb') as f_in:
                with open(extract_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif file_path.endswith('.tar'):
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
        elif file_path.endswith('.br'):
            try:
                import brotli
                with open(file_path, 'rb') as f_in:
                    with open(extract_path, 'wb') as f_out:
                        f_out.write(brotli.decompress(f_in.read()))
            except ImportError:
                raise HTTPException(status_code=400, detail="需要安装 brotli 库来支持 .br 文件")
        
        return extract_path
    
    async def _process_extracted_directory(self, extract_path: str):
        """处理解压后的目录结构"""
        if os.path.exists(extract_path) and os.path.isdir(extract_path):
            # 如果解压后目录下只有一个文件夹，那么就将这个文件夹的内容移动到上级目录
            subdirs = [d for d in os.listdir(extract_path) 
                      if os.path.isdir(os.path.join(extract_path, d))]
            
            if len(subdirs) == 1:
                subdir_path = os.path.join(extract_path, subdirs[0])
                # 移动子目录内容到上级目录
                for item in os.listdir(subdir_path):
                    src = os.path.join(subdir_path, item)
                    dst = os.path.join(extract_path, item)
                    shutil.move(src, dst)
                # 删除空的子目录
                os.rmdir(subdir_path)
    
    async def _create_warehouse_from_upload(
        self, 
        organization: str, 
        repository_name: str, 
        path: str, 
        user_id: str
    ) -> Warehouse:
        """从上传创建仓库"""
        warehouse = Warehouse(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=repository_name,
            description=f"从 {organization}/{repository_name} 上传的仓库",
            type="upload",
            organization_name=organization,
            git_path=path,
            address=f"uploads/{organization}/{repository_name}",
            branch="main",
            status="pending",
            is_public=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(warehouse)
        await self.db.commit()
        await self.db.refresh(warehouse)
        
        logger.info(f"Created warehouse from upload: {warehouse.name}")
        return warehouse
    
    async def _create_document_for_warehouse(self, warehouse_id: str, user_id: str) -> Document:
        """为仓库创建文档记录"""
        document = Document(
            id=str(uuid.uuid4()),
            warehouse_id=warehouse_id,
            user_id=user_id,
            title="仓库文档",
            content="",
            document_type="markdown",
            language="zh-CN",
            created_at=datetime.utcnow()
        )
        
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        
        logger.info(f"Created document for warehouse: {document.id}")
        return document
    
    async def submit_warehouse(self, warehouse_id: str, user_id: str) -> Dict[str, Any]:
        """提交仓库处理"""
        try:
            # 获取仓库信息
            from sqlalchemy import select
            result = await self.db.execute(
                select(Warehouse).where(Warehouse.id == warehouse_id)
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            # 更新仓库状态为处理中
            from sqlalchemy import update
            await self.db.execute(
                update(Warehouse)
                .where(Warehouse.id == warehouse_id)
                .values(status="processing")
            )
            await self.db.commit()
            
            # 这里应该触发后台任务来处理仓库
            # 暂时返回成功状态
            return {
                "success": True,
                "warehouse_id": warehouse_id,
                "message": "仓库提交成功，正在处理中"
            }
            
        except Exception as e:
            logger.error(f"提交仓库失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"提交仓库失败: {str(e)}")
    
    async def custom_submit_warehouse(
        self, 
        organization: str, 
        repository_name: str, 
        git_url: str, 
        branch: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """自定义提交仓库"""
        try:
            # 创建仓库记录
            warehouse = Warehouse(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=repository_name,
                description=f"从 {git_url} 克隆的仓库",
                type="git",
                organization_name=organization,
                address=git_url,
                branch=branch,
                status="pending",
                is_public=True,
                created_at=datetime.utcnow()
            )
            
            self.db.add(warehouse)
            await self.db.commit()
            await self.db.refresh(warehouse)
            
            # 创建文档记录
            document = await self._create_document_for_warehouse(warehouse.id, user_id)
            
            return {
                "success": True,
                "warehouse_id": warehouse.id,
                "document_id": document.id,
                "message": "仓库提交成功"
            }
            
        except Exception as e:
            logger.error(f"自定义提交仓库失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"自定义提交仓库失败: {str(e)}") 