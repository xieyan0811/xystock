"""
股票分析页面 - 股票查询和分析结果显示
"""

import sys
import os
import datetime
import pandas as pd
import streamlit as st
import akshare as ak
import plotly.graph_objects as go

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from analysis.stock_ai_analysis import generate_fundamental_analysis_report, generate_stock_analysis_report, generate_news_analysis_report, generate_chip_analysis_report
from ui.components.page_index import display_technical_indicators
from utils.format_utils import format_volume, format_market_value, format_price, format_percentage, format_change
from providers.stock_tools import get_stock_name, get_market_info, get_indicators, normalize_stock_input
from providers.stock_data_fetcher import data_manager
from providers.risk_metrics import calculate_portfolio_risk
from providers.news_tools import get_stock_news_by_akshare

def display_stock_info(stock_code, market_type):
    """
    显示证券信息
    
    Args:
        stock_code: 证券代码
        market_type: 市场类型 (A股/港股/指数/基金)
    """
    if not stock_code:
        st.warning("请输入证券代码或名称")
        return
    
    # 根据市场类型确定证券类型
    security_type = 'index' if market_type == "指数" else 'stock'
    stock_code,stock_name = normalize_stock_input(stock_code, security_type)

    # 显示加载中
    with st.spinner(f"正在加载{market_type} {stock_code} ({stock_name})的数据..."):
        try:
            # 根据市场类型决定标签页配置
            if market_type == "港股" or market_type == "指数":
                # 港股和指数显示3个标签页（基本信息包含基本面分析）
                tab1, tab2, tab3 = st.tabs(["📊 基本信息", "📈 行情走势", "📰 新闻资讯"])
                
                with tab1:
                    display_basic_info(stock_code)

                with tab2:
                    display_market_trend(stock_code)
                                    
                with tab3:
                    display_news(stock_code)
            else:
                # A股、基金等显示4个标签页（基本信息包含基本面分析）
                tab1, tab2, tab3, tab4 = st.tabs(["📊 基本信息", "📈 行情走势", "📰 新闻资讯", "🧮 筹码分析"])
                
                with tab1:
                    display_basic_info(stock_code)
                    
                with tab2:
                    display_market_trend(stock_code)
                                    
                with tab3:
                    display_news(stock_code)
                    
                with tab4:
                    display_chips_analysis(stock_code)
                
        except Exception as e:
            st.error(f"加载数据失败: {str(e)}")
            st.write("请检查股票代码是否正确，或稍后重试。")
            
            # 显示错误详情（调试用）
            with st.expander("🔍 错误详情", expanded=False):
                st.code(str(e), language="text")


