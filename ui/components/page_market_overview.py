"""
大盘整体分析页面 - 市场全局分析和指数分析
"""

import streamlit as st
import datetime
import sys
import os
import pandas as pd
from typing import Dict

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_large_number
from market.market_data_tools import get_market_tools
from market.market_report import write_market_report
from ui.config import FOCUS_INDICES


def display_valuation_analysis(index_name='沪深300', use_cache=True):
    """显示估值水平分析"""
    st.markdown("#### 💰 估值水平")
    
    # 根据指数获取对应的估值数据
    market_tools = get_market_tools()
    index_valuation_data = market_tools.get_index_valuation_data(index_name, use_cache=use_cache)
    
    if not index_valuation_data:
        st.warning("未获取到估值数据")
    else:
        # 获取估值参考信息
        reference_index = index_valuation_data.get('reference_index', index_name)
        is_direct = index_valuation_data.get('is_direct_valuation', True)
        valuation_desc = index_valuation_data.get('valuation_description', '')
        
        # 显示估值数据来源说明
        if not is_direct:
            st.info(f"💡 **{index_name} 估值参考说明**: {valuation_desc}")
        
        val_col1, val_col2 = st.columns(2)
        with val_col1:
            index_pe = index_valuation_data.get('index_pe')
            # 根据是否为直接估值决定显示方式
            if is_direct:
                pe_title = f"{index_name} PE"
                pe_help = f"基于{index_name}成分股的市盈率"
            else:
                pe_title = f"{index_name} PE"
                pe_help = f"基于{reference_index}估值数据作为参考，{valuation_desc}"
            
            st.metric(pe_title, f"{index_pe:.2f}" if index_pe else "N/A", help=pe_help)
            
        with val_col2:
            dividend_yield = index_valuation_data.get('index_dividend_yield')
            if is_direct:
                div_title = f"{index_name} 股息率"
                div_help = f"基于{index_name}成分股的股息收益率"
            else:
                div_title = f"{index_name} 股息率" 
                div_help = f"基于{reference_index}股息率数据作为参考"
                
            st.metric(div_title, f"{dividend_yield:.2f}%" if dividend_yield else "N/A", help=div_help)
            
        with st.expander("📈 估值分析", expanded=True):
            pe_value = index_valuation_data.get('index_pe', 0)
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
                
            dividend_value = index_valuation_data.get('index_dividend_yield', 0)
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
    
    val_time = index_valuation_data.get('update_time') or index_valuation_data.get('index_date')
    if val_time:
        st.caption(f"估值数据获取时间: {val_time}")


def display_money_flow_analysis(use_cache=True):
    """显示资金流向分析"""
    st.markdown("#### 💸 资金流向")
    
    money_data = get_market_tools().get_money_flow_data(use_cache=use_cache)
    
    if not money_data:
        st.warning("未获取到资金流向数据")
    else:
        money_col1, money_col2 = st.columns(2)
        with money_col1:
            m2_amount = money_data.get('m2_amount')
            st.metric("M2余额", f"{m2_amount/10000:.2f}万亿" if m2_amount else "N/A")
        with money_col2:
            m2_growth = money_data.get('m2_growth')
            st.metric("M2同比增长", f"{m2_growth:.2f}%" if m2_growth else "N/A")
        
        m1_col1, m1_col2 = st.columns(2)
        with m1_col1:
            m1_amount = money_data.get('m1_amount')
            st.metric("M1余额", f"{m1_amount/10000:.2f}万亿" if m1_amount else "N/A")
        with m1_col2:
            m1_growth = money_data.get('m1_growth')
            st.metric("M1同比增长", f"{m1_growth:.2f}%" if m1_growth else "N/A")
        
        with st.expander("💧 流动性分析", expanded=True):
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
    
    money_time = money_data.get('update_time') or money_data.get('date')
    if money_time:
        st.caption(f"资金流向数据获取时间: {money_time}")


def convert_markdown_to_streamlit(markdown_text: str, sentiment_data: Dict):
    """简化版本：直接显示markdown内容"""
    if not markdown_text:
        st.warning("未获取到市场情绪数据")
        return
    
    # 直接显示markdown内容
    st.markdown(markdown_text)


def display_market_sentiment_analysis(use_cache=True):
    """显示市场情绪指标分析"""
    
    # 获取综合市场情绪数据
    market_tools = get_market_tools()
    sentiment_data = market_tools.get_market_sentiment(use_cache=use_cache, comprehensive=True)
    
    if not sentiment_data or 'error' in sentiment_data:
        st.warning("未获取到市场情绪数据")
    else:
        # 使用统一的markdown生成函数
        sentiment_markdown = market_tools.generate_sentiment_markdown(sentiment_data)
        
        # 转换为Streamlit显示格式
        convert_markdown_to_streamlit(sentiment_markdown, sentiment_data)


