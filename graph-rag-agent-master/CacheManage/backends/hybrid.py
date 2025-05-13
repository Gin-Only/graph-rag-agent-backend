from typing import Any, Optional, Set
from .base import CacheStorageBackend
from .memory import MemoryCacheBackend
from .disk import DiskCacheBackend


class HybridCacheBackend(CacheStorageBackend):
    """混合缓存后端实现（内存+磁盘）"""
    
    def __init__(self, cache_dir: str = "./cache", memory_max_size: int = 100, disk_max_size: int = 1000):
        """
        初始化混合缓存后端
        
        参数:
            cache_dir: 缓存目录
            memory_max_size: 内存缓存最大项数
            disk_max_size: 磁盘缓存最大项数
        """
        self.memory_cache = MemoryCacheBackend(max_size=memory_max_size)
        self.disk_cache = DiskCacheBackend(cache_dir=cache_dir, max_size=disk_max_size)
        self.memory_hits = 0
        self.disk_hits = 0
        self.misses = 0
        self.frequent_keys: Set[str] = set()  # 跟踪频繁访问的键
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存项，先检查内存再检查磁盘
        
        参数:
            key: 缓存键
            
        返回:
            Optional[Any]: 缓存项值，不存在则返回None
        """
        # 首先检查内存缓存
        value = self.memory_cache.get(key)
        if value is not None:
            self.memory_hits += 1
            return value
        
        # 如果内存中没有，检查磁盘缓存
        value = self.disk_cache.get(key)
        if value is not None:
            self.disk_hits += 1
            
            # 检查是否是高质量缓存项，优先加入内存
            is_high_quality = False
            if isinstance(value, dict) and "metadata" in value:
                metadata = value.get("metadata", {})
                is_high_quality = metadata.get("user_verified", False) or metadata.get("fast_path_eligible", False)
            
            # 将磁盘中的项添加到内存缓存，优先考虑高质量项
            if is_high_quality:
                self.memory_cache.set(key, value)
            
            return value
            
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        设置缓存项，同时更新内存和磁盘缓存
        
        参数:
            key: 缓存键
            value: 缓存值
        """
        # 检查是否是高质量缓存项
        is_high_quality = False
        if isinstance(value, dict) and "metadata" in value:
            metadata = value.get("metadata", {})
            is_high_quality = metadata.get("user_verified", False) or metadata.get("fast_path_eligible", False)
        
        # 总是更新磁盘缓存
        self.disk_cache.set(key, value)
        
        # 高质量项总是加入内存缓存
        if is_high_quality:
            self.memory_cache.set(key, value)
        else:
            # 非高质量项根据策略决定是否加入内存
            self.memory_cache.set(key, value)
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        参数:
            key: 缓存键
            
        返回:
            bool: 是否成功删除
        """
        memory_success = self.memory_cache.delete(key)
        disk_success = self.disk_cache.delete(key)
        return memory_success or disk_success
    
    def clear(self) -> None:
        """清空缓存"""
        self.memory_cache.clear()
        self.disk_cache.clear()