def display_basic_info(stock_code):
    """显示股票基本信息"""
    
    st.subheader("基本信息")
    
    try:
        # 获取股票实时行情
        if not data_manager.is_available():
            if not data_manager.initialize():
                st.error("数据提供者初始化失败")
                return
                
        realtime_data = data_manager.get_realtime_quote(stock_code)
        stock_info = data_manager.get_stock_info(stock_code)
        
        if realtime_data:
            # 基本信息
            col1, col2 = st.columns(2)
            
            with col1:
                
                if stock_info:
                    if stock_info.name:
                        st.write(f"**股票名称:** {stock_info.name}")

                    if stock_info.industry:
                        st.info(f"所属行业: {stock_info.industry}")
                    
                    if stock_info.total_market_value:
                        st.write(f"总市值: {format_market_value(stock_info.total_market_value)}")
                        
                    if stock_info.circulating_market_value:
                        st.write(f"流通市值: {format_market_value(stock_info.circulating_market_value)}")

                st.metric(
                    label="当前价格", 
                    value=f"{format_price(realtime_data.current_price)}",
                    delta=format_change(realtime_data.change, realtime_data.change_percent)
                )
                
                st.metric("成交量", format_volume(realtime_data.volume))

            with col2:
                # 当日价格区间
                st.write(f"**开盘价:** {format_price(realtime_data.open)}")
                st.write(f"**最高价:** {format_price(realtime_data.high)}")
                st.write(f"**最低价:** {format_price(realtime_data.low)}")
                st.write(f"**昨收价:** {format_price(realtime_data.prev_close)}")
                
                if stock_info:
                    # 估值指标
                    if stock_info.pe_ratio:
                        st.write(f"**市盈率(动):** {stock_info.pe_ratio}")
                    
                    if stock_info.pb_ratio:
                        st.write(f"**市净率:** {stock_info.pb_ratio}")
                    
                    if stock_info.roe:
                        st.write(f"**ROE:** {stock_info.roe}")
            
            # 更多指标 - 使用Expander折叠显示
            if stock_info:
                with st.expander("更多财务指标", expanded=False):
                    if stock_info.gross_profit_margin:
                        st.write(f"**毛利率:** {stock_info.gross_profit_margin}")
                    
                    if stock_info.net_profit_margin:
                        st.write(f"**净利润率:** {stock_info.net_profit_margin}")
                    
                    if stock_info.net_profit:
                        st.write(f"**净利润:** {stock_info.net_profit}")
                
                # 查询时间
                st.caption(f"数据更新时间: {realtime_data.timestamp}")
        else:
            st.warning(f"未能获取到股票 {stock_code} 的实时数据")
        
        # === 基本面分析部分 - 合并到基本信息中 ===
        st.divider()  # 添加分隔线
        st.subheader("基本面分析")
        
        try:
            # 获取股票名称和市场信息
            market_info = get_market_info(stock_code)
            stock_name_fundamental = get_stock_name(stock_code, 'stock')
            
            # 获取基本面数据（这里实际上就是上面已经获取的stock_info）
            fundamental_data = data_manager.get_stock_info(stock_code)
            
            # 初始化session_state
            if "ai_fundamental_report" not in st.session_state:
                st.session_state.ai_fundamental_report = {}
                
            # 检查是否需要执行AI基本面分析
            if st.session_state.get('run_fundamental_ai_for', '') == stock_code:
                # 重置触发状态，避免重复分析
                st.session_state['run_fundamental_ai_for'] = ''
                
                with st.spinner("🤖 AI正在进行基本面分析，请稍候..."):
                    try:
                        # 生成基本面分析报告
                        fundamental_report, timestamp = generate_fundamental_analysis_report(
                            stock_code=stock_code,
                            stock_name=str(stock_name_fundamental),
                            market_info=market_info,
                            fundamental_data=fundamental_data
                        )
                        print(fundamental_report)  # 调试用
                        
                        # 保存分析报告到session_state
                        st.session_state.ai_fundamental_report[stock_code] = {
                            "report": fundamental_report,
                            "timestamp": timestamp
                        }
                        
                    except ImportError as e:
                        st.error(f"加载AI基本面分析模块失败: {str(e)}")
                        st.info("请确保已安装必要的依赖和正确配置API密钥")
                        
                    except Exception as e:
                        st.error(f"AI基本面分析失败: {str(e)}")
                        st.info("请稍后再试或联系管理员")
            
            # 显示AI基本面分析报告(如果有)
            if stock_code in st.session_state.ai_fundamental_report:
                with st.expander("🤖 AI 基本面分析报告", expanded=True):
                    st.markdown(st.session_state.ai_fundamental_report[stock_code]["report"])
                    st.caption(f"分析报告生成时间: {st.session_state.ai_fundamental_report[stock_code]['timestamp']}")
                    
        except Exception as e:
            st.error(f"加载基本面分析数据失败: {str(e)}")
            
    except Exception as e:
        st.error(f"获取基本信息失败: {str(e)}")


def run_ai_analysis(stock_code, df):
    """
    执行AI分析并返回分析报告
    
    Args:
        stock_code: 股票代码
        df: K线数据DataFrame
        
    Returns:
        tuple: (分析报告文本, 时间戳)
    """
    try:
        # 获取股票名称和市场信息
        market_info = get_market_info(stock_code)
        stock_name = get_stock_name(stock_code, 'stock')
        
        # 获取技术指标
        indicators = get_indicators(df)
        
        # 生成分析报告
        ai_report = generate_stock_analysis_report(
            stock_code=stock_code,
            stock_name=stock_name,
            market_info=market_info,
            df=df,
            indicators=indicators
        )
        
        # 生成时间戳
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        return ai_report, timestamp
        
    except ImportError as e:
        st.error(f"加载AI分析模块失败: {str(e)}")
        st.info("请确保已安装必要的依赖和正确配置API密钥")
        return f"分析失败: {str(e)}", None
        
    except Exception as e:
        st.error(f"AI分析失败: {str(e)}")
        st.info("请稍后再试或联系管理员")
        return f"分析失败: {str(e)}", None


