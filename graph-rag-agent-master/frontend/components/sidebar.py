import streamlit as st
import json
from datetime import datetime
from utils.api import clear_chat
from frontend_config.settings import examples

def save_current_chat():
    """保存当前对话到历史记录"""
    if len(st.session_state.messages) > 0:
        # 生成对话标题（使用第一个用户消息的前30个字符）
        first_user_msg = None
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                first_user_msg = msg["content"]
                break
        
        if first_user_msg:
            title = first_user_msg[:30] + "..." if len(first_user_msg) > 30 else first_user_msg
        else:
            title = f"对话 {len(st.session_state.chat_history) + 1}"
        
        # 创建历史记录条目
        history_item = {
            "id": len(st.session_state.chat_history),
            "title": title,
            "messages": st.session_state.messages.copy(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent_type": st.session_state.agent_type
        }
        
        # 添加到历史记录（最新的在前面）
        st.session_state.chat_history.insert(0, history_item)
        
        # 限制历史记录数量（最多保存20个对话）
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[:20]

def load_chat_history(history_item):
    """加载历史对话"""
    st.session_state.messages = history_item["messages"].copy()
    st.session_state.current_chat_title = history_item["title"]
    st.rerun()

def delete_chat_history(history_id):
    """删除指定的历史对话"""
    st.session_state.chat_history = [
        item for item in st.session_state.chat_history 
        if item["id"] != history_id
    ]

def display_sidebar():
    """显示应用侧边栏"""
    with st.sidebar:
        st.title("📚 GraphRAG")
        st.markdown("---")
        
        # 历史对话记录部分
        st.header("💬 对话历史")
        
        # 保存当前对话按钮
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("💾 保存当前对话", key="save_chat", use_container_width=True):
                if len(st.session_state.messages) > 0:
                    save_current_chat()
                    st.success("对话已保存！")
                else:
                    st.warning("当前没有对话内容可保存")
        
        with col2:
            # 展开/收起历史记录
            if st.button("📋" if not st.session_state.show_history else "🔼", 
                        key="toggle_history"):
                st.session_state.show_history = not st.session_state.show_history
                st.rerun()
        
        # 显示历史对话列表
        if st.session_state.show_history and len(st.session_state.chat_history) > 0:
            st.subheader("历史对话记录")
            
            # 添加搜索框
            search_term = st.text_input("🔍 搜索对话", placeholder="输入关键词搜索...", key="history_search")
            
            # 过滤历史记录
            filtered_history = st.session_state.chat_history
            if search_term:
                filtered_history = [
                    item for item in st.session_state.chat_history
                    if search_term.lower() in item["title"].lower()
                ]
            
            # 显示历史记录
            for i, history_item in enumerate(filtered_history[:10]):  # 只显示前10个
                with st.container():
                    col1, col2, col3 = st.columns([6, 1, 1])
                    
                    with col1:
                        # 对话标题和时间
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; margin: 2px 0;">
                            <div style="font-weight: bold; font-size: 14px;">{history_item['title']}</div>
                            <div style="font-size: 12px; color: #666;">{history_item['timestamp']} | {history_item['agent_type']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # 加载按钮
                        if st.button("📂", key=f"load_{history_item['id']}", 
                                   help="加载此对话"):
                            load_chat_history(history_item)
                    
                    with col3:
                        # 删除按钮
                        if st.button("🗑️", key=f"delete_{history_item['id']}", 
                                   help="删除此对话"):
                            delete_chat_history(history_item['id'])
                            st.rerun()
        
        elif st.session_state.show_history:
            st.info("还没有保存的对话记录")
        
        st.markdown("---")
        
        # Agent选择部分
        st.header("Agent 选择")
        agent_options = ["retrieval_agent", "deep_research_agent", "evaluator_agent"]
        
        def agent_changed():
            # Agent变化的回调函数，同步到主页面
            if "agent_type_main" in st.session_state:
                st.session_state.agent_type_main = st.session_state.agent_type

        try:
            current_agent_index = agent_options.index(st.session_state.agent_type)
        except ValueError:
            current_agent_index = 0 # Default to the first option

        st.radio(
            "选择检索策略:",
            options=agent_options,
            index=current_agent_index,
            help="retrieval_agent：使用混合搜索方式；deep_research_agent：私域深度研究；evaluator_agent：检测幻觉Agent",
            key="agent_type", # 直接使用agent_type作为key
            on_change=agent_changed
        )

        # 思考过程选项 - 仅当选择 deep_research_agent 时显示
        if st.session_state.agent_type == "deep_research_agent":
            def show_thinking_sidebar_changed():
                # 同步到主页面
                if "show_thinking_main" in st.session_state:
                    st.session_state.show_thinking_main = st.session_state.show_thinking
            
            # 思考过程选项
            show_thinking = st.checkbox("显示推理过程", 
                                    value=st.session_state.get("show_thinking", False), 
                                    key="show_thinking",  # 直接使用show_thinking作为key
                                    help="显示AI的思考过程",
                                    on_change=show_thinking_sidebar_changed)
            
            def use_deeper_sidebar_changed():
                # 同步到主页面
                if "use_deeper_tool_main" in st.session_state:
                    st.session_state.use_deeper_tool_main = st.session_state.use_deeper_tool
            
            # 添加增强版工具选择
            use_deeper = st.checkbox("使用增强版研究工具", 
                                value=st.session_state.get("use_deeper_tool", True), 
                                key="use_deeper_tool",  # 直接使用use_deeper_tool作为key
                                help="启用社区感知和知识图谱增强功能",
                                on_change=use_deeper_sidebar_changed)
            
            # 添加工具说明
            if st.session_state.use_deeper_tool:
                st.info("增强版研究工具：整合社区感知和知识图谱增强，实现更深度的多级推理")
            else:
                st.info("标准版研究工具：实现基础的多轮推理和搜索")
                
        elif "show_thinking" in st.session_state:
            # 如果切换到其他Agent类型，重置show_thinking为False
            st.session_state.show_thinking = False
        
        st.markdown("---")
        
        # 系统设置部分 - 组合调试模式和响应设置
        st.header("系统设置")
        
        # 调试选项 - 使用回调函数处理状态变化
        def debug_mode_changed():
            # 当调试模式启用时，自动禁用流式响应
            if st.session_state.debug_mode:
                st.session_state.use_stream = False
                # 同步到主页面
                if "use_stream_main" in st.session_state:
                    st.session_state.use_stream_main = False
        
        debug_mode = st.checkbox("启用调试模式", 
                               value=st.session_state.debug_mode, 
                               key="debug_mode",  # 直接使用debug_mode作为key
                               help="显示执行轨迹、知识图谱和源内容",
                               on_change=debug_mode_changed)
        
        # 添加流式响应选项（仅当调试模式未启用时显示）
        if not st.session_state.debug_mode:
            def use_stream_sidebar_changed():
                # 同步到主页面
                if "use_stream_main" in st.session_state:
                    st.session_state.use_stream_main = st.session_state.use_stream
            
            use_stream = st.checkbox("使用流式响应", 
                                   value=st.session_state.get("use_stream", True), 
                                   key="use_stream",  # 直接使用use_stream作为key
                                   help="启用流式响应，实时显示生成结果",
                                   on_change=use_stream_sidebar_changed)
        else:
            # 在调试模式下显示提示
            st.info("调试模式下已禁用流式响应")
        
        st.markdown("---")
        
        # 示例问题部分
        st.header("示例问题")
        example_questions = examples
        
        for question in example_questions:
            st.markdown(f"""
            <div style="background-color: #f7f7f7; padding: 8px; 
                 border-radius: 4px; margin: 5px 0; font-size: 14px; cursor: pointer;">
                {question}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 项目信息
        st.markdown("""
        ### 关于
        这个 GraphRAG 演示基于本地文档建立的知识图谱，可以使用不同的Agent策略回答问题。
        
        **调试模式**可查看:
        - 执行轨迹
        - 知识图谱可视化
        - 原始文本内容
        - 性能监控
        """)
        
        # 重置按钮
        if st.button("🗑️ 清除对话历史", key="clear_chat"):
            clear_chat()