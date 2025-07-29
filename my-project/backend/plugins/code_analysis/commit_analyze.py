"""
提交分析插件

分析Git提交信息，提取代码变更和影响
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class CommitAnalyzePlugin:
    """提交分析插件"""
    
    def __init__(self):
        self.commit_patterns = {
            "feature": r"(feat|feature|add|new)",
            "bugfix": r"(fix|bug|bugfix|repair)",
            "refactor": r"(refactor|refactoring|improve)",
            "docs": r"(doc|docs|documentation|readme)",
            "test": r"(test|testing|spec)",
            "style": r"(style|format|lint)",
            "perf": r"(perf|performance|optimize)",
            "chore": r"(chore|maintenance|cleanup)"
        }
    
    @sk_function(
        description="分析Git提交信息",
        name="analyze_commit"
    )
    def analyze_commit(self, context: Dict[str, Any]) -> str:
        """
        分析Git提交信息
        
        Args:
            context: 包含提交信息的上下文
            
        Returns:
            分析结果
        """
        try:
            # 获取提交信息
            commit_message = context.get("commit_message", "")
            commit_hash = context.get("commit_hash", "")
            author = context.get("author", "")
            date = context.get("date", "")
            files_changed = context.get("files_changed", [])
            lines_added = context.get("lines_added", 0)
            lines_deleted = context.get("lines_deleted", 0)
            
            # 分析提交类型
            commit_type = self._analyze_commit_type(commit_message)
            
            # 分析影响范围
            impact_analysis = self._analyze_impact(files_changed, lines_added, lines_deleted)
            
            # 生成分析报告
            analysis_report = self._generate_analysis_report(
                commit_message, commit_hash, author, date,
                commit_type, impact_analysis, files_changed
            )
            
            return analysis_report
            
        except Exception as e:
            logger.error(f"分析提交异常: {str(e)}")
            return f"分析提交时发生错误: {str(e)}"
    
    @sk_function(
        description="分析提交历史趋势",
        name="analyze_commit_trends"
    )
    def analyze_commit_trends(self, context: Dict[str, Any]) -> str:
        """
        分析提交历史趋势
        
        Args:
            context: 包含提交历史的上下文
            
        Returns:
            趋势分析结果
        """
        try:
            commits = context.get("commits", [])
            
            # 分析趋势
            trends = self._analyze_trends(commits)
            
            # 生成趋势报告
            trend_report = self._generate_trend_report(trends)
            
            return trend_report
            
        except Exception as e:
            logger.error(f"分析提交趋势异常: {str(e)}")
            return f"分析提交趋势时发生错误: {str(e)}"
    
    @sk_function(
        description="生成提交建议",
        name="generate_commit_suggestions"
    )
    def generate_commit_suggestions(self, context: Dict[str, Any]) -> str:
        """
        生成提交建议
        
        Args:
            context: 包含代码变更的上下文
            
        Returns:
            提交建议
        """
        try:
            files_changed = context.get("files_changed", [])
            changes_summary = context.get("changes_summary", "")
            
            # 分析变更类型
            change_types = self._analyze_change_types(files_changed)
            
            # 生成建议
            suggestions = self._generate_suggestions(change_types, changes_summary)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成提交建议异常: {str(e)}")
            return f"生成提交建议时发生错误: {str(e)}"
    
    def _analyze_commit_type(self, commit_message: str) -> Dict[str, Any]:
        """分析提交类型"""
        commit_type = {
            "type": "unknown",
            "confidence": 0.0,
            "keywords": []
        }
        
        message_lower = commit_message.lower()
        
        # 检查各种提交类型
        for type_name, pattern in self.commit_patterns.items():
            if re.search(pattern, message_lower):
                commit_type["type"] = type_name
                commit_type["confidence"] = 0.8
                commit_type["keywords"].append(type_name)
                break
        
        # 如果没有匹配到特定类型，进行更详细的分析
        if commit_type["type"] == "unknown":
            if any(word in message_lower for word in ["update", "change", "modify"]):
                commit_type["type"] = "update"
                commit_type["confidence"] = 0.6
            elif any(word in message_lower for word in ["remove", "delete", "drop"]):
                commit_type["type"] = "remove"
                commit_type["confidence"] = 0.7
            elif any(word in message_lower for word in ["merge", "rebase"]):
                commit_type["type"] = "merge"
                commit_type["confidence"] = 0.9
        
        return commit_type
    
    def _analyze_impact(self, files_changed: List[str], lines_added: int, lines_deleted: int) -> Dict[str, Any]:
        """分析影响范围"""
        impact = {
            "severity": "low",
            "scope": "local",
            "risk_level": "low",
            "affected_areas": []
        }
        
        # 分析影响严重程度
        total_changes = lines_added + lines_deleted
        if total_changes > 1000:
            impact["severity"] = "high"
            impact["risk_level"] = "high"
        elif total_changes > 100:
            impact["severity"] = "medium"
            impact["risk_level"] = "medium"
        
        # 分析影响范围
        if len(files_changed) > 20:
            impact["scope"] = "global"
        elif len(files_changed) > 5:
            impact["scope"] = "module"
        else:
            impact["scope"] = "local"
        
        # 分析受影响的区域
        for file_path in files_changed:
            if "test" in file_path.lower():
                impact["affected_areas"].append("testing")
            elif "doc" in file_path.lower():
                impact["affected_areas"].append("documentation")
            elif "config" in file_path.lower():
                impact["affected_areas"].append("configuration")
            elif "api" in file_path.lower():
                impact["affected_areas"].append("api")
            elif "ui" in file_path.lower() or "view" in file_path.lower():
                impact["affected_areas"].append("user_interface")
            else:
                impact["affected_areas"].append("core_logic")
        
        # 去重
        impact["affected_areas"] = list(set(impact["affected_areas"]))
        
        return impact
    
    def _analyze_trends(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析提交趋势"""
        trends = {
            "commit_frequency": {},
            "type_distribution": {},
            "author_activity": {},
            "file_change_patterns": {},
            "time_patterns": {}
        }
        
        # 分析提交频率
        dates = [commit.get("date", "") for commit in commits]
        trends["commit_frequency"] = self._analyze_frequency(dates)
        
        # 分析类型分布
        types = [commit.get("type", "unknown") for commit in commits]
        trends["type_distribution"] = self._analyze_distribution(types)
        
        # 分析作者活动
        authors = [commit.get("author", "") for commit in commits]
        trends["author_activity"] = self._analyze_author_activity(authors)
        
        # 分析文件变更模式
        all_files = []
        for commit in commits:
            all_files.extend(commit.get("files_changed", []))
        trends["file_change_patterns"] = self._analyze_file_patterns(all_files)
        
        return trends
    
    def _analyze_change_types(self, files_changed: List[str]) -> Dict[str, Any]:
        """分析变更类型"""
        change_types = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "file_types": {},
            "modules_affected": set()
        }
        
        for file_path in files_changed:
            # 分析文件类型
            file_ext = self._get_file_extension(file_path)
            change_types["file_types"][file_ext] = change_types["file_types"].get(file_ext, 0) + 1
            
            # 分析模块影响
            module = self._extract_module(file_path)
            if module:
                change_types["modules_affected"].add(module)
        
        change_types["modules_affected"] = list(change_types["modules_affected"])
        
        return change_types
    
    def _generate_analysis_report(self, commit_message: str, commit_hash: str, author: str, 
                                 date: str, commit_type: Dict[str, Any], impact: Dict[str, Any], 
                                 files_changed: List[str]) -> str:
        """生成分析报告"""
        report = f"""
# 提交分析报告

## 基本信息
- **提交哈希**: {commit_hash}
- **作者**: {author}
- **日期**: {date}
- **提交信息**: {commit_message}

## 提交类型分析
- **类型**: {commit_type['type']}
- **置信度**: {commit_type['confidence']}
- **关键词**: {', '.join(commit_type['keywords'])}

## 影响范围分析
- **严重程度**: {impact['severity']}
- **影响范围**: {impact['scope']}
- **风险等级**: {impact['risk_level']}
- **受影响区域**: {', '.join(impact['affected_areas'])}

## 文件变更
- **变更文件数**: {len(files_changed)}
- **变更文件列表**:
"""
        
        for file_path in files_changed:
            report += f"  - {file_path}\n"
        
        report += "\n## 建议\n"
        
        # 根据分析结果生成建议
        if impact['severity'] == 'high':
            report += "- 建议进行详细的代码审查\n"
            report += "- 建议运行完整的测试套件\n"
            report += "- 建议进行性能测试\n"
        
        if impact['scope'] == 'global':
            report += "- 建议通知相关团队成员\n"
            report += "- 建议更新相关文档\n"
        
        return report
    
    def _generate_trend_report(self, trends: Dict[str, Any]) -> str:
        """生成趋势报告"""
        report = """
# 提交趋势分析报告

## 提交频率分析
"""
        
        for period, count in trends.get("commit_frequency", {}).items():
            report += f"- {period}: {count} 次提交\n"
        
        report += "\n## 提交类型分布\n"
        for commit_type, count in trends.get("type_distribution", {}).items():
            report += f"- {commit_type}: {count} 次\n"
        
        report += "\n## 作者活动分析\n"
        for author, activity in trends.get("author_activity", {}).items():
            report += f"- {author}: {activity} 次提交\n"
        
        return report
    
    def _generate_suggestions(self, change_types: Dict[str, Any], changes_summary: str) -> str:
        """生成提交建议"""
        suggestions = """
# 提交建议

## 基于变更类型的建议
"""
        
        if change_types.get("file_types", {}).get(".test", 0) > 0:
            suggestions += "- 包含测试文件变更，建议验证测试覆盖率\n"
        
        if change_types.get("file_types", {}).get(".md", 0) > 0:
            suggestions += "- 包含文档变更，建议检查文档完整性\n"
        
        if change_types.get("file_types", {}).get(".config", 0) > 0:
            suggestions += "- 包含配置变更，建议验证配置正确性\n"
        
        if len(change_types.get("modules_affected", [])) > 3:
            suggestions += "- 影响多个模块，建议进行集成测试\n"
        
        suggestions += f"\n## 变更摘要\n{changes_summary}\n"
        
        return suggestions
    
    def _analyze_frequency(self, dates: List[str]) -> Dict[str, int]:
        """分析频率"""
        frequency = {}
        for date in dates:
            if date:
                # 简化实现，实际可以按天、周、月统计
                frequency[date[:10]] = frequency.get(date[:10], 0) + 1
        return frequency
    
    def _analyze_distribution(self, types: List[str]) -> Dict[str, int]:
        """分析分布"""
        distribution = {}
        for commit_type in types:
            distribution[commit_type] = distribution.get(commit_type, 0) + 1
        return distribution
    
    def _analyze_author_activity(self, authors: List[str]) -> Dict[str, int]:
        """分析作者活动"""
        activity = {}
        for author in authors:
            activity[author] = activity.get(author, 0) + 1
        return activity
    
    def _analyze_file_patterns(self, files: List[str]) -> Dict[str, int]:
        """分析文件模式"""
        patterns = {}
        for file_path in files:
            ext = self._get_file_extension(file_path)
            patterns[ext] = patterns.get(ext, 0) + 1
        return patterns
    
    def _get_file_extension(self, file_path: str) -> str:
        """获取文件扩展名"""
        import os
        return os.path.splitext(file_path)[1]
    
    def _extract_module(self, file_path: str) -> Optional[str]:
        """提取模块名"""
        parts = file_path.split('/')
        if len(parts) > 1:
            return parts[0]
        return None 