def display_margin_trading_analysis(use_cache=True):
    """显示融资融券数据"""
    st.markdown("#### 💳 融资融券数据")
    
    margin_data = get_market_tools().get_margin_data(use_cache=use_cache)
    
    if not margin_data:
        st.warning("未获取到融资融券数据")
    else:
        # 第一行：余额数据
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
        
        # 第二行：周变化率
        change_col1 = st.columns(1)[0]  # 获取第一个（也是唯一的）列
        with change_col1:
            change_ratio = margin_data.get('change_ratio')
            if change_ratio is not None:
                delta_color = "normal" if change_ratio > 0 else "inverse" if change_ratio < 0 else "off"
                st.metric("周变化率", f"{change_ratio:.2f}%", delta_color=delta_color)
            else:
                st.metric("周变化率", "N/A")

        # 统计时间
        margin_date = margin_data.get('margin_date')
        if margin_date:
            st.caption(f"统计时间: {margin_date}")
        
    margin_time = margin_data.get('update_time') or margin_data.get('margin_date')
    if margin_time:
        st.caption(f"融资融券数据获取时间: {margin_time}")


def display_market_fundamentals(index_name='沪深300'):
    """显示市场基本面分析"""
    st.subheader("市场基本面分析")
    
    use_cache = st.session_state.get('market_use_cache', True)
    
    # 显示各个分析模块
    display_valuation_analysis(index_name, use_cache)
    display_money_flow_analysis(use_cache)
    display_market_sentiment_analysis(use_cache)
    display_margin_trading_analysis(use_cache)

def display_market_news():
    """显示市场新闻"""
    from config_manager import config
    
    # 检查是否启用市场新闻功能
    if not config.is_market_news_enabled():
        return  # 直接返回，不显示任何内容
    
    st.subheader("📰 市场资讯")
    
    use_cache = st.session_state.get('market_use_cache', True)
    
    market_tools = get_market_tools()
    news_data = market_tools.get_market_news_data(use_cache=use_cache)
    
    if 'error' in news_data:
        if news_data.get('disabled'):
            return  # 功能已禁用，不显示任何内容
        st.warning(f"获取市场新闻失败: {news_data['error']}")
    elif news_data and news_data.get('market_news'):
        market_news = news_data['market_news']
        news_summary = news_data.get('news_summary', {})
        
        st.info(f"共获取到 {news_summary.get('total_market_news_count', len(market_news))} 条宏观经济新闻")
        
        if market_news:
            # 显示前10条新闻
            for idx, news in enumerate(market_news[:10]):
                title = news.get('新闻标题', '')
                time_info = news.get('发布时间', '')
                relative_time = news.get('相对时间', '')
                url = news.get('新闻链接', '')
                
                # 组合时间信息显示
                time_display = time_info
                if relative_time:
                    time_display = f"{time_info} ({relative_time})"
                
                with st.expander(f"📄 {title} - {time_display}", expanded=False):
                    if '新闻内容' in news and news['新闻内容']:
                        st.write(news['新闻内容'])
                    else:
                        st.write("无详细内容")
                    
                    if url:
                        st.caption(f"[查看原文]({url})")
            
            if len(market_news) > 10:
                st.caption(f"显示前10条，共{len(market_news)}条新闻")
        else:
            st.write("暂无市场新闻")
    else:
        st.info("未能获取到市场新闻")
    
    news_time = news_data.get('news_summary', {}).get('data_freshness')
    if news_time:
        st.caption(f"市场新闻数据获取时间: {news_time}")

def display_market_indices():
    """显示大盘指数信息"""
    
    market_tools = get_market_tools()
    
    st.subheader("大盘指数")
    
    try:
        use_cache = st.session_state.get('market_use_cache', True)
        force_refresh = not use_cache
        
        indices_data = market_tools.get_current_indices(use_cache=use_cache, force_refresh=force_refresh)
        
        if 'error' in indices_data:
            st.error(f"获取指数数据失败: {indices_data['error']}")
            return
            
        if 'indices_dict' not in indices_data:
            st.warning("暂无指数数据")
            return
        
        indices_dict = indices_data['indices_dict']
        
        main_indices = FOCUS_INDICES
        
        col1, col2, col3 = st.columns(3)
        
        for i, index_name in enumerate(main_indices):
            col = [col1, col2, col3][i % 3]
            
            with col:
                if index_name in indices_dict:
                    index_info = indices_dict[index_name]
                    
                    current_price = index_info['current_price']
                    change_percent = index_info['change_percent']
                    change_amount = index_info['change_amount']
                    
                    if change_percent > 0:
                        metric_delta_text = f"+{change_amount:.2f} (+{change_percent:.2f}%)"
                    elif change_percent < 0:
                        metric_delta_text = f"{change_amount:.2f} ({change_percent:.2f}%)"
                    else:
                        metric_delta_text = "➖ 0.00 (0.00%)"
                                        
                    st.metric(
                        label=index_name,
                        value=f"{current_price:.2f}",
                        delta=metric_delta_text,
                        delta_color="inverse" if change_percent != 0 else "off"
                    )
        
        if 'update_time' in indices_data:
            st.caption(f"数据更新时间: {indices_data['update_time']}")
                            
    except Exception as e:
        st.error(f"显示指数数据时出错: {str(e)}")
        

