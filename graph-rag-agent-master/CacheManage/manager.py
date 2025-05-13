import time
from typing import Any, Dict, Optional, Callable

from .strategies import CacheKeyStrategy, SimpleCacheKeyStrategy, ContextAwareCacheKeyStrategy, ContextAndKeywordAwareCacheKeyStrategy
from .backends import CacheStorageBackend, MemoryCacheBackend, HybridCacheBackend, ThreadSafeCacheBackend
from .models import CacheItem


class CacheManager:
    """统一缓存管理器，提供高级缓存功能"""
    
    def __init__(self, 
             key_strategy: CacheKeyStrategy = None, 
             storage_backend: CacheStorageBackend = None,
             cache_dir: str = "./cache",
             memory_only: bool = False,
             max_memory_size: int = 100,
             max_disk_size: int = 1000,
             thread_safe: bool = True):
        # 设置缓存键策略
        self.key_strategy = key_strategy or SimpleCacheKeyStrategy()
        
        # 设置存储后端
        backend = None
        if storage_backend:
            backend = storage_backend
        elif memory_only:
            backend = MemoryCacheBackend(max_size=max_memory_size)
        else:
            backend = HybridCacheBackend(
                cache_dir=cache_dir,
                memory_max_size=max_memory_size,
                disk_max_size=max_disk_size
            )
        
        # 如果需要线程安全，添加包装器
        if thread_safe:
            self.storage = ThreadSafeCacheBackend(backend)
        else:
            self.storage = backend
        
        # 性能指标收集
        self.performance_metrics = {}
    
    def _get_consistent_key(self, query: str, **kwargs) -> str:
        """
        生成一致的缓存键，确保不同方法间的键生成逻辑一致
        
        参数:
            query: 查询内容
            **kwargs: 其他参数，如thread_id、关键词等
            
        返回:
            str: 生成的一致缓存键
        """
        return self.key_strategy.generate_key(query, **kwargs)
    
    def get(self, query: str, skip_validation: bool = False, **kwargs) -> Optional[Any]:
        """
        获取缓存内容
        
        参数:
            query: 查询字符串
            skip_validation: 是否跳过验证
            **kwargs: 其他参数，传递给缓存键策略
        
        返回:
            Optional[Any]: 缓存内容，不存在则返回None
        """
        start_time = time.time()
        
        # 生成缓存键
        key = self._get_consistent_key(query, **kwargs)
        
        # 获取缓存项
        cached_data = self.storage.get(key)
        if cached_data is None:
            self.performance_metrics["get_time"] = time.time() - start_time
            return None
        
        # 包装为缓存项
        cache_item = CacheItem.from_any(cached_data)
        
        # 更新访问统计
        cache_item.update_access_stats()
        
        # 如果是高质量缓存或跳过验证，直接返回内容
        if skip_validation or cache_item.is_high_quality():
            content = cache_item.get_content()
            self.performance_metrics["get_time"] = time.time() - start_time
            return content
        
        # 返回缓存内容
        content = cache_item.get_content()
        self.performance_metrics["get_time"] = time.time() - start_time
        return content
    
    def get_fast(self, query: str, **kwargs) -> Optional[Any]:
        """
        快速获取高质量缓存内容
        
        参数:
            query: 查询字符串
            **kwargs: 其他参数，传递给缓存键策略
        
        返回:
            Optional[Any]: 缓存内容，非高质量缓存则返回None
        """
        start_time = time.time()
        
        # 生成缓存键
        key = self._get_consistent_key(query, **kwargs)
        
        # 获取缓存项
        cached_data = self.storage.get(key)
        if cached_data is None:
            self.performance_metrics["fast_get_time"] = time.time() - start_time
            return None
        
        # 包装为缓存项
        cache_item = CacheItem.from_any(cached_data)
        
        # 只返回高质量缓存
        if cache_item.is_high_quality():
            # 更新访问统计
            cache_item.update_access_stats()
            
            # 如果是上下文感知的策略，更新历史
            if isinstance(self.key_strategy, ContextAwareCacheKeyStrategy) or \
            isinstance(self.key_strategy, ContextAndKeywordAwareCacheKeyStrategy):
                thread_id = kwargs.get("thread_id", "default")
                self.key_strategy.update_history(query, thread_id)
            
            content = cache_item.get_content()
            self.performance_metrics["fast_get_time"] = time.time() - start_time
            return content
        
        self.performance_metrics["fast_get_time"] = time.time() - start_time
        return None
    
    def set(self, query: str, result: Any, **kwargs) -> None:
        """
        设置缓存内容
        
        参数:
            query: 查询字符串
            result: 缓存内容
            **kwargs: 其他参数，传递给缓存键策略
        """
        start_time = time.time()
        
        # 如果key_strategy是上下文感知的，更新会话历史
        if isinstance(self.key_strategy, (ContextAwareCacheKeyStrategy, ContextAndKeywordAwareCacheKeyStrategy)):
            thread_id = kwargs.get("thread_id", "default")
            self.key_strategy.update_history(query, thread_id)
        
        # 生成缓存键
        key = self._get_consistent_key(query, **kwargs)
        
        # 包装缓存项
        if isinstance(result, dict) and "content" in result and "metadata" in result:
            # 已经是缓存项格式
            cache_item = CacheItem.from_dict(result)
        else:
            # 创建新的缓存项
            cache_item = CacheItem(result)
        
        # 存储缓存项
        self.storage.set(key, cache_item.to_dict())
        
        self.performance_metrics["set_time"] = time.time() - start_time
    
    def mark_quality(self, query: str, is_positive: bool, **kwargs) -> bool:
        """
        标记缓存质量
        
        参数:
            query: 查询字符串
            is_positive: 是否为正面评价
            **kwargs: 其他参数，传递给缓存键策略
        
        返回:
            bool: 是否成功标记
        """
        start_time = time.time()
        
        # 生成缓存键
        key = self._get_consistent_key(query, **kwargs)
        
        # 获取缓存项
        cached_data = self.storage.get(key)
        if cached_data is None:
            self.performance_metrics["mark_time"] = time.time() - start_time
            return False
        
        # 包装为缓存项
        cache_item = CacheItem.from_any(cached_data)
        
        # 标记质量
        cache_item.mark_quality(is_positive)
        
        # 更新缓存
        self.storage.set(key, cache_item.to_dict())
        
        if is_positive and cache_item.is_high_quality():
            # 明确标记为高质量缓存，增加额外属性确保快速路径能识别
            item_dict = cache_item.to_dict()
            item_dict["metadata"]["fast_path_eligible"] = True
            self.storage.set(key, item_dict)
        
        self.performance_metrics["mark_time"] = time.time() - start_time
        return True
    
    def delete(self, query: str, **kwargs) -> bool:
        """
        删除缓存项
        
        参数:
            query: 查询字符串
            **kwargs: 其他参数，传递给缓存键策略
        
        返回:
            bool: 是否成功删除
        """
        # 生成缓存键
        key = self._get_consistent_key(query, **kwargs)
        
        # 删除缓存项
        return self.storage.delete(key)
    
    def clear(self) -> None:
        """清空缓存"""
        self.storage.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        返回:
            Dict[str, Any]: 性能指标字典
        """
        return self.performance_metrics
    
    def validate_answer(self, query: str, answer: str, validator: Callable[[str, str], bool] = None, **kwargs) -> bool:
        """
        验证答案质量
        
        参数:
            query: 查询字符串
            answer: 答案内容
            validator: 自定义验证函数
            **kwargs: 其他参数，传递给缓存键策略
        
        返回:
            bool: 答案是否有效
        """
        # 生成缓存键
        key = self.key_strategy.generate_key(query, **kwargs)
        
        # 获取缓存项
        cached_data = self.storage.get(key)
        if cached_data is None:
            # 如果缓存不存在，直接使用验证函数
            if validator:
                return validator(query, answer)
            return True  # 默认为有效
        
        # 包装为缓存项
        cache_item = CacheItem.from_any(cached_data)
        
        # 检查用户验证状态
        if cache_item.metadata.get("user_verified", False):
            return True  # 用户已验证的答案直接视为有效
        
        # 检查质量分数
        quality_score = cache_item.metadata.get("quality_score", 0)
        if quality_score < 0:
            return False  # 负面评价的答案视为无效
        
        # 如果提供了自定义验证函数，使用它
        if validator:
            return validator(query, answer)
        
        # 基本验证：长度检查
        if len(answer) < 20:
            return False
        
        return True  # 默认为有效