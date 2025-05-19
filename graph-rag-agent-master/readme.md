# GraphRAG + DeepSearch 实现与问答系统（Agent）构建

本项目聚焦于结合 **GraphRAG** 与 **私域 Deep Search** 的方式，实现可解释、可推理的智能问答系统，同时结合多 Agent 协作与知识图谱增强，构建完整的 RAG 智能交互解决方案。

> 💡 灵感来源于检索增强推理与深度搜索场景，探索 RAG 与 Agent 在未来应用中的结合路径。

## 🏠 项目架构图

由Claude生成

![svg](./assets/structure.svg)

## 📂 项目结构

```
graph-rag-agent/
├── agent/                  # 🤖 Agent 模块 - 核心交互层
│   ├── __init__.py         # 模块初始化文件
│   ├── base.py             # Agent 基类
│   ├── deep_research_agent.py # 深度研究 Agent
│   ├── evaluator_agent.py  # 评估 Agent
│   ├── retrieval_agent.py  # 检索 Agent
├── assets/                 # 🖼️ 静态资源
│   ├── deepsearch.svg      # rag演进图
│   └── start.md            # 快速开始文档
├── build/                  # 🏗️ 知识图谱构建模块
│   ├── __init__.py         # 模块入口，导出类和函数
│   ├── build_chunk_index.py # 文本块索引构建器
│   ├── build_graph.py      # 基础知识图谱构建器
│   ├── build_index_and_community.py # 实体索引和社区构建器
│   ├── incremental/        # 增量更新子模块
│   │   ├── __init__.py     # 增量更新模块入口
│   │   ├── file_change_manager.py # 文件变更管理器
│   │   ├── incremental_update_scheduler.py # 增量更新调度器
│   │   └── manual_edit_manager.py # 手动编辑同步管理器
│   ├── incremental_graph_builder.py # 增量图谱更新构建器
│   ├── incremental_update.py # 增量更新管理程序
│   └── main.py            # 主程序入口，整合完整流程
├── CacheManage/            # 📦 缓存管理模块
│   ├── __init__.py         # 模块初始化文件
│   ├── manager.py          # 统一缓存管理器
│   ├── backends/           # 存储后端
│   ├── models/             # 数据模型
│   └── strategies/         # 缓存键生成策略
├── community/              # 🔍 社区检测与摘要模块
│   ├── __init__.py         # 模块初始化文件
│   ├── detector/           # 社区检测算法
│   └── summary/            # 社区摘要生成
├── config/                 # ⚙️ 配置模块
│   ├── __init__.py         # 包初始化文件
│   ├── neo4jdb.py          # Neo4j数据库连接管理
│   ├── prompt.py           # 各类提示模板定义
│   ├── reasoning_prompts.py # 推理提示模板
│   └── settings.py         # 全局配置参数
├── evaluator/              # 📊 评估系统
│   ├── __init__.py         # 模块初始化文件
│   ├── core/               # 评估核心组件
│   ├── evaluator_config/   # 评估配置
│   ├── evaluators/         # 评估器实现
│   ├── metrics/            # 评估指标实现
│   ├── preprocessing/      # 预处理组件
│   ├── test/               # 评估测试脚本
│   └── utils/              # 评估工具
├── files/                  # 📁 示例文件
│   ├── 2023学生手册.pdf
│   ├── txt文件/
│   ├── 华东理工大学关于印发《学生勤工助学管理办法》的通知.pdf
│   ├── 华东理工大学本科生请假申请表.doc
│   └── 华东理工大学研究生论文答辩程序.doc
├── frontend/               # 🖥️ 前端界面
│   ├── app.py              # 应用入口
│   ├── components/         # UI组件
│   ├── frontend_config/    # 前端配置
│   └── utils/              # 前端工具
├── graph/                  # 📈 图谱构建模块
│   ├── __init__.py         # 模块初始化文件
│   ├── core/               # 核心组件
│   ├── extraction/         # 实体关系提取
│   ├── graph_consistency_validator.py # 图谱一致性验证器
│   ├── indexing/           # 索引管理
│   ├── processing/         # 实体处理
│   └── structure/          # 图结构定义
├── model/                  # 🧩 模型管理
│   ├── __init__.py         # 模块初始化文件
│   ├── get_models.py       # 模型初始化
│   └── test_stream_model.py # 流式模型测试
├── processor/              # 📄 文档处理器
│   ├── __init__.py         # 包初始化文件
│   ├── document_processor.py # 文档处理核心类
│   ├── file_reader.py      # 多格式文件读取器
│   └── text_chunker.py     # 中文文本分块器
├── search/                 # 🔎 搜索模块
│   ├── __init__.py         # 模块初始化文件
│   ├── global_search.py    # 全局搜索
│   ├── local_search.py     # 本地搜索
│   ├── tool/               # 搜索工具集
│   └── utils.py            # 搜索工具
├── server/                 # 🖧 后端服务
│   ├── main.py             # FastAPI 应用入口
│   ├── models/             # 数据模型
│   ├── routers/            # API 路由
│   ├── server_config/      # 服务配置
│   ├── services/           # 业务逻辑
│   └── utils/              # 服务工具
├── test/                   # 🧪 测试模块
│   ├── environment.yml     # 环境配置文件
│   ├── search_with_stream.py    # 流式输出测试
│   ├── search_without_stream.py # 标准输出测试
│   ├── testLettuce.py      # Lettuce测试
│   ├── test_deep_agent.py  # 深度Agent测试
│   └── testevaluator.py    # 评估器测试
├── training/               # 🧠 训练模块
│   ├── grpo.ipynb          # GRPO训练笔记本
│   └── readme.md           # 训练说明
├── docker-compose.yaml     # Docker配置
├── requirements.txt        # 依赖包列表
└── setup.py                # 安装脚本
```

