from typing import List, Dict, Union, Any, AsyncGenerator
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import tools_condition
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
import asyncio
import re
import json

from config.prompt import LC_SYSTEM_PROMPT, REDUCE_SYSTEM_PROMPT, NAIVE_PROMPT  # 统一Prompt
from config.settings import response_type
from search.tool.local_search_tool import LocalSearchTool
from search.tool.global_search_tool import GlobalSearchTool
from search.tool.hybrid_tool import HybridSearchTool
from search.tool.naive_search_tool import NaiveSearchTool
from agent.base import BaseAgent


class RetrievalAgent(BaseAgent):
    """
    核心检索Agent，支持多种检索策略，包括本地搜索、全局搜索、混合搜索和简单向量搜索。
    """

    def __init__(self, retrieval_strategy: str = "hybrid"):
        """
        初始化检索Agent.

        Args:
            retrieval_strategy (str): 检索策略, 可以是 "local", "global", "hybrid", "naive".
        """
        self.retrieval_strategy = retrieval_strategy
        self.cache_dir = f"./cache/retrieval_agent_{retrieval_strategy}"

        # 初始化搜索工具
        if retrieval_strategy == "local":
            self.search_tool = LocalSearchTool()
        elif retrieval_strategy == "global":
            self.search_tool = GlobalSearchTool()
        elif retrieval_strategy == "hybrid":
            self.search_tool = HybridSearchTool()
        elif retrieval_strategy == "naive":
            self.search_tool = NaiveSearchTool()
        else:
            raise ValueError(f"不支持的检索策略: {retrieval_strategy}")

        super().__init__(cache_dir=self.cache_dir)

    def _setup_tools(self) -> List[Any]:
        """设置工具."""
        if self.retrieval_strategy == "global":
            return [self.search_tool.search]
        elif self.retrieval_strategy == "hybrid":
            return [self.search_tool.get_tool(), self.search_tool.get_global_tool()]
        else:
            return [self.search_tool.get_tool()]

    def _add_retrieval_edges(self, workflow) -> None:
        """添加从检索到生成的边."""

        if self.retrieval_strategy == "graph":
            # GraphAgent的路由逻辑
            workflow.add_node("reduce", self._reduce_node)
            workflow.add_conditional_edges(
                "retrieve",
                self._grade_documents,
                {"generate": "generate", "reduce": "reduce"},
            )
            workflow.add_edge("reduce", END)
        else:
            # 其他策略：简单的从检索到生成
            workflow.add_edge("retrieve", "generate")

    def _extract_keywords(self, query: str) -> Dict[str, List[str]]:
        """提取查询关键词."""

        cached_keywords = self.cache_manager.get(f"keywords:{query}")
        if cached_keywords:
            return cached_keywords

        try:
            if self.retrieval_strategy == "hybrid":
                keywords = self.search_tool.extract_keywords(query)
            elif self.retrieval_strategy == "graph":
                #  GraphAgent的关键词提取逻辑
                prompt = f"""提取以下查询的关键词:
                    查询: {query}
                    
                    请提取两类关键词:
                    1. 低级关键词: 具体实体、名称、术语
                    2. 高级关键词: 主题、概念、领域
                    
                    以JSON格式返回。
                    """

                result = self.llm.invoke(prompt)
                content = result.content if hasattr(result, "content") else result

                json_match = re.search(r"({.*})", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    keywords = json.loads(json_str)
                    if not isinstance(keywords, dict):
                        keywords = {}
                    if "low_level" not in keywords:
                        keywords["low_level"] = []
                    if "high_level" not in keywords:
                        keywords["high_level"] = []
                else:
                    keywords = {"low_level": [], "high_level": []}  # 提取失败
            elif self.retrieval_strategy == "naive":
                keywords = {"low_level": [], "high_level": []}  # NaiveAgent 不提取关键词
            else:
                keywords = {"low_level": [], "high_level": []}  # 默认情况
        except Exception as e:
            print(f"关键词提取失败: {e}")
            keywords = {"low_level": [], "high_level": []}  # 提取失败

        self.cache_manager.set(f"keywords:{query}", keywords)
        return keywords

    def _grade_documents(self, state) -> str:
        """评估文档相关性 - 仅用于GraphAgent."""

        messages = state["messages"]
        retrieve_message = messages[-2]

        tool_calls = retrieve_message.additional_kwargs.get("tool_calls", [])
        if (
            tool_calls
            and tool_calls[0].get("function", {}).get("name") == "global_retriever"
        ):
            self._log_execution("grade_documents", messages, "reduce")
            return "reduce"

        try:
            question = messages[-3].content
            docs = messages[-1].content
        except Exception as e:
            print(f"文档评分出错: {e}")
            return "generate"

        if not docs or len(docs) < 100:
            print("文档内容不足，尝试使用本地搜索")
            try:
                local_result = self.local_tool.search(question)
                if local_result and len(local_result) > 100:
                    messages[-1].content = local_result
            except Exception as e:
                print(f"本地搜索失败: {e}")

        keywords = []
        if hasattr(messages[-3], 'additional_kwargs') and messages[-3].additional_kwargs:
            kw_data = messages[-3].additional_kwargs.get("keywords", {})
            if isinstance(kw_data, dict):
                keywords = kw_data.get("low_level", []) + kw_data.get("high_level", [])

        if not keywords:
            keywords = [word for word in question.lower().split() if len(word) > 2]

        docs_text = docs.lower() if docs else ""
        matches = sum(1 for keyword in keywords if keyword.lower() in docs_text)
        match_rate = matches / len(keywords) if keywords else 0

        self._log_execution(
            "grade_documents",
            {"question": question, "keywords": keywords, "match_rate": match_rate, "docs_length": len(docs_text)},
            f"匹配率: {match_rate}",
        )

        return "generate"  # 简化，总是返回 "generate"

    def _generate_node(self, state) -> Dict[str, List[AIMessage]]:
        """生成回答节点逻辑."""

        messages = state["messages"]
        try:
            question = messages[-3].content if len(messages) >= 3 else "未找到问题"
        except Exception:
            question = "无法获取问题"

        try:
            docs = messages[-1].content if messages[-1] else "未找到相关信息"
        except Exception:
            docs = "无法获取检索结果"

        global_result = self.global_cache_manager.get(question)
        if global_result:
            self._log_execution(
                "generate",
                {"question": question, "docs_length": len(docs)},
                "全局缓存命中",
            )
            return {"messages": [AIMessage(content=global_result)]}

        thread_id = state.get("configurable", {}).get("thread_id", "default")
        cached_result = self.cache_manager.get(question, thread_id=thread_id)
        if cached_result:
            self._log_execution(
                "generate",
                {"question": question, "docs_length": len(docs)},
                "会话缓存命中",
            )
            self.global_cache_manager.set(question, cached_result)
            return {"messages": [AIMessage(content=cached_result)]}

        if self.retrieval_strategy != "naive":
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", LC_SYSTEM_PROMPT),
                    (
                        "human",
                        """
                        ---分析报告--- 
                        以下是检索到的相关信息，按重要性排序：
                        
                        {context}
                        
                        用户的问题是：
                        {question}
                        
                        请以清晰、全面的方式回答问题，确保：
                        1. 回答结合了检索到的低级（实体细节）和高级（主题概念）信息
                        2. 使用三级标题(###)组织内容，增强可读性
                        3. 结尾处用"#### 引用数据"标记引用来源
                        """,
                    ),
                ]
            )
        else:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", NAIVE_PROMPT),
                    (
                        "human",
                        """
                        ---检索结果--- 
                        {context}
                        
                        问题：
                        {question}
                        """,
                    ),
                ]
            )

        rag_chain = prompt | self.llm | StrOutputParser()
        try:
            response = rag_chain.invoke(
                {"context": docs, "question": question, "response_type": response_type}
            )

            if response and len(response) > 10:
                self.cache_manager.set(question, response, thread_id=thread_id)
                self.global_cache_manager.set(question, response)

            self._log_execution(
                "generate",
                {"question": question, "docs_length": len(docs)},
                response,
            )

            return {"messages": [AIMessage(content=response)]}
        except Exception as e:
            error_msg = f"生成回答时出错: {str(e)}"
            self._log_execution(
                "generate_error",
                {"question": question, "docs_length": len(docs)},
                error_msg,
            )
            return {
                "messages": [
                    AIMessage(content=f"抱歉，我无法回答这个问题。技术原因: {str(e)}")]}

    def _reduce_node(self, state) -> Dict[str, List[AIMessage]]:
        """处理全局搜索的Reduce节点逻辑 - 仅用于GraphAgent."""

        messages = state["messages"]
        question = messages[-3].content
        docs = messages[-1].content

        cached_result = self.cache_manager.get(f"reduce:{question}")
        if cached_result:
            self._log_execution(
                "reduce",
                {"question": question, "docs_length": len(docs)},
                cached_result,
            )
            return {"messages": [AIMessage(content=cached_result)]}

        reduce_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REDUCE_SYSTEM_PROMPT),
                (
                    "human",
                    """
                    ---分析报告--- 
                    {report_data}

                    用户的问题是：
                    {question}
                    """,
                ),
            ]
        )

        reduce_chain = reduce_prompt | self.llm | StrOutputParser()
        response = reduce_chain.invoke(
            {"report_data": docs, "question": question, "response_type": response_type}
        )

        self.cache_manager.set(f"reduce:{question}", response)

        self._log_execution(
            "reduce",
            {"question": question, "docs_length": len(docs)},
            response,
        )

        return {"messages": [AIMessage(content=response)]}

    async def _generate_node_stream(self, state) -> AsyncGenerator[str, None]:
        """生成回答节点逻辑的流式版本."""

        messages = state["messages"]

        try:
            question = messages[-3].content if len(messages) >= 3 else "未找到问题"
        except Exception:
            question = "无法获取问题"

        try:
            docs = messages[-1].content if messages[-1] else "未找到相关信息"
        except Exception:
            docs = "无法获取检索结果"

        thread_id = state.get("configurable", {}).get("thread_id", "default")

        cached_result = self.cache_manager.get(
            f"generate:{question}", thread_id=thread_id
        )
        if cached_result:
            chunks = re.split(r"([.!?。！？]\s*)", cached_result)
            buffer = ""

            for i in range(0, len(chunks)):
                buffer += chunks[i]

                if (i % 2 == 1) or len(buffer) >= 40:
                    yield buffer
                    buffer = ""
                    await asyncio.sleep(0.01)

            if buffer:
                yield buffer
            return

        if self.retrieval_strategy != "naive":
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", LC_SYSTEM_PROMPT),
                    (
                        "human",
                        """
                        ---分析报告--- 
                        以下是检索到的相关信息，按重要性排序：
                        
                        {context}
                        
                        用户的问题是：
                        {question}
                        
                        请以清晰、全面的方式回答问题，确保：
                        1. 回答结合了检索到的低级（实体细节）和高级（主题概念）信息
                        2. 使用三级标题(###)组织内容，增强可读性
                        3. 结尾处用"#### 引用数据"标记引用来源
                        """,
                    ),
                ]
            )
        else:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", NAIVE_PROMPT),
                    (
                        "human",
                        """
                        ---检索结果--- 
                        {context}
                        
                        问题：
                        {question}
                        """,
                    ),
                ]
            )

        rag_chain = prompt | self.llm | StrOutputParser()
        response = rag_chain.invoke(
            {"context": docs, "question": question, "response_type": response_type}
        )

        sentences = re.split(r"([.!?。！？]\s*)", response)
        buffer = ""

        for i in range(len(sentences)):
            buffer += sentences[i]
            if i % 2 == 1 or len(buffer) >= 40:
                yield buffer
                buffer = ""
                await asyncio.sleep(0.01)

        if buffer:
            yield buffer

    async def _agent_node_async(self, state):
        """Agent 节点逻辑的异步版本"""
        messages = state["messages"]
        
        # 提取关键词优化查询
        if len(messages) > 0 and isinstance(messages[-1], HumanMessage):
            query = messages[-1].content
            try:
                keywords = self._extract_keywords(query)
                
                # 记录关键词
                self._log_execution("extract_keywords", query, keywords)
                
                # 增强消息，添加关键词信息
                if keywords:
                    # 创建一个新的消息，带有关键词元数据
                    enhanced_message = HumanMessage(
                        content=query,
                        additional_kwargs={"keywords": keywords}
                    )
                    # 替换原始消息
                    messages = messages[:-1] + [enhanced_message]
            except Exception as e:
                print(f"关键词提取异步处理失败: {e}")
        
        # 使用工具处理请求
        model = self.llm.bind_tools(self.tools)
        
        # 在线程池中运行同步代码，避免阻塞事件循环
        def sync_invoke():
            return model.invoke(messages)
            
        response = await asyncio.get_event_loop().run_in_executor(None, sync_invoke)
        
        self._log_execution("agent_async", messages, response)
        return {"messages": [response]}

    async def _retrieve_node_async(self, state):
        """检索节点逻辑的异步版本"""
        # 这个默认实现只是调用ToolNode的同步版本
        # 在线程池中运行同步代码，避免阻塞事件循环
        def sync_retrieve():
            tool_node = ToolNode(self.tools)
            return tool_node.invoke(state)
            
        return await asyncio.get_event_loop().run_in_executor(None, sync_retrieve)

    async def _reduce_node_async(self, state):
        """Reduce节点逻辑的异步版本"""
        # 在线程池中运行同步代码，避免阻塞事件循环
        def sync_reduce():
            return self._reduce_node(state)
            
        return await asyncio.get_event_loop().run_in_executor(None, sync_reduce)

    async def _stream_process(
        self, inputs: Dict[str, List[HumanMessage]], config: Dict[str, Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """实现流式处理过程."""

        thread_id = config.get("configurable", {}).get("thread_id", "default")
        query = inputs["messages"][-1].content

        cached_response = self.cache_manager.get(query.strip(), thread_id=thread_id)
        if cached_response:
            chunks = re.split(r"([.!?。！？]\s*)", cached_response)
            buffer = ""

            for i in range(0, len(chunks)):
                buffer += chunks[i]

                if (i % 2 == 1) or len(buffer) >= 40:
                    yield buffer
                    buffer = ""
                    await asyncio.sleep(0.01)

            if buffer:
                yield buffer
            return

        workflow_state = {"messages": [HumanMessage(content=query)]}

        yield "**正在分析问题**...\n\n"

        agent_output = await self._agent_node_async(workflow_state)
        workflow_state = {"messages": workflow_state["messages"] + agent_output["messages"]}

        tool_decision = tools_condition(workflow_state)
        if tool_decision == "tools":
            yield "**正在检索相关信息**...\n\n"

            retrieve_output = await self._retrieve_node_async(workflow_state)
            workflow_state = {
                "messages": workflow_state["messages"] + retrieve_output["messages"]
            }

            if self.retrieval_strategy == "graph":
                #  GraphAgent 的流式处理逻辑
                last_message = workflow_state["messages"][-1]
                content = last_message.content if hasattr(last_message, "content") else ""

                if not content or len(content) < 100:
                    try:
                        local_result = self.local_tool.search(query)
                        if local_result and len(local_result) > 100:
                            workflow_state["messages"][-1] = ToolMessage(
                                content=local_result,
                                tool_call_id="local_search",  # 使用适当的工具调用 ID
                                name=self.local_tool.get_tool().name,
                            )
                    except Exception as e:
                        print(f"本地搜索失败: {e}")

                workflow_state = {"messages": workflow_state["messages"]}
                grade_output = self._grade_documents(workflow_state)
                if grade_output == "reduce":
                    reduce_output = await self._reduce_node_async(workflow_state)
                    workflow_state = {
                        "messages": workflow_state["messages"] + reduce_output["messages"]
                    }
                else:
                    workflow_state = {"messages": workflow_state["messages"]}

            yield "**正在生成回答**...\n\n"
            generate_output = self._generate_node_stream(workflow_state)
            async for chunk in generate_output:
                yield chunk
        else:
            yield "**正在生成回答**...\n\n"
            generate_output = self._generate_node_stream(workflow_state)
            async for chunk in generate_output:
                yield chunk

        if self.cache_manager:
            final_response = ""
            for message in workflow_state["messages"]:
                if isinstance(message, AIMessage):
                    final_response = message.content
                    break
            if final_response:
                self.cache_manager.set(query.strip(), final_response, thread_id=thread_id)

    def close(self):
        """关闭资源."""
        if hasattr(self, "search_tool") and hasattr(self.search_tool, "close"):
            self.search_tool.close()
        super().close()
