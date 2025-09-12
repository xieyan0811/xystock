"""
股票分析页面 - 股票查询和分析结果显示
"""

import sys
import os
import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from ui.components.page_common import display_technical_indicators
from utils.format_utils import format_volume, format_market_value, format_price, format_percentage, format_change, format_number, format_large_number
from providers.stock_data_tools import get_stock_tools
from providers.stock_report import generate_stock_report
from providers.report_utils import PDF_SUPPORT_AVAILABLE

stock_tools = get_stock_tools()

def get_ai_analysis_status_and_reports(stock_code):
    """检查界面是否已有AI分析报告"""
    has_fundamental_ai = (hasattr(st, 'session_state') and 
                         hasattr(st.session_state, 'ai_fundamental_report') and 
                         stock_code in st.session_state.ai_fundamental_report)
    has_market_ai = (hasattr(st, 'session_state') and 
                   hasattr(st.session_state, 'ai_market_report') and 
                   stock_code in st.session_state.ai_market_report)
    has_news_ai = (hasattr(st, 'session_state') and 
                 hasattr(st.session_state, 'ai_news_report') and 
                 stock_code in st.session_state.ai_news_report)
    has_chip_ai = (hasattr(st, 'session_state') and 
                 hasattr(st.session_state, 'ai_chip_report') and 
                 stock_code in st.session_state.ai_chip_report)
    has_comprehensive_ai = (hasattr(st, 'session_state') and 
                           hasattr(st.session_state, 'ai_comprehensive_report') and 
                           stock_code in st.session_state.ai_comprehensive_report)
    
    return has_fundamental_ai, has_market_ai, has_news_ai, has_chip_ai, has_comprehensive_ai


