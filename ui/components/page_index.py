"""
指数分析页面 - 指数查询和分析结果显示
"""

import streamlit as st
from datetime import datetime

def display_technical_indicators(tech_data):
    st.markdown("""
    <style>
    /* 调整 metric 组件的 value 字体大小 */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    """显示技术指标分析卡片"""
    st.subheader("技术指标分析")
    
    if not tech_data:
        st.warning("未获取到技术指标数据")
        return
    
    # 基础信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        latest_close = tech_data.get('latest_close', 0)
        if latest_close:
            st.metric("当前点位", f"{latest_close:.2f}")
        else:
            st.metric("当前点位", "N/A")
    with col2:
        latest_volume = tech_data.get('latest_volume', 0)
        if latest_volume:
            st.metric("成交量", f"{latest_volume:,.0f}")
        else:
            st.metric("成交量", "N/A")
    with col3:
        st.metric("MA趋势", tech_data.get('ma_trend', 'N/A'))
    with col4:
        st.metric("MACD趋势", tech_data.get('macd_trend', 'N/A'))
    
    # 移动平均线
    with st.expander("📈 移动平均线", expanded=True):
        ma_col1, ma_col2, ma_col3, ma_col4 = st.columns(4)
        with ma_col1:
            ma_5 = tech_data.get('ma_5')
            st.metric("MA5", f"{ma_5:.2f}" if ma_5 else "N/A")
        with ma_col2:
            ma_10 = tech_data.get('ma_10')
            st.metric("MA10", f"{ma_10:.2f}" if ma_10 else "N/A")
        with ma_col3:
            ma_20 = tech_data.get('ma_20')
            st.metric("MA20", f"{ma_20:.2f}" if ma_20 else "N/A")
        with ma_col4:
            ma_60 = tech_data.get('ma_60')
            st.metric("MA60", f"{ma_60:.2f}" if ma_60 else "N/A")
    
    # 技术指标
    with st.expander("🔢 技术指标", expanded=True):
        tech_col1, tech_col2, tech_col3 = st.columns(3)
        with tech_col1:
            rsi_14 = tech_data.get('rsi_14')
            st.metric("RSI(14)", f"{rsi_14:.2f}" if rsi_14 else "N/A")
        with tech_col2:
            kdj_k = tech_data.get('kdj_k')
            st.metric("KDJ-K", f"{kdj_k:.2f}" if kdj_k else "N/A")
        with tech_col3:
            kdj_d = tech_data.get('kdj_d')
            st.metric("KDJ-D", f"{kdj_d:.2f}" if kdj_d else "N/A")
        
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
            st.metric("布林上轨", f"{boll_upper:.2f}" if boll_upper else "N/A")
        with boll_col2:
            boll_middle = tech_data.get('boll_middle')
            st.metric("布林中轨", f"{boll_middle:.2f}" if boll_middle else "N/A")
        with boll_col3:
            boll_lower = tech_data.get('boll_lower')
            st.metric("布林下轨", f"{boll_lower:.2f}" if boll_lower else "N/A")
        
        # 其他技术指标
        other_col1, other_col2, other_col3 = st.columns(3)
        with other_col1:
            wr_14 = tech_data.get('wr_14')
            st.metric("威廉指标", f"{wr_14:.2f}" if wr_14 else "N/A")
        with other_col2:
            cci_14 = tech_data.get('cci_14')
            st.metric("CCI指标", f"{cci_14:.2f}" if cci_14 else "N/A")
        with other_col3:
            kdj_j = tech_data.get('kdj_j')
            st.metric("KDJ-J", f"{kdj_j:.2f}" if kdj_j else "N/A")


def display_market_sentiment(sentiment_data):
    """显示市场情绪指标卡片"""
    st.subheader("市场情绪指标")
    
    if not sentiment_data:
        st.warning("未获取到市场情绪数据")
        return
    
    # 涨跌家数
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        up_stocks = sentiment_data.get('up_stocks', 0)
        st.metric("上涨家数", f"{up_stocks:,}" if up_stocks else "N/A", delta=None)
    with col2:
        down_stocks = sentiment_data.get('down_stocks', 0)
        st.metric("下跌家数", f"{down_stocks:,}" if down_stocks else "N/A", delta=None)
    with col3:
        flat_stocks = sentiment_data.get('flat_stocks', 0)
        st.metric("平盘家数", f"{flat_stocks:,}" if flat_stocks else "N/A", delta=None)
    with col4:
        up_ratio = sentiment_data.get('up_ratio', 0)
        st.metric("上涨占比", f"{up_ratio*100:.1f}%" if up_ratio else "N/A")
    
    # 融资融券数据
    with st.expander("💳 融资融券数据", expanded=True):
        margin_col1, margin_col2, margin_col3 = st.columns(3)
        with margin_col1:
            margin_balance = sentiment_data.get('margin_balance')
            st.metric("融资融券余额", f"{margin_balance:.2f}亿" if margin_balance else "N/A")
        with margin_col2:
            margin_buy = sentiment_data.get('margin_buy_balance')
            st.metric("融资余额", f"{margin_buy:.2f}亿" if margin_buy else "N/A")
        with margin_col3:
            margin_sell = sentiment_data.get('margin_sell_balance')
            st.metric("融券余额", f"{margin_sell:.2f}亿" if margin_sell else "N/A")
    
    # 市场统计
    with st.expander("📊 市场统计", expanded=False):
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            total_stocks = sentiment_data.get('total_stocks', 0)
            st.metric("总股票数", f"{total_stocks:,}" if total_stocks else "N/A")
        with stats_col2:
            down_ratio = sentiment_data.get('down_ratio', 0)
            st.metric("下跌占比", f"{down_ratio*100:.1f}%" if down_ratio else "N/A")


def display_valuation_level(valuation_data):
    """显示估值水平卡片"""
    st.subheader("估值水平")
    
    if not valuation_data:
        st.warning("未获取到估值数据")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        hs300_pe = valuation_data.get('hs300_pe')
        st.metric("沪深300 PE", f"{hs300_pe:.2f}" if hs300_pe else "N/A")
    with col2:
        hs300_pb = valuation_data.get('hs300_pb')
        st.metric("沪深300 PB", f"{hs300_pb:.2f}" if hs300_pb else "N/A")
    with col3:
        dividend_yield = valuation_data.get('hs300_dividend_yield')
        st.metric("股息率", f"{dividend_yield:.2f}%" if dividend_yield else "N/A")
        
    # 估值分析
    with st.expander("📈 估值分析", expanded=False):
        pe_value = valuation_data.get('hs300_pe', 0)
        if pe_value:
            if pe_value < 12:
                pe_level = "极低估"
                pe_color = "🟢"
            elif pe_value < 15:
                pe_level = "低估"
                pe_color = "🟡"
            elif pe_value < 18:
                pe_level = "合理"
                pe_color = "🔵"
            elif pe_value < 25:
                pe_level = "偏高"
                pe_color = "🟠"
            else:
                pe_level = "高估"
                pe_color = "🔴"
            
            st.write(f"**PE估值水平:** {pe_color} {pe_level}")
            
        dividend_value = valuation_data.get('hs300_dividend_yield', 0)
        if dividend_value:
            if dividend_value > 3:
                div_level = "高股息"
                div_color = "🟢"
            elif dividend_value > 2:
                div_level = "中等股息"
                div_color = "🔵"
            else:
                div_level = "低股息"
                div_color = "🟡"
            
            st.write(f"**股息水平:** {div_color} {div_level}")


def display_money_flow(money_data):
    """显示资金流向卡片"""
    st.subheader("资金流向")
    
    if not money_data:
        st.warning("未获取到资金流向数据")
        return
    
    # M2数据
    col1, col2 = st.columns(2)
    with col1:
        m2_amount = money_data.get('m2_amount')
        st.metric("M2余额", f"{m2_amount/10000:.2f}万亿" if m2_amount else "N/A")
    with col2:
        m2_growth = money_data.get('m2_growth')
        st.metric("M2增速", f"{m2_growth:.2f}%" if m2_growth else "N/A")
    
    # M1数据
    with st.expander("💰 详细货币数据", expanded=False):
        m1_col1, m1_col2 = st.columns(2)
        with m1_col1:
            m1_amount = money_data.get('m1_amount')
            st.metric("M1余额", f"{m1_amount/10000:.2f}万亿" if m1_amount else "N/A")
        with m1_col2:
            m1_growth = money_data.get('m1_growth')
            st.metric("M1增速", f"{m1_growth:.2f}%" if m1_growth else "N/A")
        
        # 流动性分析
        st.write("**流动性分析:**")
        if money_data.get('m2_growth') and money_data.get('m1_growth'):
            m2_gr = money_data['m2_growth']
            m1_gr = money_data['m1_growth']
            if m2_gr > 10:
                st.write("🟢 M2增速较高，流动性充裕")
            elif m2_gr > 8:
                st.write("🔵 M2增速适中，流动性正常")
            else:
                st.write("🟡 M2增速偏低，流动性偏紧")
                
            if m1_gr > m2_gr:
                st.write("📈 M1增速超过M2，资金活跃度较高")
            else:
                st.write("📉 M1增速低于M2，资金活跃度一般")


def display_market_summary(result_data):
    """显示综合摘要卡片"""
    st.subheader("综合摘要")
    summary_data = result_data.get('market_summary', {})
    
    if not summary_data:
        st.info("综合摘要数据准备中...")
        return
    
    # 显示各个维度的摘要
    if 'technical_trend' in summary_data:
        st.write("**📈 技术面:**", summary_data['technical_trend'])
    if 'market_sentiment' in summary_data:
        st.write("**😊 情绪面:**", summary_data['market_sentiment'])
    if 'valuation_level' in summary_data:
        st.write("**💰 估值面:**", summary_data['valuation_level'])
    if 'liquidity_condition' in summary_data:
        st.write("**💸 资金面:**", summary_data['liquidity_condition'])
        
    # 综合评级
    st.markdown("---")
    st.write("**🎯 综合评级:**")
    
    # 根据各项指标给出综合评级
    tech_data = result_data.get('technical_indicators', {})
    sentiment_data = result_data.get('sentiment_indicators', {})
    
    score = 0
    total_indicators = 0
    
    # 技术面评分
    if tech_data.get('ma_trend') == '多头排列':
        score += 1
    total_indicators += 1
    
    if tech_data.get('macd_trend') == '金叉向上':
        score += 1
    total_indicators += 1
    
    # 情绪面评分
    up_ratio = sentiment_data.get('up_ratio', 0)
    if up_ratio > 0.6:
        score += 1
    elif up_ratio > 0.4:
        score += 0.5
    total_indicators += 1
    
    # 计算综合评级
    if total_indicators > 0:
        rating_ratio = score / total_indicators
        if rating_ratio >= 0.8:
            rating = "🟢 强势"
        elif rating_ratio >= 0.6:
            rating = "🔵 偏强"
        elif rating_ratio >= 0.4:
            rating = "🟡 中性"
        elif rating_ratio >= 0.2:
            rating = "🟠 偏弱"
        else:
            rating = "🔴 弱势"
        
        st.write(f"市场综合评级: {rating} (评分: {score:.1f}/{total_indicators})")
    else:
        st.write("市场综合评级: 数据不足")


def display_index_analysis_result(result_data):
    """显示指数分析结果"""
    # 应用自定义样式
    
    if not result_data:
        st.error("未获取到指数数据")
        return
    
    # 显示报告基本信息
    st.info(f"📊 **{result_data.get('focus_index', '未知指数')}** 综合分析报告")
    st.caption(f"报告时间: {result_data.get('report_time', '未知')}")
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 技术指标", "😊 市场情绪", "💰 估值水平", "💸 资金流向", "📋 综合摘要"])
    
    with tab1:
        display_technical_indicators(result_data.get('technical_indicators', {}))
    
    with tab2:
        display_market_sentiment(result_data.get('sentiment_indicators', {}))
    
    with tab3:
        display_valuation_level(result_data.get('valuation_indicators', {}))
    
    with tab4:
        display_money_flow(result_data.get('money_flow_indicators', {}))
    
    with tab5:
        display_market_summary(result_data)


def show_index_query_interface():
    """显示指数查询界面"""
    st.header("📊 指数分析")
    
    # 指数选择
    index_options = {
        "上证指数": "000001",
        "深证成指": "399001", 
        "创业板指": "399006",
        "沪深300": "000300",
        "中证500": "000905",
        "科创50": "000688"
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_index = st.selectbox(
            "选择指数:",
            list(index_options.keys()),
            help="选择要分析的指数"
        )
    
    with col2:
        st.write("")
        st.write("")
        query_btn = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    # 显示指数代码
    st.caption(f"指数代码: {index_options[selected_index]}")
    
    return selected_index, query_btn


def query_index_data(index_name: str):
    """查询指数数据"""
    try:
        from providers.market_tools import MarketIndicators
        market_collector = MarketIndicators()
        result = market_collector.get_comprehensive_market_report(index_name)
        return result
    except Exception as e:
        st.error(f"查询指数数据失败: {str(e)}")
        return None


def main():
    """指数分析页面主函数"""
    
    # 显示查询界面
    selected_index, query_btn = show_index_query_interface()
    
    # 处理查询
    if query_btn:
        with st.spinner(f"正在分析{selected_index}数据..."):
            result = query_index_data(selected_index)
            if result:
                display_index_analysis_result(result)


if __name__ == "__main__":
    main()
