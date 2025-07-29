import os
import shutil
import tempfile
from typing import Tuple, List, Optional
from dataclasses import dataclass
import git
from git import Repo
import logging

logger = logging.getLogger(__name__)


@dataclass
class GitInfo:
    """Git仓库信息"""
    repository_name: str
    branch_name: str
    organization: str
    version: str
    local_path: str


class GitUtils:
    """Git操作工具类"""
    
    def __init__(self, repositories_path: str = "./repositories"):
        self.repositories_path = repositories_path
        os.makedirs(repositories_path, exist_ok=True)
    
    def clone_repository(
        self, 
        repository_url: str, 
        username: str = "", 
        password: str = "", 
        branch: str = "main"
    ) -> GitInfo:
        """克隆仓库"""
        try:
            # 从URL中提取仓库信息
            repo_name = self._extract_repo_name(repository_url)
            org_name = self._extract_org_name(repository_url)
            
            # 构建本地路径
            local_path = os.path.join(self.repositories_path, org_name, repo_name)
            
            # 如果目录已存在，先删除
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            
            # 克隆仓库
            if username and password:
                # 使用用户名密码克隆
                auth_url = repository_url.replace("https://", f"https://{username}:{password}@")
                repo = Repo.clone_from(auth_url, local_path, branch=branch)
            else:
                # 公开仓库克隆
                repo = Repo.clone_from(repository_url, local_path, branch=branch)
            
            # 获取最新提交信息
            latest_commit = repo.head.commit
            
            return GitInfo(
                repository_name=repo_name,
                branch_name=branch,
                organization=org_name,
                version=latest_commit.hexsha,
                local_path=local_path
            )
            
        except Exception as e:
            logger.error(f"克隆仓库失败: {repository_url}, 错误: {str(e)}")
            raise
    
    def pull_repository(
        self, 
        local_path: str, 
        current_version: str = None,
        username: str = "",
        password: str = ""
    ) -> Tuple[List[dict], str]:
        """拉取仓库更新"""
        try:
            repo = Repo(local_path)
            
            # 获取远程更新
            origin = repo.remotes.origin
            origin.fetch()
            
            # 获取当前分支
            current_branch = repo.active_branch.name
            
            # 获取提交历史
            commits = []
            if current_version:
                # 获取从指定版本到HEAD的提交
                try:
                    current_commit = repo.commit(current_version)
                    for commit in repo.iter_commits(f"{current_version}..HEAD"):
                        commits.append({
                            "sha": commit.hexsha,
                            "message": commit.message,
                            "author": commit.author.name,
                            "date": commit.authored_datetime.isoformat()
                        })
                except git.BadName:
                    # 如果找不到指定版本，获取最近的提交
                    for commit in repo.iter_commits(max_count=10):
                        commits.append({
                            "sha": commit.hexsha,
                            "message": commit.message,
                            "author": commit.author.name,
                            "date": commit.authored_datetime.isoformat()
                        })
            else:
                # 获取最近的提交
                for commit in repo.iter_commits(max_count=10):
                    commits.append({
                        "sha": commit.hexsha,
                        "message": commit.message,
                        "author": commit.author.name,
                        "date": commit.authored_datetime.isoformat()
                    })
            
            # 拉取最新代码
            origin.pull()
            
            # 获取最新提交
            latest_commit = repo.head.commit
            
            return commits, latest_commit.hexsha
            
        except Exception as e:
            logger.error(f"拉取仓库失败: {local_path}, 错误: {str(e)}")
            raise
    
    def get_repository_info(self, local_path: str) -> GitInfo:
        """获取仓库信息"""
        try:
            repo = Repo(local_path)
            
            # 从路径中提取信息
            path_parts = local_path.split(os.sep)
            repo_name = path_parts[-1]
            org_name = path_parts[-2] if len(path_parts) > 1 else "unknown"
            
            return GitInfo(
                repository_name=repo_name,
                branch_name=repo.active_branch.name,
                organization=org_name,
                version=repo.head.commit.hexsha,
                local_path=local_path
            )
            
        except Exception as e:
            logger.error(f"获取仓库信息失败: {local_path}, 错误: {str(e)}")
            raise
    
    def _extract_repo_name(self, repository_url: str) -> str:
        """从URL中提取仓库名"""
        # 移除.git后缀
        url = repository_url.replace(".git", "")
        # 获取最后一部分作为仓库名
        return url.split("/")[-1]
    
    def _extract_org_name(self, repository_url: str) -> str:
        """从URL中提取组织名"""
        # 移除.git后缀
        url = repository_url.replace(".git", "")
        # 获取倒数第二部分作为组织名
        parts = url.split("/")
        return parts[-2] if len(parts) > 1 else "unknown"
    
    def get_file_content(self, local_path: str, file_path: str) -> Optional[str]:
        """获取文件内容"""
        try:
            full_path = os.path.join(local_path, file_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"读取文件失败: {full_path}, 错误: {str(e)}")
            return None
    
    def get_file_tree(self, local_path: str) -> dict:
        """获取文件树结构"""
        def build_tree(path: str, relative_path: str = "") -> dict:
            tree = {"type": "directory", "name": os.path.basename(path), "children": []}
            
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    item_relative_path = os.path.join(relative_path, item).replace("\\", "/")
                    
                    if os.path.isdir(item_path):
                        # 跳过.git目录
                        if item == ".git":
                            continue
                        tree["children"].append(build_tree(item_path, item_relative_path))
                    else:
                        tree["children"].append({
                            "type": "file",
                            "name": item,
                            "path": item_relative_path,
                            "size": os.path.getsize(item_path)
                        })
            except PermissionError:
                # 跳过无权限的目录
                pass
            
            return tree
        
        return build_tree(local_path) 