"""
XY Stock 股票分析系统 - Streamlit Web界面
"""

import streamlit as st
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from ui.components.page_settings import main as display_settings
from ui.components.page_token_stats import main as display_token_stats
from ui.components.page_stock import display_analysis_page
from ui.components.page_market_overview import display_market_overview
from ui.components.page_cache_management import main as display_cache_management
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


if __name__ == "__main__":
    main()
