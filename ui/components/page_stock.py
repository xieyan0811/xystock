"""
股票分析页面 - 股票查询和分析结果显示
"""

import sys
import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_volume, format_market_value, format_price, format_percentage, format_change, format_number, format_large_number
from utils.data_formatters import get_stock_formatter
from stock.stock_data_tools import get_stock_tools
from stock.stock_report import generate_stock_report

stock_tools = get_stock_tools()
formatter = get_stock_formatter()

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
                display_technical_analysis(stock_identity)
                                
            with tab3:
                display_news_analysis(stock_identity)

            with tab4:
                display_chips_analysis(stock_identity)

            with tab5:
                display_comprehensive_analysis(stock_identity)

            # 使用通用的导出功能
            def generate_stock_report_wrapper(format_type):
                """包装股票报告生成函数"""
                has_fundamental_ai, has_market_ai, has_news_ai, has_chip_ai, has_comprehensive_ai = get_ai_analysis_status_and_reports(stock_code)
                
                return generate_stock_report(
                    stock_identity, format_type,
                    has_fundamental_ai=has_fundamental_ai,
                    has_market_ai=has_market_ai,
                    has_news_ai=has_news_ai,
                    has_chip_ai=has_chip_ai,
                    has_comprehensive_ai=has_comprehensive_ai
                )
            
            from ui.components.page_export import display_report_export_section
            display_report_export_section(
                entity_id=stock_code,
                report_type="report",
                title="📋 导出完整报告",
                info_text="💡 可以导出包含所有Tab内容的完整分析报告",
                generate_func=generate_stock_report_wrapper,
                generate_args=None,
                filename_prefix=f"分析报告"
            )
                
        except Exception as e:
            st.error(f"加载数据失败: {str(e)}")
            st.write("请检查股票代码是否正确，或稍后重试。")
            
            with st.expander("🔍 错误详情", expanded=False):
                st.code(str(e), language="text")


def display_more_financial_indicators(basic_info_data, stock_identity):
    """显示更多财务指标"""
    market_name = stock_identity.get('market_name', 'A股')
    
    with st.expander("更多财务指标", expanded=True):
        # 检查是否为A股，如果不是则显示提示信息
        if market_name not in ['A股']:
            st.info(f"💡 更多财务指标功能主要支持A股，{market_name}的详细财务指标数据可能有限")
        
        # 使用格式化器获取所有财务指标（包含股息分红信息）
        formatted_info = formatter.format_basic_info(basic_info_data, stock_identity, include_dividend=True)
        
        # 检查是否有实际的财务指标数据
        has_financial_data = False
        sections = formatted_info.split('\n### ')
        
        for section in sections:
            if section.startswith('📊 盈利能力指标'):
                lines = section.split('\n')[1:]
                if any(line.strip() and line.startswith('- ') for line in lines):
                    has_financial_data = True
                    st.subheader("📊 盈利能力指标")
                    for line in lines:
                        if line.strip() and line.startswith('- '):
                            st.write(f"**{line[2:]}**")
            
            elif section.startswith('💰 偿债能力指标'):
                lines = section.split('\n')[1:]
                if any(line.strip() and line.startswith('- ') for line in lines):
                    has_financial_data = True
                    st.subheader("💰 偿债能力指标")
                    for line in lines:
                        if line.strip() and line.startswith('- '):
                            st.write(f"**{line[2:]}**")
            
            elif section.startswith('🔄 营运能力指标'):
                lines = section.split('\n')[1:]
                if any(line.strip() and line.startswith('- ') for line in lines):
                    has_financial_data = True
                    st.subheader("🔄 营运能力指标")
                    for line in lines:
                        if line.strip() and line.startswith('- '):
                            st.write(f"**{line[2:]}**")
            
            elif section.startswith('📈 成长能力指标'):
                lines = section.split('\n')[1:]
                if any(line.strip() and line.startswith('- ') for line in lines):
                    has_financial_data = True
                    st.subheader("📈 成长能力指标")
                    for line in lines:
                        if line.strip() and line.startswith('- '):
                            st.write(f"**{line[2:]}**")
            
            elif section.startswith('📋 估值指标'):
                lines = section.split('\n')[1:]
                if any(line.strip() and line.startswith('- ') for line in lines):
                    has_financial_data = True
                    st.subheader("📋 估值指标")
                    for line in lines:
                        if line.strip() and line.startswith('- '):
                            st.write(f"**{line[2:]}**")
            
            elif section.startswith('💎 每股指标'):
                lines = section.split('\n')[1:]
                if any(line.strip() and line.startswith('- ') for line in lines):
                    has_financial_data = True
                    st.subheader("💎 每股指标")
                    for line in lines:
                        if line.strip() and line.startswith('- '):
                            st.write(f"**{line[2:]}**")
                        
        # 如果没有财务数据，显示相应提示
        if not has_financial_data:
            if market_name == 'A股':
                st.warning("⚠️ 暂无该股票的详细财务指标数据")
            else:
                st.warning(f"⚠️ {market_name}暂不支持详细财务指标数据获取，建议查看基本价格信息")


