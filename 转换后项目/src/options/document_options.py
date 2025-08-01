import os
from typing import List
from pydantic import BaseSettings, Field


class DocumentOptions(BaseSettings):
    """文档配置选项"""
    
    name: str = Field(default="Document", description="配置名称")
    
    # 增量更新相关
    enable_incremental_update: bool = Field(default=True, description="是否启用增量更新")
    
    # 排除文件相关
    excluded_files: List[str] = Field(default=[], description="排除的文件")
    excluded_folders: List[str] = Field(default=[], description="排除的文件夹")
    
    # 智能过滤
    enable_smart_filter: bool = Field(default=True, description="是否启用智能过滤")
    
    # 目录结构格式
    catalogue_format: str = Field(default="compact", description="目录结构格式 (compact, json, pathlist, unix)")
    
    # 代码依赖分析
    enable_code_dependency_analysis: bool = Field(default=False, description="是否启用代码依赖分析")
    
    # 仓库功能相关
    enable_warehouse_function_prompt_task: bool = Field(default=True, description="是否启用仓库功能提示任务")
    enable_warehouse_description_task: bool = Field(default=True, description="是否启用仓库描述任务")
    
    # 提交相关
    enable_file_commit: bool = Field(default=True, description="是否启用文件提交")
    enable_warehouse_commit: bool = Field(default=True, description="是否启用仓库提交")
    
    # 质量提升
    refine_and_enhance_quality: bool = Field(default=True, description="精炼并且提高质量")
    
    # 代码压缩
    enable_code_compression: bool = Field(default=False, description="是否启用代码压缩")
    
    class Config:
        env_prefix = "DOCUMENT_"
    
    @classmethod
    def init_config(cls) -> "DocumentOptions":
        """初始化配置"""
        # 从环境变量读取配置
        enable_warehouse_commit = os.getenv("ENABLE_WAREHOUSE_COMMIT", "true").lower() == "true"
        enable_file_commit = os.getenv("ENABLE_FILE_COMMIT", "true").lower() == "true"
        enable_incremental_update = os.getenv("ENABLE_INCREMENTAL_UPDATE", "true").lower() == "true"
        refine_and_enhance_quality = os.getenv("REFINE_AND_ENHANCE_QUALITY", "true").lower() == "true"
        enable_code_dependency_analysis = os.getenv("ENABLE_CODED_DEPENDENCY_ANALYSIS", "false").lower() == "true"
        enable_warehouse_function_prompt_task = os.getenv("ENABLE_WAREHOUSE_FUNCTION_PROMPT_TASK", "true").lower() == "true"
        enable_warehouse_description_task = os.getenv("ENABLE_WAREHOUSE_DESCRIPTION_TASK", "true").lower() == "true"
        catalogue_format = os.getenv("CATALOGUE_FORMAT", "compact").lower()
        enable_code_compression = os.getenv("ENABLE_CODE_COMPRESSION", "false").lower() == "true"
        
        return cls(
            enable_warehouse_commit=enable_warehouse_commit,
            enable_file_commit=enable_file_commit,
            enable_incremental_update=enable_incremental_update,
            refine_and_enhance_quality=refine_and_enhance_quality,
            enable_code_dependency_analysis=enable_code_dependency_analysis,
            enable_warehouse_function_prompt_task=enable_warehouse_function_prompt_task,
            enable_warehouse_description_task=enable_warehouse_description_task,
            catalogue_format=catalogue_format,
            enable_code_compression=enable_code_compression
        )
    
    @classmethod
    def get_enable_incremental_update(cls) -> bool:
        """获取是否启用增量更新"""
        return cls.init_config().enable_incremental_update
    
    @classmethod
    def get_excluded_files(cls) -> List[str]:
        """获取排除的文件"""
        return cls.init_config().excluded_files
    
    @classmethod
    def get_excluded_folders(cls) -> List[str]:
        """获取排除的文件夹"""
        return cls.init_config().excluded_folders
    
    @classmethod
    def get_enable_smart_filter(cls) -> bool:
        """获取是否启用智能过滤"""
        return cls.init_config().enable_smart_filter
    
    @classmethod
    def get_catalogue_format(cls) -> str:
        """获取目录结构格式"""
        return cls.init_config().catalogue_format
    
    @classmethod
    def get_enable_code_dependency_analysis(cls) -> bool:
        """获取是否启用代码依赖分析"""
        return cls.init_config().enable_code_dependency_analysis
    
    @classmethod
    def get_enable_warehouse_function_prompt_task(cls) -> bool:
        """获取是否启用仓库功能提示任务"""
        return cls.init_config().enable_warehouse_function_prompt_task
    
    @classmethod
    def get_enable_warehouse_description_task(cls) -> bool:
        """获取是否启用仓库描述任务"""
        return cls.init_config().enable_warehouse_description_task
    
    @classmethod
    def get_enable_file_commit(cls) -> bool:
        """获取是否启用文件提交"""
        return cls.init_config().enable_file_commit
    
    @classmethod
    def get_enable_warehouse_commit(cls) -> bool:
        """获取是否启用仓库提交"""
        return cls.init_config().enable_warehouse_commit
    
    @classmethod
    def get_refine_and_enhance_quality(cls) -> bool:
        """获取是否精炼并且提高质量"""
        return cls.init_config().refine_and_enhance_quality
    
    @classmethod
    def get_enable_code_compression(cls) -> bool:
        """获取是否启用代码压缩"""
        return cls.init_config().enable_code_compression 