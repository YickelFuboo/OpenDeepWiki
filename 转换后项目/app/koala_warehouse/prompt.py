import os
from typing import Optional


class Prompt:
    """提示词服务"""
    
    def __init__(self):
        # 获取环境变量中的语言设置
        self._language = os.getenv("LANGUAGE", "简体中文")
    
    @property
    def language(self) -> str:
        """获取语言设置"""
        return f"\nPlease communicate with me in {self._language}\n"
    
    @property
    def analyze_new_catalogue(self) -> str:
        """分析新目录的提示词"""
        return """
        You are an AI assistant tasked with updating a document structure based on changes in a code repository. Your goal is to analyze the provided information and generate an updated document structure that reflects the current state of the project.

        First, carefully review the following information:

        1. Current repository directory structure:
        <repository_structure>
        {catalogue}
        </repository_structure>

        2. Current repository information:
        <repository_info>
        {git_repository}
        </repository_info>

        3. Recent Git update content:
        <git_update>
        {git_commit}
        </git_update>

        4. Existing document structure:
        <existing_document_structure>
        {document_catalogue}
        </existing_document_structure>

        Your task is to update the document structure based on the changes in the repository. Before providing the final output, conduct a thorough analysis using the following steps:

        1. Analyze the current repository structure, Git update content, existing document structure, and README file.
        2. Identify new content that needs to be added to the document structure.
        3. Identify existing content that needs to be updated.
        4. Identify content that should be removed from the document structure.

        Wrap your analysis inside <repository_change_analysis> tags. In this analysis:

        1. List all new files added to the repository.
        2. List all modified files in the repository.
        3. List all deleted files from the repository.
        4. For each change:
           a. Specify the file change (addition, modification, or deletion).
           b. Identify which parts of the document structure this change affects.
           c. Explain how it impacts the document structure (e.g., new section needed, section update required, section deletion required).
           d. Provide reasoning for the proposed change to the document structure.
           e. Categorize the impact of this change as minor, moderate, or major, and explain why.
           f. Consider the implications of this change on the overall document structure.
        5. Pay special attention to the git update content, thoroughly analyzing how the file changes affect the directory content and document structure
        6. Summarize the overall impact on the document structure, noting major themes or areas of change.
        7. Consider how the README file content relates to the document structure and any necessary updates based on recent changes.
        8. Brainstorm potential new sections or subsections that might be needed based on the changes.

        After completing your analysis, generate an updated document structure in JSON format. Follow these guidelines:

        - Each section should have a title, name, type (add or update), dependent files, and a prompt for content creation.
        - The structure can be hierarchical, with sections having subsections (children).
        - For updated sections, include the ID of the section being updated.
        - Provide a list of IDs for sections that should be deleted.

        Your final output should be in the following JSON format:
        <document_structure>
        {
          "delete_id": [],
          "items": [
            {
              "title": "section-identifier",
              "name": "Section Name",
              "type": "add",
              "prompt": "Create comprehensive content for this section focused on [SPECIFIC PROJECT COMPONENT/FEATURE]. Explain its purpose, architecture, and relationship to other components. Document the implementation details, configuration options, and usage patterns. Include both conceptual overviews for beginners and technical details for experienced developers. Use terminology consistent with the codebase. Provide practical examples demonstrating common use cases. Document public interfaces, parameters, and return values. Include diagrams where appropriate to illustrate key concepts.",
              "children": [
                {
                  "title": "subsection-identifier",
                  "name": "Subsection Name",
                  "type": "update",
                  "id": "existing-section-id",
                  "prompt": "Develop detailed content for this subsection covering [SPECIFIC ASPECT OF PARENT COMPONENT]. Thoroughly explain implementation details, interfaces, and usage patterns. Include concrete examples from the actual codebase. Document configuration options, parameters, and return values. Explain relationships with other components. Address common issues and their solutions. Make content accessible to beginners while providing sufficient technical depth for experienced developers."
                }
              ]
            }
          ]
        }
        </document_structure>
        Please proceed with your analysis and provide the updated document structure.
        """
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """获取指定名称的提示词"""
        if prompt_name == "analyze_new_catalogue":
            return self.analyze_new_catalogue
        else:
            return None


# 创建全局实例
prompt_service = Prompt() 