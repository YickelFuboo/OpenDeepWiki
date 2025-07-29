"""
Gitee配置模块

处理Gitee相关的配置
"""

import os
from typing import Optional
from pydantic import BaseModel, Field

class GiteeOptions(BaseModel):
    """Gitee配置选项"""
    
    # Gitee API令牌
    api_token: Optional[str] = Field(
        default=None,
        description="Gitee API令牌"
    )
    
    # Gitee API基础URL
    api_base_url: str = Field(
        default="https://gitee.com/api/v5",
        description="Gitee API基础URL"
    )
    
    # Gitee用户名
    username: Optional[str] = Field(
        default=None,
        description="Gitee用户名"
    )
    
    # Gitee密码
    password: Optional[str] = Field(
        default=None,
        description="Gitee密码"
    )
    
    # 是否启用Gitee功能
    enable_gitee: bool = Field(
        default=True,
        description="是否启用Gitee功能"
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

def get_gitee_options() -> GiteeOptions:
    """获取Gitee配置选项"""
    return GiteeOptions(
        api_token=os.getenv("GITEE_API_TOKEN"),
        api_base_url=os.getenv("GITEE_API_BASE_URL", "https://gitee.com/api/v5"),
        username=os.getenv("GITEE_USERNAME"),
        password=os.getenv("GITEE_PASSWORD"),
        enable_gitee=os.getenv("ENABLE_GITEE", "true").lower() == "true",
        timeout=int(os.getenv("GITEE_TIMEOUT", "30")),
        max_retries=int(os.getenv("GITEE_MAX_RETRIES", "3")),
        per_page=int(os.getenv("GITEE_PER_PAGE", "100"))
    )

# 全局Gitee配置实例
gitee_options = get_gitee_options() 