from pathlib import Path

# 知识库主题，用于deepresearch
KB_NAME = "华东理工大学"

# 知识图谱设置
theme="华东理工大学学生管理"
entity_types=[
    "学生类型", 
    "奖学金类型", 
    "处分类型", 
    "部门", 
    "学生职责", 
    "管理规定"
]
relationship_types=[
    "申请", 
    "评选", 
    "违纪", 
    "资助", 
    "申诉", 
    "管理", 
    "权利义务",
    "互斥",
]

# 增量更新设置：冲突解决策略（新文件和手动编辑neo4j之间的冲突），可以是 "manual_first"（优先保留手动编辑），"auto_first"（优先自动更新）或 "merge"（尝试合并）
conflict_strategy="manual_first"

# 实体相似度
similarity_threshold = 0.9

# 社区算法：sllpa or leiden
# sllpa如果发现不了社区，则换成leiden效果会好一点
community_algorithm = 'leiden'

# 构建路径
BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / 'files'

# 文本分块，注意如果是本地的embedding模型，比如BAAI/bge-large-zh-v1.5, 他的上下文才512token，这里的数字需要调的很小
# 而用openai的text-embedding-3-large，上下文有8192token，这里的数字可以适当大点
CHUNK_SIZE=500
OVERLAP=100

# 回答方式
response_type="多个段落"

# agent 工具描述
lc_description = "用于需要具体细节的查询。检索华东理工大学学生管理文件中的具体规定、条款、流程等详细内容。适用于'某个具体规定是什么'、'处理流程如何'等问题。"
gl_description = "用于需要总结归纳的查询。分析华东理工大学学生管理体系的整体框架、管理原则、学生权利义务等宏观内容。适用于'学校的学生管理总体思路'、'学生权益保护机制'等需要系统性分析的问题。"
naive_description = "基础检索工具，直接查找与问题最相关的文本片段，不做复杂分析。快速获取华东理工大学相关政策，返回最匹配的原文段落。"

# 项目前端的“示例问题”显示
examples = [
    "旷课多少学时会被退学？",
    "国家奖学金和国家励志奖学金互斥吗？",
    "优秀学生要怎么申请？",
    "那上海市奖学金呢？",
]

# fastapi 并发进程数
workers = 2