def handle_ai_analysis(index_name, use_cache=True):
    """处理AI分析功能"""
    if st.session_state.get('run_ai_index', False):
        # 检查是否已经生成过AI报告
        stock_code_for_ai = index_name
        with st.spinner(f"🤖 AI正在分析{stock_code_for_ai}数据..."):
            try:
                user_opinion = st.session_state.get('market_user_opinion', '')
                market_tools = get_market_tools()
                ai_data = market_tools.get_ai_analysis(
                    use_cache=use_cache, 
                    index_name=stock_code_for_ai, 
                    force_regenerate=not use_cache,
                    user_opinion=user_opinion
                )
                
                if "ai_index_report" not in st.session_state:
                    st.session_state.ai_index_report = {}
                st.session_state.ai_index_report[stock_code_for_ai] = ai_data
                
                if 'run_ai_index' in st.session_state:
                    del st.session_state['run_ai_index']
            except Exception as e:
                st.error(f"AI分析失败: {str(e)}")
                if 'run_ai_index' in st.session_state:
                    del st.session_state['run_ai_index']


def display_ai_analysis_section(index_name):
    """显示AI分析部分"""
    current_stock_code = index_name
    if st.session_state.get('ai_index_report') and current_stock_code in st.session_state['ai_index_report']:
        ai_data = st.session_state['ai_index_report'][current_stock_code]
        
        st.markdown("---")
        st.subheader("🤖 AI深度分析")
        
        with st.expander(f"📊 AI{current_stock_code}分析报告", expanded=True):
            st.markdown(ai_data['report'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"分析时间: {ai_data['timestamp']}")
            with col2:
                if ai_data.get('user_opinion'):
                    st.caption(f"包含用户观点: ✅")
                else:
                    st.caption(f"包含用户观点: ❌")
        return True
    return False


def display_comprehensive_rating(result_data, use_cache=True):
    """显示综合评级"""
    st.markdown("---")
    st.write("**🎯 综合评级:**")
    
    tech_data = result_data.get('technical_indicators', {})
    margin_data = get_market_tools().get_margin_data(use_cache=use_cache)
    sentiment_data = get_market_tools().get_market_sentiment(use_cache=use_cache, comprehensive=True)
    
    score = 0
    total_indicators = 0
    
    # 技术面评分
    if tech_data.get('ma_trend') == '多头排列':
        score += 1
    total_indicators += 1
    
    if tech_data.get('macd_trend') == '金叉向上':
        score += 1
    total_indicators += 1
    
    # 资金面评分  
    margin_balance = margin_data.get('margin_balance', 0)
    if margin_balance and margin_balance > 15000:
        score += 1
    elif margin_balance and margin_balance > 12000:
        score += 0.5
    total_indicators += 1
    
    # 情绪面评分
    if sentiment_data and 'sentiment_score' in sentiment_data:
        sentiment_score = sentiment_data.get('sentiment_score', 0)
        if sentiment_score > 20:
            score += 1
        elif sentiment_score > 0:
            score += 0.5
        elif sentiment_score > -20:
            score += 0.25
        # 负分不加分
        total_indicators += 1
    
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
        
        # 显示各维度贡献
        with st.expander("📊 评级构成详情", expanded=False):
            st.write("**各维度评分贡献：**")
            
            # 技术面
            tech_score = 0
            if tech_data.get('ma_trend') == '多头排列':
                tech_score += 1
            if tech_data.get('macd_trend') == '金叉向上':
                tech_score += 1
            st.write(f"- 📈 技术面: {tech_score}/2")
            
            # 资金面
            fund_score = 0
            if margin_balance and margin_balance > 15000:
                fund_score = 1
            elif margin_balance and margin_balance > 12000:
                fund_score = 0.5
            st.write(f"- 💳 资金面: {fund_score}/1")
            
            # 情绪面
            if sentiment_data and 'sentiment_score' in sentiment_data:
                sentiment_score = sentiment_data.get('sentiment_score', 0)
                emotion_score = 0
                if sentiment_score > 20:
                    emotion_score = 1
                elif sentiment_score > 0:
                    emotion_score = 0.5
                elif sentiment_score > -20:
                    emotion_score = 0.25
                st.write(f"- 😊 情绪面: {emotion_score}/1 (评分: {sentiment_score:.1f})")
            else:
                st.write(f"- 😊 情绪面: 数据缺失")
    else:
        st.write("市场综合评级: 数据不足")


def display_market_report_export(index_name):
    """显示市场报告导出功能"""
    def generate_market_report_wrapper(format_type):
        """包装市场报告生成函数"""
        # 检查是否有AI分析报告
        has_ai_analysis = bool(st.session_state.get('ai_index_report', {}).get(index_name))
        user_opinion = st.session_state.get('market_user_opinion', '')
        
        return write_market_report(
            index_name=index_name,
            format_type=format_type,
            has_ai_analysis=has_ai_analysis,
            user_opinion=user_opinion
        )
    
    # 使用通用的导出功能
    from ui.components.page_export import display_report_export_section
    display_report_export_section(
        entity_id=index_name,
        report_type="market_report",
        title="📋 导出市场报告",
        info_text="💡 可以导出当前市场分析的完整报告",
        generate_func=generate_market_report_wrapper,
        generate_args=None,
        filename_prefix="市场分析报告"
    )


def display_market_technical_analysis(index_name='上证指数'):
    """显示市场技术分析"""
    # 显示K线图
    st.subheader(f"{index_name} K线走势")
    try:
        use_cache = st.session_state.get('market_use_cache', True)
        force_refresh = not use_cache
        market_tools = get_market_tools()
        
        # 获取K线数据
        kline_info = market_tools.get_index_kline_data(
            index_name, 
            period=160, 
            use_cache=use_cache, 
            force_refresh=force_refresh
        )
        
        if 'error' in kline_info:
            st.error(f"获取K线数据失败: {kline_info['error']}")
        elif kline_info and kline_info.get('kline_data'):
            df = pd.DataFrame(kline_info['kline_data'])
            
            # 显示K线图和成交量图
            from ui.components.page_common import display_kline_charts
            display_kline_charts(df, chart_type="index", title_prefix=index_name)
            
            # 显示数据来源信息
            data_source = kline_info.get('data_source', '未知')
            update_time = kline_info.get('update_time', '')
            if update_time:
                st.caption(f"数据来源: {data_source} | 更新时间: {update_time}")
        else:
            st.warning(f"未获取到 {index_name} 的K线数据")
    
    except Exception as e:
        st.error(f"加载K线数据失败: {str(e)}")
    
    # 显示技术指标分析
    from ui.components.page_common import display_technical_analysis_tab, display_risk_analysis
    display_technical_analysis_tab(index_name=index_name)
    
    # 显示大盘风险分析
    st.markdown("---")
    st.subheader(f"风险分析")
    try:
        use_cache = st.session_state.get('market_use_cache', True)
        market_tools = get_market_tools()
        
        # 获取指定指数的技术指标数据（包含风险数据）
        tech_data = market_tools.get_index_technical_indicators(index_name)
        
        if tech_data and not ('error' in tech_data):
            # 直接使用返回数据中的风险指标
            risk_metrics = tech_data.get('risk_metrics', None)
            display_risk_analysis(risk_metrics)
        else:
            st.warning(f"暂无风险分析数据")
            
    except Exception as e:
        st.error(f"获取风险分析失败: {str(e)}")


def display_market_summary(index_name='上证指数'):
    """显示综合摘要卡片"""
    use_cache = st.session_state.get('market_use_cache', True)
    
    market_tools = get_market_tools()    
    result_data = market_tools.get_comprehensive_market_report(use_cache=use_cache, index_name=index_name)
    summary_text = market_tools.generate_market_report(result_data, format_type='summary')

    if not summary_text:
        st.info("综合摘要数据准备中...")
        return
    
    # 处理AI分析
    handle_ai_analysis(index_name, use_cache)
    
    # 显示AI分析结果和综合摘要
    current_stock_code = result_data.get('focus_index', index_name)
    has_ai_analysis = display_ai_analysis_section(current_stock_code)
    
    # 显示综合评级
    display_comprehensive_rating(result_data, use_cache)
    
    # 显示导出功能
    display_market_report_export(current_stock_code)

            
def display_market_overview():
    """显示大盘整体分析"""
    
    st.header("📊 大盘整体分析")
    
    # 指数选择
    selected_index = st.selectbox(
        "选择分析指数",
        options=FOCUS_INDICES,
        index=0,  # 默认选择上证指数
        help="选择要分析的指数"
    )
    
    st.caption(f"基于{selected_index}的全市场分析")
    
    use_ai_analysis = st.checkbox("🤖 AI大盘分析", value=False, help="选中后将使用AI对大盘进行深入分析")
    use_cache = st.checkbox("💾 使用缓存数据", value=True, help="使用缓存数据可以加快查询速度，取消勾选将强制获取最新数据")
    
    user_opinion = ""
    if use_ai_analysis:
        user_opinion = st.text_area(
            "补充观点（可选）:",
            placeholder="请输入您对大盘的观点、看法或关注的重点...",
            help="输入您的投资观点或对大盘的看法，AI将结合市场数据给出综合分析",
            height=100
        )
    
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        analyze_btn = st.button("🔍 开始分析", type="primary")
    with col2:
        refresh_btn = st.button("🔄 刷新数据")
    
    market_tools = get_market_tools()
    
    if refresh_btn:
        market_tools.refresh_all_cache()
        st.session_state.pop('show_analysis_results', None)
        st.rerun()
    
    result_container = st.container()
    
    if analyze_btn:
        st.session_state['show_analysis_results'] = True
        st.session_state['market_use_cache'] = True
        if not use_cache:
            market_tools.clear_cache()
            st.success("💾 已清除缓存，强制获取最新数据")
    
    if st.session_state.get('show_analysis_results', False):
        with result_container:
            with st.spinner("正在分析大盘数据..."):
                try:
                    # 只有在点击分析按钮时才设置AI分析相关的session_state
                    if analyze_btn:
                        if use_ai_analysis:
                            if "ai_index_report" not in st.session_state:
                                st.session_state.ai_index_report = {}
                            st.session_state['run_ai_index'] = True
                            st.session_state['market_user_opinion'] = user_opinion
                            st.session_state['selected_index'] = selected_index
                        else:
                            st.session_state.ai_index_report = {}
                        
                        # 保存当前选择的指数
                        st.session_state['current_analysis_index'] = selected_index
                                            
                    # 从session_state获取当前分析的指数，如果没有则使用当前选择的指数
                    current_index = st.session_state.get('current_analysis_index', selected_index)
                    
                    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success(f"📊 **指数分析报告** (基于{current_index})")
                    st.caption(f"报告时间: {report_time}")
                    
                    # 根据新闻功能是否启用来创建标签页
                    from config_manager import config
                    news_enabled = config.is_market_news_enabled()
                    
                    if news_enabled:
                        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 大盘指数", "📊 技术指标", "💰 市场基本面", "📰 市场资讯", "📋 综合摘要"])
                    else:
                        tab1, tab2, tab3, tab5 = st.tabs(["📈 大盘指数", "📊 技术指标", "💰 市场基本面", "📋 综合摘要"])

                    with tab1:
                        display_market_indices()
                    
                    with tab2:
                        display_market_technical_analysis(current_index)

                    with tab3:
                        display_market_fundamentals(current_index)

                    if news_enabled:
                        with tab4:
                            display_market_news()

                    with tab5:
                        display_market_summary(current_index)
                        
                    with st.expander("📊 详细信息", expanded=False):
                        st.write(f"**分析时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**分析对象:** {current_index}")
                        st.write(f"**数据源:** 实时市场数据")
                        
                except Exception as e:
                    st.error(f"分析失败: {str(e)}")
                    st.write("请稍后重试或检查网络连接。")
                    
                    with st.expander("🔍 错误详情", expanded=False):
                        st.code(str(e), language="text")
    else:
        with result_container:
            st.info("点击'开始分析'按钮获取大盘整体分析报告")
            
            with st.expander("ℹ️ 功能说明", expanded=True):
                st.markdown("""
                **大盘整体分析功能包括：**
                
                - 📈 **大盘指数**: 显示主要指数的实时价格和涨跌幅，包括上证指数、深证成指、创业板指等
                - 📊 **技术指标分析**: 基于选择指数的技术指标，反映市场走势
                - 💰 **市场基本面**: 包含估值水平和资金流向分析，反映市场的基本面情况
                - 📋 **综合摘要**: AI生成的指数分析综合报告
                
                **指数选择：** 支持分析多个主要指数，包括上证指数、深证成指、沪深300、中证500、创业板指等。
                
                **AI分析功能：** 选中AI分析选项后，系统会对选择的指数数据进行深度分析，提供更详细的投资建议。
                """)
