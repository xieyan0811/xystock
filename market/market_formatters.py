"""
市场数据格式化工具模块
统一管理所有市场数据的格式化逻辑，包括Markdown格式化和数据收集整理
"""

import os
import sys
from typing import Dict
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.format_utils import format_volume, judge_rsi_level, get_section_separator
from config_manager import config


class MarketTextFormatter:
    """统一的市场数据Markdown格式化器"""
    
    @staticmethod
    def _validate_data(data, required_keys=None):
        """统一的数据验证"""
        if not data or 'error' in data:
            return False
        
        if required_keys:
            return all(key in data for key in required_keys)
        
        return True
    
    @staticmethod
    def _format_financial_value(value, unit="亿", decimals=2):
        """统一的金融数值格式化"""
        if not isinstance(value, (int, float)) or value == 0:
            return "N/A"
        
        if unit == "亿":
            return f"{value/100000000:.{decimals}f}亿"
        elif unit == "万亿":
            return f"{value/10000:.{decimals}f}万亿"
        elif unit == "万亿元":
            return f"{value/10000:.{decimals}f}万亿元"
        elif unit == "亿元":
            return f"{value/100000000:.{decimals}f}亿元"
        else:
            return f"{value:.{decimals}f}"
    
    @staticmethod
    def _format_percentage(value, decimals=2):
        """统一的百分比格式化"""
        if not isinstance(value, (int, float)):
            return "N/A"
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def _format_basic_metric(label, value, format_func=None, unit=""):
        """统一的基础指标格式化"""
        if format_func:
            formatted_value = format_func(value)
        elif isinstance(value, (int, float)):
            formatted_value = f"{value}{unit}" if unit else str(value)
        else:
            formatted_value = str(value) if value else "N/A"
        
        return f"- **{label}:** {formatted_value}"
    
    @staticmethod
    def _get_section_header(title, icon="📊"):
        """统一的章节标题生成"""
        return f"## {icon} {title}\n"
    
    @staticmethod
    def _create_metrics_list(metrics_data):
        """统一的指标列表生成"""
        lines = []
        for item in metrics_data:
            if len(item) == 3:  # (label, value, format_func_or_unit)
                label, value, format_or_unit = item
                if callable(format_or_unit):
                    lines.append(MarketTextFormatter._format_basic_metric(label, value, format_func=format_or_unit))
                else:
                    lines.append(MarketTextFormatter._format_basic_metric(label, value, unit=format_or_unit))
            elif len(item) == 2:  # (label, value)
                label, value = item
                lines.append(MarketTextFormatter._format_basic_metric(label, value))
        return lines
    
    @staticmethod
    def _filter_valid_metrics(metrics_data, zero_values=["0.00", "0.00%", "0.00亿元", "0.00万亿元", "N/A"]):
        """过滤掉无效的指标数据"""
        filtered = []
        for item in metrics_data:
            if len(item) == 3:  # (label, value, format_func)
                label, value, format_func = item
                if value and str(value) not in zero_values:
                    filtered.append((label, value, format_func))
            elif len(item) == 2:  # (label, value)
                label, value = item
                if value and str(value) not in zero_values:
                    filtered.append((label, value))
        return filtered
    
    @staticmethod
    def format_sentiment_data(sentiment: Dict, detailed: bool = True, use_table: bool = True, with_header=True) -> str:
        """格式化市场情绪数据为Markdown
        
        Args:
            sentiment: 市场情绪数据
            detailed: 是否显示详细信息，True表示完整分析，False表示简单格式
            use_table: 是否使用表格格式，True表示使用表格，False表示使用文本描述
        """
        if not MarketTextFormatter._validate_data(sentiment):
            return ""
        
        # 根据详细程度设置标题和前缀
        lines = []
        
        if with_header:
            if detailed:
                lines.extend(["## 😐 市场情绪指标", ""])
            else:
                lines.extend(["---", "", "## 😐 市场情绪指标", ""])

        # 获取基础情绪数据
        basic_sentiment = sentiment.get('basic_sentiment', sentiment)
        
        if detailed:
            # 详细版本：情绪评分部分
            if 'sentiment_score' in sentiment:
                score = sentiment.get('sentiment_score', 0)
                level = sentiment.get('sentiment_level', 'unknown')
                confidence = sentiment.get('confidence', 0)
                
                # 根据情绪等级设置显示
                if level == 'bullish':
                    level_display = "🟢 乐观"
                elif level == 'bearish':
                    level_display = "🔴 悲观"
                else:
                    level_display = "🟡 中性"
                
                lines.append("### 📊 综合情绪评分")
                lines.append(f"- **情绪评分:** {score:.1f} 分 (范围: -100 到 100)")
                lines.append(f"- **情绪等级:** {level_display}")
                lines.append(f"- **数据可信度:** {confidence}%")
                lines.append("")
            
            # 详细版本：基础涨跌数据概览
            if basic_sentiment:
                up_stocks = basic_sentiment.get('up_stocks', 0)
                down_stocks = basic_sentiment.get('down_stocks', 0)
                flat_stocks = basic_sentiment.get('flat_stocks', 0)
                total_stocks = basic_sentiment.get('total_stocks', 0)
                limit_up = basic_sentiment.get('limit_up_stocks', 0)
                limit_down = basic_sentiment.get('limit_down_stocks', 0)
                
                lines.append("### 📊 市场涨跌概览")
                lines.append("")
                
                if use_table:
                    # 表格格式
                    lines.append("| 指标 | 数量 | 占比 | 备注 |")
                    lines.append("|------|------|------|------|")
                    
                    if total_stocks > 0:
                        up_ratio = basic_sentiment.get('up_ratio', up_stocks / total_stocks)
                        down_ratio = basic_sentiment.get('down_ratio', down_stocks / total_stocks)
                        flat_ratio = flat_stocks / total_stocks if total_stocks > 0 else 0
                        
                        lines.append(f"| 🟢 上涨股票 | {up_stocks:,} 只 | {up_ratio:.1%} | 市场主流 |")
                        lines.append(f"| 🔴 下跌股票 | {down_stocks:,} 只 | {down_ratio:.1%} | 调整压力 |")
                        lines.append(f"| ⚪ 平盘股票 | {flat_stocks:,} 只 | {flat_ratio:.1%} | 观望态度 |")
                        lines.append(f"| 📊 **总计** | **{total_stocks:,} 只** | **100.0%** | **全市场** |")
                    
                    # 涨跌停数据
                    if limit_up > 0 or limit_down > 0:
                        limit_up_ratio = basic_sentiment.get('limit_up_ratio', 0)
                        limit_down_ratio = basic_sentiment.get('limit_down_ratio', 0)
                        lines.append(f"| 🔥 涨停股票 | {limit_up} 只 | {limit_up_ratio:.2%} | 强势信号 |")
                        lines.append(f"| 💥 跌停股票 | {limit_down} 只 | {limit_down_ratio:.2%} | 恐慌信号 |")
                else:
                    # 文本描述格式
                    if total_stocks > 0:
                        up_ratio = basic_sentiment.get('up_ratio', up_stocks / total_stocks)
                        down_ratio = basic_sentiment.get('down_ratio', down_stocks / total_stocks)
                        flat_ratio = flat_stocks / total_stocks if total_stocks > 0 else 0
                        
                        # 主要涨跌数据
                        lines.append(f"今日市场共有 **{total_stocks:,}** 只股票参与交易。其中：")
                        lines.append("")
                        lines.append(f"- 🟢 **上涨股票:** {up_stocks:,} 只，占比 {up_ratio:.1%}，显示市场主流趋势")
                        lines.append(f"- 🔴 **下跌股票:** {down_stocks:,} 只，占比 {down_ratio:.1%}，反映调整压力")
                        lines.append(f"- ⚪ **平盘股票:** {flat_stocks:,} 只，占比 {flat_ratio:.1%}，体现观望态度")
                        
                        # 涨跌停数据
                        if limit_up > 0 or limit_down > 0:
                            lines.append("")
                            limit_up_ratio = basic_sentiment.get('limit_up_ratio', 0)
                            limit_down_ratio = basic_sentiment.get('limit_down_ratio', 0)
                            
                            if limit_up > 0:
                                lines.append(f"- 🔥 **涨停股票:** {limit_up} 只 (占比 {limit_up_ratio:.2%})，释放强势信号")
                            if limit_down > 0:
                                lines.append(f"- 💥 **跌停股票:** {limit_down} 只 (占比 {limit_down_ratio:.2%})，显示恐慌信号")
                
                lines.append("")
            
            # 详细版本：资金流向情绪
            fund_flow = sentiment.get('fund_flow', {})
            if fund_flow:
                lines.append("### 💸 资金流向情绪")
                main_inflow = fund_flow.get('main_net_inflow', 0)
                main_ratio = fund_flow.get('main_net_ratio', 0)
                
                if main_inflow or main_ratio:
                    lines.append("")
                    
                    if use_table:
                        # 表格格式
                        lines.append("| 资金指标 | 数值 | 说明 |")
                        lines.append("|----------|------|------|")
                        
                        if main_inflow:
                            inflow_text = f"{main_inflow/1e8:.1f}亿"
                            flow_trend = "💰 净流入" if main_inflow > 0 else "💸 净流出"
                            lines.append(f"| 主力资金 | {inflow_text} | {flow_trend} |")
                        
                        if main_ratio:
                            ratio_trend = "活跃" if abs(main_ratio) > 0.5 else "平稳"
                            lines.append(f"| 流入占比 | {main_ratio:.2f}% | 资金{ratio_trend} |")
                    else:
                        # 文本描述格式
                        if main_inflow:
                            inflow_text = f"{abs(main_inflow)/1e8:.1f}亿元"
                            if main_inflow > 0:
                                lines.append(f"主力资金呈现 💰 **净流入** 态势，规模达 **{inflow_text}**，显示机构资金对市场的积极态度。")
                            else:
                                lines.append(f"主力资金出现 💸 **净流出** 现象，规模达 **{inflow_text}**，反映机构资金的谨慎情绪。")
                        
                        if main_ratio:
                            ratio_trend = "活跃" if abs(main_ratio) > 0.5 else "平稳"
                            lines.append(f"资金流入占比为 **{main_ratio:.2f}%**，整体资金流向相对{ratio_trend}，体现了当前市场的资金配置偏好。")
                    
                    lines.append("")
            
            # 详细版本：情绪分析解读
            if 'sentiment_score' in sentiment:
                lines.append("### 🧠 情绪分析解读")
                lines.append("")
                
                # 评分构成分析
                if 'score_components' in sentiment:
                    components = sentiment['score_components']
                    lines.append("#### 📋 评分构成分析")
                    lines.append("")
                    
                    for component, value in components.items():
                        if component == 'ratio':
                            desc = f"**涨跌比例贡献:** {value:.1f}分"
                            if value > 10:
                                desc += " - 🟢 上涨股票占优势，市场偏强"
                            elif value < -10:
                                desc += " - 🔴 下跌股票占优势，市场偏弱"
                            else:
                                desc += " - 🟡 涨跌相对均衡，市场震荡"
                        elif component == 'limit':
                            desc = f"**涨跌停贡献:** {value:.1f}分"
                            if value > 5:
                                desc += " - 🔥 涨停股票较多，情绪高涨"
                            elif value < -5:
                                desc += " - 💥 跌停股票较多，恐慌蔓延"
                            else:
                                desc += " - ⚖️ 涨跌停相对均衡"
                        elif component == 'fund':
                            desc = f"**资金流向贡献:** {value:.1f}分"
                            if value > 10:
                                desc += " - 💰 主力大幅净流入，资金追捧"
                            elif value < -10:
                                desc += " - 💸 主力大幅净流出，资金撤离"
                            else:
                                desc += " - 📊 资金流向相对平衡"
                        else:
                            desc = f"**{component}:** {value:.1f}分"
                        
                        lines.append(f"- {desc}")
                    lines.append("")
                
                # 总体情绪判断
                total_score = sentiment.get('sentiment_score', 0)
                lines.append("#### 🎯 总体情绪判断")
                lines.append("")
                
                if total_score > 30:
                    lines.append("> 🚀 **市场情绪极度乐观**")
                    lines.append(">")
                    lines.append("> 多数指标显示积极信号，市场人气高涨，适合关注强势股票和热点板块。")
                    lines.append("> 建议积极参与，但注意风险控制和适时止盈。")
                elif total_score > 10:
                    lines.append("> 📈 **市场情绪偏乐观**")
                    lines.append(">")
                    lines.append("> 整体趋势向好，但需要注意潜在风险点。")
                    lines.append("> 建议谨慎乐观，做好风险管理和仓位控制。")
                elif total_score > -10:
                    lines.append("> 😐 **市场情绪中性**")
                    lines.append(">")
                    lines.append("> 多空力量相对均衡，市场处于震荡状态，等待明确方向。")
                    lines.append("> 建议保持观望，等待更明确的趋势信号。")
                elif total_score > -30:
                    lines.append("> 📉 **市场情绪偏悲观**")
                    lines.append(">")
                    lines.append("> 下跌压力较大，投资者信心不足，需要注意防守。")
                    lines.append("> 建议降低仓位，关注防御性品种和超跌反弹机会。")
                else:
                    lines.append("> 💥 **市场情绪极度悲观**")
                    lines.append(">")
                    lines.append("> 恐慌情绪浓厚，市场风险偏好极低，需要谨慎操作。")
                    lines.append("> 建议以观望为主，等待市场企稳信号再考虑介入。")
            
            # 详细版本：数据源信息
            """
            data_source = basic_sentiment.get('data_source', '未知')
            update_time = sentiment.get('update_time', basic_sentiment.get('update_time', ''))
            if update_time:
                lines.append("")
                lines.append("---")
                lines.append(f"**📅 数据更新时间:** {update_time}")
                lines.append(f"**🔗 数据源:** {data_source}")
            """
        else:
            # 简单版本：只显示核心指标和总结
            if basic_sentiment:
                metrics = [
                    ('上涨家数', basic_sentiment.get('up_stocks', 0)),
                    ('下跌家数', basic_sentiment.get('down_stocks', 0)),
                    ('平盘家数', basic_sentiment.get('flat_stocks', 0)),
                    ('上涨占比', basic_sentiment.get('up_ratio', 0) * 100, MarketTextFormatter._format_percentage),
                    ('下跌占比', basic_sentiment.get('down_ratio', 0) * 100, MarketTextFormatter._format_percentage),
                    ('涨停家数', basic_sentiment.get('limit_up', 0)),
                    ('跌停家数', basic_sentiment.get('limit_down', 0))
                ]
                
                # 过滤掉无效的指标
                valid_metrics = MarketTextFormatter._filter_valid_metrics(
                    metrics, 
                    zero_values=["0", "0.0%", "N/A"]
                )
                lines.extend(MarketTextFormatter._create_metrics_list(valid_metrics))
                lines.append("")
                
                # 市场情绪总结
                up_ratio = basic_sentiment.get('up_ratio', 0)
                if up_ratio > 0.6:
                    mood = "积极乐观"
                elif up_ratio > 0.4:
                    mood = "中性偏多"
                elif up_ratio > 0.3:
                    mood = "中性偏空"
                else:
                    mood = "悲观谨慎"
                
                lines.append("## 市场情绪总结")
                lines.append("")
                lines.append(f"当前市场整体情绪：**{mood}**")
                lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_valuation_data(valuation: Dict, detailed: bool = False) -> str:
        """格式化估值数据为Markdown
        
        Args:
            valuation: 估值数据
            detailed: 是否显示详细信息，True表示报告格式，False表示简单格式
        """
        if not MarketTextFormatter._validate_data(valuation):
            return ""
        
        # 根据详细程度设置标题和指标
        if detailed:
            lines = ["---", "", MarketTextFormatter._get_section_header("估值水平分析", "💰")]
            # 详细版本包含更多指标
            metrics = [
                ('沪深300 PE', valuation.get('hs300_pe', 0), None),
                ('沪深300 PB', valuation.get('hs300_pb', 0), None),
                ('沪深300股息率', valuation.get('hs300_dividend_yield', 0), MarketTextFormatter._format_percentage),
                ('中证500 PE', valuation.get('zz500_pe', 0), None),
                ('中证500 PB', valuation.get('zz500_pb', 0), None),
                ('创业板指 PE', valuation.get('cyb_pe', 0), None),
                ('创业板指 PB', valuation.get('cyb_pb', 0), None)
            ]
        else:
            lines = [MarketTextFormatter._get_section_header("估值水平", "💰")]
            # 简单版本只显示主要指标
            metrics = [
                ("沪深300 PE", valuation.get('hs300_pe'), None),
                ("股息率", valuation.get('hs300_dividend_yield'), MarketTextFormatter._format_percentage)
            ]
        
        # 过滤掉无效的指标
        valid_metrics = MarketTextFormatter._filter_valid_metrics(metrics)
        lines.extend(MarketTextFormatter._create_metrics_list(valid_metrics))
        
        if detailed:
            lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_money_flow_data(money: Dict, detailed: bool = False) -> str:
        """格式化资金流向数据为Markdown
        
        Args:
            money: 资金流向数据
            detailed: 是否显示详细信息，True表示报告格式，False表示简单格式
        """
        if not MarketTextFormatter._validate_data(money):
            return ""
        
        # 根据详细程度设置标题和指标
        if detailed:
            lines = ["---", "", MarketTextFormatter._get_section_header("资金流向分析", "💸")]
            # 详细版本包含更多指标
            metrics = [
                ('M2货币供应量', money.get('m2_amount', 0), lambda x: MarketTextFormatter._format_financial_value(x, "万亿元")),
                ('M2同比增长', money.get('m2_growth', 0), MarketTextFormatter._format_percentage),
                ('社会融资规模', money.get('social_financing', 0), lambda x: MarketTextFormatter._format_financial_value(x, "万亿元")),
                ('新增人民币贷款', money.get('new_loans', 0), lambda x: MarketTextFormatter._format_financial_value(x, "万亿元")),
                ('北向资金净流入', money.get('northbound_flow', 0), lambda x: MarketTextFormatter._format_financial_value(x, "亿元"))
            ]
            zero_values = ["0.00万亿元", "0.00亿元", "0.00%", "N/A"]
        else:
            lines = [MarketTextFormatter._get_section_header("资金流向", "💸")]
            # 简单版本只显示主要指标
            metrics = [
                ("M2余额", money.get('m2_amount'), lambda x: MarketTextFormatter._format_financial_value(x, "万亿")),
                ("M2同比增长", money.get('m2_growth'), MarketTextFormatter._format_percentage)
            ]
            zero_values = ["0.00万亿", "0.00%", "N/A"]
        
        # 过滤掉无效的指标
        valid_metrics = MarketTextFormatter._filter_valid_metrics(metrics, zero_values)
        lines.extend(MarketTextFormatter._create_metrics_list(valid_metrics))
        
        if detailed:
            lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_margin_data(margin_data: Dict, detailed: bool = False) -> str:
        """格式化融资融券数据为Markdown
        
        Args:
            margin_data: 融资融券数据
            detailed: 是否显示详细信息，True表示报告格式，False表示简单格式
        """
        if not MarketTextFormatter._validate_data(margin_data):
            return ""
        
        # 根据详细程度设置标题和前缀
        if detailed:
            lines = ["---", "", MarketTextFormatter._get_section_header("融资融券分析", "💳")]
            # 详细版本包含更多指标
            metrics = [
                ('融资余额', margin_data.get('margin_buy_balance', 0), lambda x: MarketTextFormatter._format_financial_value(x, "亿元")),
                ('融券余额', margin_data.get('margin_sell_balance', 0), lambda x: MarketTextFormatter._format_financial_value(x, "亿元")),
                ('融资融券总额', margin_data.get('margin_balance', 0), lambda x: MarketTextFormatter._format_financial_value(x, "亿元")),
                ('周变化率', margin_data.get('change_ratio', 0), MarketTextFormatter._format_percentage),
                ('融资买入额', margin_data.get('margin_buy_amount', 0), lambda x: MarketTextFormatter._format_financial_value(x, "亿元")),
                ('融资偿还额', margin_data.get('margin_repay_amount', 0), lambda x: MarketTextFormatter._format_financial_value(x, "亿元"))
            ]
            zero_values = ["0.00亿元", "0.00%", "N/A"]
        else:
            lines = [MarketTextFormatter._get_section_header("融资融券", "💳")]
            # 简单版本只显示主要指标
            metrics = [
                ("融资余额", margin_data.get('margin_balance'), lambda x: MarketTextFormatter._format_financial_value(x, "亿")),
                ("融资买入", margin_data.get('margin_buy_balance'), lambda x: MarketTextFormatter._format_financial_value(x, "亿")),
                ("周变化率", margin_data.get('change_ratio'), MarketTextFormatter._format_percentage)
            ]
            zero_values = ["0.00亿", "0.00%", "N/A"]
        
        # 过滤掉无效的指标
        valid_metrics = MarketTextFormatter._filter_valid_metrics(metrics, zero_values)
        lines.extend(MarketTextFormatter._create_metrics_list(valid_metrics))
        
        # 详细版本添加趋势分析
        if detailed:
            lines.append("")
            change_ratio = margin_data.get('change_ratio', 0)
            if change_ratio > 1:
                trend = "大幅增长"
            elif change_ratio > 0.5:
                trend = "明显增长"
            elif change_ratio > 0:
                trend = "小幅增长"
            elif change_ratio > -0.5:
                trend = "小幅下降"
            elif change_ratio > -1:
                trend = "明显下降"
            else:
                trend = "大幅下降"
            
            lines.append("## 融资融券趋势")
            lines.append("")
            lines.append(f"融资融券余额较上周 **{trend}** ({change_ratio:.2f}%)")
            lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_news_data(news_data: Dict) -> str:
        """格式化新闻数据为Markdown"""
        # 检查是否禁用了市场新闻功能
        if not config.is_market_news_enabled() or news_data.get('disabled'):
            return ""
        if not news_data or not news_data.get('market_news'):
            return ""
            
        lines = []
        lines.append("## 📰 市场资讯")
        lines.append("")
        
        market_news = news_data['market_news']
        news_summary = news_data.get('news_summary', {})
        
        # 添加新闻概况
        lines.append(f"- **新闻数量:** {news_summary.get('total_market_news_count', len(market_news))}条")
        lines.append(f"- **数据源:** {news_summary.get('data_source', '财新网')}")
        
        # 添加重要新闻列表
        if market_news:
            news_list = market_news[:10]  # 限制显示前10条
            
            lines.append("")
            lines.append("### 📄 重要资讯")
            lines.append("")
            
            for idx, news in enumerate(news_list):
                title = news.get('新闻标题', '无标题')
                time_info = news.get('发布时间', '')
                relative_time = news.get('相对时间', '')
                
                time_display = f"{time_info} ({relative_time})" if relative_time else time_info
                lines.append(f"{idx+1}. **{title}**")
                if time_display:
                    lines.append(f"   *发布时间: {time_display}*")
                
                # 添加新闻内容摘要
                content = news.get('新闻内容', '')
                if content:
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                    lines.append(f"   {content_preview}")
                lines.append("")  # 空行分隔
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_simple_report_header(report: Dict) -> str:
        """格式化报告头部为Markdown"""
        lines = []
        lines.append("# 📊 A股市场综合报告")
        lines.append("")
        lines.append(f"**🕐 报告时间:** {report.get('report_time', 'N/A')}")
        lines.append(f"**🎯 关注指数:** {report.get('focus_index', 'N/A')}")
        lines.append("")
        
        return '\n'.join(lines)
    
    
    @staticmethod
    def format_summary_report(report: Dict) -> str:
        """格式化摘要报告为Markdown"""
        summary = {}
        
        # 技术指标
        tech = report.get('technical_indicators', {})
        if tech:
            summary['technical_trend'] = f"{tech.get('ma_trend', '未知')} | MACD {tech.get('macd_trend', '未知')}"
            summary['rsi_level'] = judge_rsi_level(tech.get('rsi_14', 50))
        
        # 融资融券
        margin = report.get('margin_detail', {})
        if margin:
            margin_balance = margin.get('margin_buy_balance', 0)
            summary['margin_balance'] = f"融资余额 {margin_balance/100000000:.2f}亿"
        
        # 估值指标
        valuation = report.get('valuation_indicators', {})
        if valuation:
            pe = valuation.get('hs300_pe', 0)
            summary['valuation_level'] = f"沪深300 PE {pe:.2f}"
        
        # 资金流向
        money = report.get('money_flow_indicators', {})
        if money:
            m2_growth = money.get('m2_growth', 0)
            summary['liquidity_condition'] = f"M2同比增长 {m2_growth:.1f}%"
        
        markdown_lines = []
        
        dimension_map = {
            'technical_trend': ('📈', '技术面'),
            'margin_balance': ('💳', '融资面'), 
            'valuation_level': ('💰', '估值面'),
            'liquidity_condition': ('💸', '资金面'),
            'rsi_level': ('📊', 'RSI'),
        }
        
        for key, (icon, label) in dimension_map.items():
            if key in summary and summary[key]:
                markdown_lines.append(f"**{icon} {label}:** {summary[key]}")
        
        return '\n\n'.join(markdown_lines)
    
    @staticmethod
    def format_ai_analysis(ai_analysis: Dict) -> str:
        """格式化AI分析数据为Markdown"""
        if not ai_analysis or 'error' in ai_analysis or 'report' not in ai_analysis:
            return ""
        
        lines = []
        lines.append("# 🤖 AI市场分析")
        lines.append("")
        
        user_opinion = ai_analysis.get('user_opinion', '')
        if user_opinion:
            lines.append(f"**用户观点**: {user_opinion}")
            lines.append("")
        
        report_text = ai_analysis.get('report', '')
        if report_text:
            lines.append(report_text)
            lines.append("")
        
        report_time = ai_analysis.get('timestamp', '')
        if report_time:
            lines.append(f"*AI分析生成时间: {report_time}*")
            lines.append("")
            lines.append("*以下为参考数据: 当前指数数据, 技术指标, 市场情绪, 估值水平, 资金流向, 融资融券*")
            lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_indices_overview(current_indices: Dict, focus_indices: list) -> str:
        """格式化指数概览为Markdown"""
        if not current_indices or 'error' in current_indices:
            return ""
        
        lines = []
        
        indices_dict = current_indices.get('indices_dict', {})
        if indices_dict:
            lines.append("## 主要指数")
            lines.append("")
            
            for idx_name in focus_indices:
                if idx_name in indices_dict:
                    idx_data = indices_dict[idx_name]
                    current = idx_data.get('current_price', 0)
                    change_pct = idx_data.get('change_percent', 0)
                    change = idx_data.get('change_amount', 0)
                    
                    if change_pct > 0:
                        change_str = f"🔴 +{change_pct:.2f}%"
                        change_val_str = f"+{change:.2f}"
                        arrow = "📈"
                    elif change_pct < 0:
                        change_str = f"🟢 {change_pct:.2f}%"
                        change_val_str = f"{change:.2f}"
                        arrow = "📉"
                    else:
                        change_str = f"⚪ {change_pct:.2f}%"
                        change_val_str = f"{change:.2f}"
                        arrow = "➡️"
                    
                    lines.append(f"### {arrow} {idx_name}")
                    lines.append(f"- **当前点位**: {current:.2f}")
                    lines.append(f"- **涨跌幅**: {change_str}")
                    lines.append(f"- **涨跌点数**: {change_val_str}")
                    lines.append("")
        
        return '\n'.join(lines)
    
    
    @staticmethod
    def format_index_detail(index_data, index_name, format_type="analysis"):
        """
        格式化指数详细信息（统一函数，支持多种格式）
        
        Args:
            index_data: 指数数据字典
            index_name: 指数名称
            format_type: 格式类型，"analysis" 或 "report"
        
        Returns:
            格式化后的字符串
        """
        metrics = [
            ('当前点位', index_data.get('current_price', 0), lambda x: f"{x:.2f}"),
            ('今日开盘', index_data.get('open', 0), lambda x: f"{x:.2f}"),
            ('今日最高', index_data.get('high', 0), lambda x: f"{x:.2f}"),
            ('今日最低', index_data.get('low', 0), lambda x: f"{x:.2f}"),
            ('昨日收盘', index_data.get('prev_close', 0), lambda x: f"{x:.2f}"),
            ('涨跌点数', index_data.get('change_amount', 0), lambda x: f"{x:.2f}"),
            ('涨跌幅', index_data.get('change_percent', 0), MarketTextFormatter._format_percentage),
            ('成交量', index_data.get('volume', 0), format_volume)
        ]
        
        if format_type == "analysis":
            header = f"## 当前分析的指数（{index_name}）：\n\n"
        else:  # format_type == "report"
            header = f"## {index_name} 详细信息\n\n"
        
        # 过滤有效指标并生成列表
        valid_metrics = MarketTextFormatter._filter_valid_metrics(
            metrics, 
            zero_values=["0.00", "0.00%", "N/A"]
        )
        
        lines = [header.strip()]
        lines.extend(MarketTextFormatter._create_metrics_list(valid_metrics))
        lines.append("")
        
        return '\n'.join(lines)

    @staticmethod
    def format_all_indices_summary(indices_dict):
        """
        格式化所有指数的概要信息
        用于AI分析中的市场指数情况
        """
        indices_text = "## 当前市场指数情况：\n"
        for index_name, index_data in indices_dict.items():
            indices_text += f"- {index_name}: {index_data['current_price']:.2f} "
            indices_text += f"({index_data['change_percent']:+.2f}%) "
            indices_text += f"涨跌额: {index_data['change_amount']:+.2f}\n"
        return indices_text


    @staticmethod
    def format_indices_for_analysis(current_indices, stock_name):
        """
        为AI分析格式化指数数据
        
        Args:
            current_indices: 当前指数数据
            stock_name: 目标指数名称
        
        Returns:
            str: 格式化后的指数信息文本
        """
        try:
            current_index_detail = ""
            
            if 'indices_dict' in current_indices:
                indices_text = MarketTextFormatter.format_all_indices_summary(current_indices['indices_dict'])
                
                for index_name, index_data in current_indices['indices_dict'].items():
                    if index_data.get('name') == stock_name:
                        current_index_detail = MarketTextFormatter.format_index_detail(index_data, stock_name, "analysis")
                        break
            else:
                indices_text = "## 当前市场指数情况：\n无法获取指数数据\n"

            if current_index_detail:
                indices_text = current_index_detail + "\n" + indices_text
                
            return indices_text
                
        except Exception as e:
            return f"## 当前市场指数情况：\n获取指数数据失败: {str(e)}\n"


    @staticmethod
    def format_market_data(data: Dict, index_name: str, format_type: str = 'ai_analysis', **kwargs) -> str:
        """
        统一的市场数据格式化函数，支持多种输出格式
        
        Args:
            data: 市场数据字典
            index_name: 指数名称
            format_type: 格式化类型，'ai_analysis' 或 'report'
            **kwargs: 额外参数
                - version_info: 报告生成工具版本信息（仅report模式需要）
                - use_gray_section: 是否使用灰色背景区域（仅report模式需要）
        
        Returns:
            str: 格式化后的完整文本
        """
        # 数据预处理
        if format_type == 'ai_analysis':
            if 'focus_index' not in data or not data.get('focus_index'):
                data = dict(data)  # 创建副本避免修改原数据
                data['focus_index'] = index_name
        
        sections = []
        use_gray_section = kwargs.get('use_gray_section', False)
        
        # 1. 头部处理
        if format_type == 'report':
            version_info = kwargs.get('version_info', 'XYStock市场分析系统')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            header = f"""# 📊 {index_name} 市场分析报告

**报告生成时间:** {current_time}  
**生成工具:** {version_info}  

"""
            sections.append(header)
            
            # AI分析部分（仅报告模式）
            ai_section = MarketTextFormatter.format_ai_analysis(data.get('ai_analysis', {}))
            if ai_section:
                sections.append(ai_section)
            
            # 指数概览部分（仅报告模式）
            from ui.config import FOCUS_INDICES
            
            if use_gray_section:
                sections.append("<!-- gray-section-start -->")
            
            sections.append("---")
            sections.append("# 参考数据")
            
            indices_section = MarketTextFormatter.format_indices_overview(
                data.get('current_indices', {}), 
                FOCUS_INDICES
            )
            if indices_section:
                sections.append(indices_section)
            
            # 焦点指数详细信息（仅报告模式）
            focus_index_data = data.get('focus_index_data', {})
            if focus_index_data:
                focus_section = MarketTextFormatter.format_index_detail(focus_index_data, index_name, "report")
                if focus_section:
                    sections.append(focus_section)
        
        elif format_type == 'ai_analysis':
            # AI分析模式使用简单头部
            sections.append(MarketTextFormatter.format_simple_report_header(data))
        
        # 2. 技术指标部分
        tech_indicators = data.get('technical_indicators', {})
        if tech_indicators:
            try:
                from utils.data_formatters import format_technical_indicators, format_risk_metrics
                
                tech_text = format_technical_indicators(tech_indicators)
                if tech_indicators.get('risk_metrics'):
                    tech_text += "\n" + format_risk_metrics(tech_indicators['risk_metrics'])
                
                if tech_text.strip():
                    sections.append(tech_text)
            except Exception as e:
                sections.append(f"## 主要技术指标\n\n获取技术指标失败: {str(e)}")
        
        # 3. 市场数据部分（根据格式类型使用不同的数据键和详细级别）
        data_mapping = [
            ('sentiment_indicators', MarketTextFormatter.format_sentiment_data, {'detailed': True, 'use_table': False}),
            ('valuation_indicators', MarketTextFormatter.format_valuation_data, {'detailed': True}),
            ('money_flow_indicators', MarketTextFormatter.format_money_flow_data, {'detailed': True}),
            ('margin_detail', MarketTextFormatter.format_margin_data, {'detailed': True}),
            ('market_news_data', MarketTextFormatter.format_news_data, {}),
        ]
        
        # 处理市场数据部分
        for data_key, formatter, format_kwargs in data_mapping:
            section_data = data.get(data_key, {})
            if section_data:
                try:
                    if format_kwargs:
                        section_text = formatter(section_data, **format_kwargs)
                    else:
                        section_text = formatter(section_data)
                    
                    if section_text and section_text.strip():
                        sections.append(section_text)
                except Exception as e:
                    sections.append(f"## {data_key}\n\n获取数据失败: {str(e)}")
        
        # 4. 指数数据部分（仅AI分析模式）
        if format_type == 'ai_analysis':
            current_indices = data.get('current_indices', {})
            focus_index = data.get('focus_index', '')
            if current_indices and focus_index:
                try:
                    indices_text = MarketTextFormatter.format_indices_for_analysis(
                        current_indices, 
                        focus_index
                    )
                    if indices_text.strip():
                        sections.append(indices_text)
                except Exception as e:
                    sections.append(f"## 当前市场指数情况\n\n获取指数数据失败: {str(e)}")
        
        # 结束灰色背景区域
        if format_type == 'report' and use_gray_section:
            sections.append("<!-- gray-section-end -->")
        
        # 5. 尾部处理（仅报告模式）
        if format_type == 'report':
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            footer = f"""---

**关注指数**: {index_name}  
**报告生成时间**: {current_time}

*本报告由XYStock市场分析系统自动生成，仅供参考，不构成任何投资建议*

*XYStock工具已开源，可以在 https://github.com/xieyan0811/xystock 下载安装*
"""
            sections.append(footer)
        
        # 6. 组合结果
        if format_type == 'ai_analysis':
            return '\n\n---\n\n'.join(sections)
        else:
            return '\n\n'.join(sections)

    @staticmethod
    def format_data_for_report(index_name: str, report_data: Dict, version_info: str, use_gray_section: bool = False) -> str:
        """格式化完整的市场报告为Markdown，用于导出文件     
        """
        return MarketTextFormatter.format_market_data(
            report_data, 
            index_name, 
            format_type='report', 
            version_info=version_info,
            use_gray_section=use_gray_section
        )

    @staticmethod
    def format_data_for_ai_analysis(report: Dict, index_name: str) -> str:
        """将核心市场数据格式化为AI分析所需的文本格式        
        """
        return MarketTextFormatter.format_market_data(
            report, 
            index_name, 
            format_type='ai_analysis'
        )