**此外，每个模块下都有单独的readme来介绍模块的功能**



## 🚀 相关资源

- [大模型推理能力不断增强，RAG 和 Agent 何去何从](https://www.bilibili.com/video/BV1i6RNYpEwV)  
- [企业级知识图谱交互问答系统方案](https://www.bilibili.com/video/BV1U599YrE26)  
- [Jean - 用国产大模型 + LangChain + Neo4j 建图全过程](https://zhuanlan.zhihu.com/p/716089164)
- [GraphRAG vs DeepSearch？GraphRAG 提出者给你答案](https://mp.weixin.qq.com/s/FOT4pkEPHJR8xFvcVk1YFQ)

![svg](./assets/deepsearch.svg)

## ✨ 项目亮点

- **从零开始复现 GraphRAG**：完整实现了 GraphRAG 的核心功能，将知识表示为图结构
- **DeepSearch 与 GraphRAG 创新融合**：现有 DeepSearch 框架主要基于向量数据库，本项目创新性地将其与知识图谱结合
- **多 Agent 协同架构**：实现不同类型 Agent 的协同工作，提升复杂问题处理能力
- **完整评估系统**：提供 20+ 种评估指标，全方位衡量系统性能
- **增量更新机制**：支持知识图谱的动态增量构建与智能去重
- **思考过程可视化**：展示 AI 的推理轨迹，提高可解释性和透明度

## 🏁 快速开始

### 环境配置

```bash
# 使用conda创建环境
conda env create -f environment.yml
conda activate graphrag  # 环境名

# 或者使用pip安装依赖
pip install -r requirements.txt
```

更多详情请参考：[快速开始文档](./assets/start.md)

## 🧰 功能模块

### 图谱构建与管理

- **多格式文档处理**：支持 TXT、PDF、MD、DOCX、DOC、CSV、JSON、YAML/YML 等格式
- **LLM 驱动的实体关系提取**：利用大语言模型从文本中识别实体与关系
- **增量更新机制**：支持已有图谱上的动态更新，智能处理冲突
- **社区检测与摘要**：自动识别知识社区并生成摘要，支持 Leiden 和 SLLPA 算法
- **一致性验证**：内置图谱一致性检查与修复机制

### GraphRAG 实现

- **多级检索策略**：支持本地搜索、全局搜索、混合搜索等多种模式
- **图谱增强上下文**：利用图结构丰富检索内容，提供更全面的知识背景
- **Chain of Exploration**：实现在知识图谱上的多步探索能力
- **社区感知检索**：根据知识社区结构优化搜索结果

### DeepSearch 融合

- **多步骤思考-搜索-推理**：支持复杂问题的分解与深入挖掘
- **证据链追踪**：记录每个推理步骤的证据来源，提高可解释性
- **思考过程可视化**：实时展示 AI 的推理轨迹
- **多路径并行搜索**：同时执行多种搜索策略，综合利用不同知识来源

### 多种 Agent 实现

所有 Agent 均基于 [LangGraph](https://github.com/langchain-ai/langgraph) 框架构建，采用**状态图（StateGraph）+ 多节点工作流**的方式组织操作，并继承自统一的 `BaseAgent` 抽象类。

- **RetrievalAgent**：核心检索 Agent，支持多种检索策略：
  - `naive`：简单向量搜索，响应速度快、资源消耗低，适合直接问答类简单问题
  - `local`：结构化或嵌入式本地搜索，提供更精确的领域内检索
  - `global`：全局知识或跨域检索，适合需要广泛知识背景的问题
  - `hybrid`：融合局部细节与高层语义的混合搜索，自动在精确度和广度间取得平衡
  - `graph`：基于知识图谱结构的检索，支持沿图结构进行多跳查询，适用于需要理解概念间关联的复杂问题
  
  核心特性包括：自动关键词提取与智能缓存、状态图中支持从 `retrieve → generate` 的路径以及 `reduce` 路径用于全局结果整合、支持流式响应和文档评分与结果缩减。

- **DeepResearchAgent**：深度研究型 Agent，专为复杂问题和多步骤推理设计，实现多回合的思考-搜索-推理循环。核心特性包括：
  - 显式思考过程（`<think>`块）与推理可视化
  - 多回合推理与迭代搜索，支持复杂问题的分解与深入挖掘
  - 社区感知和知识图谱增强，提供更全面的知识背景
  - 多分支推理和矛盾检测，提高推理质量
  - 证据链追踪，记录每个推理步骤的证据来源，提高可解释性
  - 支持两种模式：标准模式（基于`DeepResearchTool`）和增强模式（结合`DeeperResearchTool`实现知识图谱路径探索）
  - 特色功能：`explore_knowledge()`基于关键词触发图谱路径追踪、`analyze_reasoning_chain()`分析推理路径、`detect_contradictions()`检测生成内容中的冲突点



- **EvaluatorAgent**：幻觉检测 Agent，负责评估答案内容的真实性，检测生成幻觉。特点包括：
  - 集成 `LettuceDetect` 模型进行上下文对齐检测
  - 返回高亮幻觉文本和置信度评分，直观展示可信度
  - 支持评估报告生成和关键词提取
  - 评估路径为 `retrieve → evaluate → generate`，自动插入中间评估步骤
  - 提供可解释的评估结果，帮助用户理解幻觉产生的原因

### 系统评估与监控

- **多维度评估**：包括答案质量、检索性能、图评估和深度研究评估
- **性能监控**：跟踪 API 调用耗时，优化系统性能
- **用户反馈机制**：收集用户对回答的评价，持续改进系统

### 前后端实现

- **流式响应**：支持 AI 生成内容的实时流式显示
- **交互式知识图谱**：提供 Neo4j 风格的图谱交互界面
- **调试模式**：开发者可查看执行轨迹和搜索过程
- **RESTful API**：完善的后端 API 设计，支持扩展开发

## 🖥️ 简单演示

### 终端测试输出：

```bash
cd test/
python search_with_stream.py

# 本例为测试RetrievalAgent的输出，其他Agent可以在测试脚本中删除注释自行测试
开始测试: 2025-04-05 21:55:04

===== 开始流式Agent测试 =====

已加载增强版深度研究工具

===== 测试查询: 优秀学生的申请条件是什么？ =====

[测试] FusionGraphRAGAgent - 流式 - 查询: '优秀学生的申请条件是什么？'
开始接收流式输出 (最长等待 300 秒)...
性能指标 - fast_cache_check: 1.0043s
DEBUG - LLM关键词结果: {
    "low_level": ["student", "institutions"],
    "high_level": ["comparison", "criteria", "educat...
Building prefix dict from the default dictionary ...
Loading model from cache /tmp/jieba.cache
Loading model cost 0.570 seconds.
Prefix dict has been built successfully.
构建查询图谱完成，包含 5 个实体和 0 个关系，耗时 0.00秒
DEBUG - LLM关键词结果: {
    "low_level": ["Institution A", "excellent student"],
    "high_level": ["criteria", "define", ...
[双路径搜索] LLM评估: 两种结果均有价值，合并结果
DEBUG - LLM关键词结果: {
    "low_level": ["Institution B"],
    "high_level": ["criteria", "excellent student", "definitio...
[双路径搜索] LLM评估: 精确查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": ["student", "institutions"],
    "high_level": ["comparison", "criteria", "excell...
[验证] 答案通过关键词相关性检查
DEBUG - LLM关键词结果: {
    "low_level": ["student admission", "top universities"],
    "high_level": ["criteria", "excell...
构建查询图谱完成，包含 5 个实体和 0 个关系，耗时 0.00秒
DEBUG - LLM关键词结果: {
    "low_level": ["excellent student", "top universities"],
    "high_level": ["academic qualifica...
[双路径搜索] LLM评估: 精确查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": ["student admission", "top universities"],
    "high_level": ["extracurricular ac...
[双路径搜索] LLM评估: 精确查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": ["student", "universities"],
    "high_level": ["admission criteria", "excellence...
[验证] 答案未包含任何高级关键词: ['admission criteria', 'excellence', 'higher education']
达到最大等待时间 300 秒，提前结束接收

[完成] 流式查询完成
- 总耗时: 414.15秒
- 首块延迟: 1.00秒
- 数据块数: 14个
- 总字符数: 766字符

结果:
**正在分析问题和制定检索计划**...

**检索计划制定完成**
- 复杂度评估: 0.60
- 需要全局视图: 是
- 需要关系路径追踪: 否
- 包含时间相关内容: 否
- 涉及知识领域: Education, Admission Policies, Student Assessment

**执行任务 1/5**: exploration - Comparison of excellent student criteria across different institutions
**开始深度探索**...
✓ 深度探索完成

**执行任务 2/5**: local_search - Specific academic achievements or qualifications required for recognition as an excellent student
✓ 本地搜索完成

**执行任务 3/5**: global_search - General application criteria for excellent students in various educational institutions
✓ 全局搜索完成

**执行任务 4/5**: local_search - Policies governing how excellent students are defined and assessed
✓ 本地搜索完成

**执行任务 5/5**: exploration - Detailed criteria for excellent student admission in top universities
**开始深度探索**...
✓ 深度探索完成




===== 测试查询: 学业奖学金有多少钱？ =====

[测试] FusionGraphRAGAgent - 流式 - 查询: '学业奖学金有多少钱？'
开始接收流式输出 (最长等待 300 秒)...
性能指标 - fast_cache_check: 0.9272s
DEBUG - LLM关键词结果: {
    "low_level": ["institutions", "scholarship offerings"],
    "high_level": ["education", "schol...
构建查询图谱完成，包含 5 个实体和 0 个关系，耗时 0.00秒
DEBUG - LLM关键词结果: {
    "low_level": ["institutions", "scholarships"],
    "high_level": ["notable", "offer", "educati...
[双路径搜索] LLM评估: 带知识库名查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": ["institutions", "scholarships"],
    "high_level": ["types"]
}
[双路径搜索] LLM评估: 带知识库名查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": ["institutions", "scholarship offerings"],
    "high_level": ["education", "finan...
[验证] 答案通过关键词相关性检查

[完成] 流式查询完成
- 总耗时: 226.51秒
- 首块延迟: 0.93秒
- 数据块数: 18个
- 总字符数: 1230字符

结果:
**正在分析问题和制定检索计划**...

**检索计划制定完成**
- 复杂度评估: 0.50
- 需要全局视图: 是
- 需要关系路径追踪: 否
- 包含时间相关内容: 否
- 涉及知识领域: Education, Finance, Scholarship Programs

**执行任务 1/6**: exploration - Explore different institutions and their scholarship offerings
**开始深度探索**...
✓ 深度探索完成

**执行任务 2/6**: local_search - Average amount of funds awarded by academic scholarships
✓ 本地搜索完成

**执行任务 3/6**: global_search - Statistics on academic scholarship funding trends
✓ 全局搜索完成

**执行任务 4/6**: global_search - Overview of academic scholarships
✓ 全局搜索完成

**执行任务 5/6**: global_search - Types and amounts of financial aid available for students
✓ 全局搜索完成

**执行任务 6/6**: local_search - Financial aid offices or resources for further information
✓ 本地搜索完成

**正在整合所有检索结果，生成最终答案**...

**正在整合所有检索结果，生成最终答案**...



根据提供的检索结果，我们可以了解到，在华东理工大学，学业奖学金的金额是根据不同等级划分的，每种等级的奖学金金额和比例如下：

1. **特等奖学金**：5000元/人/学年，占领取人数的2%。
2. **一等奖学金**：3000元/人/学年，占领取人数的3%。
3. **二等奖学金**：2000元/人/学年，占领取人数的10%。
4. **三等奖学金**：1000元/人/学年，占领取人数的25%。

根据这些不同等级的奖学金金额和比例，可以通过加权平均计算出每位获奖学生的平均奖学金金额大约为640元。

这些奖学金的设立和分发是依据学生的综合成绩和德育分进行的，学校通过这种方式激励和支持品学兼优的学生。对于每位申请奖学金的学生，学校设有严格的评选标准和程序，以确保奖学金颁发给符合条件的学生。

另外，除了学业奖学金，华东理工大学还提供其他类型的资助项目，如国家助学贷款和励志奖学金，帮助经济困难的学生完成学业。

若有其他关于奖学金种类或申请流程的问题，请参阅相关学校部门的官方指引或进一步咨询学校的学生资助管理中心。


===== 测试查询: 大学英语考试的标准是什么？ =====

[测试] FusionGraphRAGAgent - 流式 - 查询: '大学英语考试的标准是什么？'
开始接收流式输出 (最长等待 300 秒)...
关键词提取失败: Expecting value: line 1 column 1 (char 0)
性能指标 - fast_cache_check: 1.0581s
DEBUG - LLM关键词结果: {
    "low_level": ["各国", "大学", "英语考试"],
    "high_level": ["标准", "比较"]
}
构建查询图谱完成，包含 5 个实体和 0 个关系，耗时 0.00秒
DEBUG - LLM关键词结果: {
    "low_level": ["大学", "英语考试", "国家"],
    "high_level": ["教育标准", "对比分析", "语言能力评估"]
}
[双路径搜索] LLM评估: 精确查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": ["大学", "英语考试", "各国"],
    "high_level": ["难度", "形式", "标准"]
}
[双路径搜索] LLM评估: 带知识库名查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": [],
    "high_level": ["各国", "大学", "英语考试", "标准", "比较"]
}
[验证] 答案通过关键词相关性检查

[完成] 流式查询完成
- 总耗时: 224.52秒
- 首块延迟: 1.06秒
- 数据块数: 16个
- 总字符数: 1126字符

结果:
**正在分析问题和制定检索计划**...

**检索计划制定完成**
- 复杂度评估: 0.70
- 需要全局视图: 是
- 需要关系路径追踪: 否
- 包含时间相关内容: 是
- 涉及知识领域: 教育制度, 语言学习, 考试评估

**执行任务 1/5**: global_search - 大学英语考试对学生的影响
✓ 全局搜索完成

**执行任务 2/5**: local_search - 时间上大学英语考试标准的变化
✓ 本地搜索完成

**执行任务 3/5**: exploration - 各国大学英语考试标准比较
**开始深度探索**...
✓ 深度探索完成

**执行任务 4/5**: global_search - 大学英语考试的一般概况
✓ 全局搜索完成

**执行任务 5/5**: local_search - 大学英语考试的标准详细介绍
✓ 本地搜索完成

**正在整合所有检索结果，生成最终答案**...

**正在整合所有检索结果，生成最终答案**...



### 大学英语考试的标准

根据本地和全球检索结果，我们可以了解大学英语考试标准的几个主要方面，包括考试目的、免修条件、课程设置与考核方法。

#### 1. 背景与目标
大学英语课程的目标是培养学生的英语应用能力、学术或职业英语交流能力以及跨文化交际能力，以满足不同层次学生的学习需求，提高教学质量。[结果 1]

#### 2. 考试免修标准
大学英语免修条件与国家统一考试成绩相关：
- **国家大学英语四级考试**: 四级成绩达到480分以上者，可以免考《大学英语》学位考试。[结果 2]
- **国家大学英语六级考试**: 六级成绩达到425分以上者，同样可以免考《大学英语》学位考试。[结果 2]

#### 3. 课程设置与考核
大学英语课程由三个阶段的课程组成，所有参与课程的学生需通过各阶段的期末考核，并修满学分。[结果 1, 结果 2]

#### 4. 学位考试安排
学位考试通常安排在毕业前的最后学年，未通过的学生可参加补考。[结果 2]

#### 5. 国际标准比较
各国采用不同的英语考试，例如，英国通常使用雅思（IELTS），美国常用托福（TOEFL）。各国考试虽形式不同，但都包括听、说、读、写四个部分。其目的是确保学生能够在英语环境中顺利学习。[探索结果 1]

### 总结
大学英语考试标准主要以国家统一考试成绩为依据，通过分级和补考等机制确保学生英语能力的培养。另外，各国在英语考试标准上有所差异，这反映在考试方式和评分上。总体来说，大学英语考试的核心标准在于评估学生的英语能力，以便适应用语言的学术或专业环境。


===== 测试查询: 小明同学旷课了30学时，又私藏了吹风机，他还殴打了同学，他还能评选国家奖学金吗？ =====

[测试] FusionGraphRAGAgent - 流式 - 查询: '小明同学旷课了30学时，又私藏了吹风机，他还殴打了同学，他还能评选国家奖学金吗？'
开始接收流式输出 (最长等待 300 秒)...
性能指标 - fast_cache_check: 1.1123s
已接收 20 块，共 824 字符，耗时 101.35 秒
DEBUG - LLM关键词结果: {
    "low_level": ["旷课", "私藏物品", "暴力行为"], 
    "high_level": ["综合处理", "校园纪律管理", "行为规范"]
}
构建查询图谱完成，包含 5 个实体和 0 个关系，耗时 0.00秒
DEBUG - LLM关键词结果: {
    "low_level": ["旷课", "学校"],
    "high_level": ["处理措施", "行为"]
}
[双路径搜索] LLM评估: 精确查询结果更具体更有价值
DEBUG - LLM关键词结果: {
    "low_level": ["私藏物品", "学校"],
    "high_level": ["处理措施", "行为", "规章制度"]
}
[双路径搜索] LLM评估: 精确查询结果更具体更有价值
DEBUG - LLM关键词结果: 
{
    "low_level": [],
    "high_level": ["旷课", "私藏物品", "暴力行为", "综合处理", "学校"]
}
[验证] 答案通过关键词相关性检查

[完成] 流式查询完成
- 总耗时: 291.64秒
- 首块延迟: 1.11秒
- 数据块数: 32个
- 总字符数: 2011字符

结果:
**正在分析问题和制定检索计划**...

**检索计划制定完成**
- 复杂度评估: 0.80
- 需要全局视图: 是
- 需要关系路径追踪: 是
- 包含时间相关内容: 否
- 涉及知识领域: 教育政策, 奖学金评选标准, 学生纪律条例

这个问题的核心是评选国家奖学金的条件和小明同学的行为是否符合这些条件。为了回答这个问题，我们需要了解以下信息：

1. **国家奖学金的评选条件和标准**：通常来说，国家奖学金的评选标准包括学术成绩、道德品行、社会表现、综合素质等多个方面。具体的标准会因国家和具体的教育机构而异，但通常会有对品行和纪律的要求。

2. **小明同学的行为影响**：旷课、私藏违禁物品和殴打同学这几种行为在一般的学校纪律和道德评定中都是负面的，会对小明的评选资格产生影响。然而具体的影响程度以及是否绝对排除他获得奖学金的资格要视具体的学校规定和情况而定。...
**执行任务 1/7**: local_search - 学校的旷课处分条款
✓ 本地搜索完成

**执行任务 2/7**: local_search - 学校关于私藏危险物品的处罚规定
✓ 本地搜索完成

**执行任务 3/7**: local_search - 学校对于教师、学生的纪律处罚规定
✓ 本地搜索完成

**执行任务 4/7**: local_search - 学校对于学生暴力行为的处分规定
✓ 本地搜索完成

**执行任务 5/7**: global_search - 国家奖学金评选标准
✓ 全局搜索完成

**执行任务 6/7**: chain_exploration - 评选标准中对于纪律违反的具体要求
**开始Chain of Exploration**...
- 从已有结果中提取实体: 国家奖学金, 学校纪律规定
- 探索路径:
  • 步骤0: 国家奖学金
  • 步骤0: 学校纪律规定
  • 步骤1: 奖学金评审原则
  • 步骤1: 评审委员会
  • 步骤1: 学生学籍档案
- 找到 21 条相关内容
✓ Chain of Exploration完成

**执行任务 7/7**: exploration - 学校对旷课、私藏物品、暴力行为的综合处理情况
**开始深度探索**...
✓ 深度探索完成

**正在基于所有搜索结果进行最终思考**...

基于提供的验证结果汇总，我们可以看到所有假设均未被支持、拒绝或标记为不确定。这种情况下，我们缺乏具体数据来支持或反对任何假设。对于这种情境，我的更新的思考过程是：

1. **缺乏数据支持：** 在当前验证结果中，没有任何假设得到了明确的支持、拒绝或不确定的标记，这意味着我们缺乏足够的数据或证据来进行进一步的分析和得出结论。

2. **继续收集数据：** 由于目前没有确定性的结果，建议加强数据的收集和分析，以便为每个假设提供更强的证据支撑。这包括设计新的实验、寻找额外的数据来源、增加样本数量等。...

**正在整合所有检索结果，生成最终答案**...

**正在整合所有检索结果，生成最终答案**...



根据检索结果，回答小明同学是否能够评选国家奖学金的问题，需考虑其行为对奖学金评选条件的影响。以下是分析：

### 一、国家奖学金评选条件

国家奖学金评定标准不仅强调学习成绩优秀（例如排名前10%），还要求申请者具备高尚的道德品行，表现出色，例如参与社会服务或遵守宪法和法律。这些要求显示道德品行和纪律表现是评选的重要考量因素。

### 二、行为分析与影响

#### 1. **旷课行为**

根据学校纪律处分规定，旷课是严重违纪行为。未请假擅自不参加课程超过一定学时可导致警告、记过或更严重的处分。因此，旷课30学时对奖学金评选可能产生较大的负面影响。

#### 2. **私藏危险物品**

学校对私藏危险物品，如违反使用电器的行为，有明确的处分措施，可能以警告或记过处分。此行为不仅影响个人安全，也被认为是违反学校规章制度的行为。

#### 3. **暴力行为**

暴力行为如殴打同学通常会被严重处理，可能导致记过或留校察看处分。在奖学金评选中，被记录的暴力行为会显著影响学生道德品行的评估。

### 三、综合分析与结论

由于国家奖学金评选要求申请者无严重违纪行为，小明同学的多项违规包括旷课、私藏危险物品和暴力行为，均会严重影响其道德品行评价。因此，按照通常的评选标准，小明同学不符合“无违纪记录”的条件，这将直接剥夺他评选国家奖学金的资格。

基于以上分析，小明因多种违纪行为无法评选国家奖学金。建议小明思考自身行为带来的后果，并在未来更加遵守学校规定，积极改善自己的表现。

### 信息来源

- 学校的学籍管理条例和纪律处分规定内容。
- 国家奖学金的评选标准，包括道德品行考核。


===== 测试总结 =====
成功测试: 4/4
平均总耗时: 289.21秒
平均首块延迟: 1.03秒
平均数据块数: 20.0个
测试完成: 2025-04-05 22:14:29
```

可以看到，由于嵌入的相似性原因，LLM有概率会把“优秀学生”（学校的荣誉称号）近似为“国家奖学金”（称号≠奖学金），这个问题需要后续的微调embedding来解决。

# 本例为测试evalator_agent中幻觉检测报告的输出
```bash
cd test
pytest -s testevaluator.py

=================================== test session starts ===================================
platform win32 -- Python 3.10.16, pytest-8.3.5, pluggy-1.5.0
rootdir: C:\Users\ZHZOn\Desktop\graph-rag-agent-backend\graph-rag-agent-master
plugins: anyio-4.9.0, langsmith-0.3.38
collected 1 item                                                                           

testevaluator.py
✅ 报告内容:
 <span style='color: green'>**幻觉检测报告**:

检测到以下幻觉片段:
- 文本: '是牛顿在1687年提出的。', 置信度: 0.9771

**总结**:
答案中存在幻觉，需要进一步检查和修正。幻觉部分已高亮标注，并提供了验证链接以便核实。        

**高亮标注的答案**:

相对论<span class='hallucination' id='hallucination-1' data-confidence='0.9771'>是牛顿在1687年提出的。</span></span>

✨ 高亮结果:
 相对论<span class='hallucination' id='hallucination-1' data-confidence='0.9771'>是牛顿在1687年提出的。</span>
.

==================================== warnings summary=================================
test/testevaluator.py::test_hallucination_detection_with_highlight
  D:\Anaconda\envs\graphrag\lib\site-packages\lettucedetect\models\inference.py:85: UserWarning: To copy construct from a tensor, it is recommended to use sourceTensor.detach().clone() or sourceTensor.detach().clone().requires_grad_(True), rather than torch.tensor(sourceTensor).
    labels = torch.tensor(labels, device=self.device)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
### 网页端演示

非调试模式下的问答：

![no-debug](./assets/web-nodebug.png)

调试模式下的问答（包含轨迹追踪（langgraph节点）、命中的知识图谱与文档源内容，知识图谱推理问答等）：

![debug1](./assets/web-debug1.png)

![debug2](./assets/web-debug2.png)

![debug3](./assets/web-debug3.png)

## 🔮 未来规划

1. **自动化数据获取**：
   - 加入定时爬虫功能，替代当前的手动文档更新方式
   - 实现资源自动发现与增量爬取

2. **图谱构建优化**：
   

3. **Agent 性能优化**：
   - 提升 Agent 框架响应速度
   - 优化多 Agent 协作机制

4. **实现联网搜索链接验证功能**

5. **幻觉模型改进**：
   - 
    

## 🙏 参考与致谢

- [GraphRAG](https://github.com/microsoft/graphrag) – 微软开源的知识图谱增强 RAG 框架  
- [llm-graph-builder](https://github.com/neo4j-labs/llm-graph-builder) – Neo4j 官方 LLM 建图工具  
- [LightRAG](https://github.com/HKUDS/LightRAG) – 轻量级知识增强生成方案  
- [deep-searcher](https://github.com/zilliztech/deep-searcher) – Zilliz团队开源的私域语义搜索框架  
- [ragflow](https://github.com/infiniflow/ragflow) – 企业级 RAG 系统