def display_market_trend(stock_code):
    """显示股票行情走势"""
    st.subheader("行情走势")
    
    try:
        from providers.stock_data_fetcher import KLineType
        
        # 固定使用日K数据，160天
        kline_data = data_manager.get_kline_data(
            stock_code, 
            KLineType.DAY, 
            160
        )
        
        if kline_data and len(kline_data) > 0:
            # 转换为DataFrame
            df = pd.DataFrame([k.__dict__ for k in kline_data])
            df = df.sort_values('datetime')
            
            # 初始化session_state
            if "ai_report" not in st.session_state:
                st.session_state.ai_report = {}
                
            # 检查是否需要执行AI分析 (由main函数中的查询按钮和checkbox控制)
            if st.session_state.get('run_ai_for', '') == stock_code:
                # 重置触发状态，避免重复分析
                st.session_state['run_ai_for'] = ''
                
                with st.spinner("🤖 AI正在分析股票行情，请稍候..."):
                    # 执行AI分析
                    report, timestamp = run_ai_analysis(stock_code, df)
                    
                    if timestamp:  # 如果分析成功
                        st.session_state.ai_report[stock_code] = {
                            "report": report,
                            "timestamp": timestamp
                        }
            
            # 显示AI分析报告(如果有)
            if stock_code in st.session_state.ai_report:
                with st.expander("🤖 AI 行情分析报告", expanded=True):
                    st.markdown(st.session_state.ai_report[stock_code]["report"])
                    st.caption(f"分析报告生成时间: {st.session_state.ai_report[stock_code]['timestamp']}")
            
            # 风险指标计算
            if len(df) >= 5:  # 确保有足够数据计算风险指标
                try:
                    risk_metrics = calculate_portfolio_risk(df, price_col='close')
                    
                    with st.expander("风险分析", expanded=True):
                        st.table(risk_metrics['summary_table'])
                except Exception as e:
                    st.error(f"计算风险指标失败: {str(e)}")
            
            # 图表数据预处理
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # 计算移动平均线
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            # 使用plotly创建K线图和均线图表
            fig_price = go.Figure()
            
            # 添加K线图
            fig_price.add_trace(go.Candlestick(
                x=df['datetime'],
                open=df['open'], 
                high=df['high'],
                low=df['low'], 
                close=df['close'],
                name='K线',
                increasing_line_color="#DA1A10",  # 上涨为红色
                decreasing_line_color="#14AA06",  # 下跌为绿色
                increasing_fillcolor="#F51D12",  # 上涨填充色
                decreasing_fillcolor="#1BCC0B"   # 下跌填充色
            ))
            
            # 添加MA5
            fig_price.add_trace(go.Scatter(
                x=df['datetime'], 
                y=df['MA5'],
                mode='lines',
                name='MA5',
                line=dict(color="#D2FF07", width=1.5)
            ))
            
            # 添加MA10
            fig_price.add_trace(go.Scatter(
                x=df['datetime'], 
                y=df['MA10'],
                mode='lines',
                name='MA10',
                line=dict(color="#FF22DA", width=1.5)
            ))
            
            # 添加MA20
            fig_price.add_trace(go.Scatter(
                x=df['datetime'], 
                y=df['MA20'],
                mode='lines',
                name='MA20',
                line=dict(color="#0593F1", width=1.5)
            ))
            
            # 设置图表布局
            fig_price.update_layout(
                title='K线图与均线',
                xaxis_title='日期',
                yaxis_title='价格',
                height=500,  # 增加高度以便更好地显示K线
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                # 禁用滚轮缩放
                xaxis=dict(rangeslider=dict(visible=False)),
                yaxis=dict(fixedrange=True)
            )
            
            # 显示价格图表
            st.plotly_chart(fig_price, use_container_width=True, config={"scrollZoom": False})
            
            # 使用plotly创建成交量图表
            fig_volume = go.Figure()
            
            # 添加成交量柱状图
            fig_volume.add_trace(go.Bar(
                x=df['datetime'], 
                y=df['volume'],
                name='成交量',
                marker=dict(color='#90CAF9')
            ))
            
            # 设置图表布局
            fig_volume.update_layout(
                title='成交量',
                xaxis_title='日期',
                yaxis_title='成交量',
                height=250,
                margin=dict(l=0, r=0, t=40, b=0),
                # 禁用滚轮缩放
                xaxis=dict(rangeslider=dict(visible=False)),
                yaxis=dict(fixedrange=True)
            )
            
            # 显示成交量图表
            st.plotly_chart(fig_volume, use_container_width=True, config={"scrollZoom": False})

            # 显示最近交易日信息
            last_row = df.iloc[-1]
            cols = st.columns(5)
            cols[0].metric("开盘", format_price(last_row['open']))
            cols[1].metric("最高", format_price(last_row['high']))
            cols[2].metric("最低", format_price(last_row['low']))
            cols[3].metric("收盘", format_price(last_row['close']))
            cols[4].metric("成交量", format_volume(last_row['volume']))
            
            indicators = get_indicators(df)
            display_technical_indicators(indicators)

        else:
            st.warning(f"未获取到 {stock_code} 的K线数据")
    
    except Exception as e:
        st.error(f"加载行情数据失败: {str(e)}")


