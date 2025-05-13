from typing import Any, Optional
from config.neo4jdb import get_db_manager

class GraphConnectionManager:
    """
    图数据库连接管理器。
    负责创建和管理Neo4j图数据库连接，确保连接的复用。
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现，确保只创建一个连接管理器实例"""
        if cls._instance is None:
            cls._instance = super(GraphConnectionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化连接管理器，只在第一次创建时执行"""
        if not getattr(self, "_initialized", False):
            db_manager = get_db_manager()
            self.graph = db_manager.graph
            self._initialized = True
    
    def get_connection(self):
        """
        获取图数据库连接
        
        Returns:
            连接到Neo4j数据库的对象
        """
        return self.graph
    
    def refresh_schema(self):
        """刷新图数据库模式"""
        self.graph.refresh_schema()
    
    def execute_query(self, query: str, params: Optional[dict] = None) -> Any:
        """
        执行图数据库查询
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        return self.graph.query(query, params or {})
    
    def create_index(self, index_query: str) -> None:
        """
        创建索引
        
        Args:
            index_query: 索引创建查询
        """
        self.graph.query(index_query)
        
    def create_multiple_indexes(self, index_queries: list) -> None:
        """
        创建多个索引
        
        Args:
            index_queries: 索引创建查询列表
        """
        for query in index_queries:
            self.create_index(query)
            
    def drop_index(self, index_name: str) -> None:
        """
        删除索引
        
        Args:
            index_name: 索引名称
        """
        try:
            self.graph.query(f"DROP INDEX {index_name} IF EXISTS")
            print(f"已删除索引 {index_name}（如果存在）")
        except Exception as e:
            print(f"删除索引 {index_name} 时出错 (可忽略): {e}")

# 创建全局连接管理器实例
connection_manager = GraphConnectionManager()