import logging
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from config import get_settings
from models.warehouse import Warehouse
from ..core.kernel_factory import KernelFactory

logger = logging.getLogger(__name__)


class MiniMapService:
    """知识图谱服务类，负责生成项目的知识图谱"""
    
    def __init__(self, db: Session):
        """
        初始化知识图谱服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.settings = get_settings()
    
    async def generate_minimap(self, catalogue: str, warehouse: Warehouse, git_path: str) -> Dict[str, Any]:
        """
        生成知识图谱
        
        Args:
            catalogue: 目录结构
            warehouse: 仓库信息
            git_path: Git仓库路径
            
        Returns:
            生成的知识图谱
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path=git_path,
                model=self.settings.analysis_model
            )
            
            # 构建知识图谱生成提示词
            prompt = f"""
            请根据以下信息生成项目的知识图谱：
            
            仓库信息：
            - 名称：{warehouse.name}
            - 地址：{warehouse.address}
            - 分支：{warehouse.branch}
            
            目录结构：
            {catalogue}
            
            请生成一个完整的知识图谱，包含：
            1. 核心概念和实体
            2. 实体间的关系
            3. 技术架构图
            4. 数据流程图
            5. 模块依赖关系
            
            请使用Mermaid图表格式返回。
            """
            
            # 调用AI模型生成知识图谱
            result = await self._invoke_ai_model(kernel, prompt)
            
            # 解析结果
            minimap_data = self._parse_minimap_result(result)
            
            return {
                "success": True,
                "minimap": minimap_data,
                "warehouse_id": warehouse.id,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"知识图谱生成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_minimap_result(self, result: str) -> Dict[str, Any]:
        """
        解析知识图谱结果
        
        Args:
            result: AI模型返回的结果
            
        Returns:
            解析后的知识图谱数据
        """
        try:
            # 提取Mermaid图表
            mermaid_charts = self._extract_mermaid_charts(result)
            
            # 提取实体和关系
            entities = self._extract_entities(result)
            relationships = self._extract_relationships(result)
            
            return {
                "mermaid_charts": mermaid_charts,
                "entities": entities,
                "relationships": relationships,
                "raw_content": result
            }
            
        except Exception as e:
            logger.error(f"解析知识图谱结果失败: {e}")
            return {
                "mermaid_charts": [],
                "entities": [],
                "relationships": [],
                "raw_content": result
            }
    
    def _extract_mermaid_charts(self, content: str) -> List[str]:
        """
        提取Mermaid图表
        
        Args:
            content: 内容字符串
            
        Returns:
            Mermaid图表列表
        """
        charts = []
        lines = content.split('\n')
        in_mermaid = False
        current_chart = []
        
        for line in lines:
            if '```mermaid' in line:
                in_mermaid = True
                current_chart = []
            elif '```' in line and in_mermaid:
                in_mermaid = False
                if current_chart:
                    charts.append('\n'.join(current_chart))
            elif in_mermaid:
                current_chart.append(line)
        
        return charts
    
    def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """
        提取实体
        
        Args:
            content: 内容字符串
            
        Returns:
            实体列表
        """
        entities = []
        
        # 简单的实体提取逻辑
        # 可以根据需要扩展更复杂的提取算法
        
        return entities
    
    def _extract_relationships(self, content: str) -> List[Dict[str, Any]]:
        """
        提取关系
        
        Args:
            content: 内容字符串
            
        Returns:
            关系列表
        """
        relationships = []
        
        # 简单的关系提取逻辑
        # 可以根据需要扩展更复杂的提取算法
        
        return relationships
    
    async def _invoke_ai_model(self, kernel, prompt: str) -> str:
        """
        调用AI模型
        
        Args:
            kernel: AI内核
            prompt: 提示词
            
        Returns:
            AI模型响应
        """
        try:
            from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
            
            # 获取聊天完成服务
            chat_service = kernel.get_service(ChatCompletionClientBase)
            
            # 调用AI模型
            messages = [{"role": "user", "content": prompt}]
            response = await chat_service.complete_chat(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"AI模型调用失败: {e}")
            raise 