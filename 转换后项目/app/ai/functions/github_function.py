import httpx
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from semantic_kernel import kernel_function

from src.conf.settings import settings
from src.infrastructure.document_context import DocumentContext


@dataclass
class GithubUser:
    """GitHub用户信息"""
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
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
    site_admin: bool
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    hireable: Optional[bool] = None
    twitter_username: Optional[str] = None
    public_repos: Optional[int] = None
    public_gists: Optional[int] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class GithubIssue:
    """GitHub Issue信息"""
    url: str
    repository_url: str
    labels_url: str
    comments_url: str
    events_url: str
    html_url: str
    id: int
    node_id: str
    number: int
    title: str
    user: GithubUser
    labels: List[dict]
    state: str
    locked: bool
    assignee: Optional[GithubUser]
    assignees: List[GithubUser]
    milestone: Optional[dict]
    comments: int
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    author_association: str
    active_lock_reason: Optional[str]
    body: Optional[str]
    reactions: dict
    timeline_url: str
    performed_via_github_app: Optional[bool]
    state_reason: Optional[str]


@dataclass
class GithubIssueComment:
    """GitHub Issue评论信息"""
    url: str
    html_url: str
    issue_url: str
    id: int
    node_id: str
    user: GithubUser
    created_at: str
    updated_at: str
    author_association: str
    body: str
    reactions: dict


class GithubFunction:
    """GitHub相关功能"""
    
    def __init__(self, owner: str, name: str, branch: str):
        self.owner = owner
        self.name = name
        self.branch = branch
        self.base_url = "https://api.github.com"
    
    def _get_headers(self):
        """获取请求头"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "KoalaWiki/1.0"
        }
        
        if hasattr(settings, 'github') and settings.github.token:
            headers["Authorization"] = f"token {settings.github.token}"
        
        return headers
    
    @kernel_function(
        name="SearchIssues",
        description="搜索相关 Issue 内容"
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
            async with httpx.AsyncClient() as client:
                # 构建搜索查询
                search_query = f"{query} repo:{self.owner}/{self.name} is:issue"
                url = f"{self.base_url}/search/issues"
                params = {
                    "q": search_query,
                    "per_page": max_results,
                    "sort": "updated",
                    "order": "desc"
                }
                
                response = await client.get(url, params=params, headers=self._get_headers())
                
                if not response.is_success:
                    return f"GitHub API 请求失败: {response.status_code}"
                
                search_result = response.json()
                issues_data = search_result.get("items", [])
                
                if not issues_data:
                    return "未找到相关 Issue。"
                
                # 构建结果字符串
                result_lines = []
                for issue_data in issues_data:
                    issue = GithubIssue(**issue_data)
                    result_lines.append(f"[{issue.title}]({issue.html_url}) # {issue.number} - {issue.state}")
                
                # 保存到文档上下文
                if hasattr(DocumentContext, 'document_store') and DocumentContext.document_store:
                    for issue_data in issues_data:
                        issue = GithubIssue(**issue_data)
                        git_issue_item = {
                            "author": issue.user.name or issue.user.login,
                            "title": issue.title,
                            "url": issue.url,
                            "content": issue.body or "",
                            "created_at": datetime.fromisoformat(issue.created_at.replace('Z', '+00:00')) if issue.created_at else None,
                            "url_html": issue.html_url,
                            "state": issue.state,
                            "number": str(issue.number)
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
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/repos/{self.owner}/{self.name}/issues/{issue_number}/comments"
                params = {
                    "per_page": max_results
                }
                
                response = await client.get(url, params=params, headers=self._get_headers())
                
                if not response.is_success:
                    return f"GitHub API 请求失败: {response.status_code}"
                
                comments_data = response.json()
                
                if not comments_data:
                    return "未找到相关评论。"
                
                # 构建结果字符串
                result_lines = [f"Issue #{issue_number} 评论：\n"]
                
                for comment_data in comments_data:
                    comment = GithubIssueComment(**comment_data)
                    result_lines.append(f"  创建时间: {comment.created_at}")
                    result_lines.append(f"- [{comment.user.login}]({comment.user.html_url}): {comment.body}")
                
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
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/repos/{self.owner}/{self.name}"
                
                response = await client.get(url, headers=self._get_headers())
                
                if not response.is_success:
                    return f"GitHub API 请求失败: {response.status_code}"
                
                repo_data = response.json()
                
                info_lines = [
                    f"# {repo_data.get('name', '')}",
                    f"**描述**: {repo_data.get('description', '无描述')}",
                    f"**语言**: {repo_data.get('language', '未知')}",
                    f"**星标数**: {repo_data.get('stargazers_count', 0)}",
                    f"**Fork数**: {repo_data.get('forks_count', 0)}",
                    f"**开放Issue数**: {repo_data.get('open_issues_count', 0)}",
                    f"**默认分支**: {repo_data.get('default_branch', 'main')}",
                    f"**创建时间**: {repo_data.get('created_at', '')}",
                    f"**最后更新**: {repo_data.get('updated_at', '')}",
                    f"**仓库地址**: {repo_data.get('html_url', '')}",
                    f"**克隆地址**: {repo_data.get('clone_url', '')}"
                ]
                
                return "\n".join(info_lines)
                
        except Exception as e:
            return f"获取仓库信息失败: {str(e)}" 