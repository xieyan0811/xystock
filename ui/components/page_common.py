import streamlit as st
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_price

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