def display_etf_holdings_info(stock_identity):
    """显示ETF持仓信息"""
    stock_code = stock_identity['code']
    market_name = stock_identity.get('market_name', 'A股')
    
    # 判断是否为ETF - 通过代码特征或市场类型判断
    is_etf = (market_name == 'ETF' or 
              stock_code.startswith('51') or stock_code.startswith('15') or stock_code.startswith('50') or
              '基金' in stock_identity.get('name', '') or 'ETF' in stock_identity.get('name', ''))
    
    if not is_etf:
        return
        
    with st.expander("📊 ETF持仓信息", expanded=True):
        try:
            # 导入ETF持仓获取器
            from stock.etf_holdings_fetcher import etf_holdings_fetcher
            from utils.data_formatters import get_stock_formatter
            
            # 获取ETF持仓数据
            holdings_data = etf_holdings_fetcher.get_etf_holdings(stock_code, top_n=10)
            
            if 'error' in holdings_data:
                st.warning(f"⚠️ 获取ETF持仓信息失败: {holdings_data['error']}")
                st.info("💡 可能原因：该产品不是ETF基金，或暂无持仓数据")
                return
            
            # 显示ETF基本持仓信息
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("持仓股票总数", f"{holdings_data.get('total_holdings_count', 0)}只")
            
            with col2:
                if 'statistics' in holdings_data and 'concentration_analysis' in holdings_data['statistics']:
                    conc = holdings_data['statistics']['concentration_analysis']
                    st.metric("集中度水平", conc.get('concentration_level', '未知'))
            
            with col3:
                if 'statistics' in holdings_data and 'concentration_analysis' in holdings_data['statistics']:
                    conc = holdings_data['statistics']['concentration_analysis']
                    st.metric("前10大持仓占比", f"{conc.get('top_10_weight', 0)}%")
            
            # 显示主要持仓股票
            st.subheader("🏆 主要持仓股票 (前10名)")
            
            holdings = holdings_data.get('holdings', [])
            if holdings:
                # 创建表格数据
                table_data = []
                for i, holding in enumerate(holdings[:10]):
                    table_data.append({
                        '排名': holding.get('序号', i+1),
                        '股票代码': holding.get('股票代码', ''),
                        '股票名称': holding.get('股票名称', ''),
                        '占净值比例(%)': f"{holding.get('占净值比例', 0):.2f}",
                        '持仓市值(万元)': f"{holding.get('持仓市值', 0):,.0f}" if holding.get('持仓市值') else '-'
                    })
                
                # 显示表格
                df_holdings = pd.DataFrame(table_data)
                st.dataframe(df_holdings, width='stretch', hide_index=True)
            
            st.caption(f"数据更新时间: {holdings_data.get('update_time', '')} | 数据日期: {holdings_data.get('data_date', '')}")
            
        except ImportError:
            st.error("❌ ETF持仓分析功能未安装，请联系管理员")
        except Exception as e:
            st.error(f"❌ 获取ETF持仓信息时出错: {str(e)}")


