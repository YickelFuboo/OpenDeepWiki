from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from src.models.base import BaseEntity


class DocumentCatalog(BaseEntity):
    """文档目录模型"""
    __tablename__ = "document_catalogs"

    name = Column(String(200), nullable=False, comment="目录名称")
    url = Column(String(500), nullable=False, comment="目录URL")
    description = Column(Text, nullable=True, comment="目录描述")
    parent_id = Column(String(36), nullable=True, comment="目录父级ID")
    order = Column(Integer, default=0, comment="当前目录排序")
    document_id = Column(String(36), nullable=False, comment="文档ID")
    warehouse_id = Column(String(36), nullable=False, comment="仓库ID")
    is_completed = Column(Boolean, default=False, comment="是否处理完成")
    prompt = Column(Text, nullable=True, comment="提示词")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    deleted_time = Column(DateTime, nullable=True, comment="删除时间")

    # 关系
    file_items = relationship("DocumentFileItem", back_populates="catalog", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "parent_id": self.parent_id,
            "order": self.order,
            "document_id": self.document_id,
            "warehouse_id": self.warehouse_id,
            "is_completed": self.is_completed,
            "prompt": self.prompt,
            "is_deleted": self.is_deleted,
            "deleted_time": self.deleted_time.isoformat() if self.deleted_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DocumentFileItem(BaseEntity):
    """文档文件项模型"""
    __tablename__ = "document_file_items"

    title = Column(String(200), nullable=False, comment="标题")
    description = Column(Text, nullable=True, comment="描述")
    content = Column(Text, nullable=True, comment="文档实际内容")
    comment_count = Column(Integer, default=0, comment="评论数量")
    size = Column(Integer, default=0, comment="文档大小")
    document_catalog_id = Column(String(36), nullable=False, comment="绑定的目录ID")
    request_token = Column(Integer, default=0, comment="请求token消耗")
    response_token = Column(Integer, default=0, comment="响应token")
    is_embedded = Column(Boolean, default=False, comment="是否嵌入完成")
    metadata = Column(JSON, default=dict, comment="源数据")
    extra = Column(JSON, default=dict, comment="扩展数据")

    # 关系
    catalog = relationship("DocumentCatalog", back_populates="file_items")
    sources = relationship("DocumentFileItemSource", back_populates="file_item", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "comment_count": self.comment_count,
            "size": self.size,
            "document_catalog_id": self.document_catalog_id,
            "request_token": self.request_token,
            "response_token": self.response_token,
            "is_embedded": self.is_embedded,
            "metadata": self.metadata,
            "extra": self.extra,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DocumentFileItemSource(BaseEntity):
    """文档文件项源模型"""
    __tablename__ = "document_file_item_sources"

    file_item_id = Column(String(36), nullable=False, comment="文件项ID")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    line_start = Column(Integer, nullable=True, comment="开始行号")
    line_end = Column(Integer, nullable=True, comment="结束行号")
    content = Column(Text, nullable=True, comment="源内容")

    # 关系
    file_item = relationship("DocumentFileItem", back_populates="sources")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "file_item_id": self.file_item_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 