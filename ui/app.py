"""
XY Stock 股票分析系统 - Streamlit Web界面
"""

import streamlit as st
import sys
import os
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from ui.config import MARKET_TYPES, STOCK_CODE_EXAMPLES
from ui.components.page_settings import main as display_settings
from ui.components.page_token_stats import main as display_token_stats
from ui.components.page_stock import display_stock_info
from ui.components.page_market_overview import display_market_overview
from ui.components.page_cache_management import main as display_cache_management
from providers.stock_utils import normalize_stock_input

def main():
    """主应用程序"""
    
    # 设置页面配置
    st.set_page_config(
        page_title="XY Stock 股票分析系统",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 隐藏默认的页面导航
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    /* 隐藏Streamlit默认的导航 */
    [data-testid="collapsedControl"] {display: none}
    section[data-testid="stSidebar"] > div.css-1d391kg {padding-top: 1rem;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # 页面标题
    st.title("📈 XY Stock 股票分析系统")
    
    # 创建侧边栏和主内容区域的布局
    with st.sidebar:
        st.header("功能菜单")
        
        # 添加侧边栏导航菜单
        menu = st.radio(
            "选择功能:",
            ["大盘分析", "股票分析", "缓存管理", "Token统计", "设置"],
            index=0,
            help="选择要使用的功能模块"
        )
        
        st.markdown("---")
        st.write("版本信息:")
        st.write("- Streamlit UI v1.1")
        st.write("- 端口: 8811")
    
    # 根据菜单选择显示不同的页面
    if menu == "大盘分析":
        display_market_overview()
    elif menu == "股票分析":
        display_analysis_page()
    elif menu == "缓存管理":
        display_cache_management()
    elif menu == "Token统计":
        # 导入并显示Token统计页面
        display_token_stats()
    elif menu == "设置":
        # 导入并显示设置页面
        display_settings()


def display_analysis_page():
    """显示股票分析页面"""
    # 主内容区域
    st.header("🏢 股票查询")
    
    # 类型选择下拉框
    market_type = st.selectbox(
        "选择市场类型:",
        MARKET_TYPES,
        index=0,
        help="选择要查询的股票市场类型"
    )
    
    # 显示对应市场的股票代码示例
    if market_type in STOCK_CODE_EXAMPLES:
        examples = ", ".join(STOCK_CODE_EXAMPLES[market_type])
        st.caption(f"示例代码: {examples}")
    
    # 股票代码输入框
    stock_code = st.text_input(
        "代码/名称:",
        placeholder=f"请输入{market_type}代码",
        help=f"输入{market_type}代码进行查询"
    )
    
    # 添加选项
    use_ai_analysis = st.checkbox("🤖 AI智能分析", value=False, help="选中后将使用AI对股票进行全面分析，包括行情、新闻、筹码、基本面等")
    use_cache = st.checkbox("💾 使用缓存数据", value=True, help="使用缓存数据可以加快查询速度，取消勾选将强制获取最新数据")
    
    # 用户观点输入框（仅在选择AI分析时显示）
    user_opinion = ""
    if use_ai_analysis:
        user_opinion = st.text_area(
            "补充观点（可选）:",
            placeholder="请输入您对该股票的观点、看法或关注的重点...",
            help="输入您的投资观点或关注的重点，AI将结合多维度分析给出综合建议",
            height=100
        )
    
    # 查询按钮
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        query_btn = st.button("🔍 查询", type="primary")
    with col2:
        clear_btn = st.button("🗑️ 重置")
    
    # 处理按钮逻辑 - 使用session_state保持状态
    if query_btn and stock_code.strip():
        # 设置显示状态和股票信息
        st.session_state['show_stock_info'] = True
        st.session_state['current_stock_code'] = stock_code.strip()
        st.session_state['current_market_type'] = market_type
        st.session_state['query_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.session_state['use_cache'] = use_cache
        
        # 设置AI分析选项
        if use_ai_analysis:
            # 设置AI分析标志 - 使用统一的状态管理
            st.session_state['include_ai_analysis'] = True
            st.session_state['user_opinion'] = user_opinion
            
            # 初始化AI报告存储（如果不存在）
            for report_type in ['ai_market_report', 'ai_news_report', 'ai_chip_report', 
                               'ai_fundamental_report', 'ai_comprehensive_report']:
                if report_type not in st.session_state:
                    st.session_state[report_type] = {}
        else:
            st.session_state['include_ai_analysis'] = False
    
    # 处理清空按钮
    if clear_btn:
        # 清除显示状态和相关数据
        st.session_state['show_stock_info'] = False
        if 'current_stock_code' in st.session_state:
            del st.session_state['current_stock_code']
        if 'current_market_type' in st.session_state:
            del st.session_state['current_market_type']
        if 'query_time' in st.session_state:
            del st.session_state['query_time']
        # 清除AI分析相关状态
        if 'include_ai_analysis' in st.session_state:
            del st.session_state['include_ai_analysis']
        if 'user_opinion' in st.session_state:
            del st.session_state['user_opinion']
        st.rerun()
    
    # 显示返回内容的区域
    st.subheader("查询结果")
    
    result_container = st.container()
    
    # 根据session_state状态显示内容
    if st.session_state.get('show_stock_info', False):
        # 从session_state获取股票信息
        current_stock_code = st.session_state.get('current_stock_code', '')
        current_market_type = st.session_state.get('current_market_type', '')
        query_time = st.session_state.get('query_time', '')
        
        with result_container:
            with st.spinner("正在查询数据..."):
                try:
                    # 标准化股票代码
                    normalized_stock_code, name = normalize_stock_input(current_stock_code)
                    
                    # 显示股票信息
                    display_stock_info(normalized_stock_code, current_market_type)
                    
                    # 额外的展示选项
                    with st.expander("📊 详细信息", expanded=False):
                        st.write(f"**查询时间:** {query_time}")
                        st.write(f"**市场类型:** {current_market_type}")
                        st.write(f"**股票代码:** {normalized_stock_code}")
                        st.write(f"**股票名称:** {name}")
                        
                except Exception as e:
                    st.error(f"查询失败: {str(e)}")
                    st.write("请检查股票代码是否正确，或稍后重试。")
                    
                    # 显示错误详情（调试用）
                    with st.expander("🔍 错误详情", expanded=False):
                        st.code(str(e), language="text")
    else:
        # 处理查询逻辑 - 仅处理按钮点击，但不显示结果
        if query_btn:
            if not stock_code.strip():
                with result_container:
                    st.warning("请输入股票代码")
            # 如果有股票代码，状态已在上面的按钮处理中设置，页面会重新运行并显示结果
        else:
            with result_container:
                st.info("请输入股票代码并点击查询按钮")
    
    # 页面底部信息
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <small>XY Stock 股票分析系统 | 数据仅供参考，不构成任何投资建议</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