def display_dividend_details(basic_info_data, stock_identity):
    """显示股息分红详情"""
    market_name = stock_identity.get('market_name', 'A股')
    
    # 单独显示股息分红信息区块
    dividend_fields = [key for key in basic_info_data.keys() if '分红' in key or '派息' in key or '送股' in key or '转增' in key]
    
    # 无论是否有分红数据都显示该区块，以便提供用户提示
    with st.expander("💰 股息分红详情", expanded=True):
        # 检查是否为A股，如果不是则显示提示信息
        if market_name not in ['A股']:
            st.info(f"💡 股息分红功能主要支持A股，{market_name}的分红数据可能无法获取")
            
            # 对于港股，可能有股息但格式不同，对于ETF通常没有分红
            if market_name == '港股':
                st.info("💡 港股分红信息建议查看相关港股资讯网站或券商APP")
            elif market_name == 'ETF':
                st.info("💡 ETF产品通常采用净值增长方式，较少进行现金分红")
        
        if dividend_fields:
            col1, col2 = st.columns(2)
            
            with col1:
                # 最新分红信息
                if basic_info_data.get('最新分红公告日期'):
                    st.write(f"**最新分红公告日期:** {basic_info_data['最新分红公告日期']}")
                
                if basic_info_data.get('最新派息比例') and basic_info_data['最新派息比例'] not in [None, 0]:
                    st.write(f"**最新派息比例:** {basic_info_data['最新派息比例']:.2f}元/10股")
                
                if basic_info_data.get('近年平均派息比例') and basic_info_data['近年平均派息比例'] not in [None, 0]:
                    st.write(f"**近年平均派息比例:** {basic_info_data['近年平均派息比例']:.2f}元/10股")
            
            with col2:
                if basic_info_data.get('最新分红类型'):
                    st.write(f"**分红类型:** {basic_info_data['最新分红类型']}")
                
                if basic_info_data.get('近年分红次数'):
                    st.write(f"**近年分红次数:** {basic_info_data['近年分红次数']}次")
                
                # 显示送股和转增信息
                if basic_info_data.get('最新送股比例') and basic_info_data['最新送股比例'] not in [None, 0]:
                    st.write(f"**最新送股比例:** {basic_info_data['最新送股比例']:.2f}股/10股")
                
                if basic_info_data.get('最新转增比例') and basic_info_data['最新转增比例'] not in [None, 0]:
                    st.write(f"**最新转增比例:** {basic_info_data['最新转增比例']:.2f}股/10股")
            
            # 显示近年分红详情
            if basic_info_data.get('近年分红详情'):
                st.subheader("📊 近年分红记录")
                dividend_records = basic_info_data['近年分红详情'][:5]  # 显示最多5条记录
                
                # 创建表格数据
                table_data = []
                for record in dividend_records:
                    year = record.get('年份', '')
                    dividend_type = record.get('分红类型', '')
                    dividend_ratio = record.get('派息比例', 0)
                    send_ratio = record.get('送股比例', 0)
                    bonus_ratio = record.get('转增比例', 0)
                    
                    table_data.append({
                        '年份': year,
                        '分红类型': dividend_type,
                        '派息比例(元/10股)': f"{dividend_ratio:.2f}" if dividend_ratio > 0 else "-",
                        '送股比例(股/10股)': f"{send_ratio:.2f}" if send_ratio > 0 else "-",
                        '转增比例(股/10股)': f"{bonus_ratio:.2f}" if bonus_ratio > 0 else "-"
                    })
                
                if table_data:
                    import pandas as pd
                    df_dividend = pd.DataFrame(table_data)
                    st.dataframe(df_dividend, width='stretch')
        else:
            # 没有分红数据时的提示
            if market_name == 'A股':
                st.warning("⚠️ 暂无该股票的分红记录数据")
            else:
                st.warning(f"⚠️ {market_name}暂不支持分红数据获取，或该品种无分红记录")


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
                if basic_info_data.get('股票名称'):
                    st.info(f"**股票名称:** {basic_info_data['股票名称']}")

                if basic_info_data.get('所处行业'):
                    st.write(f"所属行业: {basic_info_data['所处行业']}")
                
                if basic_info_data.get('总市值'):
                    st.write(f"总市值: {format_market_value(basic_info_data['总市值'])}")
                    
                if basic_info_data.get('流通市值'):
                    st.write(f"流通市值: {format_market_value(basic_info_data['流通市值'])}")

                if basic_info_data.get('市盈率'):
                    st.write(f"市盈率(动): {basic_info_data['市盈率']}")
                
                if basic_info_data.get('市净率'):
                    st.write(f"市净率: {basic_info_data['市净率']}")
                
                roe_value = basic_info_data.get('净资产收益率(ROE)') or basic_info_data.get('ROE')
                if roe_value:
                    st.write(f"ROE: {roe_value}")

            with col2:
                st.metric(
                    label="当前价格", 
                    value=f"{format_price(basic_info_data.get('current_price', 0))}",
                    delta=format_change(basic_info_data.get('change', 0), 
                                        basic_info_data.get('change_percent', 0)),
                    delta_color="inverse"
                )                
                st.metric("成交量", format_volume(basic_info_data.get('volume', 0)))
                st.write(f"开盘价: {format_price(basic_info_data.get('open', 0))}")
                st.write(f"最高价: {format_price(basic_info_data.get('high', 0))}")
                st.write(f"最低价: {format_price(basic_info_data.get('low', 0))}")
                prev_close = basic_info_data.get('prev_close', 0)
                if prev_close > 0:
                    st.write(f"昨收价: {format_price(prev_close)}")
            
            # 显示ETF持仓信息（如果是ETF）
            display_etf_holdings_info(stock_identity)
            
            # 显示更多财务指标
            display_more_financial_indicators(basic_info_data, stock_identity)
            
            # 显示股息分红详情
            display_dividend_details(basic_info_data, stock_identity)

            st.caption(f"数据更新时间: {basic_info_data.get('timestamp', basic_info_data.get('update_time', ''))}")
        else:
            st.warning(f"未能获取到股票 {stock_code} 的实时数据")
        
        # 显示基本面分析
        display_fundamental_analysis(stock_identity)
            
    except Exception as e:
        st.error(f"获取基本信息失败: {str(e)}")


