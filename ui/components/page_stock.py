"""
股票分析页面 - 股票查询和分析结果显示
"""

import sys
import os
import numpy as np
import pandas as pd
import streamlit as st
import akshare as ak
import plotly.graph_objects as go
import plotly.express as px

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入相关模块
from providers.stock_data_fetcher import data_manager
from providers.risk_metrics import calculate_portfolio_risk
from providers.news_tools import get_stock_news_by_akshare
from providers.stock_tools import explain_cyq_data
from ui.components.page_index import display_technical_indicators
from providers.stock_tools import get_indicators

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
    
    # 获取证券名称（用于显示）
    from providers.stock_tools import normalize_stock_input
    # 根据市场类型确定证券类型
    security_type = 'index' if market_type == "指数" else 'stock'
    stock_code,stock_name = normalize_stock_input(stock_code, security_type)

    # 显示加载中
    with st.spinner(f"正在加载{market_type} {stock_code} ({stock_name})的数据..."):
        try:
            # 根据市场类型决定是否显示筹码分析
            if market_type == "港股" or market_type == "指数":
                # 港股不显示筹码分析
                tab1, tab2, tab3 = st.tabs(["📊 基本信息", "📈 行情走势", "📰 新闻资讯"])
                
                with tab1:
                    display_basic_info(stock_code)

                with tab2:
                    display_market_trend(stock_code)
                                    
                with tab3:
                    display_news(stock_code)
            else:
                # A股、指数、基金等显示全部标签页
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
                        st.write(f"总市值: {stock_info.total_market_value/100000000:.2f}亿")
                        
                    if stock_info.circulating_market_value:
                        st.write(f"流通市值: {stock_info.circulating_market_value/100000000:.2f}亿")

                st.metric(
                    label="当前价格", 
                    value=f"{realtime_data.current_price:.2f}",
                    delta=f"{realtime_data.change:.2f} ({realtime_data.change_percent:.2f}%)"
                )
                
                st.metric("成交量", f"{realtime_data.volume:,}")

            with col2:
                # 当日价格区间
                st.write(f"**开盘价:** {realtime_data.open:.2f}")
                st.write(f"**最高价:** {realtime_data.high:.2f}")
                st.write(f"**最低价:** {realtime_data.low:.2f}")
                st.write(f"**昨收价:** {realtime_data.prev_close:.2f}")
                
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
            
    except Exception as e:
        st.error(f"获取基本信息失败: {str(e)}")


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
            cols[0].metric("开盘", f"{last_row['open']:.2f}")
            cols[1].metric("最高", f"{last_row['high']:.2f}")
            cols[2].metric("最低", f"{last_row['low']:.2f}")
            cols[3].metric("收盘", f"{last_row['close']:.2f}")
            cols[4].metric("成交量", f"{last_row['volume']:,}")
            
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
                
            """
            # 显示研究报告
            if 'research_reports' in stock_data and stock_data['research_reports']:
                st.subheader("研究报告")
                
                reports = stock_data['research_reports']
                st.info(f"共获取到 {len(reports)} 份研究报告")
                
                for idx, report in enumerate(reports[:5]):  # 只显示前5条
                    # 研究报告字段名可能不一致，尝试多种可能的字段名
                    title = (report.get('报告名称') or 
                           report.get('研报标题') or 
                           report.get('title') or 
                           '未知报告')
                    
                    author = (report.get('研究员') or 
                            report.get('分析师') or 
                            report.get('author') or 
                            '未知作者')
                    
                    org = (report.get('机构名称') or 
                          report.get('发布机构') or 
                          report.get('organization') or 
                          '未知机构')
                    
                    st.write(f"**{title}**")
                    st.caption(f"{org} - {author}")\
            """
        else:
            st.info("未能获取到相关新闻")
            
    except Exception as e:
        st.error(f"加载新闻数据失败: {str(e)}")


def display_chips_analysis(stock_code):
    """显示筹码分析"""
    st.subheader("筹码分析")
    
    try:
        # 使用stock_tools模块中的explain_cyq_data函数
        # 由于该函数本身是打印输出，我们需要改造一下来适应Streamlit
        
        import io
        import contextlib
        
        # 获取函数输出
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            latest = explain_cyq_data(stock_code)
        
        output = f.getvalue()
        
        if output:
            # 显示筹码数据
            st.text(output)
            
            if latest is not None:
                # 用可视化方式显示筹码数据
                with st.expander("筹码可视化", expanded=True):
                    # 创建筹码区间的图表
                    data = {
                        '成本区间': [f"{latest['90成本-低']:.2f}-{latest['90成本-高']:.2f}", 
                                  f"{latest['70成本-低']:.2f}-{latest['70成本-高']:.2f}"],
                        '占比': [90, 70],
                        '集中度': [latest['90集中度']*100, latest['70集中度']*100]
                    }
                    
                    df = pd.DataFrame(data)
                    
                    # 显示筹码数据表格
                    st.dataframe(df, use_container_width=True)
                    
                    # 获取价格和集中度数据来绘制图表
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
                            
                            # 添加获利比例曲线
                            fig_profit.add_trace(go.Scatter(
                                x=cyq_data['日期'], 
                                y=cyq_data['获利比例'],
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
        else:
            st.info("未能获取到筹码分析数据")
            
    except Exception as e:
        st.error(f"加载筹码分析数据失败: {str(e)}")


def main():
    """股票分析页面主函数"""
    st.title("股票分析")
    
    # 导入市场类型和股票工具
    from ui.config import MARKET_TYPES, STOCK_CODE_EXAMPLES
    from providers.stock_tools import get_stock_code, get_stock_name, normalize_stock_input
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        market_type = st.selectbox(
            "选择市场类型:",
            MARKET_TYPES,
            index=0,
            help="选择要查询的股票市场类型"
        )
    
    with col2:
        # 显示对应市场的股票代码示例
        if market_type in STOCK_CODE_EXAMPLES:
            examples = ", ".join(STOCK_CODE_EXAMPLES[market_type])
            st.caption(f"示例代码或名称: {examples}")
        
        stock_input = st.text_input(
            "股票代码或名称:",
            placeholder=f"请输入{market_type}代码或股票名称",
            help=f"输入{market_type}代码或股票名称进行查询"
        )
    
    # 查询按钮
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        query_btn = st.button("🔍 查询", type="primary")
    with col2:
        clear_btn = st.button("🗑️ 清空")
    
    # 处理清空按钮
    if clear_btn:
        st.rerun()
    
    # 处理查询按钮
    if query_btn and stock_input.strip():
        # 根据市场类型确定证券类型
        security_type = 'index' if market_type == "指数" else 'stock'
        
        stock_code = get_stock_code(stock_input.strip(), security_type)
        stock_name = get_stock_name(stock_code, security_type)
        
        # 在界面上展示转换结果
        if stock_code != stock_input.strip():
            if market_type == "指数":
                st.info(f"已将输入 \"{stock_input.strip()}\" 识别为指数 {stock_name} ({stock_code})")
            else:
                st.info(f"已将输入 \"{stock_input.strip()}\" 识别为{market_type} {stock_name} ({stock_code})")
        
        # 调用显示函数
        display_stock_info(stock_code, market_type)
    elif query_btn:
        st.warning("请输入证券代码或名称")


if __name__ == "__main__":
    main()
