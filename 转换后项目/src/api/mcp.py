from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.mcp.mcp_extensions import MCPExtensions
from src.models.user import User

mcp_router = APIRouter()


@mcp_router.post("/tools")
@require_user()
async def list_tools(
    owner: str,
    name: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取工具列表"""
    try:
        tools = MCPExtensions.create_tools(owner, name)
        
        # 转换为JSON格式
        tools_data = []
        for tool in tools:
            tools_data.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            })
        
        return {
            "message": "success",
            "code": 200,
            "data": tools_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


@mcp_router.post("/call")
@require_user()
async def call_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """调用工具"""
    try:
        result = await MCPExtensions.handle_tool_call(tool_name, parameters, db)
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "tool_name": tool_name,
                "result": result
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"调用工具失败: {str(e)}"
        )


@mcp_router.post("/generate-document")
@require_user()
async def generate_document(
    owner: str,
    name: str,
    question: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成文档"""
    try:
        from src.mcp.tools.warehouse_tool import WarehouseTool
        
        warehouse_tool = WarehouseTool(db)
        result = await warehouse_tool.generate_document(question, owner, name)
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "question": question,
                "answer": result
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成文档失败: {str(e)}"
        ) 