def display_fundamental_analysis(stock_identity):
    """显示基本面分析"""
    st.divider()
    st.subheader("基本面分析")
    
    stock_code = stock_identity['code']
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


def display_ai_market_analysis(kline_info, stock_code):
    """显示AI行情分析报告"""
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


def display_technical_analysis(stock_identity):
    """显示股票技术分析"""
    st.subheader("技术分析")
    stock_code = stock_identity['code']
    
    try:
        use_cache = st.session_state.get('use_cache', True)
        force_refresh = not use_cache
        
        include_ai_analysis = (st.session_state.get('include_ai_analysis', False) and 
                             stock_code not in st.session_state.get('ai_market_report', {}))
        
        # 获取K线数据
        if include_ai_analysis:
            with st.spinner("🤖 AI正在分析股票行情，请稍候..."):
                kline_info = stock_tools.get_stock_kline_data(
                    stock_identity, 
                    period=160, 
                    use_cache=use_cache, 
                    force_refresh=force_refresh, 
                    include_ai_analysis=True
                )
        else:
            kline_info = stock_tools.get_stock_kline_data(
                stock_identity, 
                period=160, 
                use_cache=use_cache, 
                force_refresh=force_refresh
            )
        
        if 'error' in kline_info:
            st.error(f"获取K线数据失败: {kline_info['error']}")
            return
        
        if kline_info and kline_info.get('kline_data'):
            df = pd.DataFrame(kline_info['kline_data'])
            
            # 显示AI分析报告
            display_ai_market_analysis(kline_info, stock_code)
                        
            # 显示K线图和成交量图
            from ui.components.page_common import display_kline_charts
            stock_name = stock_identity.get('name', stock_identity.get('code', ''))
            display_kline_charts(df, chart_type="stock", title_prefix=stock_name)
            
            # 显示技术指标分析
            from ui.components.page_common import display_technical_analysis_tab
            display_technical_analysis_tab(stock_identity=stock_identity)

            # 显示风险分析
            risk_metrics = kline_info.get('risk_metrics', None)
            from ui.components.page_common import display_risk_analysis
            display_risk_analysis(risk_metrics)

        else:
            st.warning(f"未获取到 {stock_code} 的K线数据")
    
    except Exception as e:
        st.error(f"加载行情数据失败: {str(e)}")


def display_news_analysis(stock_identity):
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
            
            st.dataframe(df, width='stretch')
            
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
                
                st.plotly_chart(fig_profit, use_container_width=True)
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
                
                st.plotly_chart(fig_cost, use_container_width=True)
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

