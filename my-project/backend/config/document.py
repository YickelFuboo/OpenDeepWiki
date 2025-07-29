"""
文档配置模块

处理文档生成相关的配置
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field

class DocumentOptions(BaseModel):
    """文档配置选项"""
    
    # 是否启用增量更新
    enable_incremental_update: bool = Field(
        default=True,
        description="是否启用增量更新"
    )
    
    # 增量更新间隔（天）
    incremental_update_interval: int = Field(
        default=7,
        description="增量更新间隔（天）"
    )
    
    # 是否启用文档生成
    enable_document_generation: bool = Field(
        default=True,
        description="是否启用文档生成"
    )
    
    # 文档生成并发数
    document_generation_concurrency: int = Field(
        default=5,
        description="文档生成并发数"
    )
    
    # 文档生成超时时间（分钟）
    document_generation_timeout: int = Field(
        default=30,
        description="文档生成超时时间（分钟）"
    )
    
    # 是否启用思维导图生成
    enable_mindmap_generation: bool = Field(
        default=True,
        description="是否启用思维导图生成"
    )
    
    # 思维导图生成超时时间（分钟）
    mindmap_generation_timeout: int = Field(
        default=15,
        description="思维导图生成超时时间（分钟）"
    )
    
    # 是否启用项目概览生成
    enable_overview_generation: bool = Field(
        default=True,
        description="是否启用项目概览生成"
    )
    
    # 项目概览生成超时时间（分钟）
    overview_generation_timeout: int = Field(
        default=10,
        description="项目概览生成超时时间（分钟）"
    )
    
    # 支持的文件扩展名
    supported_file_extensions: List[str] = Field(
        default=[
            ".md", ".txt", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h",
            ".go", ".rs", ".php", ".rb", ".cs", ".swift", ".kt", ".scala",
            ".html", ".css", ".xml", ".json", ".yaml", ".yml", ".toml",
            ".ini", ".cfg", ".conf", ".sh", ".bat", ".ps1"
        ],
        description="支持的文件扩展名"
    )
    
    # 忽略的文件和目录
    ignored_patterns: List[str] = Field(
        default=[
            "node_modules", ".git", ".svn", ".hg", ".DS_Store",
            "*.log", "*.tmp", "*.temp", "*.cache", "*.lock",
            "dist", "build", "target", "bin", "obj"
        ],
        description="忽略的文件和目录模式"
    )
    
    # 最大文件大小（MB）
    max_file_size_mb: int = Field(
        default=10,
        description="最大文件大小（MB）"
    )
    
    # 文档存储路径
    document_storage_path: str = Field(
        default="./documents",
        description="文档存储路径"
    )
    
    # 是否启用文档缓存
    enable_document_cache: bool = Field(
        default=True,
        description="是否启用文档缓存"
    )
    
    # 文档缓存过期时间（小时）
    document_cache_expire_hours: int = Field(
        default=24,
        description="文档缓存过期时间（小时）"
    )
    
    # 是否启用文档压缩
    enable_document_compression: bool = Field(
        default=True,
        description="是否启用文档压缩"
    )
    
    # 文档压缩级别
    document_compression_level: int = Field(
        default=6,
        description="文档压缩级别（1-9）"
    )

def get_document_options() -> DocumentOptions:
    """获取文档配置选项"""
    return DocumentOptions(
        enable_incremental_update=os.getenv("ENABLE_INCREMENTAL_UPDATE", "true").lower() == "true",
        incremental_update_interval=int(os.getenv("INCREMENTAL_UPDATE_INTERVAL", "7")),
        enable_document_generation=os.getenv("ENABLE_DOCUMENT_GENERATION", "true").lower() == "true",
        document_generation_concurrency=int(os.getenv("DOCUMENT_GENERATION_CONCURRENCY", "5")),
        document_generation_timeout=int(os.getenv("DOCUMENT_GENERATION_TIMEOUT", "30")),
        enable_mindmap_generation=os.getenv("ENABLE_MINDMAP_GENERATION", "true").lower() == "true",
        mindmap_generation_timeout=int(os.getenv("MINDMAP_GENERATION_TIMEOUT", "15")),
        enable_overview_generation=os.getenv("ENABLE_OVERVIEW_GENERATION", "true").lower() == "true",
        overview_generation_timeout=int(os.getenv("OVERVIEW_GENERATION_TIMEOUT", "10")),
        supported_file_extensions=os.getenv("SUPPORTED_FILE_EXTENSIONS", "").split(",") if os.getenv("SUPPORTED_FILE_EXTENSIONS") else [
            ".md", ".txt", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h",
            ".go", ".rs", ".php", ".rb", ".cs", ".swift", ".kt", ".scala",
            ".html", ".css", ".xml", ".json", ".yaml", ".yml", ".toml",
            ".ini", ".cfg", ".conf", ".sh", ".bat", ".ps1"
        ],
        ignored_patterns=os.getenv("IGNORED_PATTERNS", "").split(",") if os.getenv("IGNORED_PATTERNS") else [
            "node_modules", ".git", ".svn", ".hg", ".DS_Store",
            "*.log", "*.tmp", "*.temp", "*.cache", "*.lock",
            "dist", "build", "target", "bin", "obj"
        ],
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
        document_storage_path=os.getenv("DOCUMENT_STORAGE_PATH", "./documents"),
        enable_document_cache=os.getenv("ENABLE_DOCUMENT_CACHE", "true").lower() == "true",
        document_cache_expire_hours=int(os.getenv("DOCUMENT_CACHE_EXPIRE_HOURS", "24")),
        enable_document_compression=os.getenv("ENABLE_DOCUMENT_COMPRESSION", "true").lower() == "true",
        document_compression_level=int(os.getenv("DOCUMENT_COMPRESSION_LEVEL", "6"))
    )

# 全局文档配置实例
document_options = get_document_options() 