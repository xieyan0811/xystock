import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_price
from utils.data_formatters import format_risk_metrics
from utils.string_utils import remove_markdown_format

def display_technical_indicators(tech_data):
    """显示技术指标分析卡片"""

    st.markdown("""
    <style>
    /* 调整 metric 组件的 value 字体大小 */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("技术指标分析")

    if not tech_data:
        st.warning("未获取到技术指标数据")
        return
    
    # 基础信息
    col1, col2 = st.columns(2)
    with col1:
        st.metric("MA趋势", tech_data.get('ma_trend', 'N/A'))
    with col2:
        st.metric("MACD趋势", tech_data.get('macd_trend', 'N/A'))
    
    # 移动平均线
    with st.expander("📈 移动平均线", expanded=True):
        ma_col1, ma_col2, ma_col3, ma_col4 = st.columns(4)
        with ma_col1:
            ma_5 = tech_data.get('ma_5')
            st.metric("MA5", format_price(ma_5) if ma_5 else "N/A")
        with ma_col2:
            ma_10 = tech_data.get('ma_10')
            st.metric("MA10", format_price(ma_10) if ma_10 else "N/A")
        with ma_col3:
            ma_20 = tech_data.get('ma_20')
            st.metric("MA20", format_price(ma_20) if ma_20 else "N/A")
        with ma_col4:
            ma_60 = tech_data.get('ma_60')
            st.metric("MA60", format_price(ma_60) if ma_60 else "N/A")
    
    # 技术指标
    with st.expander("🔢 技术指标", expanded=True):
        tech_col1, tech_col2, tech_col3 = st.columns(3)
        with tech_col1:
            rsi_14 = tech_data.get('rsi_14')
            st.metric("RSI(14)", format_price(rsi_14) if rsi_14 else "N/A")
        with tech_col2:
            kdj_k = tech_data.get('kdj_k')
            st.metric("KDJ-K", format_price(kdj_k) if kdj_k else "N/A")
        with tech_col3:
            kdj_d = tech_data.get('kdj_d')
            st.metric("KDJ-D", format_price(kdj_d) if kdj_d else "N/A")
        
        # MACD指标
        macd_col1, macd_col2, macd_col3 = st.columns(3)
        with macd_col1:
            macd = tech_data.get('macd')
            st.metric("MACD", f"{macd:.4f}" if macd else "N/A")
        with macd_col2:
            macd_signal = tech_data.get('macd_signal')
            st.metric("MACD信号", f"{macd_signal:.4f}" if macd_signal else "N/A")
        with macd_col3:
            macd_hist = tech_data.get('macd_histogram')
            st.metric("MACD柱状", f"{macd_hist:.4f}" if macd_hist else "N/A")
        
        # 布林带指标
        boll_col1, boll_col2, boll_col3 = st.columns(3)
        with boll_col1:
            boll_upper = tech_data.get('boll_upper')
            st.metric("布林上轨", format_price(boll_upper) if boll_upper else "N/A")
        with boll_col2:
            boll_middle = tech_data.get('boll_middle')
            st.metric("布林中轨", format_price(boll_middle) if boll_middle else "N/A")
        with boll_col3:
            boll_lower = tech_data.get('boll_lower')
            st.metric("布林下轨", format_price(boll_lower) if boll_lower else "N/A")
        
        # 其他技术指标
        other_col1, other_col2, other_col3 = st.columns(3)
        with other_col1:
            wr_14 = tech_data.get('wr_14')
            st.metric("威廉指标", format_price(wr_14) if wr_14 else "N/A")
        with other_col2:
            cci_14 = tech_data.get('cci_14')
            st.metric("CCI指标", format_price(cci_14) if cci_14 else "N/A")
        with other_col3:
            kdj_j = tech_data.get('kdj_j')
            st.metric("KDJ-J", format_price(kdj_j) if kdj_j else "N/A")


def display_technical_analysis_tab(stock_identity=None, index_name=None):
    """
    显示技术指标分析Tab的完整内容
    适用于股票和大盘指数的技术分析
    
    Args:
        stock_identity: 股票标识信息 (用于股票分析)
        index_name: 指数名称 (用于大盘分析，如'上证指数')
    """
    if stock_identity and index_name:
        st.error("stock_identity 和 index_name 不能同时提供")
        return
        
    if not stock_identity and not index_name:
        st.error("必须提供 stock_identity 或 index_name 中的一个")
        return
    
    try:
        use_cache = st.session_state.get('use_cache', True) or st.session_state.get('market_use_cache', True)
        force_refresh = not use_cache
        
        # 根据类型获取技术指标数据
        if stock_identity:
            # 股票技术分析
            from stock.stock_data_tools import get_stock_tools
            stock_tools = get_stock_tools()
            
            kline_info = stock_tools.get_stock_kline_data(
                stock_identity, 
                period=160, 
                use_cache=use_cache, 
                force_refresh=force_refresh
            )
            
            if 'error' in kline_info:
                st.error(f"获取K线数据失败: {kline_info['error']}")
                return
                
            indicators = kline_info.get('indicators', {})
            
        elif index_name:
            # 大盘指数技术分析
            from market.market_data_tools import get_market_tools
            market_tools = get_market_tools()
            
            indicators = market_tools.get_index_technical_indicators(index_name)
        
        # 显示技术指标
        if indicators:
            display_technical_indicators(indicators)
        else:
            st.warning("未获取到技术指标数据")
            
    except Exception as e:
        st.error(f"加载技术分析数据失败: {str(e)}")
        with st.expander("🔍 错误详情", expanded=False):
            st.code(str(e), language="text")


def display_risk_analysis(risk_metrics):
    """显示风险分析"""
    if risk_metrics is None or 'error' in risk_metrics:
        st.error(f"获取风险指标失败: {risk_metrics.get('error', '未知错误')}")
        return
    
    # 尝试使用格式化的风险指标文本
    formatted_risk_text = format_risk_metrics(risk_metrics, with_header=False)
    
    if formatted_risk_text:
        # 显示格式化的风险分析文本
        with st.expander("⚠️ 详细风险分析", expanded=True):
            formatted_risk_text = remove_markdown_format(formatted_risk_text, only_headers=True)
            st.markdown(formatted_risk_text)
    
    # 如果有summary_table，也显示表格形式
    if risk_metrics and 'summary_table' in risk_metrics:
        with st.expander("📊 风险分析表格", expanded=False):
            st.table(risk_metrics['summary_table'])
    
    # 如果以上都没有，显示原始数据
    elif not formatted_risk_text and 'error' not in risk_metrics:
        with st.expander("📊 风险分析摘要", expanded=True):
            st.json(risk_metrics)


def display_kline_charts(df, chart_type="stock", title_prefix=""):
    """
    统一的K线图和成交量图表显示函数
    
    Args:
        df: 包含K线数据的DataFrame，必须包含 datetime, open, high, low, close, volume 列
        chart_type: 图表类型，"stock"表示股票，"index"表示指数
        title_prefix: 标题前缀，如股票名称或指数名称
    """
    if df is None or df.empty:
        st.warning("无K线数据可显示")
        return
    
    # 转换日期格式
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # 根据类型设置标题和Y轴标签
    if chart_type == "index":
        price_title = f"{title_prefix}指数K线图与均线" if title_prefix else "指数K线图与均线"
        yaxis_title = "指数点位"
    else:
        price_title = f"{title_prefix}K线图与均线" if title_prefix else "K线图与均线"
        yaxis_title = "价格"
    
    # K线图与均线
    fig_price = go.Figure()
    
    # 添加K线图
    fig_price.add_trace(go.Candlestick(
        x=df['datetime'],
        open=df['open'], 
        high=df['high'],
        low=df['low'], 
        close=df['close'],
        name='K线',
        increasing_line_color="#DA1A10",
        decreasing_line_color="#14AA06",
        increasing_fillcolor="#F51D12",
        decreasing_fillcolor="#1BCC0B"
    ))
    
    # 添加均线（如果存在）
    ma_lines = [
        ('MA5', '#D2FF07'),
        ('MA10', '#FF22DA'), 
        ('MA20', '#0593F1'),
        ('MA60', '#FFA500')
    ]
    
    for ma_name, color in ma_lines:
        if ma_name in df.columns and not df[ma_name].isna().all():
            fig_price.add_trace(go.Scatter(
                x=df['datetime'], 
                y=df[ma_name],
                mode='lines',
                name=ma_name,
                line=dict(color=color, width=1.5)
            ))
    
    # 设置K线图布局
    fig_price.update_layout(
        title=price_title,
        xaxis_title='日期',
        yaxis_title=yaxis_title,
        height=500,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(rangeslider=dict(visible=False)),
        yaxis=dict(fixedrange=True)
    )
    
    st.plotly_chart(fig_price, use_container_width=True, config={"scrollZoom": False})
    
    # 成交量图
    if 'volume' in df.columns and not df['volume'].isna().all():
        fig_volume = go.Figure()
        
        fig_volume.add_trace(go.Bar(
            x=df['datetime'], 
            y=df['volume'],
            name='成交量',
            marker=dict(color='#90CAF9')
        ))
        
        fig_volume.update_layout(
            title='成交量',
            xaxis_title='日期',
            yaxis_title='成交量',
            height=250,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(rangeslider=dict(visible=False)),
            yaxis=dict(fixedrange=True)
        )
        
        st.plotly_chart(fig_volume, use_container_width=True, config={"scrollZoom": False})
    else:
        st.info("暂无成交量数据")

