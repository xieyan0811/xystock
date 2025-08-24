"""
指数分析页面 - 指数查询和分析结果显示
"""

import streamlit as st
import datetime
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_large_number, format_percentage
from ui.components.page_common import display_technical_indicators
from providers.market_tools import MarketIndicators

def display_market_sentiment(sentiment_data = None):
    """显示市场情绪指标卡片"""
    
    if sentiment_data is None:
        sentiment_data = MarketIndicators().get_market_sentiment_indicators()
    
    st.subheader("市场情绪指标")
    
    if not sentiment_data:
        st.warning("未获取到市场情绪数据")
        return
    
    # 涨跌家数
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        up_stocks = sentiment_data.get('up_stocks', 0)
        st.metric("上涨家数", format_large_number(up_stocks, 0) if up_stocks else "N/A", delta=None)
    with col2:
        down_stocks = sentiment_data.get('down_stocks', 0)
        st.metric("下跌家数", format_large_number(down_stocks, 0) if down_stocks else "N/A", delta=None)
    with col3:
        flat_stocks = sentiment_data.get('flat_stocks', 0)
        st.metric("平盘家数", format_large_number(flat_stocks, 0) if flat_stocks else "N/A", delta=None)
    with col4:
        up_ratio = sentiment_data.get('up_ratio', 0)
        st.metric("上涨占比", format_percentage(up_ratio*100) if up_ratio else "N/A")
    
    # 融资融券数据
    with st.expander("💳 融资融券数据", expanded=True):
        margin_col1, margin_col2, margin_col3 = st.columns(3)
        with margin_col1:
            margin_balance = sentiment_data.get('margin_balance')
            st.metric("融资融券余额", f"{format_large_number(margin_balance)}" if margin_balance else "N/A")
        with margin_col2:
            margin_buy = sentiment_data.get('margin_buy_balance')
            st.metric("融资余额", f"{format_large_number(margin_buy)}" if margin_buy else "N/A")
        with margin_col3:
            margin_sell = sentiment_data.get('margin_sell_balance')
            st.metric("融券余额", f"{format_large_number(margin_sell)}" if margin_sell else "N/A")
    
        st.metric("统计时间", sentiment_data.get('margin_date', 'N/A'))
    # 市场统计
    with st.expander("📊 市场统计", expanded=False):
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            total_stocks = sentiment_data.get('total_stocks', 0)
            st.metric("总股票数", format_large_number(total_stocks, 0) if total_stocks else "N/A")
        with stats_col2:
            down_ratio = sentiment_data.get('down_ratio', 0)
            st.metric("下跌占比", f"{down_ratio*100:.1f}%" if down_ratio else "N/A")


def display_valuation_level(valuation_data=None):
    """显示估值水平卡片"""
    
    if valuation_data is None:
        valuation_data = MarketIndicators().get_valuation_indicators()
        
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


def display_money_flow(money_data=None):
    """显示资金流向卡片"""
    
    if money_data is None:
        money_data = MarketIndicators().get_money_flow_indicators()

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
    
    # 检查是否需要生成AI分析报告
    if st.session_state.get('run_ai_index_for'):
        stock_code_for_ai = st.session_state.get('run_ai_index_for')
        
        # 检查是否已经生成过这个股票的AI报告
        if stock_code_for_ai not in st.session_state.get('ai_index_report', {}):
            with st.spinner("🤖 AI正在分析指数数据..."):
                try:
                    from analysis.stock_ai_analysis import generate_index_analysis_report
                    
                    # 使用result_data作为市场报告数据
                    ai_report, timestamp = generate_index_analysis_report(
                        stock_code_for_ai,
                        result_data.get('focus_index', stock_code_for_ai),
                        result_data
                    )
                    
                    # 保存AI报告到session_state
                    if "ai_index_report" not in st.session_state:
                        st.session_state.ai_index_report = {}
                    st.session_state.ai_index_report[stock_code_for_ai] = {
                        'report': ai_report,
                        'timestamp': timestamp
                    }
                except Exception as e:
                    st.error(f"AI分析失败: {str(e)}")
        
        # 清除标志
        if 'run_ai_index_for' in st.session_state:
            del st.session_state['run_ai_index_for']
    
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
    
    # 显示AI分析报告（如果有的话）
    current_stock_code = result_data.get('focus_index', '')
    if st.session_state.get('ai_index_report') and current_stock_code in st.session_state['ai_index_report']:
        ai_data = st.session_state['ai_index_report'][current_stock_code]
        
        st.markdown("---")
        st.subheader("🤖 AI深度分析")
        
        # 显示AI分析报告
        with st.expander("📊 AI指数分析报告", expanded=True):
            st.markdown(ai_data['report'])
            st.caption(f"分析时间: {ai_data['timestamp']}")
            
            # 添加重新分析按钮
            if st.button("🔄 重新生成AI分析", key="regenerate_ai_index"):
                # 清除当前AI报告并重新生成
                if current_stock_code in st.session_state['ai_index_report']:
                    del st.session_state['ai_index_report'][current_stock_code]
                st.session_state['run_ai_index_for'] = current_stock_code
                st.rerun()


def display_index_info(stock_code, stock_name):
    """显示指数分析结果"""
        
    market_collector = MarketIndicators()
    result_data = market_collector.get_comprehensive_market_report(stock_name)

    if not result_data:
        st.error("未获取到指数数据")
        return
    
    if not isinstance(result_data, dict):
        st.code(str(result_data), language="text")
        return
        
    # 显示报告基本信息
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.info(f"📊 **{stock_name}** 综合分析报告")
    st.caption(f"报告时间: {report_time}")
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 技术指标", "😊 市场情绪", "💰 估值水平", "💸 资金流向", "📋 综合摘要"])
    
    with tab1:
        # tech_data = market_collector.get_index_technical_indicators(stock_name)
        tech_data = result_data.get('technical_indicators', {})
        display_technical_indicators(tech_data)

    with tab2:
        display_market_sentiment(result_data.get('sentiment_indicators', {}))
    
    with tab3:
        display_valuation_level(result_data.get('valuation_indicators', {}))
    
    with tab4:
        display_money_flow(result_data.get('money_flow_indicators', {}))

    with tab5:
        display_market_summary(result_data)

