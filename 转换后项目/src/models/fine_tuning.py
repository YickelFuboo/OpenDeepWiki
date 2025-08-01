from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import BaseEntity


class TrainingDatasetStatus(str, Enum):
    """训练数据集状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class FineTuningTaskStatus(str, Enum):
    """微调任务状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingDataset(BaseEntity):
    """训练数据集"""
    __tablename__ = "training_datasets"
    
    id = Column(String(50), primary_key=True)
    warehouse_id = Column(String(50), nullable=False)
    user_id = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    endpoint = Column(String(500), nullable=False)
    model = Column(String(100), nullable=False)
    api_key = Column(String(500), nullable=False)
    prompt = Column(Text, nullable=True)
    status = Column(String(50), default=TrainingDatasetStatus.NOT_STARTED)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    warehouse = relationship("Warehouse", back_populates="training_datasets")
    fine_tuning_tasks = relationship("FineTuningTask", back_populates="training_dataset")


class FineTuningTask(BaseEntity):
    """微调任务"""
    __tablename__ = "fine_tuning_tasks"
    
    id = Column(String(50), primary_key=True)
    warehouse_id = Column(String(50), nullable=False)
    training_dataset_id = Column(String(50), ForeignKey("training_datasets.id"), nullable=False)
    document_catalog_id = Column(String(50), ForeignKey("document_catalogs.id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default=FineTuningTaskStatus.NOT_STARTED)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    dataset = Column(Text, nullable=True)  # 生成的训练数据
    original_dataset = Column(Text, nullable=True)  # 原始数据
    error = Column(Text, nullable=True)  # 错误信息
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    warehouse = relationship("Warehouse", back_populates="fine_tuning_tasks")
    training_dataset = relationship("TrainingDataset", back_populates="fine_tuning_tasks")
    document_catalog = relationship("DocumentCatalog", back_populates="fine_tuning_tasks") 