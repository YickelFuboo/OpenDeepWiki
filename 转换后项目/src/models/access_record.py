from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, DateTime
from sqlalchemy.sql import func

from src.models.base import Base


class AccessRecord(Base):
    """访问记录模型"""
    __tablename__ = "access_records"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # 访问的资源类型（Repository、Document、User等）
    resource_type = Column(String(50), nullable=False, default="")
    
    # 访问的资源ID
    resource_id = Column(String(36), nullable=False, default="")
    
    # 访问用户ID（可选，匿名访问时为空）
    user_id = Column(String(36), nullable=True)
    
    # 访问者IP地址
    ip_address = Column(String(45), nullable=False, default="")
    
    # 用户代理信息
    user_agent = Column(String(500), nullable=False, default="")
    
    # 访问路径
    path = Column(String(500), nullable=False, default="")
    
    # 访问方法（GET、POST等）
    method = Column(String(10), nullable=False, default="")
    
    # 响应状态码
    status_code = Column(Integer, nullable=False, default=200)
    
    # 响应时间（毫秒）
    response_time = Column(BigInteger, nullable=False, default=0)
    
    # 请求时间
    request_time = Column(DateTime, nullable=False, default=func.now())
    
    # 响应时间
    response_time_stamp = Column(DateTime, nullable=False, default=func.now())
    
    # 创建时间
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 更新时间
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now()) 