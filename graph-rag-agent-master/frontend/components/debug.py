import streamlit as st
import json
import re
from utils.helpers import display_source_content
from utils.performance import display_performance_stats, clear_performance_data
from components.knowledge_graph import display_knowledge_graph_tab
from components.knowledge_graph.management import display_kg_management_tab
from components.styles import KG_MANAGEMENT_CSS

def display_source_content_tab(tabs):
    """显示源内容标签页内容"""
    with tabs[2]:
        if st.session_state.source_content:
            st.markdown('<div class="source-content-container">', unsafe_allow_html=True)
            display_source_content(st.session_state.source_content)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # 对deep_research_agent显示不同的消息
            if st.session_state.agent_type == "deep_research_agent":
                st.info("Deep Research Agent 不提供源内容查看功能。请查看执行轨迹标签页了解详细推理过程。")
            else:
                st.info("点击AI回答中的'查看源内容'按钮查看源文本")

def display_execution_trace_tab(tabs):
    """显示执行轨迹标签页内容"""
    with tabs[0]:
        # 显示DeepResearchAgent的执行轨迹
        if st.session_state.agent_type == "deep_research_agent":
            # 创建一个标题，使用黑色
            st.markdown("""
            <div style="padding:10px 0px; margin:15px 0;">
                <h2 style="margin:0; color:#333333;">深度研究执行过程</h2>
            </div>
            """, unsafe_allow_html=True)

            # 增加显示当前使用的工具类型
            tool_type = "增强版(DeeperResearch)" if st.session_state.get("use_deeper_tool", True) else "标准版(DeepResearch)"
            st.markdown(f"""
            <div style="background-color:#f0f7ff; padding:8px 15px; border-radius:5px; margin-bottom:15px; border-left:4px solid #4285F4;">
                <span style="font-weight:500;">当前工具：</span>{tool_type}
            </div>
            """, unsafe_allow_html=True)
            
            # 如果是增强版，显示增强功能区域
            if st.session_state.get("use_deeper_tool", True):
                with st.expander("增强功能详情", expanded=False):
                    st.markdown("""
                    #### 社区感知增强
                    智能识别相关知识社区，自动提取有价值的背景知识和关联信息。
                    
                    #### 知识图谱增强
                    实时构建查询相关的知识图谱，提供结构化推理和关系发现。
                    
                    #### 证据链追踪
                    记录完整的推理路径和证据来源，提供可解释的结论过程。
                    """)

            # 先尝试获取执行日志
            execution_logs = []
            
            # 首先检查session_state.execution_logs
            if hasattr(st.session_state, 'execution_logs') and st.session_state.execution_logs:
                execution_logs = st.session_state.execution_logs
            
            # 如果没有，尝试从execution_log中获取
            elif hasattr(st.session_state, 'execution_log') and st.session_state.execution_log:
                for entry in st.session_state.execution_log:
                    if entry.get("node") == "deep_research" and entry.get("output"):
                        output = entry.get("output")
                        if isinstance(output, str):
                            # 分割为行
                            execution_logs = output.strip().split('\n')
            
            # 如果深度研究消息中有raw_thinking，也可以从中提取执行日志
            if not execution_logs and len(st.session_state.messages) > 0:
                for msg in reversed(st.session_state.messages):  # 从最新的消息开始检查
                    if msg.get("role") == "assistant" and "raw_thinking" in msg:
                        thinking_text = msg["raw_thinking"]
                        # 提取日志行
                        if "[深度研究]" in thinking_text or "[KB检索]" in thinking_text:
                            execution_logs = thinking_text.strip().split('\n')
                            break
            
            # 确保我们至少检查了会话状态中可能的响应
            if not execution_logs and 'raw_thinking' in st.session_state:
                thinking_text = st.session_state.raw_thinking
                if thinking_text and ("[深度研究]" in thinking_text or "[KB检索]" in thinking_text):
                    execution_logs = thinking_text.strip().split('\n')
            
            # 如果是增强版，提取社区和图谱信息 (如果有)
            if st.session_state.get("use_deeper_tool", True) and "reasoning_chain" in st.session_state:
                reasoning_chain = st.session_state.reasoning_chain
                
                # 显示社区分析和知识图谱统计
                if reasoning_chain:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 社区分析")
                        steps = reasoning_chain.get("steps", [])
                        community_step = next((s for s in steps if "knowledge_community_analysis" in s.get("search_query", "")), None)
                        
                        if community_step:
                            st.success(f"✓ 识别到相关社区")
                            evidence = community_step.get("evidence", [])
                            
                            for ev in evidence:
                                if ev.get("source_type") == "community_knowledge":
                                    with st.expander(f"社区知识 {ev.get('evidence_id', '')}"):
                                        st.write(ev.get("content", ""))
                        else:
                            st.info("未执行社区分析")
                    
                    with col2:
                        st.markdown("#### 知识图谱")
                        # 检查是否有知识图谱数据
                        if "knowledge_graph" in st.session_state:
                            kg = st.session_state.knowledge_graph
                            st.metric("实体数量", kg.get("entity_count", 0))
                            st.metric("关系数量", kg.get("relation_count", 0))
                            
                            # 显示核心实体
                            central_entities = kg.get("central_entities", [])
                            if central_entities:
                                st.write("**核心实体:**")
                                for entity in central_entities[:5]:
                                    entity_id = entity.get("id", "")
                                    entity_type = entity.get("type", "未知")
                                    st.markdown(f"- **{entity_id}** ({entity_type})")
                        else:
                            st.info("暂无知识图谱数据")
            
            # 如果仍然没有找到，显示提示信息
            if not execution_logs:
                st.info("正在等待执行日志。请发送新的查询生成执行轨迹，如果看到此消息但已发送查询，请再试一次。")
            else:
                # 直接使用日志行列表进行格式化显示
                display_formatted_logs(execution_logs)
        else:
            # 其他执行轨迹显示逻辑
            if st.session_state.execution_log:
                for entry in st.session_state.execution_log:
                    with st.expander(f"节点: {entry['node']}", expanded=False):
                        st.markdown("**输入:**")
                        st.code(json.dumps(entry["input"], ensure_ascii=False, indent=2), language="json")
                        st.markdown("**输出:**")
                        st.code(json.dumps(entry["output"], ensure_ascii=False, indent=2), language="json")
            else:
                st.info("发送查询后将在此显示执行轨迹。")

