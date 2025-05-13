import time
from typing import Any, Dict, Optional


class CacheItem:
    """缓存项包装类，支持元数据"""
    
    def __init__(self, content: Any, metadata: Optional[Dict[str, Any]] = None):
        """初始化缓存项"""
        self.content = content
        
        # 确保元数据包含必要字段
        self.metadata = metadata or {}
        
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = time.time()
        if "quality_score" not in self.metadata:
            self.metadata["quality_score"] = 0
        if "user_verified" not in self.metadata:
            self.metadata["user_verified"] = False
        if "access_count" not in self.metadata:
            self.metadata["access_count"] = 0
        if "fast_path_eligible" not in self.metadata:
            # 增加快速路径标记
            self.metadata["fast_path_eligible"] = False
    
    def get_content(self) -> Any:
        """
        获取内容
        
        返回:
            Any: 缓存内容
        """
        return self.content
    
    def is_high_quality(self) -> bool:
        """
        判断是否为高质量缓存
        
        返回:
            bool: 是否为高质量缓存
        """
        return self.metadata.get("user_verified", False) or self.metadata.get("quality_score", 0) > 2
    
    def mark_quality(self, is_positive: bool) -> None:
        """标记缓存质量"""
        if is_positive:
            current_score = self.metadata.get("quality_score", 0)
            self.metadata["quality_score"] = current_score + 1
            self.metadata["user_verified"] = True
            # 标记为适合快速路径
            self.metadata["fast_path_eligible"] = True
        else:
            current_score = self.metadata.get("quality_score", 0)
            self.metadata["quality_score"] = max(0, current_score - 2)  # 负面评价权重更大
            # 标记为不适合快速路径
            self.metadata["fast_path_eligible"] = False
    
    def update_access_stats(self) -> None:
        """更新访问统计"""
        self.metadata["access_count"] = self.metadata.get("access_count", 0) + 1
        self.metadata["last_accessed"] = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        返回:
            Dict[str, Any]: 包含内容和元数据的字典
        """
        return {
            "content": self.content,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheItem':
        """
        从字典创建缓存项
        
        参数:
            data: 字典数据
            
        返回:
            CacheItem: 缓存项
        """
        try:
            if isinstance(data, dict):
                if "content" in data and "metadata" in data:
                    # 处理完整格式
                    metadata = data["metadata"]
                    # 确保metadata具有所有必要字段
                    if not isinstance(metadata, dict):
                        metadata = {}
                    if "created_at" not in metadata:
                        metadata["created_at"] = time.time()
                    if "quality_score" not in metadata:
                        metadata["quality_score"] = 0
                    if "user_verified" not in metadata:
                        metadata["user_verified"] = False
                    if "access_count" not in metadata:
                        metadata["access_count"] = 0
                    
                    return cls(data["content"], metadata)
                else:
                    # 处理简单格式
                    return cls(data, {
                        "created_at": time.time(),
                        "quality_score": 0,
                        "user_verified": False,
                        "access_count": 0
                    })
            else:
                # 如果是非字典类型，直接作为内容
                return cls(data, {
                    "created_at": time.time(),
                    "quality_score": 0,
                    "user_verified": False,
                    "access_count": 0
                })
        except Exception as e:
            print(f"反序列化缓存项失败: {e}")
            # 返回默认对象，确保程序不会崩溃
            return cls("Error deserializing cache item", {
                "created_at": time.time(),
                "quality_score": 0,
                "user_verified": False,
                "access_count": 0,
                "error": str(e)
            })
    
    @classmethod
    def from_any(cls, data: Any) -> 'CacheItem':
        """
        从任意数据创建缓存项，具有自动类型检测
        
        参数:
            data: 任意数据
            
        返回:
            CacheItem: 缓存项
        """
        if isinstance(data, cls):
            return data
        elif isinstance(data, dict) and "content" in data:
            return cls.from_dict(data)
        else:
            return cls(data)