"""
GitHub配置模块

处理GitHub相关的配置
"""

import os
from typing import Optional
from pydantic import BaseModel, Field

class GithubOptions(BaseModel):
    """GitHub配置选项"""
    
    # GitHub API令牌
    api_token: Optional[str] = Field(
        default=None,
        description="GitHub API令牌"
    )
    
    # GitHub API基础URL
    api_base_url: str = Field(
        default="https://api.github.com",
        description="GitHub API基础URL"
    )
    
    # GitHub用户名
    username: Optional[str] = Field(
        default=None,
        description="GitHub用户名"
    )
    
    # GitHub密码
    password: Optional[str] = Field(
        default=None,
        description="GitHub密码"
    )
    
    # 是否启用GitHub功能
    enable_github: bool = Field(
        default=True,
        description="是否启用GitHub功能"
    )
    
    # 请求超时时间（秒）
    timeout: int = Field(
        default=30,
        description="请求超时时间（秒）"
    )
    
    # 最大重试次数
    max_retries: int = Field(
        default=3,
        description="最大重试次数"
    )
    
    # 每页结果数
    per_page: int = Field(
        default=100,
        description="每页结果数"
    )
    
    # 是否使用个人访问令牌
    use_personal_access_token: bool = Field(
        default=True,
        description="是否使用个人访问令牌"
    )

def get_github_options() -> GithubOptions:
    """获取GitHub配置选项"""
    return GithubOptions(
        api_token=os.getenv("GITHUB_API_TOKEN"),
        api_base_url=os.getenv("GITHUB_API_BASE_URL", "https://api.github.com"),
        username=os.getenv("GITHUB_USERNAME"),
        password=os.getenv("GITHUB_PASSWORD"),
        enable_github=os.getenv("ENABLE_GITHUB", "true").lower() == "true",
        timeout=int(os.getenv("GITHUB_TIMEOUT", "30")),
        max_retries=int(os.getenv("GITHUB_MAX_RETRIES", "3")),
        per_page=int(os.getenv("GITHUB_PER_PAGE", "100")),
        use_personal_access_token=os.getenv("GITHUB_USE_PERSONAL_ACCESS_TOKEN", "true").lower() == "true"
    )

# 全局GitHub配置实例
github_options = get_github_options() 