def display_formatted_logs(log_lines):
    """格式化显示日志行"""
    if not log_lines:
        st.warning("没有执行日志")
        return
        
    # 检查是否包含[深度研究]标记
    has_deep_research_markers = any("[深度研究]" in line for line in log_lines)
    has_kb_search_markers = any("[KB检索]" in line for line in log_lines)
    
    if has_deep_research_markers or has_kb_search_markers:
        # 直接强化显示深度研究日志
        current_round = None
        in_search_results = False
        
        # 可折叠的轮次容器
        current_iteration = None
        current_iteration_content = []
        iterations = []
        current_round = None

        for line in log_lines:
            # 检测新的迭代轮次
            if "[深度研究] 开始第" in line and "轮迭代" in line:
                # 如果已有内容，保存前一轮
                if current_iteration_content:
                    iterations.append({
                        "round": current_round,
                        "content": current_iteration_content
                    })
                
                # 提取轮次数字
                round_match = re.search(r'开始第(\d+)轮迭代', line)
                if round_match:
                    current_round = int(round_match.group(1))
                    current_iteration_content = [line]
            # 即使当前轮为空，也将这一行添加到当前内容中
            elif current_round is not None:
                if current_iteration_content is not None:
                    current_iteration_content.append(line)
            
            # 检测查询执行      
            elif "[深度研究] 执行查询:" in line:
                if current_iteration_content is not None:
                    current_iteration_content.append(line)
            
            # 检测KB检索开始
            elif "[KB检索] 开始搜索:" in line:
                in_search_results = True
                if current_iteration_content is not None:
                    current_iteration_content.append(line)
            
            # 检测KB检索结果
            elif "[KB检索]" in line:
                if current_iteration_content is not None:
                    current_iteration_content.append(line)
            
            # 检测发现有用信息
            elif "[深度研究] 发现有用信息:" in line:
                if current_iteration_content is not None:
                    current_iteration_content.append(line)
            
            # 检测结束迭代
            elif "[深度研究] 没有生成新查询且已有信息，结束迭代" in line:
                if current_iteration_content is not None:
                    current_iteration_content.append(line)
            
            # 其他行
            elif current_iteration_content is not None:
                current_iteration_content.append(line)
        
        # 添加最后一轮
        if current_iteration_content:
            iterations.append({
                "round": current_round,
                "content": current_iteration_content
            })
        
        # 如果识别到了迭代轮次
        if iterations:
            # 创建一个选择器来选择查看哪一轮迭代
            st.markdown("#### 选择迭代轮次")
            
            # 过滤掉None轮次，并默认选择第1轮
            valid_iterations = [it for it in iterations if it["round"] is not None]
            if not valid_iterations:
                st.warning("未找到有效的迭代轮次")
                return
                
            # 创建选择项，确保round是整数
            iteration_options = {f"第 {it['round']} 轮迭代": it for it in valid_iterations}
            
            # 如果包含第1轮，默认选中它
            default_key = next((k for k in iteration_options.keys() if "1 轮" in k), list(iteration_options.keys())[0])
            
            selected_round_key = st.selectbox(
                "选择迭代轮次", 
                list(iteration_options.keys()),
                index=list(iteration_options.keys()).index(default_key)
            )
            
            # 获取选中的迭代
            iteration = iteration_options[selected_round_key]
            
            # 显示所选迭代的内容
            st.markdown("""
            <div style="padding:10px 0; margin:10px 0; border-bottom:1px solid #eee;">
                <h4 style="margin:0;">迭代详情</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # 分类处理不同类型的日志行
            queries = []
            kb_searches = []
            kb_results = []
            useful_info = None
            other_lines = []
            
            for line in iteration.get("content", []):
                if "[深度研究] 执行查询:" in line:
                    query = re.sub(r'\[深度研究\] 执行查询:', '', line).strip()
                    queries.append(query)
                elif "[KB检索] 开始搜索:" in line:
                    search = re.sub(r'\[KB检索\] 开始搜索:', '', line).strip()
                    kb_searches.append(search)
                elif "[KB检索] 结果:" in line:
                    result = line
                    kb_results.append(result)
                elif "[深度研究] 发现有用信息:" in line:
                    useful_info = re.sub(r'\[深度研究\] 发现有用信息:', '', line).strip()
                else:
                    other_lines.append(line)
            
            # 显示查询
            if queries:
                st.markdown("##### 执行的查询")
                for query in queries:
                    st.markdown(f"""
                    <div style="background-color:#f5f5f5; padding:8px; border-left:4px solid #4CAF50; margin:8px 0; border-radius:3px;">
                        {query}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 显示有用信息
            if useful_info:
                st.markdown("##### 发现的有用信息")
                st.markdown(f"""
                <div style="background-color:#E8F5E9; padding:10px; border-left:4px solid #4CAF50; margin:10px 0; border-radius:4px;">
                    {useful_info}
                </div>
                """, unsafe_allow_html=True)
            
            # 显示知识库检索
            if kb_searches or kb_results:
                st.markdown("##### 知识库检索")
                col1, col2 = st.columns(2)
                
                with col1:
                    if kb_searches:
                        st.markdown("**搜索内容**")
                        for search in kb_searches:
                            st.markdown(f"""
                            <div style="background-color:#FFF8E1; padding:8px; border-left:4px solid #FFA000; margin:8px 0; border-radius:3px;">
                                {search}
                            </div>
                            """, unsafe_allow_html=True)
                
                with col2:
                    if kb_results:
                        st.markdown("**检索结果**")
                        st.code("\n".join(kb_results), language="text")
            
            # 显示其他日志行（使用美化后的展示区域）
            if other_lines:
                with st.expander("详细日志", expanded=False):
                    # 创建一个美化的容器
                    st.markdown("""
                    <div style="background-color:#f8f9fa; padding:10px; border-radius:5px; margin:10px 0; font-family:monospace;">
                    """, unsafe_allow_html=True)
                    
                    # 显示每一行，使用不同的颜色
                    for line in other_lines:
                        if "[KB检索]" in line:
                            st.markdown(f'<div style="padding:2px 0; color:#f57c00;">{line}</div>', unsafe_allow_html=True)
                        elif "[深度研究]" in line:
                            st.markdown(f'<div style="padding:2px 0; color:#1976d2;">{line}</div>', unsafe_allow_html=True)
                        elif "[双路径搜索]" in line:
                            st.markdown(f'<div style="padding:2px 0; color:#7b1fa2;">{line}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="padding:2px 0; color:#666;">{line}</div>', unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            # 没有识别到迭代轮次，直接按类型显示
            deep_research_logs = [line for line in log_lines if "[深度研究]" in line]
            kb_search_logs = [line for line in log_lines if "[KB检索]" in line]
            other_logs = [line for line in log_lines if "[深度研究]" not in line and "[KB检索]" not in line]
            
            # 使用标签页代替嵌套的expander
            log_tabs = st.tabs(["深度研究日志", "知识库检索日志", "其他日志"])
            
            with log_tabs[0]:
                for line in deep_research_logs:
                    if "发现有用信息" in line:
                        useful_info = re.sub(r'\[深度研究\] 发现有用信息:', '', line).strip()
                        st.markdown(f"""
                        <div style="background-color:#E8F5E9; padding:10px; border-left:4px solid #4CAF50; margin:10px 0; border-radius:4px;">
                            <span style="color:#4CAF50; font-weight:bold;">发现有用信息:</span><br>{useful_info}
                        </div>
                        """, unsafe_allow_html=True)
                    elif "执行查询" in line:
                        query = re.sub(r'\[深度研究\] 执行查询:', '', line).strip()
                        st.markdown(f"""
                        <div style="background-color:#f5f5f5; padding:8px; border-left:4px solid #4CAF50; margin:8px 0; border-radius:3px;">
                            <span style="color:#4CAF50; font-weight:bold;">执行查询:</span> {query}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:#1976d2;'>{line}</span>", unsafe_allow_html=True)
            
            with log_tabs[1]:
                for line in kb_search_logs:
                    if "开始搜索" in line:
                        search = re.sub(r'\[KB检索\] 开始搜索:', '', line).strip()
                        st.markdown(f"""
                        <div style="background-color:#FFF8E1; padding:8px; border-left:4px solid #FFA000; margin:8px 0; border-radius:3px;">
                            <span style="color:#FFA000; font-weight:bold;">开始搜索:</span> {search}
                        </div>
                        """, unsafe_allow_html=True)
                    elif "结果" in line:
                        st.markdown(f"<span style='color:#f57c00; font-weight:bold;'>{line}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:#f57c00;'>{line}</span>", unsafe_allow_html=True)
            
            with log_tabs[2]:
                if other_logs:
                    # 美化显示其他日志
                    st.markdown("""
                    <div style="background-color:#f8f9fa; padding:10px; border-radius:5px; font-family:monospace;">
                    """, unsafe_allow_html=True)
                    
                    for line in other_logs:
                        if "[双路径搜索]" in line:
                            st.markdown(f'<div style="padding:2px 0; color:#7b1fa2;">{line}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="padding:2px 0; color:#666;">{line}</div>', unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("没有其他日志")
    else:
        # 无特殊标记，使用简单格式显示
        st.code("\n".join(log_lines), language="text")

def add_performance_tab(tabs):
    """添加性能监控标签页"""
    with tabs[4]:  # 第五个标签页
        st.markdown('<div class="debug-header">性能统计</div>', unsafe_allow_html=True)
        display_performance_stats()
        
        # 添加清除性能数据的按钮
        if st.button("清除性能数据"):
            clear_performance_data()
            st.rerun()

def display_debug_panel():
    """显示调试面板"""
    # 使用简单的容器标记，不进行复杂的DOM操作
    st.markdown('<div class="debug-panel-wrapper">', unsafe_allow_html=True)
    
    st.subheader("�� 可解释性")
    
    # 添加快速导航提示
    if st.session_state.agent_type != "deep_research_agent":
        # 检查是否有知识图谱数据
        has_kg_data = False
        if "current_kg_message" in st.session_state and st.session_state.current_kg_message is not None:
            msg_idx = st.session_state.current_kg_message
            if (0 <= msg_idx < len(st.session_state.messages) and 
                "kg_data" in st.session_state.messages[msg_idx] and 
                st.session_state.messages[msg_idx]["kg_data"] is not None):
                has_kg_data = True
        
        if has_kg_data:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success("✅ 检测到知识图谱数据！")
            with col2:
                if st.button("📊 查看图谱", key="quick_view_kg"):
                    st.session_state.current_tab = "知识图谱"
                    st.rerun()
        else:
            st.info("💡 AI回答后点击\"提取知识图谱\"按钮可在此查看图谱可视化")
    
    # 创建标签页用于不同类型的调试信息
    tabs = st.tabs(["执行轨迹", "知识图谱", "源内容", "知识图谱管理", "性能监控"])
    
    # 执行轨迹标签
    display_execution_trace_tab(tabs)
    
    # 知识图谱标签
    display_knowledge_graph_tab(tabs)
    
    # 源内容标签
    display_source_content_tab(tabs)
    
    # 知识图谱管理标签 - 延迟加载，不自动触发API请求
    if st.session_state.current_tab == "知识图谱管理":
        display_kg_management_tab(tabs)
    else:
        with tabs[3]:
            if st.button("加载知识图谱管理面板", key="load_kg_management"):
                st.session_state.current_tab = "知识图谱管理"
                st.rerun()
            else:
                st.info("点击上方按钮加载知识图谱管理面板")
    
    # 性能监控标签
    add_performance_tab(tabs)
    
    # 通过JS脚本直接控制标签切换
    tab_index = 0  # 默认显示执行轨迹标签
    
    if st.session_state.current_tab == "执行轨迹":
        tab_index = 0
    elif st.session_state.current_tab == "知识图谱":
        tab_index = 1
    elif st.session_state.current_tab == "源内容":
        tab_index = 2
    elif st.session_state.current_tab == "知识图谱管理":
        tab_index = 3
    elif st.session_state.current_tab == "性能监控":
        tab_index = 4
    
    # 知识图谱管理CSS样式
    kg_management_css = KG_MANAGEMENT_CSS
    st.markdown(kg_management_css, unsafe_allow_html=True)

    # 使用自定义JS自动切换到指定标签页
    tab_js = f"""
    <script>
        // 等待DOM加载完成
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                // 查找所有标签按钮
                const tabs = document.querySelectorAll('[data-baseweb="tab"]');
                if (tabs.length > {tab_index}) {{
                    // 模拟点击目标标签
                    tabs[{tab_index}].click();
                }}
            }}, 100);
        }});
    </script>
    """
    
    # 只有当需要切换标签时才注入JS
    if "current_tab" in st.session_state:
        st.markdown(tab_js, unsafe_allow_html=True)
    
    # 关闭容器div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 添加强制固定定位的JavaScript
    st.markdown("""
    <script>
        console.log("调试面板JavaScript开始执行");
        
        // 强制固定调试面板的函数
        function forceFixDebugPanel() {
            console.log("正在尝试固定调试面板...");
            
            // 查找调试面板容器
            const debugWrapper = document.querySelector('.debug-panel-wrapper');
            console.log("找到调试面板容器:", debugWrapper);
            
            if (debugWrapper) {
                // 查找最近的列容器
                let columnContainer = debugWrapper.closest('[data-testid="column"]');
                console.log("找到列容器:", columnContainer);
                
                if (columnContainer) {
                    console.log("应用固定定位样式...");
                    
                    // 强制设置固定定位样式，使用cssText一次性设置所有样式
                    columnContainer.style.cssText = `
                        position: fixed !important;
                        top: 80px !important;
                        right: 20px !important;
                        width: 400px !important;
                        max-width: 35vw !important;
                        height: calc(100vh - 100px) !important;
                        z-index: 9999 !important;
                        background: white !important;
                        border-radius: 10px !important;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.25) !important;
                        border: 2px solid #e0e0e0 !important;
                        overflow: hidden !important;
                        transform: none !important;
                    `;
                    
                    // 设置内部内容的滚动
                    const innerContent = columnContainer.querySelector('div');
                    if (innerContent) {
                        innerContent.style.cssText = `
                            height: 100% !important;
                            overflow-y: auto !important;
                            padding: 20px !important;
                            box-sizing: border-box !important;
                        `;
                    }
                    
                    // 调整主内容区域的边距
                    const mainContainer = document.querySelector('.main .block-container');
                    if (mainContainer) {
                        mainContainer.style.marginRight = '420px';
                        console.log("已调整主内容边距");
                    }
                    
                    // 调整聊天输入框的宽度
                    const chatInput = document.querySelector('[data-testid="stChatInput"]');
                    if (chatInput) {
                        // 计算新的宽度：100% - 左侧边栏(320px) - 调试面板(420px)
                        const newWidth = 'calc(100% - 740px)';
                        chatInput.style.width = newWidth;
                        chatInput.style.left = '320px';
                        console.log("已调整聊天输入框宽度:", newWidth);
                    }
                    
                    console.log("调试面板固定定位设置完成！");
                    return true;
                }
            }
            
            console.log("未找到调试面板元素，重试...");
            return false;
        }
        
        // 重试机制
        let retryCount = 0;
        const maxRetries = 10;
        
        function tryFixDebugPanel() {
            if (forceFixDebugPanel() || retryCount >= maxRetries) {
                if (retryCount >= maxRetries) {
                    console.log("达到最大重试次数，停止尝试");
                }
                return;
            }
            
            retryCount++;
            console.log(`重试 ${retryCount}/${maxRetries}`);
            setTimeout(tryFixDebugPanel, 500);
        }
        
        // 立即尝试执行
        setTimeout(tryFixDebugPanel, 100);
        
        // 页面加载完成后再次尝试
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(tryFixDebugPanel, 500);
            });
        }
        
        // 监听DOM变化，当Streamlit重新渲染时重新应用
        const observer = new MutationObserver(function(mutations) {
            let shouldReapply = false;
            
            mutations.forEach(function(mutation) {
                // 检查是否有新的节点添加，且包含调试面板
                if (mutation.type === 'childList') {
                    for (let node of mutation.addedNodes) {
                        if (node.nodeType === 1) { // Element node
                            if (node.querySelector && node.querySelector('.debug-panel-wrapper')) {
                                shouldReapply = true;
                                break;
                            }
                        }
                    }
                }
            });
            
            if (shouldReapply) {
                console.log("检测到DOM变化，重新应用固定定位");
                retryCount = 0;
                setTimeout(tryFixDebugPanel, 300);
            }
        });
        
        // 开始观察整个文档的变化
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log("调试面板JavaScript设置完成");
    </script>
    """, unsafe_allow_html=True)