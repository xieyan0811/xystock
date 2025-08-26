"""
大盘整体分析页面 - 市场全局分析和上证指数分析
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
from providers.market_tools import get_market_tools

def display_market_sentiment():
    """显示市场情绪指标卡片"""
    
    sentiment_data = get_market_tools().get_market_sentiment()
    margin_data = get_market_tools().get_margin_data()
    
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
            margin_balance = margin_data.get('margin_balance')
            st.metric("融资融券余额", f"{format_large_number(margin_balance)}" if margin_balance else "N/A")
        with margin_col2:
            margin_buy = margin_data.get('margin_buy_balance')
            st.metric("融资余额", f"{format_large_number(margin_buy)}" if margin_buy else "N/A")
        with margin_col3:
            margin_sell = margin_data.get('margin_sell_balance')
            st.metric("融券余额", f"{format_large_number(margin_sell)}" if margin_sell else "N/A")
    
        st.metric("统计时间", margin_data.get('margin_date', 'N/A'))
    # 市场统计
    with st.expander("📊 市场统计", expanded=False):
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            total_stocks = sentiment_data.get('total_stocks', 0)
            st.metric("总股票数", format_large_number(total_stocks, 0) if total_stocks else "N/A")
        with stats_col2:
            down_ratio = sentiment_data.get('down_ratio', 0)
            st.metric("下跌占比", f"{down_ratio*100:.1f}%" if down_ratio else "N/A")


def display_valuation_level():
    """显示估值水平卡片"""
    
    valuation_data = get_market_tools().get_valuation_data()
        
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


def display_money_flow():
    """显示资金流向卡片"""
    
    money_data = get_market_tools().get_money_flow_data()

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


def display_market_indices():
    """显示大盘指数信息"""
    
    market_tools = get_market_tools()
    
    st.subheader("大盘指数")
    
    # 定义主要指数
    indices = {
        '上证指数': '000001',
        '深证成指': '399001',
        '创业板指': '399006',
        '沪深300': '000300',
        '中证500': '000905',
        '科创50': '000688'
    }
    
    # 获取指数数据
    col1, col2, col3 = st.columns(3)
    
    index_names = list(indices.keys())
    
    for i, (index_name, index_code) in enumerate(indices.items()):
        col = [col1, col2, col3][i % 3]
        
        with col:
            try:
                # 获取技术指标数据
                tech_data = market_tools.get_index_technical_indicators(index_name, period=30)
                
                if tech_data and 'latest_close' in tech_data:
                    current_price = tech_data['latest_close']
                    change_percent = tech_data.get('change_percent', 0)
                    change_amount = tech_data.get('change_amount', 0)
                    
                    # 显示指数信息
                    if change_percent > 0:
                        delta_color = "normal"
                        delta_text = f"+{change_amount:.2f} (+{change_percent:.2f}%)"
                    elif change_percent < 0:
                        delta_color = "inverse"
                        delta_text = f"{change_amount:.2f} ({change_percent:.2f}%)"
                    else:
                        delta_color = "off"
                        delta_text = "0.00 (0.00%)"
                    
                    st.metric(
                        label=index_name,
                        value=f"{current_price:.2f}",
                        delta=delta_text,
                        delta_color=delta_color
                    )
                else:
                    st.metric(
                        label=index_name,
                        value="N/A",
                        delta="数据获取中..."
                    )
                    
            except Exception as e:
                st.metric(
                    label=index_name,
                    value="N/A",
                    delta="获取失败"
                )
    
    # 显示指数分析摘要
    with st.expander("📊 指数分析", expanded=False):
        selected_index = st.selectbox("选择指数进行详细分析", list(indices.keys()), index=0)
        
        if selected_index:
            try:
                tech_data = market_tools.get_index_technical_indicators(selected_index, period=100)
                
                if tech_data:
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write("**技术指标:**")
                        ma_trend = tech_data.get('ma_trend', '未知')
                        macd_trend = tech_data.get('macd_trend', '未知')
                        rsi_14 = tech_data.get('rsi_14', 0)
                        
                        st.write(f"MA趋势: {ma_trend}")
                        st.write(f"MACD趋势: {macd_trend}")
                        st.write(f"RSI(14): {rsi_14:.2f}" if isinstance(rsi_14, (int, float)) else f"RSI(14): {rsi_14}")
                    
                    with col_b:
                        st.write("**价格信息:**")
                        latest_high = tech_data.get('latest_high', 0)
                        latest_low = tech_data.get('latest_low', 0)
                        latest_volume = tech_data.get('latest_volume', 0)
                        
                        st.write(f"最高价: {latest_high:.2f}" if latest_high else "最高价: N/A")
                        st.write(f"最低价: {latest_low:.2f}" if latest_low else "最低价: N/A")
                        st.write(f"成交量: {format_large_number(latest_volume)}" if latest_volume else "成交量: N/A")
                else:
                    st.warning(f"无法获取{selected_index}的技术数据")
            except Exception as e:
                st.error(f"分析{selected_index}时出错: {str(e)}")


def display_market_summary():
    """显示综合摘要卡片"""

    market_tools = get_market_tools()    
    result_data = market_tools.get_comprehensive_market_report()

    st.subheader("综合摘要")
    summary_data = result_data.get('market_summary', {})
    
    if not summary_data:
        st.info("综合摘要数据准备中...")
        return
    
    if st.session_state.get('run_ai_index_for') == '上证指数':        
        # 检查是否已经生成过这个股票的AI报告
        stock_code_for_ai = '上证指数'
        if stock_code_for_ai not in st.session_state.get('ai_index_report', {}):
            with st.spinner("🤖 AI正在分析指数数据..."):
                try:
                    # 调用market_tools中的AI分析方法
                    ai_data = market_tools.get_ai_analysis(
                        use_cache=False, 
                        index_name=stock_code_for_ai, 
                        force_regenerate=True
                    )
                    
                    # 保存AI报告到session_state
                    if "ai_index_report" not in st.session_state:
                        st.session_state.ai_index_report = {}
                    st.session_state.ai_index_report[stock_code_for_ai] = ai_data
                    
                    # 清除标记，避免重复执行
                    if 'run_ai_index_for' in st.session_state:
                        del st.session_state['run_ai_index_for']
                except Exception as e:
                    st.error(f"AI分析失败: {str(e)}")
                    # 清除标记，即使失败也要清除
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
            
            
def display_market_overview():
    """显示大盘整体分析"""
    
    st.header("📊 大盘整体分析")
    st.caption("基于上证指数的全市场分析")
    
    # AI分析选项
    use_ai_analysis = st.checkbox("🤖 AI大盘分析", value=False, help="选中后将使用AI对大盘进行深入分析")
    
    # 分析按钮
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        analyze_btn = st.button("🔍 开始分析", type="primary")
    with col2:
        refresh_btn = st.button("🔄 刷新数据")
    
    market_tools = get_market_tools()
    
    # 处理刷新按钮
    if refresh_btn:
        market_tools.refresh_all_cache()
        st.rerun()
    
    # 显示分析结果的区域
    result_container = st.container()
    
    # 处理分析逻辑
    if analyze_btn:
        with result_container:
            with st.spinner("正在分析大盘数据..."):
                try:
                    # 如果选择了AI分析，设置session_state参数
                    if use_ai_analysis:
                        if "ai_index_report" not in st.session_state:
                            st.session_state.ai_index_report = {}
                        st.session_state['run_ai_index_for'] = "上证指数"
                                            
                    # 显示报告基本信息
                    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success(f"📊 **大盘整体分析报告** (基于上证指数)")
                    st.caption(f"报告时间: {report_time}")
                    
                    # 创建标签页
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 大盘指数", "📊 技术指标", "😊 市场情绪", "💰 估值水平", "💸 资金流向", "📋 综合摘要"])
                    
                    with tab1:
                        display_market_indices()
                    
                    with tab2:
                        tech_data = market_tools.get_index_technical_indicators('上证指数')
                        display_technical_indicators(tech_data)

                    with tab3:
                        display_market_sentiment()
                    
                    with tab4:
                        display_valuation_level()
                    
                    with tab5:
                        display_money_flow()

                    with tab6:
                        display_market_summary()
                        
                    # 额外的展示选项
                    with st.expander("📊 详细信息", expanded=False):
                        st.write(f"**分析时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**分析对象:** 上证指数 (大盘整体)")
                        st.write(f"**数据来源:** 实时市场数据")
                        
                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    st.write("请稍后重试或检查网络连接。")
                    
                    # 显示错误详情（调试用）
                    with st.expander("🔍 错误详情", expanded=False):
                        st.code(str(e), language="text")
    else:
        with result_container:
            st.info("点击'开始分析'按钮获取大盘整体分析报告")
            
            # 显示功能说明
            with st.expander("ℹ️ 功能说明", expanded=True):
                st.markdown("""
                **大盘整体分析功能包括：**
                
                - 📈 **大盘指数**: 显示主要指数的实时价格和涨跌幅，包括上证指数、深证成指、创业板指等
                - 📊 **技术指标分析**: 基于上证指数的技术指标，反映大盘走势
                - 😊 **市场情绪分析**: 全市场涨跌家数、融资融券等情绪指标
                - 💰 **估值水平分析**: 市场整体估值水平评估
                - 💸 **资金流向分析**: 主力资金流向和市场资金面分析
                - 📋 **综合摘要**: AI生成的大盘分析综合报告
                
                **AI分析功能：** 选中AI分析选项后，系统会对大盘数据进行深度分析，提供更详细的投资建议。
                """)
