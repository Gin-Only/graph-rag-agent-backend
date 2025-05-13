from typing import List, Dict, Union, Any, AsyncGenerator
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END
import asyncio
import re
from lettucedetect.models.inference import HallucinationDetector  # 导入幻觉检测器

from agent.base import BaseAgent  # 确保BaseAgent在同一目录或正确配置了导入路径


class EvaluatorAgent(BaseAgent):
    """
    评估Agent，用于评估检索生成应用中的幻觉。
    集成了LettuceDetect模型进行幻觉检测。
    """

    def __init__(self, model_path="KRLabsOrg/lettucedect-base-modernbert-en-v1"):
        """
        初始化评估Agent。

        Args:
            model_path (str): LettuceDetect模型的路径。默认为'KRLabsOrg/lettucedect-base-modernbert-en-v1'。
        """
        self.model_path = model_path
        self.cache_dir = "./cache/evaluator_agent"  # 评估Agent的缓存目录
        super().__init__(cache_dir=self.cache_dir)
        self.hallucination_detector = HallucinationDetector(
            method="transformer", model_path=self.model_path
        )

    def _setup_tools(self) -> List[Any]:
        """设置工具（当前不需要）."""
        return []

    def _add_retrieval_edges(self, workflow) -> None:
        """添加评估节点和相关边的连接"""
        # 添加评估节点
        workflow.add_node("evaluate", self._evaluate_node)
        
        # 从检索到评估的边
        workflow.add_edge("retrieve", "evaluate")
        
        # 从评估到生成的边
        workflow.add_edge("evaluate", "generate")

    def _create_prompt(self) -> ChatPromptTemplate:
        """
        创建用于生成评估报告的提示模板。
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个负责评估生成内容质量的助手。你的任务是分析给定的上下文、问题和答案，"
                    "并判断答案中是否存在幻觉（即，答案中的信息是否在上下文中找不到）。"
                    "使用LettuceDetect模型进行幻觉检测，并生成包含检测结果和总结的报告。",
                ),
                (
                    "human",
                    "---上下文---\n{context}\n\n---问题---\n{question}\n\n---答案---\n{answer}\n",
                ),
            ]
        )
        return prompt

    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """
        从输入文本中提取关键词。

        Args:
            text (str): 输入文本。

        Returns:
            Dict[str, List[str]]: 包含low_level和high_level关键词的字典。
        """
        # 使用正则表达式提取中英文关键词
        keywords = re.findall(r'\b[\w\u4e00-\u9fa5]{2,}\b', text.lower())
        # 过滤过长或过短的关键词
        filtered_keywords = [k for k in keywords if len(k) > 1 and len(k) < 15]
        # 返回字典格式，将所有关键词作为low_level关键词
        return {
            "low_level": filtered_keywords,
            "high_level": []  # 暂时不实现高级关键词提取
        }

    def _generate_node(self, state) -> Dict[str, List[AIMessage]]:
        """
        生成评估节点。

        Args:
            state (dict): 包含上下文、问题和答案的状态。

        Returns:
            dict: 包含评估报告的消息。
        """
        messages = state["messages"]
        context = messages[-3].content if len(messages) >= 3 else ""
        question = messages[-2].content if len(messages) >= 2 else ""
        answer = messages[-1].content if len(messages) >= 1 else ""

        try:
            # 提取问题和答案中的关键词
            question_keywords = self._extract_keywords(question)
            answer_keywords = self._extract_keywords(answer)

            # 使用LettuceDetect进行幻觉检测
            predictions = self.HallucinationDetector(method="transformer", model_path="KRLabsOrg/lettucedect-base-modernbert-en-v1").predict(
                context=[context], question=question, answer=answer, output_format="spans"
            )

            # 生成评估报告
            report = f"<span style='color: green'>**幻觉检测报告**:\n\n"
            
            # 创建高亮标注的答案副本
            highlighted_answer = answer
            
            if predictions:
                # 按照起始位置降序排序，以便从后向前替换文本（避免位置偏移）
                sorted_predictions = sorted(predictions, key=lambda p: p['start'], reverse=True)
                
                report += "检测到以下幻觉片段:\n"
                
                # 为每个幻觉片段生成搜索关键词
                for i, p in enumerate(sorted_predictions):
                    # 生成搜索关键词（使用幻觉文本作为搜索词）
                    search_term = p['text']
                    # 限制搜索词长度，避免过长
                    if len(search_term) > 50:
                        search_term = search_term[:50] + "..."
                    
                    # 生成验证链接（使用搜索引擎URL）
                    #verification_link = f"https://www.google.com/search?q={search_term}"
                    
                    # 在答案中高亮标注幻觉文本
                    # 使用HTML标记进行高亮（前端需要支持HTML渲染）
                    hallucination_id = f"hallucination-{i+1}"
                    highlight_html = f"<span class='hallucination' id='{hallucination_id}' data-confidence='{p['confidence']:.4f}' data-verification='{verification_link}'>{p['text']}</span>"
                    
                    # 在答案副本中替换幻觉文本为高亮版本
                    start, end = p['start'], p['end']
                    highlighted_answer = highlighted_answer[:start] + highlight_html + highlighted_answer[end:]
                    
                    # 添加幻觉片段详细信息到报告
                    report += f"\n{i+1}. 幻觉文本: {p['text']}\n"
                    report += f"   置信度: {p['confidence']:.4f}\n"
                    #report += f"   验证链接: {verification_link}\n"
            else:
                report += "未检测到幻觉。这表明：\n"
                report += "1. 回答内容与上下文信息保持一致\n"
                report += "2. 没有发现不实或无法验证的陈述\n"
                report += "3. 生成的内容可信度较高\n"

            report += "\n**总结**:\n"
            if predictions:
                report += (
                    "答案中存在幻觉，需要进一步检查和修正。幻觉部分已高亮标注，并提供了验证链接以便核实。\n"
                )
                report += "\n**高亮标注的答案**:\n\n"
                report += highlighted_answer
            else:
                report += "答案似乎与上下文一致，没有明显的幻觉。\n"

            self._log_execution(
                "evaluate",
                {"question": question, "answer": answer, "context": context},
                report,
            )
            
            # 在返回结果前关闭绿色字体标签
            report += "</span>"
            
            # 返回包含原始报告和高亮标注答案的结果
            result = {
                "messages": [AIMessage(content=report)],
                "highlighted_answer": highlighted_answer if predictions else answer,
                "has_hallucinations": len(predictions) > 0,
                "hallucination_count": len(predictions),
                "question_keywords": question_keywords,
                "answer_keywords": answer_keywords
            }
            return result

        except Exception as e:
            error_msg = f"评估过程中发生错误: {e}"
            self._log_execution(
                "evaluate_error",
                {"question": question, "answer": answer, "context": context},
                error_msg,
            )
            return {
                "messages": [
                    AIMessage(content=f"抱歉，评估过程中出现错误，无法完成评估。错误信息: {error_msg}")
                ]
            }

    def _evaluate_node(self, state) -> Dict[str, List[AIMessage]]:
        """
        评估节点逻辑：使用LettuceDetect检测幻觉并生成报告。
        支持高亮标注幻觉文本并提供验证链接。

        Args:
            state (dict): 包含上下文、问题和答案的状态。

        Returns:
            dict: 包含评估报告的消息。
        """
        messages = state["messages"]
        context = messages[-3].content if len(messages) >= 3 else ""
        question = messages[-2].content if len(messages) >= 2 else ""
        answer = messages[-1].content if len(messages) >= 1 else ""

        try:
            # 使用LettuceDetect进行幻觉检测
            predictions = self.hallucination_detector.predict(
                context=[context], question=question, answer=answer, output_format="spans"
            )

            # 生成评估报告
            report = f"<span style='color: green'>**幻觉检测报告**:\n\n"
            
            # 创建高亮标注的答案副本
            highlighted_answer = answer
            
            if predictions:
                # 按照起始位置降序排序，以便从后向前替换文本（避免位置偏移）
                sorted_predictions = sorted(predictions, key=lambda p: p['start'], reverse=True)
                
                report += "检测到以下幻觉片段:\n"
                
                # 为每个幻觉片段生成搜索关键词
                for i, p in enumerate(sorted_predictions):
                    # 生成搜索关键词（使用幻觉文本作为搜索词）
                    search_term = p['text']
                    # 限制搜索词长度，避免过长
                    if len(search_term) > 50:
                        search_term = search_term[:50] + "..."
                    
                    # 生成验证链接（使用搜索引擎URL）
                    #verification_link = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                    
                    # 在报告中添加带链接的幻觉信息
                    report += f"- 文本: '{p['text']}', 置信度: {p['confidence']:.4f}\n"
                    #report += f"  验证链接: [{search_term}]({verification_link})\n"
                    
                    # 在答案中高亮标注幻觉文本
                    # 使用HTML标记进行高亮（前端需要支持HTML渲染）
                    hallucination_id = f"hallucination-{i+1}"
                    highlight_html = f"<span class='hallucination' id='{hallucination_id}' data-confidence='{p['confidence']:.4f}'>{p['text']}</span>"

                    
                    # 在答案副本中替换幻觉文本为高亮版本
                    start, end = p['start'], p['end']
                    highlighted_answer = highlighted_answer[:start] + highlight_html + highlighted_answer[end:]
            else:
                report += "未检测到幻觉。\n"

            report += "\n**总结**:\n"
            if predictions:
                report += (
                    "答案中存在幻觉，需要进一步检查和修正。幻觉部分已高亮标注，并提供了验证链接以便核实。\n"
                )
                report += "\n**高亮标注的答案**:\n\n"
                report += highlighted_answer
            else:
                report += "答案似乎与上下文一致，没有明显的幻觉。\n"

            self._log_execution(
                "evaluate",
                {"question": question, "answer": answer, "context": context},
                report,
            )
            
            # 在返回结果前关闭绿色字体标签
            report += "</span>"
            
            # 返回包含原始报告和高亮标注答案的结果
            result = {
                "messages": [AIMessage(content=report)],
                "highlighted_answer": highlighted_answer if predictions else answer,
                "has_hallucinations": len(predictions) > 0,
                "hallucination_count": len(predictions)
            }
            return result

        except Exception as e:
            error_msg = f"评估过程中发生错误: {e}"
            self._log_execution(
                "evaluate_error",
                {"question": question, "answer": answer, "context": context},
                error_msg,
            )
            return {
                "messages": [
                    AIMessage(content=f"抱歉，评估过程中出现错误，无法完成评估。错误信息: {error_msg}")
                ]
            }

    async def _stream_process(
        self, inputs: Dict[str, List[HumanMessage]], config: Dict[str, Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """实现流式处理过程（当前不需要，保留以备将来使用）."""
        yield "评估Agent不支持流式输出。"

    def close(self):
        """关闭资源."""
        if hasattr(self, "hallucination_detector") and hasattr(
            self.hallucination_detector, "close"
        ):
            self.hallucination_detector.close()
        super().close()

