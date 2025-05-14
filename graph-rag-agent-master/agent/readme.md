# Agent 模块

`agent` 模块是项目的核心交互层，整合了多种搜索和评估工具，为用户提供灵活高效的知识检索与推理服务。支持从基础向量检索到多 Agent 协同推理，具备强大的可扩展性和流式响应能力。

## 📁 目录结构

```
agent/
├── __init__.py                  # 模块初始化
├── base.py                      # BaseAgent 抽象基类
├── deep_research_agent.py       # 深度研究 Agent 实现
├── evaluator_agent.py           # 幻觉评估 Agent 实现
├── retrieval_agent.py           # 核心检索 Agent 实现（支持多种策略）
```

## 🧠 实现理念

模块基于 [LangGraph](https://github.com/langchain-ai/langgraph) 框架构建，采用 **状态图（StateGraph）+ 多节点工作流** 的方式组织 Agent 操作。使用统一的 `BaseAgent` 抽象类管理缓存、日志、工具绑定等共通行为。

## ✨ 核心 Agent 一览

### 1. RetrievalAgent – 核心检索 Agent

支持多种检索策略：

- `naive`: 简单向量搜索
- `local`: 结构化或嵌入式本地搜索
- `global`: 全局知识或跨域检索
- `hybrid`: 融合局部细节与高层语义的混合搜索

核心特性：

- 自动关键词提取与缓存
- 状态图中支持从 `retrieve → generate` 的路径，以及 `reduce` 路径用于全局结果整合
- 支持流式响应和智能缓存
- 特殊处理“GraphAgent”策略下的文档评分与结果缩减

### 2. DeepResearchAgent – 深度研究 Agent

专为复杂问题、多步骤推理设计的 Agent：

- 显式思考过程（<think>块）
- 多回合推理与迭代搜索
- 社区增强、知识图谱探索
- 推理链分析与矛盾检测

支持多种模式：

- 标准模式：基于 `DeepResearchTool` 进行一问一答
- 增强模式：结合 `DeeperResearchTool` 实现知识图谱路径探索、推理可视化、链式逻辑追踪等

额外功能：

- `explore_knowledge()`：基于关键词触发图谱路径追踪
- `analyze_reasoning_chain()`：分析 reasoning 路径
- `detect_contradictions()`：检测生成内容中的冲突点

### 3. EvaluatorAgent – 幻觉检测 Agent

负责评估答案内容的真实性，检测生成幻觉（hallucinations）：

- 集成 `LettuceDetect` 模型进行上下文对齐检测
- 返回高亮幻觉文本和置信度评分
- 支持评估报告生成和关键词提取
- 评估路径为 `retrieve → evaluate → generate`，自动插入中间评估步骤

## 🔄 工作流结构设计

所有 Agent 继承自 `BaseAgent`，通过以下典型方法组合成工作流：

```python
def _setup_graph(self):
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", self._agent_node)
    workflow.add_node("retrieve", ToolNode(self.tools))
    workflow.add_node("generate", self._generate_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition, {
        "tools": "retrieve",
        END: END
    })
    self._add_retrieval_edges(workflow)
    workflow.add_edge("generate", END)
    self.graph = workflow.compile(checkpointer=self.memory)
```

## 🧪 使用示例

```python
from agent.retrieval_agent import RetrievalAgent

agent = RetrievalAgent(retrieval_strategy="hybrid")
response = agent.ask("量子计算与人工智能的结合有哪些前景？")
print(response)
```

## 📌 使用场景推荐

| 使用场景                     | 推荐 Agent          | 特点说明                            |
| ---------------------------- | ------------------- | ----------------------------------- |
| 基础问答、文档问答           | `RetrievalAgent`    | 支持多策略检索，轻量高效            |
| 深度研究、路径探索、链式推理 | `DeepResearchAgent` | 显式思考、多轮分析、图谱探索        |
| 幻觉检测、可信度评估         | `EvaluatorAgent`    | LettuceDetect支持幻觉高亮和解释报告 |