from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.services.code_map_service import CodeMapService
from src.code_map.models import DependencyTree
from src.models.user import User

code_map_router = APIRouter()


@code_map_router.get("/file-dependency-tree")
@require_user()
async def analyze_file_dependency_tree(
    base_path: str = Query(..., description="基础路径"),
    file_path: str = Query(..., description="文件路径"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分析文件依赖树"""
    code_map_service = CodeMapService(db)
    
    try:
        tree = await code_map_service.analyze_file_dependency_tree(base_path, file_path)
        if not tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无法分析文件依赖树"
            )
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "tree": tree,
                "visualization": code_map_service.generate_dependency_tree_visualization(tree),
                "dot_graph": code_map_service.generate_dot_graph(tree)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析文件依赖树失败: {str(e)}"
        )


@code_map_router.get("/function-dependency-tree")
@require_user()
async def analyze_function_dependency_tree(
    base_path: str = Query(..., description="基础路径"),
    file_path: str = Query(..., description="文件路径"),
    function_name: str = Query(..., description="函数名称"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分析函数依赖树"""
    code_map_service = CodeMapService(db)
    
    try:
        tree = await code_map_service.analyze_function_dependency_tree(base_path, file_path, function_name)
        if not tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无法分析函数依赖树"
            )
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "tree": tree,
                "visualization": code_map_service.generate_dependency_tree_visualization(tree),
                "dot_graph": code_map_service.generate_dot_graph(tree)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析函数依赖树失败: {str(e)}"
        ) 