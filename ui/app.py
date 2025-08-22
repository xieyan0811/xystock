"""
XY Stock 股票分析系统 - Streamlit Web界面
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime
from importlib import import_module

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入本地股票数据提供者
from ui.stock_provider import stock_data_provider
from ui.config import MARKET_TYPES, STOCK_CODE_EXAMPLES

# 隐藏默认导航的CSS
hide_default_nav = """
<style>
    /* 隐藏Streamlit默认的页面导航 */
    section[data-testid="stSidebar"] > div.st-emotion-cache-14nqv6l.ezrtsby2 > div.st-emotion-cache-1cypcdb.ezrtsby1 {
        display: none !important;
    }
    
    /* 隐藏"App"标签 */
    .st-emotion-cache-1inwz65 {
        display: none;
    }
    
    /* 隐藏缩小后的页面标签 */
    .st-emotion-cache-7ym5gk {
        display: none;
    }
    
    /* 隐藏hamburger菜单中的页面链接 */
    .st-emotion-cache-13sxguw {
        display: none;
    }
    
    /* 隐藏默认的菜单、页眉和页脚 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 调整主标题样式 */
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* 调整侧边栏宽度和样式 */
    [data-testid="stSidebar"] {
        min-width: 250px !important;
        max-width: 300px !important;
    }
    [data-testid="collapsedControl"] {display: none}
    section[data-testid="stSidebar"] > div.css-1d391kg {padding-top: 1rem;}
</style>
"""

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
            ["📊 股票分析", "🔢 Token统计", "⚙️ 设置"],
            index=0,
            help="选择要使用的功能模块"
        )
        
        st.markdown("---")
        st.write("版本信息:")
        st.write("- Streamlit UI v1.1")
        st.write("- 端口: 8811")
    
    # 根据菜单选择显示不同的页面
    if menu == "📊 股票分析":
        display_stock_analysis_page()
    elif menu == "🔢 Token统计":
        # 导入并显示Token统计页面
        from ui.components.page_token_stats import main as display_token_stats
        display_token_stats()
    elif menu == "⚙️ 设置":
        # 导入并显示设置页面
        from ui.components.page_settings import main as display_settings
        display_settings()


def display_stock_analysis_page():
    """显示股票分析页面"""
    # 主内容区域
    st.header("股票查询")
    
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
        "股票代码:",
        placeholder=f"请输入{market_type}代码",
        help=f"输入{market_type}代码进行查询"
    )
    
    # 添加AI分析选项
    use_ai_analysis = st.checkbox("🤖 AI行情分析", value=False, help="选中后将使用AI对股票行情进行技术分析")
    use_ai_news_analysis = st.checkbox("📰 AI新闻分析", value=False, help="选中后将使用AI对股票相关新闻进行分析")
    use_ai_chip_analysis = st.checkbox("🧮 AI筹码分析", value=False, help="选中后将使用AI对股票筹码分布进行分析")
    use_ai_fundamental_analysis = st.checkbox("📊 AI基本面分析", value=False, help="选中后将使用AI对股票基本面数据进行深入分析")
    
    # 查询按钮
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        query_btn = st.button("🔍 查询", type="primary")
    with col2:
        clear_btn = st.button("🗑️ 清空")
    
    # 处理清空按钮
    if clear_btn:
        st.rerun()
    
    # 显示返回内容的区域
    st.subheader("查询结果")
    
    result_container = st.container()
    
    # 处理查询逻辑
    if query_btn:
        if stock_code.strip():
            with result_container:
                with st.spinner("正在查询数据..."):
                    try:
                        # 根据市场类型选择不同的查询方法
                        if market_type == "指数":
                            # 调用指数分析功能
                            from providers.market_tools import MarketIndicators
                            market_collector = MarketIndicators()
                            from providers.stock_tools import normalize_stock_input
                            code,name = normalize_stock_input(stock_code.strip(), 'index')
                            result = market_collector.get_comprehensive_market_report(name)
                            
                            if isinstance(result, dict):
                                # 显示指数分析结果
                                from ui.components.page_index import display_index_analysis_result 
                                display_index_analysis_result(result)
                            else:
                                st.success("查询成功！")
                                st.code(str(result), language="text")
                        else:
                            # 调用普通股票数据获取函数并显示结果
                            from ui.components.page_stock import display_stock_info
                            
                            # 如果选择了AI分析，设置session_state参数
                            if use_ai_analysis:
                                if "ai_report" not in st.session_state:
                                    st.session_state.ai_report = {}
                                st.session_state['run_ai_for'] = stock_code.strip()
                            
                            # 如果选择了AI新闻分析，设置session_state参数
                            if use_ai_news_analysis:
                                if "ai_news_report" not in st.session_state:
                                    st.session_state.ai_news_report = {}
                                st.session_state['run_news_ai_for'] = stock_code.strip()
                            
                            # 如果选择了AI筹码分析，设置session_state参数
                            if use_ai_chip_analysis:
                                if "ai_chip_report" not in st.session_state:
                                    st.session_state.ai_chip_report = {}
                                st.session_state['run_chip_ai_for'] = stock_code.strip()
                            
                            # 如果选择了AI基本面分析，设置session_state参数
                            if use_ai_fundamental_analysis:
                                if "ai_fundamental_report" not in st.session_state:
                                    st.session_state.ai_fundamental_report = {}
                                st.session_state['run_fundamental_ai_for'] = stock_code.strip()
                                
                            # 显示股票信息
                            display_stock_info(stock_code.strip(), market_type)
                        
                        # 额外的展示选项
                        with st.expander("📊 详细信息", expanded=False):
                            st.write(f"**查询时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            st.write(f"**市场类型:** {market_type}")
                            st.write(f"**股票代码:** {stock_code}")
                            
                    except Exception as e:
                        st.error(f"查询失败: {str(e)}")
                        st.write("请检查股票代码是否正确，或稍后重试。")
                        
                        # 显示错误详情（调试用）
                        with st.expander("🔍 错误详情", expanded=False):
                            st.code(str(e), language="text")
        else:
            with result_container:
                st.warning("请输入股票代码")
    else:
        with result_container:
            st.info("请输入股票代码并点击查询按钮")
    
    # 页面底部信息
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <small>XY Stock 股票分析系统 | 数据仅供参考，投资有风险</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
