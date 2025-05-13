import os
import time
import json
from typing import Any, Optional, List, Tuple
from .base import CacheStorageBackend


class DiskCacheBackend(CacheStorageBackend):
    """磁盘缓存后端实现"""
    
    def __init__(self, cache_dir: str = "./cache", max_size: int = 1000):
        """
        初始化磁盘缓存后端
        
        参数:
            cache_dir: 缓存目录
            max_size: 缓存最大项数
        """
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.metadata = {}  # 用于存储元数据
        self.write_queue: List[Tuple[str, Any]] = []  # 写入队列
        self.last_flush_time = time.time()
        
        # 确保缓存目录存在
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # 加载索引
        self._load_index()
    
    def _get_cache_path(self, key: str) -> str:
        """
        获取缓存文件路径
        
        参数:
            key: 缓存键
            
        返回:
            str: 缓存文件路径
        """
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _get_index_path(self) -> str:
        """
        获取索引文件路径
        
        返回:
            str: 索引文件路径
        """
        return os.path.join(self.cache_dir, "index.json")
    
    def _load_index(self) -> None:
        """加载缓存索引"""
        index_path = self._get_index_path()
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"加载缓存索引失败: {e}")
                self.metadata = {}
        
        # 验证磁盘上的文件
        files = [f[:-5] for f in os.listdir(self.cache_dir) if f.endswith(".json") and f != "index.json"]
        
        # 同步索引和文件
        for key in list(self.metadata.keys()):
            if key not in files:
                del self.metadata[key]
        
        for key in files:
            if key not in self.metadata:
                self.metadata[key] = {"created_at": time.time(), "access_count": 0}
    
    def _save_index(self) -> None:
        """保存缓存索引"""
        try:
            with open(self._get_index_path(), 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存索引失败: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存项
        
        参数:
            key: 缓存键
            
        返回:
            Optional[Any]: 缓存项值，不存在则返回None
        """
        cache_path = self._get_cache_path(key)
        if key in self.metadata and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    value = json.load(f)
                
                # 更新访问信息
                self.metadata[key]["last_accessed"] = time.time()
                self.metadata[key]["access_count"] = self.metadata[key].get("access_count", 0) + 1
                
                # 异步保存索引（非阻塞）
                self._save_index_async()
                
                return value
            except Exception as e:
                print(f"读取缓存文件失败: {e}")
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        设置缓存项
        
        参数:
            key: 缓存键
            value: 缓存值
        """
        # 如果缓存已满，淘汰项
        if len(self.metadata) >= self.max_size and key not in self.metadata:
            self._evict_items()
        
        # 更新元数据
        self.metadata[key] = {
            "created_at": time.time(),
            "access_count": 0,
            "last_accessed": time.time()
        }
        
        # 添加到写入队列
        self.write_queue.append((key, value))
        
        # 根据条件决定是否立即刷新
        current_time = time.time()
        if len(self.write_queue) >= 10 or (current_time - self.last_flush_time) > 30:
            self._flush_write_queue()
    
    def _flush_write_queue(self) -> None:
        """刷新写入队列"""
        if not self.write_queue:
            return
        
        successful_keys = []
        failed_keys = []
        
        for key, value in self.write_queue:
            try:
                with open(self._get_cache_path(key), 'w', encoding='utf-8') as f:
                    json.dump(value, f, ensure_ascii=False, indent=2)
                successful_keys.append(key)
            except Exception as e:
                failed_keys.append(key)
                print(f"写入缓存文件失败 ({key}): {e}")
        
        # 更新写入队列，只保留失败的项
        self.write_queue = [(k, v) for k, v in self.write_queue if k in failed_keys]
        
        # 更新时间戳
        self.last_flush_time = time.time()
        
        # 如果有成功项，保存索引
        if successful_keys:
            try:
                self._save_index()
            except Exception as e:
                print(f"保存索引失败: {e}")
                # 下次写入时会再次尝试保存索引
     
    def _save_index_async(self) -> None:
        """异步保存索引（简化实现）"""
        # 在真实环境中，应该使用异步方法执行
        # 这里简化为定期保存
        current_time = time.time()
        if current_time - self.last_flush_time > 60:  # 每分钟最多保存一次
            self._save_index()
            self.last_flush_time = current_time
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        参数:
            key: 缓存键
            
        返回:
            bool: 是否成功删除
        """
        if key in self.metadata:
            # 从元数据中删除
            del self.metadata[key]
            
            # 删除文件
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except Exception as e:
                    print(f"删除缓存文件失败: {e}")
                    return False
            
            # 保存索引
            self._save_index()
            return True
        
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        # 清空写入队列
        self.write_queue = []
        
        # 清空元数据
        self.metadata = {}
        
        # 删除所有缓存文件
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                except Exception as e:
                    print(f"删除缓存文件失败: {e}")
        
        # 保存空索引
        self._save_index()
    
    def _evict_items(self) -> None:
        """淘汰缓存项，使用复合策略：优先淘汰访问量低且旧的项"""
        if not self.metadata:
            return
        
        # 计算每个项的分数：score = 访问次数 / (当前时间 - 创建时间)
        scores = {}
        current_time = time.time()
        
        for key, meta in self.metadata.items():
            age = current_time - meta.get("created_at", current_time)
            access_count = meta.get("access_count", 0)
            
            # 避免除以零
            if age < 1:
                age = 1
            
            # 分数越高表示越应该保留
            scores[key] = access_count / age
        
        # 找出分数最低的前10%项
        num_to_evict = max(1, len(scores) // 10)
        keys_to_evict = sorted(scores.keys(), key=lambda k: scores[k])[:num_to_evict]
        
        # 删除这些项
        for key in keys_to_evict:
            self.delete(key)