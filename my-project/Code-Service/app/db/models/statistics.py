from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, BigInteger
from .base import Base, TimestampMixin


class AccessRecord(Base, TimestampMixin):
    """访问记录模型"""
    __tablename__ = "access_records"
    
    id = Column(String(50), primary_key=True)
    resource_type = Column(String(50), nullable=False)  # warehouse, document, user等
    resource_id = Column(String(50), nullable=False)
    user_id = Column(String(50))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    path = Column(String(500))
    method = Column(String(10))
    status_code = Column(Integer)
    response_time = Column(BigInteger)  # 响应时间（毫秒）


class DailyStatistics(Base, TimestampMixin):
    """每日统计模型"""
    __tablename__ = "daily_statistics"
    
    id = Column(String(50), primary_key=True)
    date = Column(DateTime, nullable=False)
    total_users = Column(Integer, default=0)
    total_repositories = Column(Integer, default=0)
    total_documents = Column(Integer, default=0)
    total_views = Column(BigInteger, default=0)
    new_users = Column(Integer, default=0)
    new_repositories = Column(Integer, default=0)
    new_documents = Column(Integer, default=0)
    new_views = Column(BigInteger, default=0) 