def display_stock_info(stock_identity):
    """显示证券信息"""
    stock_code = stock_identity['code']
    if not stock_code:
        st.warning("请输入证券代码或名称")
        return

    with st.spinner(f"正在加载{stock_identity['market_name']} {stock_code} ({stock_identity['name']})的数据..."):
        try:
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 基本信息", "📈 行情走势", "📰 新闻资讯", "🧮 筹码分析", "🎯 综合分析"])
            
            with tab1:
                display_basic_info(stock_identity)
                
            with tab2:
                display_market_trend(stock_identity)
                                
            with tab3:
                display_news(stock_identity)

            with tab4:
                display_chips_analysis(stock_identity)

            with tab5:
                display_comprehensive_analysis(stock_identity)

            st.divider()
            st.subheader("📋 导出完整报告")
            
            st.info("💡 可以导出包含所有Tab内容的完整分析报告")
            
            support_pdf = PDF_SUPPORT_AVAILABLE

            col1, col2 = st.columns([1, 2])
            with col1:
                if support_pdf:
                    format_type = st.selectbox(
                        "选择导出格式",
                        ["pdf", "docx", "markdown"],
                        format_func=lambda x: {"pdf": "📄 PDF格式", "docx": "📝 Word文档", "markdown": "📝 Markdown"}[x],
                        key=f"format_select_{stock_code}"
                    )
                else:
                    format_type = st.selectbox(
                        "选择导出格式",
                        ["docx", "markdown"],
                        format_func=lambda x: {"docx": "📝 Word文档", "markdown": "📝 Markdown"}[x],
                        key=f"format_select_{stock_code}"
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
                        "markdown": "Markdown格式，适合程序员和技术人员"
                    }
                st.caption(format_descriptions[format_type])
            
            report_button_key = f"generate_report_{stock_code}"
            if st.button("🔄 生成报告", key=report_button_key, use_container_width=True):
                st.session_state[f"generating_report_{stock_code}"] = format_type
            
            generating_format = st.session_state.get(f"generating_report_{stock_code}", None)
            if generating_format:
                print(f"开始生成{generating_format.upper()}报告...")
                spinner_text = {
                    "pdf": "正在收集数据并生成PDF报告...",
                    "docx": "正在收集数据并生成Word文档...",
                    "markdown": "正在收集数据并生成Markdown文件..."
                }
                
                with st.spinner(spinner_text[generating_format]):
                    try:
                        has_fundamental_ai, has_market_ai, has_news_ai, has_chip_ai, has_comprehensive_ai = get_ai_analysis_status_and_reports(stock_code)
                        
                        report_content = generate_stock_report(
                            stock_identity, generating_format,
                            has_fundamental_ai=has_fundamental_ai,
                            has_market_ai=has_market_ai,
                            has_news_ai=has_news_ai,
                            has_chip_ai=has_chip_ai,
                            has_comprehensive_ai=has_comprehensive_ai
                        )
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        format_info = {
                            "pdf": {"ext": "pdf", "mime": "application/pdf"},
                            "docx": {"ext": "docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
                            "markdown": {"ext": "md", "mime": "text/markdown"}
                        }
                        
                        ext = format_info[generating_format]["ext"]
                        mime = format_info[generating_format]["mime"]
                        filename = f"{stock_code}_完整分析报告_{timestamp}.{ext}"
                        
                        st.session_state[f"report_content_{stock_code}"] = report_content
                        st.session_state[f"report_filename_{stock_code}"] = filename
                        st.session_state[f"report_mime_{stock_code}"] = mime
                        st.session_state[f"report_format_{stock_code}"] = generating_format
                        st.session_state[f"report_timestamp_{stock_code}"] = timestamp
                        
                        st.session_state[f"generating_report_{stock_code}"] = None
                        
                        format_names = {"pdf": "PDF", "docx": "Word", "markdown": "Markdown"}
                        st.success(f"✅ {format_names[generating_format]}报告生成成功！")
                        
                    except Exception as e:
                        st.error(f"❌ 生成{generating_format.upper()}报告失败: {str(e)}")
                        st.session_state[f"generating_report_{stock_code}"] = None
            
            if st.session_state.get(f"report_content_{stock_code}"):
                format_icons = {"pdf": "📄", "docx": "📝", "markdown": "📝"}
                current_format = st.session_state.get(f"report_format_{stock_code}", "pdf")
                
                st.download_button(
                    label=f"{format_icons[current_format]} 下载{current_format.upper()}文件",
                    data=st.session_state[f"report_content_{stock_code}"],
                    file_name=st.session_state[f"report_filename_{stock_code}"],
                    mime=st.session_state[f"report_mime_{stock_code}"],
                    key=f"download_report_{stock_code}",
                    use_container_width=True,
                    help=f"点击下载生成的{current_format.upper()}报告文件"
                )
                st.caption(f"✅ 已生成 {current_format.upper()} | {st.session_state[f'report_timestamp_{stock_code}']}")
                
        except Exception as e:
            st.error(f"加载数据失败: {str(e)}")
            st.write("请检查股票代码是否正确，或稍后重试。")
            
            with st.expander("🔍 错误详情", expanded=False):
                st.code(str(e), language="text")


def display_basic_info(stock_identity):
    """显示股票基本信息"""
    st.subheader("基本信息")

    stock_code = stock_identity['code']
    try:
        use_cache = st.session_state.get('use_cache', True)
        force_refresh = not use_cache
        
        basic_info_data = stock_tools.get_basic_info(stock_identity, use_cache=use_cache, force_refresh=force_refresh)
        
        if 'error' in basic_info_data:
            st.error(f"获取股票基本信息失败: {basic_info_data['error']}")
            return
        
        if basic_info_data:
            col1, col2 = st.columns(2)
            
            with col1:
                if basic_info_data.get('name'):
                    st.write(f"**股票名称:** {basic_info_data['name']}")

                if basic_info_data.get('industry'):
                    st.info(f"所属行业: {basic_info_data['industry']}")
                
                if basic_info_data.get('total_market_value'):
                    st.write(f"总市值: {format_market_value(basic_info_data['total_market_value'])}")
                    
                if basic_info_data.get('circulating_market_value'):
                    st.write(f"流通市值: {format_market_value(basic_info_data['circulating_market_value'])}")

                st.metric(
                    label="当前价格", 
                    value=f"{format_price(basic_info_data.get('current_price', 0))}",
                    delta=format_change(basic_info_data.get('change', 0), 
                                        basic_info_data.get('change_percent', 0)),
                    delta_color="inverse"
                )
                
                st.metric("成交量", format_volume(basic_info_data.get('volume', 0)))

            with col2:
                st.write(f"**开盘价:** {format_price(basic_info_data.get('open', 0))}")
                st.write(f"**最高价:** {format_price(basic_info_data.get('high', 0))}")
                st.write(f"**最低价:** {format_price(basic_info_data.get('low', 0))}")
                prev_close = basic_info_data.get('prev_close', 0)
                if prev_close > 0:
                    st.write(f"**昨收价:** {format_price(prev_close)}")

                if basic_info_data.get('pe_ratio'):
                    st.write(f"**市盈率(动):** {basic_info_data['pe_ratio']}")
                
                if basic_info_data.get('pb_ratio'):
                    st.write(f"**市净率:** {basic_info_data['pb_ratio']}")
                
                if basic_info_data.get('roe'):
                    st.write(f"**ROE:** {basic_info_data['roe']}")
            
            with st.expander("更多财务指标", expanded=True):
                if basic_info_data.get('gross_profit_margin'):
                    st.write(f"**毛利率:** {format_number(basic_info_data['gross_profit_margin'])}")
                
                if basic_info_data.get('net_profit_margin'):
                    st.write(f"**净利润率:** {format_number(basic_info_data['net_profit_margin'])}")
                
                if basic_info_data.get('net_profit'):
                    st.write(f"**净利润:** {format_large_number(basic_info_data['net_profit'])}")

                if basic_info_data.get('debt_to_asset_ratio'):
                    st.write(f"**资产负债率:** {format_number(basic_info_data['debt_to_asset_ratio'])}")

            st.caption(f"数据更新时间: {basic_info_data.get('timestamp', basic_info_data.get('update_time', ''))}")
        else:
            st.warning(f"未能获取到股票 {stock_code} 的实时数据")
        
        st.divider()
        st.subheader("基本面分析")
        
        try:
            use_cache = st.session_state.get('use_cache', True)
            force_refresh = not use_cache
            
            include_ai_analysis = (st.session_state.get('include_ai_analysis', False) and 
                                 stock_code not in st.session_state.get('ai_fundamental_report', {}))
            
            if include_ai_analysis:
                with st.spinner("🤖 AI正在进行基本面分析，请稍候..."):
                    fundamental_data = stock_tools.get_basic_info(stock_identity, use_cache=use_cache, force_refresh=force_refresh, include_ai_analysis=True)
            else:
                fundamental_data = stock_tools.get_basic_info(stock_identity, use_cache=use_cache, force_refresh=force_refresh)
            
            if "ai_fundamental_report" not in st.session_state:
                st.session_state.ai_fundamental_report = {}
                
            if 'ai_analysis' in fundamental_data:
                if 'error' not in fundamental_data['ai_analysis']:
                    st.session_state.ai_fundamental_report[stock_code] = {
                        "report": fundamental_data['ai_analysis']['report'],
                        "timestamp": fundamental_data['ai_analysis']['timestamp']
                    }
                else:
                    st.error(f"AI基本面分析失败: {fundamental_data['ai_analysis']['error']}")
                    st.info("请稍后再试或联系管理员")
            
            if stock_code in st.session_state.ai_fundamental_report:
                with st.expander("🤖 AI 基本面分析报告", expanded=True):
                    st.markdown(st.session_state.ai_fundamental_report[stock_code]["report"])
                    st.caption(f"分析报告生成时间: {st.session_state.ai_fundamental_report[stock_code]['timestamp']}")
                    
        except Exception as e:
            st.error(f"加载基本面分析数据失败: {str(e)}")
            
    except Exception as e:
        st.error(f"获取基本信息失败: {str(e)}")


def display_market_trend(stock_identity):
    """显示股票行情走势"""
    st.subheader("行情走势")
    stock_code = stock_identity['code']
    try:
        use_cache = st.session_state.get('use_cache', True)
        force_refresh = not use_cache
        
        include_ai_analysis = (st.session_state.get('include_ai_analysis', False) and 
                             stock_code not in st.session_state.get('ai_market_report', {}))
        
        if include_ai_analysis:
            with st.spinner("🤖 AI正在分析股票行情，请稍候..."):
                kline_info = stock_tools.get_stock_kline_data(stock_identity, period=160, use_cache=use_cache, force_refresh=force_refresh, include_ai_analysis=True)
        else:
            kline_info = stock_tools.get_stock_kline_data(stock_identity, period=160, use_cache=use_cache, force_refresh=force_refresh)
        
        if 'error' in kline_info:
            st.error(f"获取K线数据失败: {kline_info['error']}")
            return
        
        if kline_info and kline_info.get('kline_data'):
            df = pd.DataFrame(kline_info['kline_data'])
            
            if "ai_market_report" not in st.session_state:
                st.session_state.ai_market_report = {}
                
            if 'ai_analysis' in kline_info:
                if 'error' not in kline_info['ai_analysis']:
                    st.session_state.ai_market_report[stock_code] = {
                        "report": kline_info['ai_analysis']['report'],
                        "timestamp": kline_info['ai_analysis']['timestamp']
                    }
                else:
                    st.error(f"AI行情分析失败: {kline_info['ai_analysis']['error']}")
                    st.info("请稍后再试或联系管理员")
            
            if stock_code in st.session_state.ai_market_report:
                with st.expander("🤖 AI 行情分析报告", expanded=True):
                    st.markdown(st.session_state.ai_market_report[stock_code]["report"])
                    st.caption(f"分析报告生成时间: {st.session_state.ai_market_report[stock_code]['timestamp']}")
            
            risk_metrics = kline_info.get('risk_metrics', None)
            if risk_metrics is None or 'error' in risk_metrics:
                st.error(f"获取风险指标失败: {risk_metrics['error']}")
            elif risk_metrics and 'summary_table' in risk_metrics:
                with st.expander("风险分析", expanded=True):
                    st.table(risk_metrics['summary_table'])
            elif 'error' not in risk_metrics:
                with st.expander("风险分析摘要", expanded=True):
                    st.json(risk_metrics)

            df['datetime'] = pd.to_datetime(df['datetime'])
                        
            fig_price = go.Figure()
            
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
            
            fig_price.add_trace(go.Scatter(
                x=df['datetime'], 
                y=df['MA5'],
                mode='lines',
                name='MA5',
                line=dict(color="#D2FF07", width=1.5)
            ))
            
            fig_price.add_trace(go.Scatter(
                x=df['datetime'], 
                y=df['MA10'],
                mode='lines',
                name='MA10',
                line=dict(color="#FF22DA", width=1.5)
            ))
            
            fig_price.add_trace(go.Scatter(
                x=df['datetime'], 
                y=df['MA20'],
                mode='lines',
                name='MA20',
                line=dict(color="#0593F1", width=1.5)
            ))
            
            fig_price.update_layout(
                title='K线图与均线',
                xaxis_title='日期',
                yaxis_title='价格',
                height=500,
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(rangeslider=dict(visible=False)),
                yaxis=dict(fixedrange=True)
            )
            
            st.plotly_chart(fig_price, use_container_width=True, config={"scrollZoom": False})
            
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
            
            indicators = kline_info.get('indicators', {})
            if indicators:
                display_technical_indicators(indicators)
            else:
                st.warning("未获取到技术指标数据")

        else:
            st.warning(f"未获取到 {stock_code} 的K线数据")
    
    except Exception as e:
        st.error(f"加载行情数据失败: {str(e)}")


def display_news(stock_identity):
    """显示股票相关新闻"""
    st.subheader("新闻资讯")
    stock_code = stock_identity['code']
    
    try:
        use_cache = st.session_state.get('use_cache', True)
        force_refresh = not use_cache
        
        include_ai_analysis = (st.session_state.get('include_ai_analysis', False) and 
                             stock_code not in st.session_state.get('ai_news_report', {}))
        
        if include_ai_analysis:
            with st.spinner("🤖 AI正在分析相关新闻，请稍候..."):
                news_info = stock_tools.get_stock_news_data(stock_identity=stock_identity, use_cache=use_cache, force_refresh=force_refresh, include_ai_analysis=True)
        else:
            news_info = stock_tools.get_stock_news_data(stock_identity=stock_identity, use_cache=use_cache, force_refresh=force_refresh)

        if 'error' in news_info:
            st.info(f"获取新闻数据失败: {news_info['error']}")
            return
        
        if news_info and news_info.get('news_data'):
            news_data = news_info['news_data']
            
            if "ai_news_report" not in st.session_state:
                st.session_state.ai_news_report = {}
                
            if 'ai_analysis' in news_info:
                if 'error' not in news_info['ai_analysis']:
                    st.session_state.ai_news_report[stock_code] = {
                        "report": news_info['ai_analysis']['report'],
                        "timestamp": news_info['ai_analysis']['timestamp']
                    }
                else:
                    st.error(f"AI新闻分析失败: {news_info['ai_analysis']['error']}")
                    st.info("请稍后再试或联系管理员")
            
            if stock_code in st.session_state.ai_news_report:
                with st.expander("🤖 AI 新闻分析报告", expanded=True):
                    st.markdown(st.session_state.ai_news_report[stock_code]["report"])
                    st.caption(f"分析报告生成时间: {st.session_state.ai_news_report[stock_code]['timestamp']}")
            
            st.info(f"共获取到 {news_info.get('news_count', len(news_data))} 条相关新闻")
            
            if news_data:
                for idx, news in enumerate(news_data):
                    title = news.get('新闻标题', '')
                    time = news.get('发布时间', '')
                    url = news.get('新闻链接', '')
                    
                    with st.expander(f"{title} ({time})", expanded=False):
                        if '新闻内容' in news:
                            st.write(news['新闻内容'])
                        
                        if url:
                            st.caption(f"[阅读原文]({url})")
            else:
                st.write("暂无相关新闻")
        else:
            st.info("未能获取到相关新闻")
            
    except Exception as e:
        st.error(f"加载新闻数据失败: {str(e)}")


def display_chips_analysis(stock_identity):
    """显示筹码分析"""
    st.subheader("筹码分析")
    stock_code = stock_identity['code']

    try:
        use_cache = st.session_state.get('use_cache', True)
        force_refresh = not use_cache
        
        include_ai_analysis = (st.session_state.get('include_ai_analysis', False) and 
                             stock_code not in st.session_state.get('ai_chip_report', {}))
        
        if include_ai_analysis:
            with st.spinner("🤖 AI正在分析筹码分布，请稍候..."):
                chip_data = stock_tools.get_stock_chip_data(stock_identity, use_cache=use_cache, force_refresh=force_refresh, include_ai_analysis=True)
        else:
            chip_data = stock_tools.get_stock_chip_data(stock_identity, use_cache=use_cache, force_refresh=force_refresh)
        
        if "ai_chip_report" not in st.session_state:
            st.session_state.ai_chip_report = {}
            
        if 'ai_analysis' in chip_data:
            if 'error' not in chip_data['ai_analysis']:
                st.session_state.ai_chip_report[stock_code] = {
                    "report": chip_data['ai_analysis']['report'],
                    "timestamp": chip_data['ai_analysis']['timestamp']
                }
            else:
                st.warning(f"AI筹码分析失败: {chip_data['ai_analysis']['error']}")
                st.info("请稍后再试或联系管理员")
                
        if stock_code in st.session_state.ai_chip_report:
            with st.expander("🤖 AI 筹码分析报告", expanded=True):
                st.markdown(st.session_state.ai_chip_report[stock_code]["report"])
                st.caption(f"分析报告生成时间: {st.session_state.ai_chip_report[stock_code]['timestamp']}")
        
        if "error" in chip_data:
            st.warning(chip_data["error"])
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("获利比例", format_percentage(chip_data['profit_ratio'] * 100))
            
            if chip_data['profit_ratio'] > 0.7:
                st.info("获利盘较重，上涨可能遇到抛售压力")
            elif chip_data['profit_ratio'] < 0.3:
                st.success("获利盘较轻，上涨阻力相对较小")
            else:
                st.info("获利盘适中")
                
        with col2:
            st.metric("平均成本", f"{format_price(chip_data['avg_cost'])}元")
            
            if chip_data['concentration_90'] < 0.1:
                st.success("筹码高度集中，可能形成重要支撑/阻力")
            elif chip_data['concentration_90'] > 0.2:
                st.info("筹码较为分散，成本分布较广")
            else:
                st.info("筹码集中度适中")
        
        with st.expander("筹码分布数据", expanded=True):
            data = {
                '成本区间': [f"{format_price(chip_data['cost_90_low'])}-{format_price(chip_data['cost_90_high'])}", 
                         f"{format_price(chip_data['cost_70_low'])}-{format_price(chip_data['cost_70_high'])}"],
                '占比': [90, 70],
                '集中度': [chip_data['concentration_90']*100, chip_data['concentration_70']*100]
            }
            
            df = pd.DataFrame(data)
            
            st.dataframe(df, use_container_width=True)
            
            st.subheader("关键价格区间")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("支撑位", f"{format_price(chip_data['support_level'])}元")
            with col2:
                st.metric("阻力位", f"{format_price(chip_data['resistance_level'])}元")
            with col3:
                st.metric("成本中枢", f"{format_price(chip_data['cost_center'])}元")
        
        try:
            if 'raw_data' in chip_data and chip_data['raw_data']:
                if isinstance(chip_data['raw_data'], list):
                    cyq_data = pd.DataFrame(chip_data['raw_data'])
                else:
                    cyq_data = chip_data['raw_data']
                
                st.subheader("获利比例变化趋势")
                fig_profit = go.Figure()
                cyq_data['日期'] = pd.to_datetime(cyq_data['日期'])
                fig_profit.add_trace(go.Scatter(
                    x=cyq_data['日期'], 
                    y=cyq_data['获利比例'] * 100,
                    mode='lines',
                    name='获利比例',
                    line=dict(color='#4CAF50', width=2)
                ))                
                fig_profit.update_layout(
                    xaxis_title='日期',
                    yaxis_title='获利比例 (%)',
                    height=350,
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(rangeslider=dict(visible=False)),
                    yaxis=dict(fixedrange=True)
                )
                
                st.plotly_chart(fig_profit, use_container_width=True, config={"scrollZoom": False})
                st.subheader("平均成本变化趋势")
                
                fig_cost = go.Figure()
                fig_cost.add_trace(go.Scatter(
                    x=cyq_data['日期'], 
                    y=cyq_data['平均成本'],
                    mode='lines',
                    name='平均成本',
                    line=dict(color='#1E88E5', width=2)
                ))
                
                fig_cost.update_layout(
                    xaxis_title='日期',
                    yaxis_title='平均成本',
                    height=350,
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(rangeslider=dict(visible=False)),
                    yaxis=dict(fixedrange=True)
                )
                
                st.plotly_chart(fig_cost, use_container_width=True, config={"scrollZoom": False})
            else:
                st.info("未获取到筹码历史数据，无法绘制趋势图表")
        except Exception as e:
            st.error(f"绘制筹码图表失败: {str(e)}")
    
    except Exception as e:
        st.error(f"加载筹码分析数据失败: {str(e)}")


def display_comprehensive_analysis(stock_identity):
    """显示综合分析"""
    
    st.subheader("🎯 综合分析")
    stock_code = stock_identity['code']

    try:
        if (st.session_state.get('include_ai_analysis', False) and 
            stock_code not in st.session_state.get('ai_comprehensive_report', {})):
            use_cache = st.session_state.get('use_cache', True)
            force_refresh = not use_cache
            run_comprehensive_analysis(stock_identity, force_refresh=force_refresh)
        
        # 显示已有的综合分析结果
        if "ai_comprehensive_report" in st.session_state and stock_code in st.session_state.ai_comprehensive_report:
            analysis_data = st.session_state.ai_comprehensive_report[stock_code]
            
            # 显示分析信息
            if 'analysis_info' in analysis_data:
                info = analysis_data['analysis_info']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("分析时间", info.get('analysis_time', '未知'))
                with col2:
                    st.metric("数据来源", f"{info.get('data_sources_count', 0)}个数据源")
                with col3:
                    st.metric("用户观点", "已包含" if info.get('user_opinion_included', False) else "未包含")
            
            # 显示综合分析报告
            if 'report' in analysis_data:
                st.markdown(analysis_data['report'])
                st.caption(f"分析报告生成时间: {analysis_data['timestamp']}")                

            # 显示数据来源详情
            if 'data_sources' in analysis_data and analysis_data['data_sources']:
                with st.expander("📊 数据来源详情", expanded=False):
                    for source in analysis_data['data_sources']:
                        st.write(f"- **{source.get('type', '未知类型')}**: {source.get('description', '无描述')}")
        else:
            st.info("💡 请在查询时勾选「综合分析」选项，AI将结合历史分析结果为您提供综合投资建议")
            
    except Exception as e:
        st.error(f"显示综合分析失败: {str(e)}")
        with st.expander("🔍 错误详情", expanded=False):
            st.code(str(e), language="text")

def run_comprehensive_analysis(stock_identity, force_refresh):
    with st.spinner("🤖 AI正在进行综合分析..."):    
        try:
            use_cache = st.session_state.get('use_cache', True)
            user_opinion = st.session_state.get('user_opinion', '')
            user_position = st.session_state.get('user_position', '不确定')

            analysis_data = stock_tools.get_comprehensive_ai_analysis(stock_identity, user_opinion, user_position, use_cache=use_cache, force_refresh=force_refresh)
            
            if 'error' in analysis_data:
                st.error(f"获取综合分析失败: {analysis_data['error']}")
                return False
            
            if "ai_comprehensive_report" not in st.session_state:
                st.session_state.ai_comprehensive_report = {}
            st.session_state.ai_comprehensive_report[stock_identity['code']] = analysis_data
            return True
        except Exception as e:
            st.error(f"AI综合分析失败: {str(e)}")
            import traceback
            traceback.print_exc()                    
            return False

