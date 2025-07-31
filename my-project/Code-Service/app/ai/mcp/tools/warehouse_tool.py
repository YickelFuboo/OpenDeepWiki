"""
MCP仓库工具

提供仓库相关的MCP工具功能
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WarehouseToolRequest(BaseModel):
    """仓库工具请求模型"""
    warehouse_id: str
    action: str
    parameters: Optional[Dict[str, Any]] = None

class WarehouseToolResponse(BaseModel):
    """仓库工具响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class WarehouseTool:
    """MCP仓库工具"""
    
    def __init__(self):
        self.supported_actions = [
            "get_warehouse_info",
            "get_warehouse_documents", 
            "get_warehouse_statistics",
            "search_warehouse",
            "export_warehouse"
        ]
    
    def execute(self, request: WarehouseToolRequest) -> WarehouseToolResponse:
        """
        执行仓库工具操作
        
        Args:
            request: 工具请求
            
        Returns:
            工具响应
        """
        try:
            if request.action not in self.supported_actions:
                return WarehouseToolResponse(
                    success=False,
                    error=f"不支持的操作: {request.action}"
                )
            
            # 根据操作类型调用相应的方法
            if request.action == "get_warehouse_info":
                return self._get_warehouse_info(request.warehouse_id)
            
            elif request.action == "get_warehouse_documents":
                return self._get_warehouse_documents(request.warehouse_id)
            
            elif request.action == "get_warehouse_statistics":
                return self._get_warehouse_statistics(request.warehouse_id)
            
            elif request.action == "search_warehouse":
                query = request.parameters.get("query", "") if request.parameters else ""
                return self._search_warehouse(request.warehouse_id, query)
            
            elif request.action == "export_warehouse":
                format_type = request.parameters.get("format", "json") if request.parameters else "json"
                return self._export_warehouse(request.warehouse_id, format_type)
            
            else:
                return WarehouseToolResponse(
                    success=False,
                    error=f"未知操作: {request.action}"
                )
                
        except Exception as e:
            logger.error(f"执行仓库工具操作异常: {str(e)}")
            return WarehouseToolResponse(
                success=False,
                error=str(e)
            )
    
    def _get_warehouse_info(self, warehouse_id: str) -> WarehouseToolResponse:
        """获取仓库信息"""
        try:
            from app.db.connection import get_db
            from app.db.models.warehouse import Warehouse
            
            db = next(get_db())
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            
            if not warehouse:
                return WarehouseToolResponse(
                    success=False,
                    error=f"仓库不存在: {warehouse_id}"
                )
            
            warehouse_info = {
                "id": warehouse.id,
                "name": warehouse.name,
                "organization_name": warehouse.organization_name,
                "address": warehouse.address,
                "branch": warehouse.branch,
                "status": warehouse.status.value if warehouse.status else "unknown",
                "created_at": warehouse.created_at,
                "updated_at": warehouse.updated_at,
                "description": warehouse.description
            }
            
            return WarehouseToolResponse(
                success=True,
                data=warehouse_info
            )
            
        except Exception as e:
            logger.error(f"获取仓库信息异常: {str(e)}")
            return WarehouseToolResponse(
                success=False,
                error=str(e)
            )
    
    def _get_warehouse_documents(self, warehouse_id: str) -> WarehouseToolResponse:
        """获取仓库文档"""
        try:
            from app.db.connection import get_db
            from app.db.models.document import Document
            
            db = next(get_db())
            documents = db.query(Document).filter(Document.warehouse_id == warehouse_id).all()
            
            documents_info = []
            for doc in documents:
                doc_info = {
                    "id": doc.id,
                    "title": doc.title,
                    "description": doc.description,
                    "status": doc.status.value if doc.status else "unknown",
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at
                }
                documents_info.append(doc_info)
            
            return WarehouseToolResponse(
                success=True,
                data={
                    "warehouse_id": warehouse_id,
                    "documents": documents_info,
                    "total_count": len(documents_info)
                }
            )
            
        except Exception as e:
            logger.error(f"获取仓库文档异常: {str(e)}")
            return WarehouseToolResponse(
                success=False,
                error=str(e)
            )
    
    def _get_warehouse_statistics(self, warehouse_id: str) -> WarehouseToolResponse:
        """获取仓库统计信息"""
        try:
            from app.db.connection import get_db
            from app.db.models.document import Document
            from app.db.models.access_log import AccessLog
            
            db = next(get_db())
            
            # 统计文档数量
            document_count = db.query(Document).filter(Document.warehouse_id == warehouse_id).count()
            
            # 统计访问量
            access_count = db.query(AccessLog).filter(
                AccessLog.resource_type == "warehouse",
                AccessLog.resource_id == warehouse_id
            ).count()
            
            # 统计今日访问
            from datetime import datetime, timedelta
            today = datetime.utcnow().date()
            today_access = db.query(AccessLog).filter(
                AccessLog.resource_type == "warehouse",
                AccessLog.resource_id == warehouse_id,
                AccessLog.created_at >= today
            ).count()
            
            statistics = {
                "warehouse_id": warehouse_id,
                "document_count": document_count,
                "total_access": access_count,
                "today_access": today_access,
                "avg_response_time": 0  # 可以从访问日志计算
            }
            
            return WarehouseToolResponse(
                success=True,
                data=statistics
            )
            
        except Exception as e:
            logger.error(f"获取仓库统计异常: {str(e)}")
            return WarehouseToolResponse(
                success=False,
                error=str(e)
            )
    
    def _search_warehouse(self, warehouse_id: str, query: str) -> WarehouseToolResponse:
        """搜索仓库内容"""
        try:
            from app.db.connection import get_db
            from app.db.models.document import Document
            
            db = next(get_db())
            
            # 简单的文本搜索
            documents = db.query(Document).filter(
                Document.warehouse_id == warehouse_id,
                (Document.title.contains(query) | Document.description.contains(query))
            ).all()
            
            search_results = []
            for doc in documents:
                result = {
                    "id": doc.id,
                    "title": doc.title,
                    "description": doc.description,
                    "relevance_score": 1.0  # 简单实现，可以改进
                }
                search_results.append(result)
            
            return WarehouseToolResponse(
                success=True,
                data={
                    "warehouse_id": warehouse_id,
                    "query": query,
                    "results": search_results,
                    "total_count": len(search_results)
                }
            )
            
        except Exception as e:
            logger.error(f"搜索仓库异常: {str(e)}")
            return WarehouseToolResponse(
                success=False,
                error=str(e)
            )
    
    def _export_warehouse(self, warehouse_id: str, format_type: str) -> WarehouseToolResponse:
        """导出仓库数据"""
        try:
            from app.db.connection import get_db
            from app.db.models.warehouse import Warehouse
            from app.db.models.document import Document
            
            db = next(get_db())
            
            # 获取仓库信息
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            if not warehouse:
                return WarehouseToolResponse(
                    success=False,
                    error=f"仓库不存在: {warehouse_id}"
                )
            
            # 获取文档信息
            documents = db.query(Document).filter(Document.warehouse_id == warehouse_id).all()
            
            # 构建导出数据
            export_data = {
                "warehouse": {
                    "id": warehouse.id,
                    "name": warehouse.name,
                    "organization_name": warehouse.organization_name,
                    "address": warehouse.address,
                    "branch": warehouse.branch,
                    "status": warehouse.status.value if warehouse.status else "unknown",
                    "created_at": warehouse.created_at,
                    "updated_at": warehouse.updated_at,
                    "description": warehouse.description
                },
                "documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "description": doc.description,
                        "status": doc.status.value if doc.status else "unknown",
                        "created_at": doc.created_at,
                        "updated_at": doc.updated_at
                    }
                    for doc in documents
                ],
                "export_info": {
                    "export_time": datetime.utcnow().isoformat(),
                    "format": format_type,
                    "total_documents": len(documents)
                }
            }
            
            return WarehouseToolResponse(
                success=True,
                data=export_data
            )
            
        except Exception as e:
            logger.error(f"导出仓库异常: {str(e)}")
            return WarehouseToolResponse(
                success=False,
                error=str(e)
            )
    
    def get_supported_actions(self) -> List[str]:
        """获取支持的操作列表"""
        return self.supported_actions
    
    def get_tool_description(self) -> Dict[str, Any]:
        """获取工具描述"""
        return {
            "name": "warehouse_tool",
            "description": "仓库管理工具，提供仓库信息查询、文档管理、统计信息等功能",
            "supported_actions": self.supported_actions,
            "parameters": {
                "warehouse_id": "仓库ID",
                "action": "操作类型",
                "parameters": "操作参数（可选）"
            }
        } 