def display_news(stock_code):
    """显示股票相关新闻"""
    st.subheader("新闻资讯")
    
    try:
        # 使用news_tools模块获取新闻
        stock_data = get_stock_news_by_akshare(stock_code)
        
        if stock_data and 'company_news' in stock_data:
            news_data = stock_data['company_news']
            
            # 初始化session_state
            if "ai_news_report" not in st.session_state:
                st.session_state.ai_news_report = {}
                
            # 检查是否需要执行AI新闻分析 (由app.py中的查询按钮和checkbox控制)
            if st.session_state.get('run_news_ai_for', '') == stock_code:
                # 重置触发状态，避免重复分析
                st.session_state['run_news_ai_for'] = ''
                
                with st.spinner("🤖 AI正在分析相关新闻，请稍候..."):
                    try:                        
                        # 获取股票名称和市场信息
                        market_info = get_market_info(stock_code)
                        stock_name = get_stock_name(stock_code, 'stock')
                        
                        # 生成新闻分析报告
                        news_report, timestamp = generate_news_analysis_report(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            market_info=market_info,
                            news_data=news_data
                        )
                        
                        # 保存分析报告到session_state
                        st.session_state.ai_news_report[stock_code] = {
                            "report": news_report,
                            "timestamp": timestamp
                        }
                        
                    except ImportError as e:
                        st.error(f"加载AI新闻分析模块失败: {str(e)}")
                        st.info("请确保已安装必要的依赖和正确配置API密钥")
                        
                    except Exception as e:
                        st.error(f"AI新闻分析失败: {str(e)}")
                        st.info("请稍后再试或联系管理员")
            
            # 显示AI新闻分析报告(如果有)
            if stock_code in st.session_state.ai_news_report:
                with st.expander("🤖 AI 新闻分析报告", expanded=True):
                    st.markdown(st.session_state.ai_news_report[stock_code]["report"])
                    st.caption(f"分析报告生成时间: {st.session_state.ai_news_report[stock_code]['timestamp']}")
            
            # 显示新闻数量统计
            st.info(f"共获取到 {len(news_data)} 条相关新闻")
            
            # 显示最近的新闻
            if news_data:
                for idx, news in enumerate(news_data[:10]):  # 只显示前10条
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


