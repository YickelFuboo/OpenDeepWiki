"""
AI模型工厂
支持多种AI提供商（OpenAI、Anthropic、本地模型等）
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import openai
import anthropic
import httpx
from Conf.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    provider: str
    api_key: str
    base_url: Optional[str] = None
    model: str = ""
    max_tokens: int = 4000
    temperature: float = 0.7


class AIModel(ABC):
    """AI模型抽象基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """生成嵌入向量"""
        pass


class OpenAIModel(AIModel):
    """OpenAI模型"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model or "gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI文本生成失败: {e}")
            raise
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model or "gpt-4",
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI对话生成失败: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成嵌入向量"""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI嵌入生成失败: {e}")
            raise


class AnthropicModel(AIModel):
    """Anthropic模型"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        try:
            response = await self.client.messages.create(
                model=self.config.model or "claude-3-sonnet",
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic文本生成失败: {e}")
            raise
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话"""
        try:
            response = await self.client.messages.create(
                model=self.config.model or "claude-3-sonnet",
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=messages,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic对话生成失败: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成嵌入向量"""
        try:
            response = await self.client.embeddings.create(
                model="claude-3-sonnet",
                input=text
            )
            return response.embedding
        except Exception as e:
            logger.error(f"Anthropic嵌入生成失败: {e}")
            raise


class LocalModel(AIModel):
    """本地模型"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": self.config.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                        "temperature": kwargs.get("temperature", self.config.temperature),
                        **kwargs
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"本地模型文本生成失败: {e}")
            raise
    
    async def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成对话"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": self.config.model,
                        "messages": messages,
                        "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                        "temperature": kwargs.get("temperature", self.config.temperature),
                        **kwargs
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"本地模型对话生成失败: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成嵌入向量"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/embeddings",
                    json={
                        "model": "text-embedding-ada-002",
                        "input": text
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"本地模型嵌入生成失败: {e}")
            raise


class ModelFactory:
    """AI模型工厂"""
    
    def __init__(self):
        self.settings = get_settings()
        self._models: Dict[str, AIModel] = {}
    
    def create_model(self, provider: str = None) -> AIModel:
        """创建AI模型
        
        Args:
            provider: 提供商名称，如果为None则使用默认提供商
            
        Returns:
            AIModel: AI模型实例
        """
        provider = provider or self.settings.ai.default_ai_provider
        
        if provider in self._models:
            return self._models[provider]
        
        config = self._get_model_config(provider)
        model = self._create_model_instance(provider, config)
        
        self._models[provider] = model
        logger.info(f"创建AI模型: {provider}")
        
        return model
    
    def _get_model_config(self, provider: str) -> ModelConfig:
        """获取模型配置"""
        if provider == "openai":
            return ModelConfig(
                name="OpenAI",
                provider=provider,
                api_key=self.settings.ai.openai_api_key,
                base_url=self.settings.ai.openai_base_url,
                model=self.settings.ai.openai_model,
                max_tokens=self.settings.ai.max_tokens,
                temperature=self.settings.ai.temperature
            )
        elif provider == "anthropic":
            return ModelConfig(
                name="Anthropic",
                provider=provider,
                api_key=self.settings.ai.anthropic_api_key,
                model=self.settings.ai.anthropic_model,
                max_tokens=self.settings.ai.max_tokens,
                temperature=self.settings.ai.temperature
            )
        elif provider == "local":
            return ModelConfig(
                name="Local",
                provider=provider,
                api_key="",  # 本地模型不需要API key
                base_url=self.settings.ai.local_model_url,
                model=self.settings.ai.local_model_name,
                max_tokens=self.settings.ai.max_tokens,
                temperature=self.settings.ai.temperature
            )
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")
    
    def _create_model_instance(self, provider: str, config: ModelConfig) -> AIModel:
        """创建模型实例"""
        if provider == "openai":
            return OpenAIModel(config)
        elif provider == "anthropic":
            return AnthropicModel(config)
        elif provider == "local":
            return LocalModel(config)
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")
    
    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        providers = []
        
        if self.settings.ai.openai_api_key:
            providers.append("openai")
        
        if self.settings.ai.anthropic_api_key:
            providers.append("anthropic")
        
        if self.settings.ai.local_model_url:
            providers.append("local")
        
        return providers
    
    def get_model_info(self, provider: str) -> Dict[str, Any]:
        """获取模型信息"""
        config = self._get_model_config(provider)
        return {
            "provider": provider,
            "name": config.name,
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }


# 全局模型工厂实例
_model_factory: Optional[ModelFactory] = None


def get_model_factory() -> ModelFactory:
    """获取模型工厂实例"""
    global _model_factory
    if _model_factory is None:
        _model_factory = ModelFactory()
    return _model_factory


def get_ai_model(provider: str = None) -> AIModel:
    """获取AI模型实例"""
    factory = get_model_factory()
    return factory.create_model(provider) 