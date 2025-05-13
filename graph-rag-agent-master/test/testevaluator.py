import pytest
from langchain_core.messages import HumanMessage, AIMessage
from agent.evaluator_agent import EvaluatorAgent  # 替换为实际路径

def test_hallucination_detection_with_highlight():
    agent = EvaluatorAgent()

    state = {
        "messages": [
            HumanMessage(content="牛顿提出了万有引力定律。"),
            HumanMessage(content="谁提出了相对论？"),
            AIMessage(content="相对论是牛顿在1687年提出的。")
        ]
    }

    # 执行评估节点
    result = agent._evaluate_node(state)

    # 输出报告内容
    content = result["messages"][0].content
    highlighted = result["highlighted_answer"]

    # 断言结果正确性
    assert isinstance(content, str)
    assert "幻觉检测报告" in content
    assert "高亮标注" in content
    assert result["has_hallucinations"] is True
    assert result["hallucination_count"] > 0
    assert "<span class='hallucination'" in highlighted

    # 输出调试信息
    print("\n✅ 报告内容:\n", content)
    print("\n✨ 高亮结果:\n", highlighted)
