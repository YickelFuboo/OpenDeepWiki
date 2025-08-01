from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CreateDatasetInput(BaseModel):
    """创建数据集输入模型"""
    warehouse_id: str = Field(..., description="仓库ID")
    name: str = Field(..., description="数据集名称")
    endpoint: str = Field(..., description="API接口地址")
    api_key: str = Field(..., description="API密钥")
    prompt: str = Field("", description="提示词")
    model: str = Field("", description="模型名称")


class UpdateDatasetInput(BaseModel):
    """更新数据集输入模型"""
    dataset_id: str = Field(..., description="数据集ID")
    name: str = Field(..., description="数据集名称")
    endpoint: str = Field(..., description="API接口地址")
    api_key: str = Field(..., description="API密钥")
    prompt: str = Field("", description="提示词")


class CreateTaskInput(BaseModel):
    """创建微调任务输入模型"""
    training_dataset_id: str = Field(..., description="训练数据集ID")
    document_catalog_id: str = Field(..., description="文档目录ID")
    name: str = Field(..., description="微调任务名称")
    description: str = Field("", description="微调任务描述")


class StartTaskInput(BaseModel):
    """启动微调任务输入模型"""
    task_id: str = Field(..., description="任务ID")
    prompt: Optional[str] = Field(None, description="自定义提示词")


class TrainingDatasetResponse(BaseModel):
    """训练数据集响应模型"""
    id: str
    warehouse_id: str
    user_id: str
    name: str
    endpoint: str
    model: str
    api_key: str
    prompt: str
    status: str
    created_at: datetime
    updated_at: datetime


class FineTuningTaskResponse(BaseModel):
    """微调任务响应模型"""
    id: str
    warehouse_id: str
    training_dataset_id: str
    document_catalog_id: str
    user_id: str
    name: str
    description: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    dataset: Optional[str]
    original_dataset: Optional[str]
    error: Optional[str]
    created_at: datetime 