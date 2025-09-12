"""
大盘整体分析页面 - 市场全局分析和上证指数分析
"""

import streamlit as st
import datetime
import sys
import os
import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_large_number
from ui.components.page_common import display_technical_indicators
from providers.market_data_tools import get_market_tools
from providers.market_data_fetcher import fetch_index_technical_indicators
from providers.market_report import generate_market_report
from providers.report_utils import PDF_SUPPORT_AVAILABLE
from ui.config import FOCUS_INDICES

def display_market_fundamentals():
    """显示市场基本面分析"""
    st.subheader("市场基本面分析")
    
    use_cache = st.session_state.get('market_use_cache', True)
    
    st.markdown("#### 💰 估值水平")
    
    valuation_data = get_market_tools().get_valuation_data(use_cache=use_cache)
    
    if not valuation_data:
        st.warning("未获取到估值数据")
    else:
        val_col1, val_col2, val_col3 = st.columns(3)
        with val_col1:
            hs300_pe = valuation_data.get('hs300_pe')
            st.metric("沪深300 PE", f"{hs300_pe:.2f}" if hs300_pe else "N/A")
        with val_col2:
            hs300_pb = valuation_data.get('hs300_pb')
            st.metric("沪深300 PB", f"{hs300_pb:.2f}" if hs300_pb else "N/A")
        with val_col3:
            dividend_yield = valuation_data.get('hs300_dividend_yield')
            st.metric("股息率", f"{dividend_yield:.2f}%" if dividend_yield else "N/A")
            
        with st.expander("📈 估值分析", expanded=True):
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
    
    val_time = valuation_data.get('update_time') or valuation_data.get('date')
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
            st.metric("M2增速", f"{m2_growth:.2f}%" if m2_growth else "N/A")
        
        m1_col1, m1_col2 = st.columns(2)
        with m1_col1:
            m1_amount = money_data.get('m1_amount')
            st.metric("M1余额", f"{m1_amount/10000:.2f}万亿" if m1_amount else "N/A")
        with m1_col2:
            m1_growth = money_data.get('m1_growth')
            st.metric("M1增速", f"{m1_growth:.2f}%" if m1_growth else "N/A")
        
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
        

