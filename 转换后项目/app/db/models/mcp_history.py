from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime

from src.models.base import BaseEntity


class MCPHistory(BaseEntity):
    """MCP历史记录模型"""
    __tablename__ = "mcp_histories"

    warehouse_id = Column(String(36), nullable=False, comment="仓库ID")
    question = Column(Text, nullable=False, comment="问题")
    answer = Column(Text, nullable=False, comment="回答")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "warehouse_id": self.warehouse_id,
            "question": self.question,
            "answer": self.answer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 