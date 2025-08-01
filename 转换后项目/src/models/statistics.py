from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.core.database import Base


class Statistics(Base):
    """统计模型"""
    __tablename__ = "statistics"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # 统计类型
    type = Column(String, nullable=False)  # 如：page_view, api_call, etc.
    
    # 统计数据
    data = Column(Text, default="")  # JSON格式存储统计数据
    
    # 时间信息
    date = Column(String, nullable=False)  # 日期，格式：YYYY-MM-DD
    hour = Column(Integer, nullable=True)  # 小时，0-23
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "data": self.data,
            "date": self.date,
            "hour": self.hour,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        } 