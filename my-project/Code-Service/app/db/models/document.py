from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
import enum
from .base import Base, TimestampMixin


class DocumentStatus(enum.Enum):
    """文档状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(enum.Enum):
    """文档类型枚举"""
    FILE = "file"
    DIRECTORY = "directory"
    README = "readme"
    OVERVIEW = "overview"


class Document(Base, TimestampMixin):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(String(50), primary_key=True)
    warehouse_id = Column(String(50), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    git_path = Column(String(500))
    last_update = Column(DateTime)
    
    # 关系
    warehouse = relationship("Warehouse", back_populates="documents")
    catalogs = relationship("DocumentCatalog", back_populates="document")
    file_items = relationship("DocumentFileItem", back_populates="document")


class DocumentCatalog(Base, TimestampMixin):
    """文档目录模型"""
    __tablename__ = "document_catalogs"
    
    id = Column(String(50), primary_key=True)
    document_id = Column(String(50), nullable=False)
    parent_id = Column(String(50))
    title = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(DocumentType), default=DocumentType.DIRECTORY)
    prompt = Column(Text)
    content = Column(Text)
    order_index = Column(Integer, default=0)
    
    # 关系
    document = relationship("Document", back_populates="catalogs")
    parent = relationship("DocumentCatalog", remote_side=[id])
    children = relationship("DocumentCatalog")


class DocumentFileItem(Base, TimestampMixin):
    """文档文件项模型"""
    __tablename__ = "document_file_items"
    
    id = Column(String(50), primary_key=True)
    document_id = Column(String(50), nullable=False)
    catalog_id = Column(String(50))
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_extension = Column(String(50))
    content = Column(Text)
    content_type = Column(String(100))
    
    # 关系
    document = relationship("Document", back_populates="file_items")
    catalog = relationship("DocumentCatalog") 