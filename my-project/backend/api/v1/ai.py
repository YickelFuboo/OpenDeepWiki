from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.ai_service import AIService
from schemas.common import BaseResponse
from utils.auth import get_current_active_user
from models.user import User

router = APIRouter()


@router.post("/analyze-code", response_model=BaseResponse)
async def analyze_code(
    code_content: str,
    language: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """分析代码"""
    try:
        ai_service = AIService(db)
        result = ai_service.analyze_code(code_content, language)
        return BaseResponse(
            success=True,
            message="代码分析成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码分析失败: {str(e)}"
        )


@router.post("/generate-documentation", response_model=BaseResponse)
async def generate_documentation(
    code_content: str,
    doc_type: str = "markdown",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成文档"""
    try:
        ai_service = AIService(db)
        result = ai_service.generate_documentation(code_content, doc_type)
        return BaseResponse(
            success=True,
            message="文档生成成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档生成失败: {str(e)}"
        )


@router.post("/chat", response_model=BaseResponse)
async def chat_with_ai(
    message: str,
    context: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """与AI对话"""
    try:
        ai_service = AIService(db)
        result = ai_service.chat(message, context)
        return BaseResponse(
            success=True,
            message="AI对话成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI对话失败: {str(e)}"
        )


@router.post("/search-code", response_model=BaseResponse)
async def search_code(
    query: str,
    warehouse_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """搜索代码"""
    try:
        ai_service = AIService(db)
        result = ai_service.search_code(query, warehouse_id)
        return BaseResponse(
            success=True,
            message="代码搜索成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码搜索失败: {str(e)}"
        )


@router.post("/explain-code", response_model=BaseResponse)
async def explain_code(
    code_content: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """解释代码"""
    try:
        ai_service = AIService(db)
        result = ai_service.explain_code(code_content)
        return BaseResponse(
            success=True,
            message="代码解释成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码解释失败: {str(e)}"
        )


@router.post("/optimize-code", response_model=BaseResponse)
async def optimize_code(
    code_content: str,
    optimization_type: str = "performance",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """优化代码"""
    try:
        ai_service = AIService(db)
        result = ai_service.optimize_code(code_content, optimization_type)
        return BaseResponse(
            success=True,
            message="代码优化成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码优化失败: {str(e)}"
        )


@router.post("/generate-tests", response_model=BaseResponse)
async def generate_tests(
    code_content: str,
    test_framework: str = "pytest",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成测试代码"""
    try:
        ai_service = AIService(db)
        result = ai_service.generate_tests(code_content, test_framework)
        return BaseResponse(
            success=True,
            message="测试代码生成成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试代码生成失败: {str(e)}"
        ) 