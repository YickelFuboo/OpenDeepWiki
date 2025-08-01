from dataclasses import dataclass
from typing import Optional


@dataclass
class PathInfo:
    """路径信息"""
    path: str
    name: str
    type: str
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.name and self.path:
            # 如果没有名称，从路径中提取
            import os
            self.name = os.path.basename(self.path)
        
        if not self.type and self.path:
            # 如果没有类型，从文件扩展名推断
            import os
            ext = os.path.splitext(self.path)[1].lower()
            if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs']:
                self.type = "code"
            elif ext in ['.md', '.txt', '.rst']:
                self.type = "documentation"
            elif ext in ['.json', '.yaml', '.yml', '.xml', '.toml']:
                self.type = "config"
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                self.type = "image"
            else:
                self.type = "other" 