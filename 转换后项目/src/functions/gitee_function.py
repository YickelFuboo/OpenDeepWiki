import json
import httpx
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from semantic_kernel import kernel_function

from src.core.config import settings
from src.infrastructure.document_context import DocumentContext


@dataclass
class GiteeUser:
    """Gitee用户信息"""
    id: int
    login: str
    name: str
    avatar_url: str
    url: str
    html_url: str
    remark: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str


@dataclass
class GiteeIssue:
    """Gitee Issue信息"""
    id: int
    url: str
    repository_url: str
    labels_url: str
    comments_url: str
    html_url: str
    parent_url: Optional[str]
    number: str
    parent_id: int
    depth: int
    state: str
    title: str
    body: str
    user: GiteeUser
    repository: dict
    milestone: Optional[dict]
    created_at: str
    updated_at: str
    plan_started_at: Optional[str]
    deadline: Optional[str]
    finished_at: Optional[str]
    scheduled_time: int
    comments: int
    priority: int
    issue_type: str
    program: Optional[dict]
    security_hole: bool
    issue_state: str
    branch: Optional[str]
    issue_type_detail: dict
    issue_state_detail: dict


@dataclass
class GiteeIssueComment:
    """Gitee Issue评论信息"""
    id: int
    body: str
    user: GiteeUser
    source: Optional[dict]
    target: Optional[dict]
    created_at: str
    updated_at: str


class GiteeFunction:
    """Gitee相关功能"""
    
    def __init__(self, owner: str, name: str, branch: str):
        self.owner = owner
        self.name = name
        self.branch = branch
        self.base_url = "https://gitee.com/api/v5"
    
    @kernel_function(
        name="SearchIssues",
        description="搜索 Issue 内容"
    )
    async def search_issues_async(
        self,
        query: str,
        max_results: int = 5
    ) -> str:
        """
        搜索相关issue内容
        
        Args:
            query: 搜索关键词
            max_results: 最大返回数量
        """
        try:
            if not hasattr(settings, 'gitee') or not settings.gitee.token:
                return "未配置 Gitee Token，无法搜索 Issue。"
            
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/repos/{self.owner}/{self.name}/issues"
                params = {
                    "page": 1,
                    "per_page": max_results,
                    "access_token": settings.gitee.token,
                    "q": query
                }
                
                response = await client.get(url, params=params)
                
                if not response.is_success:
                    return f"Gitee API 请求失败: {response.status_code}"
                
                issues_data = response.json()
                if not issues_data:
                    return "未找到相关 Issue。"
                
                # 构建结果字符串
                result_lines = []
                for issue_data in issues_data:
                    issue = GiteeIssue(**issue_data)
                    result_lines.append(f"[{issue.title}]({issue.html_url}) # {issue.number} - {issue.state}")
                
                # 保存到文档上下文
                if hasattr(DocumentContext, 'document_store') and DocumentContext.document_store:
                    for issue_data in issues_data:
                        issue = GiteeIssue(**issue_data)
                        git_issue_item = {
                            "author": issue.user.name,
                            "title": issue.title,
                            "url": issue.url,
                            "content": issue.body,
                            "created_at": datetime.fromisoformat(issue.created_at.replace('Z', '+00:00')) if issue.created_at else None,
                            "url_html": issue.html_url,
                            "state": issue.state,
                            "number": issue.number
                        }
                        DocumentContext.document_store.git_issues.append(git_issue_item)
                
                return "\n".join(result_lines)
                
        except Exception as e:
            return f"搜索 Issue 失败: {str(e)}"
    
    @kernel_function(
        name="SearchIssueComments",
        description="搜索指定编号 Issue 评论内容"
    )
    async def search_issue_comments_async(
        self,
        issue_number: int,
        max_results: int = 5
    ) -> str:
        """
        搜索指定的一个issue下评论内容
        
        Args:
            issue_number: Issue编号
            max_results: 最大返回数量
        """
        try:
            if not hasattr(settings, 'gitee') or not settings.gitee.token:
                return "未配置 Gitee Token，无法搜索 Issue 评论。"
            
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/repos/{self.owner}/{self.name}/issues/{issue_number}/comments"
                params = {
                    "access_token": settings.gitee.token,
                    "page": 1,
                    "per_page": max_results
                }
                
                response = await client.get(url, params=params)
                
                if not response.is_success:
                    return f"Gitee API 请求失败: {response.status_code}"
                
                comments_data = response.json()
                if not comments_data:
                    return "未找到相关评论。"
                
                # 构建结果字符串
                result_lines = [f"Issue #{issue_number} 评论：\n"]
                
                for comment_data in comments_data:
                    comment = GiteeIssueComment(**comment_data)
                    result_lines.append(f"  创建时间: {comment.created_at}")
                    result_lines.append(f"- [{comment.user.name}]({comment.user.html_url}): {comment.body}")
                
                return "\n".join(result_lines)
                
        except Exception as e:
            return f"搜索 Issue 评论失败: {str(e)}"
    
    @kernel_function(
        name="GetRepositoryInfo",
        description="获取仓库信息"
    )
    async def get_repository_info_async(self) -> str:
        """获取仓库基本信息"""
        try:
            if not hasattr(settings, 'gitee') or not settings.gitee.token:
                return "未配置 Gitee Token，无法获取仓库信息。"
            
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/repos/{self.owner}/{self.name}"
                params = {
                    "access_token": settings.gitee.token
                }
                
                response = await client.get(url, params=params)
                
                if not response.is_success:
                    return f"Gitee API 请求失败: {response.status_code}"
                
                repo_data = response.json()
                
                info_lines = [
                    f"# {repo_data.get('human_name', repo_data.get('name', ''))}",
                    f"**描述**: {repo_data.get('description', '无描述')}",
                    f"**语言**: {repo_data.get('language', '未知')}",
                    f"**星标数**: {repo_data.get('stargazers_count', 0)}",
                    f"**Fork数**: {repo_data.get('forks_count', 0)}",
                    f"**开放Issue数**: {repo_data.get('open_issues_count', 0)}",
                    f"**默认分支**: {repo_data.get('default_branch', 'main')}",
                    f"**创建时间**: {repo_data.get('created_at', '')}",
                    f"**最后更新**: {repo_data.get('updated_at', '')}",
                    f"**仓库地址**: {repo_data.get('html_url', '')}"
                ]
                
                return "\n".join(info_lines)
                
        except Exception as e:
            return f"获取仓库信息失败: {str(e)}" 