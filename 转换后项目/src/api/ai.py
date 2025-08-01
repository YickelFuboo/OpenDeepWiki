from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.dto.ai_dto import (
    ResponsesInput, AIResponse, ProjectOverviewInput, 
    CodeAnalysisInput, CodeAnalysisResult, PromptInput, PromptResult,
    FileAnalysisInput, FileAnalysisResult
)
from src.services.ai_service import AIService
from src.models.user import User

ai_router = APIRouter()


@ai_router.post("/responses", response_model=AIResponse)
@require_user()
async def process_responses(
    responses_input: ResponsesInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """处理AI响应请求"""
    ai_service = AIService(db)
    
    try:
        result = await ai_service.process_responses(responses_input)
        return AIResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理AI响应时发生错误: {str(e)}"
        )


@ai_router.post("/project-overview")
@require_user()
async def generate_project_overview(
    overview_input: ProjectOverviewInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成项目概述"""
    ai_service = AIService(db)
    
    try:
        overview = await ai_service.generate_project_overview(
            repository_path=overview_input.repository_path,
            catalog=overview_input.catalog,
            git_repository=overview_input.git_repository,
            branch=overview_input.branch,
            readme=overview_input.readme
        )
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "overview": overview
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成项目概述时发生错误: {str(e)}"
        )


@ai_router.post("/code-analysis", response_model=CodeAnalysisResult)
@require_user()
async def analyze_code_structure(
    analysis_input: CodeAnalysisInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分析代码结构"""
    ai_service = AIService(db)
    
    try:
        result = await ai_service.analyze_code_structure(analysis_input.repository_path)
        return CodeAnalysisResult(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析代码结构时发生错误: {str(e)}"
        )


@ai_router.post("/prompt", response_model=PromptResult)
@require_user()
async def execute_prompt(
    prompt_input: PromptInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """执行提示词"""
    ai_service = AIService(db)
    
    try:
        # 这里可以调用AI服务执行提示词
        result = await ai_service.execute_prompt(
            prompt_name=prompt_input.prompt_name,
            parameters=prompt_input.parameters,
            model=prompt_input.model
        )
        
        return PromptResult(
            content=result.get("content", ""),
            usage=result.get("usage"),
            metadata=result.get("metadata")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行提示词时发生错误: {str(e)}"
        )


@ai_router.post("/file-analysis", response_model=FileAnalysisResult)
@require_user()
async def analyze_files(
    analysis_input: FileAnalysisInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分析文件"""
    ai_service = AIService(db)
    
    try:
        result = await ai_service.analyze_files(
            file_paths=analysis_input.file_paths,
            analysis_type=analysis_input.analysis_type
        )
        
        return FileAnalysisResult(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析文件时发生错误: {str(e)}"
        )


@ai_router.get("/models")
@require_user()
async def get_available_models(
    current_user: User = Depends(get_current_active_user)
):
    """获取可用的AI模型列表"""
    try:
        models = [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "OpenAI",
                "description": "OpenAI GPT-4 模型"
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "description": "OpenAI GPT-3.5 Turbo 模型"
            },
            {
                "id": "claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "description": "Anthropic Claude 3 Sonnet 模型"
            }
        ]
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "models": models
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表时发生错误: {str(e)}"
        )


@ai_router.get("/prompts")
@require_user()
async def get_available_prompts(
    current_user: User = Depends(get_current_active_user)
):
    """获取可用的提示词列表"""
    try:
        prompts = [
            {
                "name": "GenerateReadme",
                "description": "生成README文档",
                "category": "documentation"
            },
            {
                "name": "GenerateDescription",
                "description": "生成项目描述",
                "category": "documentation"
            },
            {
                "name": "SimplifyCodeDirectory",
                "description": "简化代码目录结构",
                "category": "analysis"
            },
            {
                "name": "AnalyzeCommit",
                "description": "分析Git提交信息",
                "category": "analysis"
            }
        ]
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "prompts": prompts
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提示词列表时发生错误: {str(e)}"
        ) 