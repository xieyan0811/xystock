"""
大盘整体分析页面 - 市场全局分析和指数分析
"""

import streamlit as st
import datetime
import sys
import os
import pandas as pd
import plotly.graph_objects as go

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_large_number
from market.market_data_tools import get_market_tools
from market.market_report import generate_market_report
from utils.report_utils import PDF_SUPPORT_AVAILABLE
from ui.config import FOCUS_INDICES




def display_market_fundamentals(index_name='沪深300'):
    """显示市场基本面分析"""
    st.subheader("市场基本面分析")
    
    use_cache = st.session_state.get('market_use_cache', True)
    
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
    
    st.markdown("#### 😐 市场情绪指标")
    
    # 获取综合市场情绪数据
    sentiment_data = get_market_tools().get_market_sentiment(use_cache=use_cache, comprehensive=True)
    
    if not sentiment_data or 'error' in sentiment_data:
        st.warning("未获取到市场情绪数据")
    else:
        # 显示情绪评分
        if 'sentiment_score' in sentiment_data:
            score = sentiment_data.get('sentiment_score', 0)
            level = sentiment_data.get('sentiment_level', 'unknown')
            confidence = sentiment_data.get('confidence', 0)
            
            score_col1, score_col2, score_col3 = st.columns(3)
            with score_col1:
                # 根据情绪等级设置颜色
                if level == 'bullish':
                    delta_color = "normal"
                    level_display = "🟢 乐观"
                elif level == 'bearish':
                    delta_color = "inverse"
                    level_display = "🔴 悲观"
                else:
                    delta_color = "off"
                    level_display = "🟡 中性"
                
                st.metric("情绪评分", f"{score:.1f}", help="综合市场情绪评分，范围-100到100")
            
            with score_col2:
                st.metric("情绪等级", level_display, help="基于评分计算的情绪等级")
            
            with score_col3:
                st.metric("数据可信度", f"{confidence}%", help="基于数据源数量计算的可信度")
        
        # 显示基础涨跌数据
        basic_sentiment = sentiment_data.get('basic_sentiment', sentiment_data)
        if basic_sentiment:
            up_stocks = basic_sentiment.get('up_stocks', 0)
            down_stocks = basic_sentiment.get('down_stocks', 0)
            flat_stocks = basic_sentiment.get('flat_stocks', 0)
            total_stocks = basic_sentiment.get('total_stocks', 0)
            
            sentiment_col1, sentiment_col2, sentiment_col3, sentiment_col4 = st.columns(4)
            with sentiment_col1:
                up_ratio = basic_sentiment.get('up_ratio', 0)
                st.metric("上涨股票", f"{up_stocks}只", delta=f"{up_ratio:.1%}", delta_color="normal")
            
            with sentiment_col2:
                down_ratio = basic_sentiment.get('down_ratio', 0)
                st.metric("下跌股票", f"{down_stocks}只", delta=f"{down_ratio:.1%}", delta_color="inverse")
            
            with sentiment_col3:
                limit_up = basic_sentiment.get('limit_up_stocks', 0)
                limit_up_ratio = basic_sentiment.get('limit_up_ratio', 0)
                st.metric("涨停股票", f"{limit_up}只", delta=f"{limit_up_ratio:.2%}", delta_color="normal")
            
            with sentiment_col4:
                limit_down = basic_sentiment.get('limit_down_stocks', 0)
                st.metric("跌停股票", f"{limit_down}只", delta_color="inverse")
        
        # 显示资金流向情绪
        fund_flow = sentiment_data.get('fund_flow', {})
        if fund_flow:
            st.markdown("##### 💸 资金流向情绪")
            fund_col1, fund_col2 = st.columns(2)
            
            with fund_col1:
                main_inflow = fund_flow.get('main_net_inflow', 0)
                inflow_text = f"{main_inflow/1e8:.1f}亿" if main_inflow else "N/A"
                inflow_delta_color = "normal" if main_inflow > 0 else "inverse" if main_inflow < 0 else "off"
                st.metric("主力净流入", inflow_text, delta_color=inflow_delta_color)
            
            with fund_col2:
                main_ratio = fund_flow.get('main_net_ratio', 0)
                ratio_text = f"{main_ratio:.2f}%" if main_ratio else "N/A"
                ratio_delta_color = "normal" if main_ratio > 0 else "inverse" if main_ratio < 0 else "off"
                st.metric("主力净流入占比", ratio_text, delta_color=ratio_delta_color)
        
        # 情绪分析解读
        with st.expander("📊 情绪分析解读", expanded=True):
            if 'sentiment_score' in sentiment_data and 'score_components' in sentiment_data:
                components = sentiment_data['score_components']
                
                st.write("**评分构成分析：**")
                for component, value in components.items():
                    if component == 'ratio':
                        desc = f"涨跌比例贡献: {value:.1f}分"
                        if value > 10:
                            desc += " (上涨股票占优)"
                        elif value < -10:
                            desc += " (下跌股票占优)"
                        else:
                            desc += " (涨跌相对均衡)"
                    elif component == 'limit':
                        desc = f"涨跌停贡献: {value:.1f}分"
                        if value > 5:
                            desc += " (涨停股票较多)"
                        elif value < -5:
                            desc += " (跌停股票较多)"
                        else:
                            desc += " (涨跌停均衡)"
                    elif component == 'fund':
                        desc = f"资金流向贡献: {value:.1f}分"
                        if value > 10:
                            desc += " (主力大幅净流入)"
                        elif value < -10:
                            desc += " (主力大幅净流出)"
                        else:
                            desc += " (资金流向相对平衡)"
                    else:
                        desc = f"{component}: {value:.1f}分"
                    
                    st.write(f"- {desc}")
                
                # 总体情绪判断
                total_score = sentiment_data.get('sentiment_score', 0)
                if total_score > 30:
                    st.success("🚀 **市场情绪极度乐观** - 多数指标显示积极信号，适合关注强势股票")
                elif total_score > 10:
                    st.info("📈 **市场情绪偏乐观** - 整体向好，但需注意风险控制")
                elif total_score > -10:
                    st.warning("😐 **市场情绪中性** - 多空力量相对均衡，等待明确方向")
                elif total_score > -30:
                    st.warning("📉 **市场情绪偏悲观** - 下跌压力较大，注意防守")
                else:
                    st.error("💥 **市场情绪极度悲观** - 恐慌情绪浓厚，谨慎操作")
        
        # 数据源信息
        data_source = basic_sentiment.get('data_source', '未知')
        update_time = sentiment_data.get('update_time', basic_sentiment.get('update_time', ''))
        if update_time:
            st.caption(f"市场情绪数据获取时间: {update_time} | 数据源: {data_source}")

    st.markdown("#### 💳 融资融券数据")
    
    margin_data = get_market_tools().get_margin_data(use_cache=use_cache)
    
    if not margin_data:
        st.warning("未获取到融资融券数据")
    else:
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
        
    margin_time = margin_data.get('update_time') or margin_data.get('margin_date')
    if margin_time:
        st.caption(f"融资融券数据获取时间: {margin_time}")

    st.markdown("#### 📰 市场资讯")
    
    market_tools = get_market_tools()
    news_data = market_tools.get_market_news_data(use_cache=use_cache)
    
    if 'error' in news_data:
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
        

