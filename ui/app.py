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
from stock.stock_code_map import get_stock_identity
from ui.config import FULL_VERSION

def set_requests_timeout(timeout=30):
    """全局设置 requests 默认超时时间（monkey patch）"""
    import requests.sessions
    old_request = requests.sessions.Session.request
    def new_request(self, *args, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = timeout
        return old_request(self, *args, **kwargs)
    requests.sessions.Session.request = new_request

def main():
    """主应用程序"""
    
    set_requests_timeout(30)
    st.set_page_config(
        page_title="XY Stock 股票分析系统",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    minimal_hide_style = """
    <style>
    /* 只隐藏主菜单，保留所有其他功能 */
    #MainMenu {visibility: hidden;}
    /* 隐藏底部的 Made with Streamlit */
    footer {visibility: hidden;}
    /* 减少侧边栏顶部间距 */
    section[data-testid="stSidebar"] > div:first-child {padding-top: 1rem;}
    </style>
    """
    st.markdown(minimal_hide_style, unsafe_allow_html=True)
    
    #st.title("📈 XY Stock 股票分析系统")
    
    with st.sidebar:
        st.header("功能菜单")
        
        menu = st.radio(
            "选择功能:",
            ["大盘分析", "股票分析", "缓存管理", "Token统计", "设置"],
            index=0,
            help="选择要使用的功能模块"
        )
        
        st.markdown("---")
        st.write("版本信息:")
        st.write(f"- {FULL_VERSION}")
        st.write("- 端口: 8811")
    
    if menu == "大盘分析":
        display_market_overview()
    elif menu == "股票分析":
        display_analysis_page()
    elif menu == "缓存管理":
        display_cache_management()
    elif menu == "Token统计":
        display_token_stats()
    elif menu == "设置":
        display_settings()


def display_analysis_page():
    """显示股票分析页面"""
    st.header("🏢 股票查询")
    
    market_type = st.selectbox(
        "选择市场类型:",
        MARKET_TYPES,
        index=0,
        help="选择要查询的股票市场类型"
    )
    
    if market_type in STOCK_CODE_EXAMPLES:
        examples = ", ".join(STOCK_CODE_EXAMPLES[market_type])
        st.caption(f"示例代码: {examples}")
    
    stock_code = st.text_input(
        "代码/名称:",
        placeholder=f"请输入{market_type}代码",
        help=f"输入{market_type}代码进行查询"
    )
    
    use_ai_analysis = st.checkbox("🤖 AI智能分析", value=False, help="选中后将使用AI对股票进行全面分析，包括行情、新闻、筹码、基本面等")
    use_cache = st.checkbox("💾 使用缓存数据", value=True, help="使用缓存数据可以加快查询速度，取消勾选将强制获取最新数据")
    
    # 用户观点输入框（仅在选择AI分析时显示）
    user_opinion = ""
    user_position = "不确定"
    if use_ai_analysis:
        user_opinion = st.text_area(
            "补充观点（可选）:",
            placeholder="请输入您对该股票的观点、看法或关注的重点...",
            help="输入您的投资观点或关注的重点，AI将结合多维度分析给出综合建议",
            height=100
        )
        user_position = st.selectbox(
            "当前持仓状态:",
            options=["不确定", "空仓", "低仓位", "中仓位", "重仓", "满仓"],
            index=0,
            help="请选择您当前的大致持仓状态"
        )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        query_btn = st.button("🔍 查询", type="primary")
    with col2:
        clear_btn = st.button("🗑️ 重置")
    
    # 处理按钮逻辑 - 使用session_state保持状态
    if query_btn and stock_code.strip():
        # 只有在明确点击查询按钮时才设置显示状态
        st.session_state['show_stock_info'] = True
        st.session_state['current_stock_code'] = stock_code.strip()
        st.session_state['current_market_type'] = market_type
        st.session_state['query_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.session_state['use_cache'] = use_cache
        st.session_state['just_reset'] = False  # 标记非重置状态
        
        if use_ai_analysis:
            st.session_state['include_ai_analysis'] = True
            st.session_state['user_opinion'] = user_opinion
            st.session_state['user_position'] = user_position
            
            for report_type in ['ai_market_report', 'ai_news_report', 'ai_chip_report', 
                               'ai_fundamental_report', 'ai_comprehensive_report']:
                if report_type not in st.session_state:
                    st.session_state[report_type] = {}
        else:
            st.session_state['include_ai_analysis'] = False
    else:
        st.session_state['use_cache'] = True # 避免在不使用缓存时由于刷新控件导致重复查询
    
    if clear_btn:
        # 标记为刚刚重置，防止意外触发查询
        st.session_state['just_reset'] = True
        
        # 清除所有相关的session state
        keys_to_clear = [
            'show_stock_info', 'current_stock_code', 'current_market_type', 
            'query_time', 'include_ai_analysis', 'user_opinion', 'user_position',
            'use_cache', 'ai_market_report', 'ai_news_report', 'ai_chip_report',
            'ai_fundamental_report', 'ai_comprehensive_report', 'ai_company_report'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.rerun()
    
    st.subheader("查询结果")
    
    result_container = st.container()
    
    # 只有在没有刚刚重置的情况下才显示股票信息
    if st.session_state.get('show_stock_info', False) and not st.session_state.get('just_reset', False):
        current_stock_code = st.session_state.get('current_stock_code', '')
        current_market_type = st.session_state.get('current_market_type', '')
        query_time = st.session_state.get('query_time', '')
        
        with result_container:
            with st.spinner("正在查询数据..."):
                try:
                    stock_identity = get_stock_identity(current_stock_code, current_market_type)
                    if stock_identity is None or stock_identity.get('error'):
                        st.error(f"获取股票代码失败")
                    else:
                        display_stock_info(stock_identity)
                        with st.expander("📊 详细信息", expanded=False):
                            st.write(f"**查询时间:** {query_time}")
                            st.write(f"**市场类型:** {current_market_type}")
                            st.write(f"**股票代码:** {stock_identity['code']}")
                            st.write(f"**股票名称:** {stock_identity['name']}")
                        
                except Exception as e:
                    st.error(f"查询失败: {str(e)}")
                    st.write("请检查股票代码是否正确，或稍后重试。")
                    
                    with st.expander("🔍 错误详情", expanded=False):
                        st.code(str(e), language="text")
    else:
        # 清除重置标志，避免影响后续操作
        if 'just_reset' in st.session_state:
            del st.session_state['just_reset']
            
        if query_btn:
            if not stock_code.strip():
                with result_container:
                    st.warning("请输入股票代码")
        else:
            with result_container:
                st.info("请输入股票代码并点击查询按钮")
    
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
