# 图谱构建模块

## 目录结构

```
graph/
├── __init__.py                # 模块入口，导出主要类和函数
├── core/                      # 核心功能组件
│   ├── __init__.py            # 导出核心组件
│   ├── base_indexer.py        # 基础索引器类
│   ├── graph_connection.py    # 图数据库连接管理
│   └── utils.py               # 工具函数(定时器、哈希生成等)
├── extraction/                # 实体关系提取组件
│   ├── __init__.py            # 导出提取组件
│   ├── entity_extractor.py    # 实体关系提取器
│   └── graph_writer.py        # 图数据写入器
├── graph_consistency_validator.py  # 图谱一致性验证工具
├── indexing/                  # 索引管理组件
│   ├── __init__.py            # 导出索引组件
│   ├── chunk_indexer.py       # 文本块索引管理
│   ├── embedding_manager.py   # 嵌入向量管理
│   └── entity_indexer.py      # 实体索引管理
├── processing/                # 实体处理组件
│   ├── __init__.py            # 导出处理组件
│   ├── entity_merger.py       # 实体合并管理
│   └── similar_entity.py      # 相似实体检测
└── structure/                 # 图结构构建组件
    ├── __init__.py            # 导出结构组件
    └── struct_builder.py      # 图结构构建器
```

## 模块概述

本模块是一个完整的图谱构建与查询系统，基于Neo4j图数据库实现。主要功能包括文档解析、实体关系提取、嵌入向量索引建立、相似实体检测与合并等。模块采用高度模块化设计，支持大规模数据处理和优化的查询性能。

## 核心实现思路

### 1. 图谱数据结构设计

系统基于以下核心节点类型构建图结构：
- `__Document__`：文档节点，代表一个完整的文档
- `__Chunk__`：文本块节点，文档的片段
- `__Entity__`：实体节点，从文本中提取的概念、对象等

节点之间的关系包括：
- `PART_OF`：Chunk与Document间的从属关系
- `NEXT_CHUNK`：文本块之间的顺序关系
- `MENTIONS`：文本块与实体间的提及关系
- `SIMILAR`：实体之间的相似关系

### 2. 图谱构建流程

1. **文档结构化**：通过`GraphStructureBuilder`将文档拆分为Chunk并建立结构
2. **实体关系提取**：`EntityRelationExtractor`使用LLM从文本中提取实体和关系
3. **图谱写入**：`GraphWriter`将提取的实体和关系写入Neo4j
4. **向量索引建立**：`ChunkIndexManager`和`EntityIndexManager`为节点创建嵌入向量索引
5. **相似实体检测**：`SimilarEntityDetector`使用向量相似度和GDS算法检测重复实体
6. **实体合并**：`EntityMerger`基于LLM决策合并相似实体

### 3. 性能优化策略

- **批处理**：所有模块实现批量操作，减少数据库交互
- **并行处理**：利用线程池并行处理数据
- **缓存机制**：实体提取过程中使用缓存避免重复计算
- **高效索引**：合理的索引策略提升查询性能
- **错误恢复**：实现重试机制和错误恢复

## 核心功能与类

### 图数据库连接

`GraphConnectionManager`提供对Neo4j的连接管理，实现单例模式确保连接复用，统一管理查询和索引创建。

```python
# 示例使用
graph = connection_manager.get_connection()
result = graph.query("MATCH (n) RETURN count(n) as count")
```

### 图结构构建

`GraphStructureBuilder`负责创建文档和文本块节点，并建立它们之间的结构关系：

```python
builder = GraphStructureBuilder()
builder.create_document(type="text", uri="path/to/doc", file_name="example.txt", domain="test")
chunks_with_hash = builder.create_relation_between_chunks(file_name, chunks)
```

### 实体关系提取

`EntityRelationExtractor`通过LLM从文本块中提取实体和关系：

```python
extractor = EntityRelationExtractor(llm, system_template, human_template, entity_types, relationship_types)
processed_chunks = extractor.process_chunks(file_contents)
```

### 向量索引管理

`ChunkIndexManager`和`EntityIndexManager`计算嵌入向量并创建索引：

```python
chunk_indexer = ChunkIndexManager()
vector_store = chunk_indexer.create_chunk_index()
```

### 相似实体检测和合并

`SimilarEntityDetector`和`EntityMerger`配合完成实体去重：

```python
detector = SimilarEntityDetector()
duplicate_candidates = detector.process_entities()

merger = EntityMerger()
merged_count = merger.process_duplicates(duplicate_candidates)
```

### 图谱一致性验证

`GraphConsistencyValidator`检查和修复图谱中的一致性问题：

```python
validator = GraphConsistencyValidator()
validation_result = validator.validate_graph()
repair_result = validator.repair_graph()
```

## 主要优势

1. **高可扩展性**：模块化设计使系统易于扩展
2. **高性能**：批处理和并行处理优化大数据处理能力
3. **健壮性**：内置错误处理和恢复机制
4. **灵活性**：适应不同类型的数据源和实体提取需求