def display_market_summary(index_name='上证指数'):
    """显示综合摘要卡片"""

    use_cache = st.session_state.get('market_use_cache', True)
    
    market_tools = get_market_tools()    
    result_data = market_tools.get_comprehensive_market_report(use_cache=use_cache, index_name=index_name)
    summary_text = market_tools.generate_market_report(result_data, format_type='summary')

    if not summary_text:
        st.info("综合摘要数据准备中...")
        return
    
    if st.session_state.get('run_ai_index', False):
        # 检查是否已经生成过AI报告
        stock_code_for_ai = index_name
        with st.spinner(f"🤖 AI正在分析{stock_code_for_ai}数据..."):
            try:
                user_opinion = st.session_state.get('market_user_opinion', '')
                
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
        
    current_stock_code = result_data.get('focus_index', index_name)
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

        st.markdown("---")
        st.subheader("综合摘要")
        st.markdown(summary_text)
    else:
        detail_text = market_tools.generate_market_report(result_data, format_type='detail')
        st.markdown("---")
        st.subheader("综合摘要")
        st.markdown(detail_text)

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

    # 导出市场报告功能
    st.markdown("---")
    st.subheader("📋 导出市场报告")
    
    st.info("💡 可以导出当前市场分析的完整报告")
    
    support_pdf = PDF_SUPPORT_AVAILABLE
    report_index_name = result_data.get('focus_index', index_name)

    col1, col2 = st.columns([1, 2])
    with col1:
        if support_pdf:
            format_type = st.selectbox(
                "选择导出格式",
                ["pdf", "docx", "markdown"],
                format_func=lambda x: {"pdf": "📄 PDF格式", "docx": "📝 Word文档", "markdown": "📝 Markdown"}[x],
                key=f"market_format_select_{report_index_name}"
            )
        else:
            format_type = st.selectbox(
                "选择导出格式",
                ["docx", "markdown", "html"],
                format_func=lambda x: {"docx": "📝 Word文档", "markdown": "📝 Markdown", "html": "🌐 HTML"}[x],
                key=f"market_format_select_{report_index_name}"
            )

    with col2:
        if support_pdf:
            format_descriptions = {
                "pdf": "专业格式，适合打印和正式分享",
                "docx": "Word文档，可编辑修改",
                "markdown": "Markdown格式，适合程序员和技术人员"
            }
        else:
            format_descriptions = {
                "docx": "Word文档，可编辑修改",
                "markdown": "Markdown格式，适合程序员和技术人员",
                "html": "HTML格式，适合网页浏览"
            }
        st.caption(format_descriptions[format_type])
    
    market_report_button_key = f"generate_market_report_{report_index_name}"
    if st.button("🔄 生成市场报告", key=market_report_button_key, use_container_width=True):
        st.session_state[f"generating_market_report_{report_index_name}"] = format_type
    
    generating_format = st.session_state.get(f"generating_market_report_{report_index_name}", None)
    if generating_format:
        spinner_text = {
            "pdf": "正在收集数据并生成PDF报告...",
            "docx": "正在收集数据并生成Word文档...",
            "markdown": "正在收集数据并生成Markdown文件...",
            "html": "正在收集数据并生成HTML文件..."
        }
        
        with st.spinner(spinner_text[generating_format]):
            try:
                # 检查是否有AI分析报告
                has_ai_analysis = bool(st.session_state.get('ai_index_report', {}).get(report_index_name))
                user_opinion = st.session_state.get('market_user_opinion', '')
                
                report_content = generate_market_report(
                    index_name=report_index_name,
                    format_type=generating_format,
                    has_ai_analysis=has_ai_analysis,
                    user_opinion=user_opinion
                )
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                
                format_info = {
                    "pdf": {"ext": "pdf", "mime": "application/pdf"},
                    "docx": {"ext": "docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
                    "markdown": {"ext": "md", "mime": "text/markdown"},
                    "html": {"ext": "html", "mime": "text/html"}
                }
                
                ext = format_info[generating_format]["ext"]
                mime = format_info[generating_format]["mime"]
                filename = f"市场分析报告_{report_index_name}_{timestamp}.{ext}"
                
                st.session_state[f"market_report_content_{report_index_name}"] = report_content
                st.session_state[f"market_report_filename_{report_index_name}"] = filename
                st.session_state[f"market_report_mime_{report_index_name}"] = mime
                st.session_state[f"market_report_format_{report_index_name}"] = generating_format
                st.session_state[f"market_report_timestamp_{report_index_name}"] = timestamp
                
                st.session_state[f"generating_market_report_{report_index_name}"] = None

                format_names = {"pdf": "PDF", "docx": "Word", "markdown": "Markdown", "html": "HTML"}
                st.success(f"✅ {format_names[generating_format]}市场报告生成成功！")
                
            except Exception as e:
                st.error(f"❌ 生成{generating_format.upper()}市场报告失败: {str(e)}")
                st.session_state[f"generating_market_report_{report_index_name}"] = None
    
    if st.session_state.get(f"market_report_content_{report_index_name}"):
        format_icons = {"pdf": "📄", "docx": "📝", "markdown": "📝", "html": "🌐"}
        current_format = st.session_state.get(f"market_report_format_{report_index_name}", "pdf")
        
        st.download_button(
            label=f"{format_icons[current_format]} 下载{current_format.upper()}文件",
            data=st.session_state[f"market_report_content_{report_index_name}"],
            file_name=st.session_state[f"market_report_filename_{report_index_name}"],
            mime=st.session_state[f"market_report_mime_{report_index_name}"],
            key=f"download_market_report_{report_index_name}",
            use_container_width=True,
            help=f"点击下载生成的{current_format.upper()}市场报告文件"
        )
        st.caption(f"✅ 已生成 {current_format.upper()} | {st.session_state[f'market_report_timestamp_{report_index_name}']}")

            
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
                    
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 大盘指数", "📊 技术指标", "💰 市场基本面", "📋 综合摘要"])
                    
                    with tab1:
                        display_market_indices()
                    
                    with tab2:
                        # 显示K线图
                        st.subheader(f"{current_index} K线走势")
                        try:
                            use_cache = st.session_state.get('market_use_cache', True)
                            force_refresh = not use_cache
                            market_tools = get_market_tools()
                            
                            # 获取K线数据
                            kline_info = market_tools.get_index_kline_data(
                                current_index, 
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
                                display_kline_charts(df, chart_type="index", title_prefix=current_index)
                                
                                # 显示数据来源信息
                                data_source = kline_info.get('data_source', '未知')
                                update_time = kline_info.get('update_time', '')
                                if update_time:
                                    st.caption(f"数据来源: {data_source} | 更新时间: {update_time}")
                            else:
                                st.warning(f"未获取到 {current_index} 的K线数据")
                        
                        except Exception as e:
                            st.error(f"加载K线数据失败: {str(e)}")
                        
                        # 显示技术指标分析
                        st.markdown("---")
                        st.subheader("技术指标分析")
                        # 使用统一的技术指标显示函数
                        from ui.components.page_common import display_technical_analysis_tab, display_risk_analysis
                        display_technical_analysis_tab(index_name=current_index)
                        
                        # 显示大盘风险分析
                        st.markdown("---")
                        st.subheader(f"风险分析")
                        try:
                            use_cache = st.session_state.get('market_use_cache', True)
                            market_tools = get_market_tools()
                            
                            # 获取指定指数的技术指标数据（包含风险数据）
                            tech_data = market_tools.get_index_technical_indicators(current_index)
                            
                            if tech_data and not ('error' in tech_data):
                                # 直接使用返回数据中的风险指标
                                risk_metrics = tech_data.get('risk_metrics', None)
                                display_risk_analysis(risk_metrics)
                            else:
                                st.warning(f"暂无风险分析数据")
                                
                        except Exception as e:
                            st.error(f"获取风险分析失败: {str(e)}")

                    with tab3:
                        display_market_fundamentals(current_index)

                    with tab4:
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
