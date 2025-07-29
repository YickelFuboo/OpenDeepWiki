import json
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class RagFunction:
    """RAG搜索函数类，提供向量搜索和检索功能"""
    
    def __init__(self, warehouse_id: str, api_key: str = None, endpoint: str = None):
        """
        初始化RAG函数
        
        Args:
            warehouse_id: 仓库ID
            api_key: API密钥
            endpoint: API端点
        """
        self.warehouse_id = warehouse_id
        self.api_key = api_key
        self.endpoint = endpoint or "http://localhost:8000"
        
        # 配置HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=600.0,  # 10分钟超时
            headers={
                "User-Agent": "OpenDeepWiki/1.0",
                "Authorization": f"Bearer {api_key}" if api_key else None
            }
        )
    
    async def search(self, query: str, limit: int = 5, min_relevance: float = 0.3) -> str:
        """
        搜索相关代码或文档内容
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            min_relevance: 最小相关性阈值
            
        Returns:
            搜索结果JSON字符串
        """
        try:
            # 构建搜索请求
            search_request = {
                "query": query,
                "user_id": self.warehouse_id,
                "threshold": min_relevance,
                "limit": limit
            }
            
            # 发送搜索请求
            response = await self.client.post(
                f"{self.endpoint}/search",
                json=search_request
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                error_msg = f"搜索请求失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})
                
        except Exception as e:
            logger.error(f"RAG搜索失败: {e}")
            return json.dumps({"error": f"RAG搜索失败: {str(e)}"})
    
    async def index_content(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        索引内容到向量数据库
        
        Args:
            content: 要索引的内容
            metadata: 元数据
            
        Returns:
            索引结果JSON字符串
        """
        try:
            # 构建索引请求
            index_request = {
                "content": content,
                "user_id": self.warehouse_id,
                "metadata": metadata or {}
            }
            
            # 发送索引请求
            response = await self.client.post(
                f"{self.endpoint}/index",
                json=index_request
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                error_msg = f"索引请求失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})
                
        except Exception as e:
            logger.error(f"RAG索引失败: {e}")
            return json.dumps({"error": f"RAG索引失败: {str(e)}"})
    
    async def delete_index(self, document_id: str) -> str:
        """
        删除索引文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            删除结果JSON字符串
        """
        try:
            # 构建删除请求
            delete_request = {
                "document_id": document_id,
                "user_id": self.warehouse_id
            }
            
            # 发送删除请求
            response = await self.client.delete(
                f"{self.endpoint}/index",
                json=delete_request
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                error_msg = f"删除索引失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})
                
        except Exception as e:
            logger.error(f"RAG删除索引失败: {e}")
            return json.dumps({"error": f"RAG删除索引失败: {str(e)}"})
    
    async def get_similar_documents(self, content: str, limit: int = 5) -> str:
        """
        获取相似文档
        
        Args:
            content: 查询内容
            limit: 返回结果数量限制
            
        Returns:
            相似文档JSON字符串
        """
        try:
            # 构建相似性搜索请求
            similarity_request = {
                "content": content,
                "user_id": self.warehouse_id,
                "limit": limit
            }
            
            # 发送相似性搜索请求
            response = await self.client.post(
                f"{self.endpoint}/similar",
                json=similarity_request
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                error_msg = f"相似性搜索失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})
                
        except Exception as e:
            logger.error(f"RAG相似性搜索失败: {e}")
            return json.dumps({"error": f"RAG相似性搜索失败: {str(e)}"})
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose() 