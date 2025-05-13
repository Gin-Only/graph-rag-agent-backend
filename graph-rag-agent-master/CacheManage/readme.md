# CacheManage 缓存管理模块

## 项目结构

```
CacheManage/
├── __init__.py                 # 模块主入口，导出主要类和接口
├── manager.py                  # 统一缓存管理器实现
├── backends/                   # 存储后端实现
│   ├── __init__.py             # 后端模块入口
│   ├── base.py                 # 存储后端抽象基类
│   ├── memory.py               # 内存缓存后端
│   ├── disk.py                 # 磁盘缓存后端
│   ├── hybrid.py               # 混合缓存后端(内存+磁盘)
│   └── thread_safe.py          # 线程安全装饰器后端
├── models/                     # 数据模型
│   ├── __init__.py             # 模型模块入口
│   └── cache_item.py           # 缓存项模型
└── strategies/                 # 缓存键生成策略
    ├── __init__.py             # 策略模块入口
    ├── base.py                 # 缓存键策略抽象基类
    ├── simple.py               # 简单MD5哈希策略
    ├── context_aware.py        # 上下文感知缓存键策略
    └── global_strategy.py      # 全局缓存键策略
```

## 模块概述

CacheManage 是一个灵活的缓存管理系统，提供多种存储后端和缓存键生成策略，旨在提高应用程序性能并减少重复计算。该模块支持内存缓存、磁盘缓存和混合缓存，并通过多种策略优化缓存命中率。

## 核心设计思路

### 1. 分层设计

CacheManage 采用了分层设计模式，主要分为三层：

1. **缓存管理器 (CacheManager)**: 提供统一的高级接口，协调缓存键策略和存储后端
2. **缓存键生成策略 (Strategies)**: 负责生成一致且高效的缓存键
3. **存储后端 (Backends)**: 实现实际的数据存储与检索

这种分层设计使得各组件可以独立变化，提高了系统的灵活性和可扩展性。

### 2. 多种存储后端

- **内存缓存 (MemoryCacheBackend)**: 使用内存存储，速度最快，但容量有限
- **磁盘缓存 (DiskCacheBackend)**: 将数据持久化到文件系统，支持更大容量
- **混合缓存 (HybridCacheBackend)**: 结合内存和磁盘的优势，提供两级缓存
- **线程安全装饰器 (ThreadSafeCacheBackend)**: 为其他后端提供线程安全保证

### 3. 智能的缓存键策略

- **简单策略 (SimpleCacheKeyStrategy)**: 使用查询字符串的MD5哈希作为缓存键
- **上下文感知策略 (ContextAwareCacheKeyStrategy)**: 考虑会话历史，适用于上下文相关的查询
- **上下文与关键词感知策略 (ContextAndKeywordAwareCacheKeyStrategy)**: 同时考虑会话历史和关键词
- **全局策略 (GlobalCacheKeyStrategy)**: 忽略上下文，适用于全局共享的查询结果

### 4. 缓存项模型

缓存项 (CacheItem) 不仅存储数据本身，还包含元数据，如：
- 创建时间
- 访问次数
- 质量评分
- 用户验证状态

这些元数据用于实现智能缓存管理和淘汰策略。

## 核心功能

### 1. 统一缓存管理

`CacheManager` 提供了一站式缓存管理方案，主要方法包括：

- `get(query, **kwargs)`: 获取缓存内容
- `get_fast(query, **kwargs)`: 快速获取高质量缓存
- `set(query, result, **kwargs)`: 设置缓存内容
- `mark_quality(query, is_positive, **kwargs)`: 标记缓存质量
- `delete(query, **kwargs)`: 删除缓存项
- `clear()`: 清空缓存
- `validate_answer(query, answer, validator)`: 验证答案质量

### 2. 智能缓存淘汰

各种存储后端实现了不同的缓存淘汰策略：

- **内存缓存**: 使用LRU (最近最少使用) 策略
- **磁盘缓存**: 使用复合策略，结合访问频率和时间因素
- **混合缓存**: 优先保留高质量缓存项，智能决定缓存位置

### 3. 性能优化

- **批量写入**: 磁盘缓存实现了写入队列和批量刷新
- **异步索引更新**: 减少磁盘I/O操作
- **高质量缓存快速路径**: 优先获取用户验证过的高质量缓存

### 4. 线程安全

提供了线程安全的包装器，确保在多线程环境中安全使用缓存。

## 使用示例

```python
from CacheManage import CacheManager, ContextAwareCacheKeyStrategy

# 创建一个使用上下文感知策略的缓存管理器
manager = CacheManager(
    key_strategy=ContextAwareCacheKeyStrategy(),
    cache_dir="./my_cache",
    memory_only=False,
    max_memory_size=200,
    max_disk_size=5000,
    thread_safe=True
)

# 设置缓存
manager.set("数据分析", {"result": "这是数据分析结果"}, thread_id="user_123")

# 获取缓存
result = manager.get("数据分析", thread_id="user_123")

# 标记高质量缓存
manager.mark_quality("数据分析", is_positive=True, thread_id="user_123")

# 清空缓存
manager.clear()
```

## 高级特性

1. **会话感知缓存**: 通过上下文感知策略，同一查询在不同会话中可能有不同的缓存键，解决了上下文相关的缓存挑战
2. **质量感知**: 支持用户反馈和质量评分，优先返回高质量缓存
3. **智能淘汰**: 基于访问频率、时间和质量的复合淘汰策略
4. **性能监控**: 收集并报告各种性能指标

## 适用场景

- 需要缓存计算开销大的操作结果
- 处理重复性请求较多的系统
- 需要提高响应速度的交互式应用
- 希望减少后端负载的分布式系统