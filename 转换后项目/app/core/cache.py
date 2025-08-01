from typing import Any, Optional
import asyncio
from datetime import datetime, timedelta
from loguru import logger


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            # 检查是否过期
            if key in self._expiry:
                if datetime.now() > self._expiry[key]:
                    del self._cache[key]
                    del self._expiry[key]
                    return None
            
            return self._cache[key]
    
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> None:
        """设置缓存值"""
        async with self._lock:
            self._cache[key] = value
            if expire_seconds:
                self._expiry[key] = datetime.now() + timedelta(seconds=expire_seconds)
            elif key in self._expiry:
                del self._expiry[key]
    
    async def delete(self, key: str) -> None:
        """删除缓存值"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
    
    async def clear(self) -> None:
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        async with self._lock:
            if key not in self._cache:
                return False
            
            # 检查是否过期
            if key in self._expiry:
                if datetime.now() > self._expiry[key]:
                    del self._cache[key]
                    del self._expiry[key]
                    return False
            
            return True
    
    async def get_or_set(self, key: str, default_func, expire_seconds: Optional[int] = None) -> Any:
        """获取缓存值，如果不存在则设置默认值"""
        value = await self.get(key)
        if value is None:
            if asyncio.iscoroutinefunction(default_func):
                value = await default_func()
            else:
                value = default_func()
            await self.set(key, value, expire_seconds)
        return value


# 创建全局缓存实例
cache = MemoryCache() 