def display_market_summary():
    """显示综合摘要卡片"""

    use_cache = st.session_state.get('market_use_cache', True)
    
    market_tools = get_market_tools()    
    result_data = market_tools.get_comprehensive_market_report(use_cache=use_cache)
    summary_text = market_tools.generate_market_report(result_data, format_type='summary')

    if not summary_text:
        st.info("综合摘要数据准备中...")
        return
    
    if st.session_state.get('run_ai_index', False):        
        # 检查是否已经生成过AI报告
        stock_code_for_ai = '上证指数'
        if stock_code_for_ai not in st.session_state.get('ai_index_report', {}):
            with st.spinner("🤖 AI正在分析指数数据..."):
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
        
    current_stock_code = result_data.get('focus_index', '')
    if st.session_state.get('ai_index_report') and current_stock_code in st.session_state['ai_index_report']:
        ai_data = st.session_state['ai_index_report'][current_stock_code]
        
        st.markdown("---")
        st.subheader("🤖 AI深度分析")
        
        with st.expander("📊 AI指数分析报告", expanded=True):
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
    
    score = 0
    total_indicators = 0
    
    if tech_data.get('ma_trend') == '多头排列':
        score += 1
    total_indicators += 1
    
    if tech_data.get('macd_trend') == '金叉向上':
        score += 1
    total_indicators += 1
    
    margin_balance = margin_data.get('margin_balance', 0)
    if margin_balance and margin_balance > 15000:
        score += 1
    elif margin_balance and margin_balance > 12000:
        score += 0.5
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
    else:
        st.write("市场综合评级: 数据不足")

    # 导出市场报告功能
    st.markdown("---")
    st.subheader("📋 导出市场报告")
    
    st.info("💡 可以导出当前市场分析的完整报告")
    
    support_pdf = PDF_SUPPORT_AVAILABLE
    index_name = result_data.get('focus_index', '上证指数')

    col1, col2 = st.columns([1, 2])
    with col1:
        if support_pdf:
            format_type = st.selectbox(
                "选择导出格式",
                ["pdf", "docx", "markdown"],
                format_func=lambda x: {"pdf": "📄 PDF格式", "docx": "📝 Word文档", "markdown": "📝 Markdown"}[x],
                key=f"market_format_select_{index_name}"
            )
        else:
            format_type = st.selectbox(
                "选择导出格式",
                ["docx", "markdown", "html"],
                format_func=lambda x: {"docx": "📝 Word文档", "markdown": "📝 Markdown", "html": "🌐 HTML"}[x],
                key=f"market_format_select_{index_name}"
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
    
    market_report_button_key = f"generate_market_report_{index_name}"
    if st.button("🔄 生成市场报告", key=market_report_button_key, use_container_width=True):
        st.session_state[f"generating_market_report_{index_name}"] = format_type
    
    generating_format = st.session_state.get(f"generating_market_report_{index_name}", None)
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
                has_ai_analysis = bool(st.session_state.get('ai_index_report', {}).get(index_name))
                user_opinion = st.session_state.get('market_user_opinion', '')
                
                report_content = generate_market_report(
                    index_name=index_name,
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
                filename = f"市场分析报告_{index_name}_{timestamp}.{ext}"
                
                st.session_state[f"market_report_content_{index_name}"] = report_content
                st.session_state[f"market_report_filename_{index_name}"] = filename
                st.session_state[f"market_report_mime_{index_name}"] = mime
                st.session_state[f"market_report_format_{index_name}"] = generating_format
                st.session_state[f"market_report_timestamp_{index_name}"] = timestamp
                
                st.session_state[f"generating_market_report_{index_name}"] = None

                format_names = {"pdf": "PDF", "docx": "Word", "markdown": "Markdown", "html": "HTML"}
                st.success(f"✅ {format_names[generating_format]}市场报告生成成功！")
                
            except Exception as e:
                st.error(f"❌ 生成{generating_format.upper()}市场报告失败: {str(e)}")
                st.session_state[f"generating_market_report_{index_name}"] = None
    
    if st.session_state.get(f"market_report_content_{index_name}"):
        format_icons = {"pdf": "📄", "docx": "📝", "markdown": "📝", "html": "🌐"}
        current_format = st.session_state.get(f"market_report_format_{index_name}", "pdf")
        
        st.download_button(
            label=f"{format_icons[current_format]} 下载{current_format.upper()}文件",
            data=st.session_state[f"market_report_content_{index_name}"],
            file_name=st.session_state[f"market_report_filename_{index_name}"],
            mime=st.session_state[f"market_report_mime_{index_name}"],
            key=f"download_market_report_{index_name}",
            use_container_width=True,
            help=f"点击下载生成的{current_format.upper()}市场报告文件"
        )
        st.caption(f"✅ 已生成 {current_format.upper()} | {st.session_state[f'market_report_timestamp_{index_name}']}")

            
def display_market_overview():
    """显示大盘整体分析"""
    
    st.header("📊 大盘整体分析")
    st.caption("基于上证指数的全市场分析")
    
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
        st.session_state['market_use_cache'] = use_cache
    
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
                        else:
                            st.session_state.ai_index_report = {}
                                            
                    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success(f"📊 **大盘整体分析报告** (基于上证指数)")
                    st.caption(f"报告时间: {report_time}")
                    
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 大盘指数", "📊 技术指标", "💰 市场基本面", "📋 综合摘要"])
                    
                    with tab1:
                        display_market_indices()
                    
                    with tab2:
                        tech_data = fetch_index_technical_indicators('上证指数')
                        display_technical_indicators(tech_data)

                    with tab3:
                        display_market_fundamentals()

                    with tab4:
                        display_market_summary()
                        
                    with st.expander("📊 详细信息", expanded=False):
                        st.write(f"**分析时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**分析对象:** 上证指数 (大盘整体)")
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
                - 📊 **技术指标分析**: 基于上证指数的技术指标，反映大盘走势
                - � **市场基本面**: 包含估值水平和资金流向分析，反映市场的基本面情况
                - 📋 **综合摘要**: AI生成的大盘分析综合报告
                
                **AI分析功能：** 选中AI分析选项后，系统会对大盘数据进行深度分析，提供更详细的投资建议。
                """)
