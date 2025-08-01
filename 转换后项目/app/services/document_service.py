import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from src.models.document import Document


class DocumentService:
    """文档管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """根据ID获取文档"""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def get_document_list(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 10, 
        keyword: Optional[str] = None
    ) -> tuple[List[Document], int]:
        """获取用户文档列表"""
        query = select(Document).where(Document.user_id == user_id)
        
        # 如果有关键词，则按标题或内容搜索
        if keyword:
            query = query.where(
                Document.title.contains(keyword) | 
                Document.content.contains(keyword)
            )
        
        # 按创建时间降序排序
        query = query.order_by(Document.created_at.desc())
        
        # 计算总数
        count_result = await self.db.execute(
            select(Document).where(query.whereclause)
        )
        total = len(count_result.scalars().all())
        
        # 获取分页数据
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        return documents, total
    
    async def create_document(
        self, 
        user_id: str, 
        title: str, 
        content: str = "", 
        repository_id: str = None,
        document_type: str = "markdown",
        language: str = "zh-CN",
        tags: str = "",
        is_public: bool = False,
        is_featured: bool = False
    ) -> Document:
        """创建文档"""
        document = Document(
            id=str(uuid.uuid4()),
            user_id=user_id,
            repository_id=repository_id,
            title=title,
            content=content,
            document_type=document_type,
            language=language,
            tags=tags,
            is_public=is_public,
            is_featured=is_featured,
            created_at=datetime.utcnow()
        )
        
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        
        logger.info(f"Created document: {document.title} by user {user_id}")
        return document
    
    async def update_document(
        self, 
        document_id: str, 
        user_id: str, 
        title: str = None,
        content: str = None,
        tags: str = None,
        is_public: bool = None,
        is_featured: bool = None
    ) -> Optional[Document]:
        """更新文档"""
        document = await self.get_document_by_id(document_id)
        if not document or document.user_id != user_id:
            return None
        
        # 更新文档信息
        if title is not None:
            document.title = title
        if content is not None:
            document.content = content
        if tags is not None:
            document.tags = tags
        if is_public is not None:
            document.is_public = is_public
        if is_featured is not None:
            document.is_featured = is_featured
        
        document.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(document)
        
        logger.info(f"Updated document: {document.title}")
        return document
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """删除文档"""
        document = await self.get_document_by_id(document_id)
        if not document or document.user_id != user_id:
            return False
        
        await self.db.execute(delete(Document).where(Document.id == document_id))
        await self.db.commit()
        
        logger.info(f"Deleted document: {document.title}")
        return True
    
    async def increment_view_count(self, document_id: str) -> None:
        """增加文档查看次数"""
        document = await self.get_document_by_id(document_id)
        if document:
            current_count = int(document.view_count or "0")
            document.view_count = str(current_count + 1)
            await self.db.commit() 