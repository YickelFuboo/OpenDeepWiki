"""
仓库分类服务

根据仓库内容自动分类仓库类型
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class RepositoryType(Enum):
    """仓库类型枚举"""
    FRAMEWORK = "framework"
    LIBRARY = "library"
    APPLICATION = "application"
    CLI_TOOL = "cli_tool"
    DEVELOPMENT_TOOL = "development_tool"
    DOCUMENTATION = "documentation"
    DEVOPS_CONFIGURATION = "devops_configuration"
    UNKNOWN = "unknown"

class WarehouseClassify:
    """仓库分类器"""
    
    def __init__(self):
        self.classification_rules = self._init_classification_rules()
    
    def classify_warehouse(self, warehouse_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分类仓库
        
        Args:
            warehouse_info: 仓库信息
            
        Returns:
            分类结果
        """
        try:
            # 获取仓库文件结构
            file_structure = warehouse_info.get("file_structure", [])
            file_content = warehouse_info.get("file_content", {})
            
            # 分析文件特征
            features = self._analyze_features(file_structure, file_content)
            
            # 应用分类规则
            classification = self._apply_classification_rules(features)
            
            # 计算置信度
            confidence = self._calculate_confidence(features, classification)
            
            return {
                "repository_type": classification["type"],
                "confidence": confidence,
                "features": features,
                "reasoning": classification["reasoning"],
                "tags": classification["tags"]
            }
            
        except Exception as e:
            logger.error(f"分类仓库异常: {str(e)}")
            return {
                "repository_type": RepositoryType.UNKNOWN.value,
                "confidence": 0.0,
                "features": {},
                "reasoning": f"分类失败: {str(e)}",
                "tags": []
            }
    
    def _init_classification_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化分类规则"""
        return {
            RepositoryType.FRAMEWORK.value: {
                "keywords": ["framework", "core", "engine", "platform"],
                "file_patterns": ["*.framework", "framework.*", "core.*"],
                "content_patterns": ["framework", "architecture", "design pattern"],
                "weight": 1.0
            },
            RepositoryType.LIBRARY.value: {
                "keywords": ["library", "lib", "utils", "helpers"],
                "file_patterns": ["lib/*", "src/lib/*", "utils/*"],
                "content_patterns": ["library", "api", "function", "utility"],
                "weight": 1.0
            },
            RepositoryType.APPLICATION.value: {
                "keywords": ["app", "application", "service", "web"],
                "file_patterns": ["app/*", "src/app/*", "main.*"],
                "content_patterns": ["application", "service", "web", "ui"],
                "weight": 1.0
            },
            RepositoryType.CLI_TOOL.value: {
                "keywords": ["cli", "command", "tool", "cmd"],
                "file_patterns": ["cmd/*", "cli/*", "bin/*"],
                "content_patterns": ["cli", "command", "argument", "flag"],
                "weight": 1.0
            },
            RepositoryType.DEVELOPMENT_TOOL.value: {
                "keywords": ["dev", "build", "test", "lint"],
                "file_patterns": ["build/*", "scripts/*", "tools/*"],
                "content_patterns": ["build", "test", "lint", "dev"],
                "weight": 1.0
            },
            RepositoryType.DOCUMENTATION.value: {
                "keywords": ["docs", "documentation", "readme"],
                "file_patterns": ["docs/*", "documentation/*", "*.md"],
                "content_patterns": ["documentation", "guide", "tutorial"],
                "weight": 1.0
            },
            RepositoryType.DEVOPS_CONFIGURATION.value: {
                "keywords": ["docker", "kubernetes", "terraform", "ci"],
                "file_patterns": ["dockerfile", "docker-compose.*", "k8s/*", "terraform/*"],
                "content_patterns": ["docker", "kubernetes", "terraform", "ci/cd"],
                "weight": 1.0
            }
        }
    
    def _analyze_features(self, file_structure: List[str], file_content: Dict[str, str]) -> Dict[str, Any]:
        """分析文件特征"""
        features = {
            "file_count": len(file_structure),
            "file_types": {},
            "keywords": [],
            "patterns": [],
            "has_readme": False,
            "has_package_json": False,
            "has_requirements_txt": False,
            "has_gemfile": False,
            "has_cargo_toml": False,
            "has_go_mod": False,
            "has_pom_xml": False,
            "has_build_gradle": False,
            "has_dockerfile": False,
            "has_docker_compose": False,
            "has_kubernetes": False,
            "has_terraform": False,
            "has_github_actions": False,
            "has_travis": False,
            "has_circleci": False,
            "has_jenkins": False
        }
        
        # 分析文件类型
        for file_path in file_structure:
            file_ext = self._get_file_extension(file_path)
            features["file_types"][file_ext] = features["file_types"].get(file_ext, 0) + 1
            
            # 检查特定文件
            if file_path.lower().endswith("readme.md"):
                features["has_readme"] = True
            elif file_path.lower() == "package.json":
                features["has_package_json"] = True
            elif file_path.lower() == "requirements.txt":
                features["has_requirements_txt"] = True
            elif file_path.lower() == "gemfile":
                features["has_gemfile"] = True
            elif file_path.lower() == "cargo.toml":
                features["has_cargo_toml"] = True
            elif file_path.lower() == "go.mod":
                features["has_go_mod"] = True
            elif file_path.lower() == "pom.xml":
                features["has_pom_xml"] = True
            elif file_path.lower() == "build.gradle":
                features["has_build_gradle"] = True
            elif file_path.lower() == "dockerfile":
                features["has_dockerfile"] = True
            elif file_path.lower().startswith("docker-compose"):
                features["has_docker_compose"] = True
            elif file_path.lower().startswith("k8s/") or file_path.lower().endswith(".yaml"):
                features["has_kubernetes"] = True
            elif file_path.lower().startswith("terraform/"):
                features["has_terraform"] = True
            elif file_path.lower().startswith(".github/workflows/"):
                features["has_github_actions"] = True
            elif file_path.lower() == ".travis.yml":
                features["has_travis"] = True
            elif file_path.lower() == ".circleci/config.yml":
                features["has_circleci"] = True
            elif file_path.lower() == "jenkinsfile":
                features["has_jenkins"] = True
        
        # 分析文件内容中的关键词
        for content in file_content.values():
            features["keywords"].extend(self._extract_keywords(content))
        
        # 去重关键词
        features["keywords"] = list(set(features["keywords"]))
        
        return features
    
    def _apply_classification_rules(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """应用分类规则"""
        scores = {}
        reasoning = []
        
        for repo_type, rules in self.classification_rules.items():
            score = 0.0
            type_reasoning = []
            
            # 检查关键词匹配
            for keyword in rules["keywords"]:
                if keyword.lower() in [k.lower() for k in features["keywords"]]:
                    score += 0.3
                    type_reasoning.append(f"关键词匹配: {keyword}")
            
            # 检查文件模式匹配
            for pattern in rules["file_patterns"]:
                if any(pattern.lower() in f.lower() for f in features.get("file_types", {}).keys()):
                    score += 0.2
                    type_reasoning.append(f"文件模式匹配: {pattern}")
            
            # 检查内容模式匹配
            for pattern in rules["content_patterns"]:
                if pattern.lower() in [k.lower() for k in features["keywords"]]:
                    score += 0.2
                    type_reasoning.append(f"内容模式匹配: {pattern}")
            
            # 特殊规则
            if repo_type == RepositoryType.DEVOPS_CONFIGURATION.value:
                if features.get("has_dockerfile") or features.get("has_kubernetes") or features.get("has_terraform"):
                    score += 0.5
                    type_reasoning.append("DevOps配置文件检测")
            
            elif repo_type == RepositoryType.DOCUMENTATION.value:
                if features.get("has_readme") and features["file_count"] < 10:
                    score += 0.4
                    type_reasoning.append("文档仓库特征")
            
            elif repo_type == RepositoryType.CLI_TOOL.value:
                if any("cmd" in f.lower() or "cli" in f.lower() for f in features.get("file_types", {}).keys()):
                    score += 0.3
                    type_reasoning.append("CLI工具特征")
            
            scores[repo_type] = score
            if type_reasoning:
                reasoning.append(f"{repo_type}: {'; '.join(type_reasoning)}")
        
        # 选择得分最高的类型
        best_type = max(scores.items(), key=lambda x: x[1])
        
        return {
            "type": best_type[0],
            "score": best_type[1],
            "reasoning": reasoning,
            "tags": self._generate_tags(features, best_type[0])
        }
    
    def _calculate_confidence(self, features: Dict[str, Any], classification: Dict[str, Any]) -> float:
        """计算分类置信度"""
        base_confidence = classification["score"]
        
        # 根据特征数量调整置信度
        if features["file_count"] > 100:
            base_confidence += 0.1
        elif features["file_count"] < 10:
            base_confidence -= 0.1
        
        # 根据关键词数量调整置信度
        if len(features["keywords"]) > 20:
            base_confidence += 0.1
        elif len(features["keywords"]) < 5:
            base_confidence -= 0.1
        
        return min(1.0, max(0.0, base_confidence))
    
    def _generate_tags(self, features: Dict[str, Any], repo_type: str) -> List[str]:
        """生成标签"""
        tags = [repo_type]
        
        # 根据文件类型添加标签
        file_types = features.get("file_types", {})
        if ".js" in file_types or ".ts" in file_types:
            tags.append("javascript")
        if ".py" in file_types:
            tags.append("python")
        if ".go" in file_types:
            tags.append("golang")
        if ".java" in file_types:
            tags.append("java")
        if ".cs" in file_types:
            tags.append("csharp")
        if ".rs" in file_types:
            tags.append("rust")
        
        # 根据特征添加标签
        if features.get("has_dockerfile"):
            tags.append("docker")
        if features.get("has_kubernetes"):
            tags.append("kubernetes")
        if features.get("has_terraform"):
            tags.append("terraform")
        if features.get("has_github_actions"):
            tags.append("github-actions")
        
        return tags
    
    def _get_file_extension(self, file_path: str) -> str:
        """获取文件扩展名"""
        import os
        return os.path.splitext(file_path)[1]
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 简化实现，实际可以使用更复杂的NLP技术
        keywords = []
        
        # 常见的技术关键词
        tech_keywords = [
            "framework", "library", "application", "service", "api", "web", "mobile",
            "database", "cache", "queue", "message", "event", "stream", "batch",
            "test", "unit", "integration", "e2e", "mock", "stub", "fixture",
            "build", "deploy", "release", "version", "tag", "branch", "merge",
            "docker", "kubernetes", "terraform", "ansible", "jenkins", "gitlab",
            "github", "bitbucket", "travis", "circleci", "teamcity", "bamboo",
            "monitoring", "logging", "metrics", "alerting", "dashboard",
            "security", "authentication", "authorization", "encryption", "ssl",
            "performance", "optimization", "scalability", "availability", "reliability"
        ]
        
        content_lower = content.lower()
        for keyword in tech_keywords:
            if keyword in content_lower:
                keywords.append(keyword)
        
        return keywords 