import re
import json
import asyncio
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from loguru import logger
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from semantic_kernel import Kernel
from semantic_kernel.connectors.openai import OpenAIPromptExecutionSettings

from src.models.fine_tuning import TrainingDataset, FineTuningTask, TrainingDatasetStatus, FineTuningTaskStatus
from src.models.warehouse import Warehouse
from src.models.document import Document
from src.models.document_catalog import DocumentCatalog, DocumentFileItem
from src.services.kernel_factory import KernelFactory
from src.infrastructure.documents_helper import DocumentsHelper
from src.infrastructure.user_context import UserContext
from src.core.config import settings


class FineTuningService:
    """微调服务"""
    
    def __init__(self, db: AsyncSession, user_context: UserContext):
        self.db = db
        self.user_context = user_context
    
    async def create_dataset(self, warehouse_id: str, name: str, endpoint: str, 
                           api_key: str, prompt: str, model: str) -> TrainingDataset:
        """创建训练数据集"""
        try:
            # 检查仓库是否存在
            warehouse_result = await self.db.execute(
                select(Warehouse).where(Warehouse.id == warehouse_id)
            )
            warehouse = warehouse_result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="仓库不存在"
                )
            
            # 创建数据集
            dataset = TrainingDataset(
                id=self._generate_id(),
                warehouse_id=warehouse_id,
                user_id=self.user_context.current_user_id,
                name=name,
                endpoint=endpoint,
                model=model,
                api_key=api_key,
                prompt=prompt,
                status=TrainingDatasetStatus.NOT_STARTED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.db.add(dataset)
            await self.db.commit()
            await self.db.refresh(dataset)
            
            logger.info(f"创建训练数据集成功: {dataset.id}")
            return dataset
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建训练数据集失败: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建训练数据集失败: {str(e)}"
            )
    
    async def get_datasets(self, warehouse_id: Optional[str] = None) -> List[TrainingDataset]:
        """获取训练数据集列表"""
        try:
            query = select(TrainingDataset).where(
                TrainingDataset.user_id == self.user_context.current_user_id
            )
            
            if warehouse_id:
                query = query.where(TrainingDataset.warehouse_id == warehouse_id)
            
            result = await self.db.execute(query)
            datasets = result.scalars().all()
            
            return datasets
            
        except Exception as e:
            logger.error(f"获取训练数据集列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取训练数据集列表失败: {str(e)}"
            )
    
    async def get_dataset(self, dataset_id: str) -> TrainingDataset:
        """获取训练数据集详情"""
        try:
            result = await self.db.execute(
                select(TrainingDataset).where(
                    TrainingDataset.id == dataset_id,
                    TrainingDataset.user_id == self.user_context.current_user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="数据集不存在"
                )
            
            return dataset
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取训练数据集详情失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取训练数据集详情失败: {str(e)}"
            )
    
    async def update_dataset(self, dataset_id: str, name: str, endpoint: str, 
                           api_key: str, prompt: str) -> TrainingDataset:
        """更新训练数据集"""
        try:
            result = await self.db.execute(
                select(TrainingDataset).where(
                    TrainingDataset.id == dataset_id,
                    TrainingDataset.user_id == self.user_context.current_user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="数据集不存在"
                )
            
            # 更新数据集
            dataset.name = name
            dataset.endpoint = endpoint
            dataset.api_key = api_key
            dataset.prompt = prompt
            dataset.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(dataset)
            
            logger.info(f"更新训练数据集成功: {dataset_id}")
            return dataset
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新训练数据集失败: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新训练数据集失败: {str(e)}"
            )
    
    async def delete_dataset(self, dataset_id: str):
        """删除训练数据集"""
        try:
            result = await self.db.execute(
                select(TrainingDataset).where(
                    TrainingDataset.id == dataset_id,
                    TrainingDataset.user_id == self.user_context.current_user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="数据集不存在"
                )
            
            # 删除相关的微调任务
            await self.db.execute(
                update(FineTuningTask)
                .where(
                    FineTuningTask.training_dataset_id == dataset_id,
                    FineTuningTask.user_id == self.user_context.current_user_id
                )
                .values(status=FineTuningTaskStatus.CANCELLED)
            )
            
            # 删除数据集
            await self.db.execute(
                update(TrainingDataset)
                .where(TrainingDataset.id == dataset_id)
                .values(status=TrainingDatasetStatus.FAILED)
            )
            
            await self.db.commit()
            
            logger.info(f"删除训练数据集成功: {dataset_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除训练数据集失败: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除训练数据集失败: {str(e)}"
            )
    
    async def create_task(self, training_dataset_id: str, document_catalog_id: str,
                         name: str, description: str) -> FineTuningTask:
        """创建微调任务"""
        try:
            # 检查数据集是否存在
            dataset_result = await self.db.execute(
                select(TrainingDataset).where(
                    TrainingDataset.id == training_dataset_id,
                    TrainingDataset.user_id == self.user_context.current_user_id
                )
            )
            dataset = dataset_result.scalar_one_or_none()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="数据集不存在"
                )
            
            # 创建任务
            task = FineTuningTask(
                id=self._generate_id(),
                warehouse_id=dataset.warehouse_id,
                training_dataset_id=training_dataset_id,
                document_catalog_id=document_catalog_id,
                name=name,
                user_id=self.user_context.current_user_id,
                description=description,
                status=FineTuningTaskStatus.NOT_STARTED,
                created_at=datetime.now()
            )
            
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)
            
            logger.info(f"创建微调任务成功: {task.id}")
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建微调任务失败: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建微调任务失败: {str(e)}"
            )
    
    async def get_tasks(self, warehouse_id: str) -> List[FineTuningTask]:
        """获取微调任务列表"""
        try:
            result = await self.db.execute(
                select(FineTuningTask).where(
                    FineTuningTask.warehouse_id == warehouse_id,
                    FineTuningTask.user_id == self.user_context.current_user_id
                )
            )
            tasks = result.scalars().all()
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取微调任务列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取微调任务列表失败: {str(e)}"
            )
    
    async def get_task(self, task_id: str) -> FineTuningTask:
        """获取微调任务详情"""
        try:
            result = await self.db.execute(
                select(FineTuningTask).where(
                    FineTuningTask.id == task_id,
                    FineTuningTask.user_id == self.user_context.current_user_id
                )
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="任务不存在"
                )
            
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取微调任务详情失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取微调任务详情失败: {str(e)}"
            )
    
    async def start_task(self, task_id: str, custom_prompt: Optional[str] = None) -> StreamingResponse:
        """启动微调任务"""
        try:
            # 获取任务
            result = await self.db.execute(
                select(FineTuningTask).where(
                    FineTuningTask.id == task_id,
                    FineTuningTask.user_id == self.user_context.current_user_id
                )
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="任务不存在"
                )
            
            if task.status == FineTuningTaskStatus.IN_PROGRESS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务已在进行中，请勿重复启动"
                )
            
            # 获取数据集
            dataset_result = await self.db.execute(
                select(TrainingDataset).where(TrainingDataset.id == task.training_dataset_id)
            )
            dataset = dataset_result.scalar_one_or_none()
            
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="数据集不存在"
                )
            
            # 获取文档内容
            file_item_result = await self.db.execute(
                select(DocumentFileItem).where(
                    DocumentFileItem.document_catalog_id == task.document_catalog_id
                )
            )
            file_item = file_item_result.scalar_one_or_none()
            
            if not file_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="当前微调任务的文档内容不存在，请先生成文档内容"
                )
            
            # 获取仓库信息
            warehouse_result = await self.db.execute(
                select(Warehouse).where(Warehouse.id == dataset.warehouse_id)
            )
            warehouse = warehouse_result.scalar_one_or_none()
            
            # 更新任务状态
            task.status = FineTuningTaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            await self.db.commit()
            
            # 创建流式响应
            return StreamingResponse(
                self._stream_training_process(task, dataset, file_item, warehouse, custom_prompt),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"启动微调任务失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"启动微调任务失败: {str(e)}"
            )
    
    async def _stream_training_process(self, task: FineTuningTask, dataset: TrainingDataset,
                                     file_item: DocumentFileItem, warehouse: Warehouse,
                                     custom_prompt: Optional[str] = None):
        """流式训练过程"""
        try:
            # 配置OpenAI客户端
            kernel = KernelFactory.get_kernel(
                dataset.endpoint,
                dataset.api_key,
                "",  # path
                dataset.model,
                False
            )
            
            # 构建提示词
            prompt = custom_prompt or dataset.prompt
            prompt = prompt.replace("{{markdown_content}}", file_item.content)
            
            # 在prompt的头部增加<catalogue>标签
            if warehouse and warehouse.optimized_directory_structure:
                prompt += f"\n<catalogue>\n{warehouse.optimized_directory_structure}\n</catalogue>"
            
            # 配置执行设置
            execution_settings = OpenAIPromptExecutionSettings(
                max_tokens=self._get_max_tokens(dataset.model),
                temperature=0.3
            )
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'content': '训练开始'})}\n\n"
            
            # 执行训练
            response = await kernel.invoke(prompt, execution_settings=execution_settings)
            content = str(response)
            
            # 发送进度事件
            yield f"data: {json.dumps({'type': 'progress', 'content': content})}\n\n"
            
            # 提取训练数据
            dataset_content = self._extract_training_data(content)
            
            # 更新任务状态
            task.status = FineTuningTaskStatus.COMPLETED
            task.dataset = dataset_content
            task.original_dataset = content
            task.completed_at = datetime.now()
            
            # 更新数据集状态
            dataset.status = TrainingDatasetStatus.COMPLETED
            dataset.updated_at = datetime.now()
            
            await self.db.commit()
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete', 'content': '训练已完成'})}\n\n"
            
        except Exception as e:
            # 处理错误情况
            task.status = FineTuningTaskStatus.FAILED
            task.error = str(e)
            await self.db.commit()
            
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        
        finally:
            yield "data: [done]\n\n"
    
    def _extract_training_data(self, content: str) -> str:
        """提取训练数据"""
        # 提取<data>标签中的内容
        data_pattern = r'<data>(.*?)</data>'
        data_match = re.search(data_pattern, content, re.DOTALL)
        
        if data_match:
            return data_match.group(1)
        
        # 提取```json```标签中的内容
        json_pattern = r'```json(.*?)```'
        json_match = re.search(json_pattern, content, re.DOTALL)
        
        if json_match:
            return json_match.group(1)
        
        return content
    
    async def cancel_task(self, task_id: str) -> FineTuningTask:
        """取消微调任务"""
        try:
            result = await self.db.execute(
                select(FineTuningTask).where(
                    FineTuningTask.id == task_id,
                    FineTuningTask.user_id == self.user_context.current_user_id
                )
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="任务不存在"
                )
            
            if task.status != FineTuningTaskStatus.IN_PROGRESS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="任务未在进行中，无法取消"
                )
            
            task.status = FineTuningTaskStatus.CANCELLED
            await self.db.commit()
            
            logger.info(f"取消微调任务成功: {task_id}")
            return task
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"取消微调任务失败: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"取消微调任务失败: {str(e)}"
            )
    
    async def delete_task(self, task_id: str):
        """删除微调任务"""
        try:
            result = await self.db.execute(
                select(FineTuningTask).where(
                    FineTuningTask.id == task_id,
                    FineTuningTask.user_id == self.user_context.current_user_id
                )
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="任务不存在"
                )
            
            await self.db.delete(task)
            await self.db.commit()
            
            logger.info(f"删除微调任务成功: {task_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除微调任务失败: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除微调任务失败: {str(e)}"
            )
    
    def _get_max_tokens(self, model: str) -> int:
        """获取模型的最大token数"""
        token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return token_limits.get(model, 4096)
    
    def _generate_id(self) -> str:
        """生成ID"""
        import uuid
        return uuid.uuid4().hex 