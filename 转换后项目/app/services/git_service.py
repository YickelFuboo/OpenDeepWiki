import os
import shutil
from typing import List, Tuple, Optional
from datetime import datetime
from urllib.parse import urlparse
import git
from loguru import logger

from src.conf.settings import settings


class GitRepositoryInfo:
    """Git仓库信息"""
    
    def __init__(self, local_path: str, repository_name: str, organization: str,
                 branch_name: str, commit_time: str, commit_author: str,
                 commit_message: str, version: str):
        self.local_path = local_path
        self.repository_name = repository_name
        self.organization = organization
        self.branch_name = branch_name
        self.commit_time = commit_time
        self.commit_author = commit_author
        self.commit_message = commit_message
        self.version = version
    
    def to_dict(self):
        """转换为字典"""
        return {
            "local_path": self.local_path,
            "repository_name": self.repository_name,
            "organization": self.organization,
            "branch_name": self.branch_name,
            "commit_time": self.commit_time,
            "commit_author": self.commit_author,
            "commit_message": self.commit_message,
            "version": self.version
        }


class GitService:
    """Git服务"""
    
    @staticmethod
    def get_repository_path(repository_url: str) -> Tuple[str, str]:
        """获取仓库路径"""
        # 解析仓库地址
        parsed_url = urlparse(repository_url)
        path_segments = parsed_url.path.strip('/').split('/')
        
        if len(path_segments) < 2:
            raise ValueError("无效的仓库地址")
        
        organization = path_segments[0]
        repository_name = path_segments[1].replace('.git', '')
        
        # 拼接本地路径
        repository_path = os.path.join(settings.git.path, organization, repository_name)
        return repository_path, organization
    
    @staticmethod
    def clone_repository(repository_url: str, user_name: str = "", 
                        password: str = "", branch: str = "master") -> GitRepositoryInfo:
        """克隆仓库"""
        try:
            local_path, organization = GitService.get_repository_path(repository_url)
            repository_name = os.path.basename(repository_url).replace('.git', '')
            
            # 添加分支到路径
            local_path = os.path.join(local_path, branch)
            
            # 检查仓库是否已存在
            if os.path.exists(local_path):
                try:
                    # 获取现有仓库信息
                    repo = git.Repo(local_path)
                    head = repo.head
                    commit = head.commit
                    
                    return GitRepositoryInfo(
                        local_path=local_path,
                        repository_name=repository_name,
                        organization=organization,
                        branch_name=head.ref.name,
                        commit_time=commit.committed_datetime.isoformat(),
                        commit_author=commit.author.name,
                        commit_message=commit.message,
                        version=commit.hexsha
                    )
                except Exception as e:
                    logger.warning(f"读取现有仓库失败，重新克隆: {e}")
                    # 删除目录后重新克隆
                    shutil.rmtree(local_path, ignore_errors=True)
            
            # 创建目录
            os.makedirs(local_path, exist_ok=True)
            
            # 克隆选项
            clone_options = {
                'branch': branch,
                'depth': 0
            }
            
            # 如果有认证信息，添加到URL中
            if user_name and password:
                # 对于Token认证，用户名可以随便填
                auth_url = repository_url.replace('https://', f'https://{user_name}:{password}@')
                repo = git.Repo.clone_from(auth_url, local_path, **clone_options)
            else:
                repo = git.Repo.clone_from(repository_url, local_path, **clone_options)
            
            # 获取仓库信息
            head = repo.head
            commit = head.commit
            
            return GitRepositoryInfo(
                local_path=local_path,
                repository_name=repository_name,
                organization=organization,
                branch_name=head.ref.name,
                commit_time=commit.committed_datetime.isoformat(),
                commit_author=commit.author.name,
                commit_message=commit.message,
                version=commit.hexsha
            )
            
        except Exception as e:
            logger.error(f"克隆仓库失败: {e}")
            raise
    
    @staticmethod
    def pull_repository(repository_path: str, commit_id: str = "") -> Tuple[List[dict], str]:
        """拉取仓库更新"""
        try:
            if not os.path.exists(repository_path):
                raise Exception("仓库不存在，请先克隆仓库")
            
            repo = git.Repo(repository_path)
            
            # 拉取最新代码
            origin = repo.remotes.origin
            origin.pull()
            
            # 获取提交记录
            if commit_id:
                try:
                    # 获取从指定commitId到HEAD的所有提交记录
                    commits = []
                    for commit in repo.iter_commits(f'{commit_id}..HEAD'):
                        commits.append({
                            'sha': commit.hexsha,
                            'author': commit.author.name,
                            'email': commit.author.email,
                            'message': commit.message,
                            'committed_datetime': commit.committed_datetime.isoformat()
                        })
                    return commits, repo.head.commit.hexsha
                except Exception as e:
                    logger.warning(f"获取指定提交记录失败: {e}")
            
            # 返回所有提交记录
            commits = []
            for commit in repo.iter_commits():
                commits.append({
                    'sha': commit.hexsha,
                    'author': commit.author.name,
                    'email': commit.author.email,
                    'message': commit.message,
                    'committed_datetime': commit.committed_datetime.isoformat()
                })
            
            return commits, repo.head.commit.hexsha
            
        except Exception as e:
            logger.error(f"拉取仓库失败: {e}")
            raise
    
    @staticmethod
    def get_repository_info(repository_path: str) -> Optional[GitRepositoryInfo]:
        """获取仓库信息"""
        try:
            if not os.path.exists(repository_path):
                return None
            
            repo = git.Repo(repository_path)
            head = repo.head
            commit = head.commit
            
            # 从路径解析组织名和仓库名
            path_parts = repository_path.split(os.sep)
            if len(path_parts) >= 3:
                organization = path_parts[-3]
                repository_name = path_parts[-2]
            else:
                organization = "unknown"
                repository_name = os.path.basename(repository_path)
            
            return GitRepositoryInfo(
                local_path=repository_path,
                repository_name=repository_name,
                organization=organization,
                branch_name=head.ref.name,
                commit_time=commit.committed_datetime.isoformat(),
                commit_author=commit.author.name,
                commit_message=commit.message,
                version=commit.hexsha
            )
            
        except Exception as e:
            logger.error(f"获取仓库信息失败: {e}")
            return None
    
    @staticmethod
    def get_branches(repository_path: str) -> List[str]:
        """获取仓库分支列表"""
        try:
            if not os.path.exists(repository_path):
                return []
            
            repo = git.Repo(repository_path)
            branches = [ref.name for ref in repo.references if isinstance(ref, git.refs.RemoteReference)]
            return branches
            
        except Exception as e:
            logger.error(f"获取分支列表失败: {e}")
            return []
    
    @staticmethod
    def checkout_branch(repository_path: str, branch_name: str) -> bool:
        """切换分支"""
        try:
            if not os.path.exists(repository_path):
                return False
            
            repo = git.Repo(repository_path)
            repo.git.checkout(branch_name)
            return True
            
        except Exception as e:
            logger.error(f"切换分支失败: {e}")
            return False
    
    @staticmethod
    def get_file_content(repository_path: str, file_path: str) -> Optional[str]:
        """获取文件内容"""
        try:
            if not os.path.exists(repository_path):
                return None
            
            repo = git.Repo(repository_path)
            full_path = os.path.join(repository_path, file_path)
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取文件内容失败: {e}")
            return None
    
    @staticmethod
    def get_file_history(repository_path: str, file_path: str) -> List[dict]:
        """获取文件提交历史"""
        try:
            if not os.path.exists(repository_path):
                return []
            
            repo = git.Repo(repository_path)
            commits = []
            
            for commit in repo.iter_commits(paths=file_path):
                commits.append({
                    'sha': commit.hexsha,
                    'author': commit.author.name,
                    'email': commit.author.email,
                    'message': commit.message,
                    'committed_datetime': commit.committed_datetime.isoformat()
                })
            
            return commits
            
        except Exception as e:
            logger.error(f"获取文件历史失败: {e}")
            return [] 