def display_chips_analysis(stock_code):
    """显示筹码分析"""
    st.subheader("筹码分析")
    
    try:
        # 使用简化版筹码数据获取函数
        from providers.stock_tools import get_chip_analysis_data, get_stock_name
        
        # 获取筹码分析数据
        chip_data = get_chip_analysis_data(stock_code)
        stock_name = get_stock_name(stock_code, 'stock')
        
        # 初始化session_state
        if "ai_chip_report" not in st.session_state:
            st.session_state.ai_chip_report = {}
            
        # 检查是否需要执行AI筹码分析 (由app.py中的查询按钮和checkbox控制)
        if st.session_state.get('run_chip_ai_for', '') == stock_code:
            # 重置触发状态，避免重复分析
            st.session_state['run_chip_ai_for'] = ''
            
            with st.spinner("🤖 AI正在分析筹码分布，请稍候..."):
                try:
                    # 生成筹码分析报告
                    chip_report, timestamp = generate_chip_analysis_report(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        chip_data=chip_data
                    )
                    
                    # 保存分析报告到session_state
                    st.session_state.ai_chip_report[stock_code] = {
                        "report": chip_report,
                        "timestamp": timestamp
                    }
                    
                except ImportError as e:
                    st.error(f"加载AI筹码分析模块失败: {str(e)}")
                    st.info("请确保已安装必要的依赖和正确配置API密钥")
                    
                except Exception as e:
                    st.error(f"AI筹码分析失败: {str(e)}")
                    st.info("请稍后再试或联系管理员")
                
        # 显示AI筹码分析报告(如果有)
        if stock_code in st.session_state.ai_chip_report:
            with st.expander("🤖 AI 筹码分析报告", expanded=True):
                st.markdown(st.session_state.ai_chip_report[stock_code]["report"])
                st.caption(f"分析报告生成时间: {st.session_state.ai_chip_report[stock_code]['timestamp']}")
        
        # 检查是否有错误信息
        if "error" in chip_data:
            st.error(chip_data["error"])
            return
            
        # 基础筹码数据显示
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("获利比例", format_percentage(chip_data['profit_ratio'] * 100))
            
            # 获利状态分析
            if chip_data['profit_ratio'] > 0.7:
                st.info("获利盘较重，上涨可能遇到抛售压力")
            elif chip_data['profit_ratio'] < 0.3:
                st.success("获利盘较轻，上涨阻力相对较小")
            else:
                st.info("获利盘适中")
                
        with col2:
            st.metric("平均成本", f"{format_price(chip_data['avg_cost'])}元")
            
            # 集中度状态分析
            if chip_data['concentration_90'] < 0.1:
                st.success("筹码高度集中，可能形成重要支撑/阻力")
            elif chip_data['concentration_90'] > 0.2:
                st.info("筹码较为分散，成本分布较广")
            else:
                st.info("筹码集中度适中")
        
        # 用可视化方式显示筹码数据
        with st.expander("筹码分布数据", expanded=True):
            # 创建筹码区间的图表
            data = {
                '成本区间': [f"{format_price(chip_data['cost_90_low'])}-{format_price(chip_data['cost_90_high'])}", 
                         f"{format_price(chip_data['cost_70_low'])}-{format_price(chip_data['cost_70_high'])}"],
                '占比': [90, 70],
                '集中度': [chip_data['concentration_90']*100, chip_data['concentration_70']*100]
            }
            
            df = pd.DataFrame(data)
            
            # 显示筹码数据表格
            st.dataframe(df, use_container_width=True)
            
            # 显示关键价位
            st.subheader("关键价格区间")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("支撑位", f"{format_price(chip_data['support_level'])}元")
            with col2:
                st.metric("阻力位", f"{format_price(chip_data['resistance_level'])}元")
            with col3:
                st.metric("成本中枢", f"{format_price(chip_data['cost_center'])}元")
        
        # 获取历史数据绘制图表
        try:
            # 获取筹码数据
            cyq_data = ak.stock_cyq_em(stock_code)
            
            if not cyq_data.empty:
                # 绘制获利比例变化趋势
                st.subheader("获利比例变化趋势")
                
                # 使用plotly创建获利比例图表
                fig_profit = go.Figure()
                
                # 确保日期列是日期类型
                cyq_data['日期'] = pd.to_datetime(cyq_data['日期'])
                
                # 添加获利比例曲线 (转换为百分比显示)
                fig_profit.add_trace(go.Scatter(
                    x=cyq_data['日期'], 
                    y=cyq_data['获利比例'] * 100,  # 转换为百分比
                    mode='lines',
                    name='获利比例',
                    line=dict(color='#4CAF50', width=2)
                ))
                
                # 设置图表布局
                fig_profit.update_layout(
                    xaxis_title='日期',
                    yaxis_title='获利比例 (%)',
                    height=350,
                    margin=dict(l=0, r=0, t=10, b=0),
                    # 禁用滚轮缩放
                    xaxis=dict(rangeslider=dict(visible=False)),
                    yaxis=dict(fixedrange=True)
                )
                
                # 显示获利比例图表
                st.plotly_chart(fig_profit, use_container_width=True, config={"scrollZoom": False})
                
                # 绘制平均成本变化趋势
                st.subheader("平均成本变化趋势")
                
                # 使用plotly创建平均成本图表
                fig_cost = go.Figure()
                
                # 添加平均成本曲线
                fig_cost.add_trace(go.Scatter(
                    x=cyq_data['日期'], 
                    y=cyq_data['平均成本'],
                    mode='lines',
                    name='平均成本',
                    line=dict(color='#1E88E5', width=2)
                ))
                
                # 设置图表布局
                fig_cost.update_layout(
                    xaxis_title='日期',
                    yaxis_title='平均成本',
                    height=350,
                    margin=dict(l=0, r=0, t=10, b=0),
                    # 禁用滚轮缩放
                    xaxis=dict(rangeslider=dict(visible=False)),
                    yaxis=dict(fixedrange=True)
                )
                
                # 显示平均成本图表
                st.plotly_chart(fig_cost, use_container_width=True, config={"scrollZoom": False})
        except Exception as e:
            st.error(f"绘制筹码图表失败: {str(e)}")
    
    except Exception as e:
        st.error(f"加载筹码分析数据失败: {str(e)}")

