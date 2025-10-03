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
    def format_sentiment_data(sentiment: Dict) -> str:
        """格式化市场情绪数据为Markdown"""
        if not sentiment:
            return ""
        
        lines = []
        lines.append("## 😐 市场情绪指标")
        lines.append("")
        
        # 情绪评分部分
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
        
        # 基础涨跌数据概览 - 添加卡片式显示
        basic_sentiment = sentiment.get('basic_sentiment', sentiment)
        if basic_sentiment:
            up_stocks = basic_sentiment.get('up_stocks', 0)
            down_stocks = basic_sentiment.get('down_stocks', 0)
            flat_stocks = basic_sentiment.get('flat_stocks', 0)
            total_stocks = basic_sentiment.get('total_stocks', 0)
            limit_up = basic_sentiment.get('limit_up_stocks', 0)
            limit_down = basic_sentiment.get('limit_down_stocks', 0)
            
            # 涨跌数据概览表格
            lines.append("### 📊 市场涨跌概览")
            lines.append("")
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
            
            lines.append("")
        
        # 资金流向情绪
        fund_flow = sentiment.get('fund_flow', {})
        if fund_flow:
            lines.append("### 💸 资金流向情绪")
            main_inflow = fund_flow.get('main_net_inflow', 0)
            main_ratio = fund_flow.get('main_net_ratio', 0)
            
            if main_inflow or main_ratio:
                lines.append("")
                lines.append("| 资金指标 | 数值 | 说明 |")
                lines.append("|----------|------|------|")
                
                if main_inflow:
                    inflow_text = f"{main_inflow/1e8:.1f}亿"
                    flow_trend = "💰 净流入" if main_inflow > 0 else "💸 净流出"
                    lines.append(f"| 主力资金 | {inflow_text} | {flow_trend} |")
                
                if main_ratio:
                    ratio_trend = "活跃" if abs(main_ratio) > 0.5 else "平稳"
                    lines.append(f"| 流入占比 | {main_ratio:.2f}% | 资金{ratio_trend} |")
                
                lines.append("")
        
        # 情绪分析解读
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
        
        # 数据源信息
        basic_sentiment = sentiment.get('basic_sentiment', sentiment)
        data_source = basic_sentiment.get('data_source', '未知')
        update_time = sentiment.get('update_time', basic_sentiment.get('update_time', ''))
        if update_time:
            lines.append("")
            lines.append("---")
            lines.append(f"**📅 数据更新时间:** {update_time}")
            lines.append(f"**🔗 数据源:** {data_source}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_valuation_data(valuation: Dict) -> str:
        """格式化估值数据为Markdown"""
        if not valuation:
            return ""
            
        lines = []
        lines.append("## 💰 估值水平")
        lines.append("")
        
        # 主要估值指标
        hs300_pe = valuation.get('hs300_pe', 'N/A')
        if isinstance(hs300_pe, (int, float)):
            lines.append(f"- **沪深300 PE:** {hs300_pe:.2f}")
        else:
            lines.append(f"- **沪深300 PE:** {hs300_pe}")
            
        dividend_yield = valuation.get('hs300_dividend_yield', 'N/A')
        if isinstance(dividend_yield, (int, float)):
            lines.append(f"- **股息率:** {dividend_yield:.2f}%")
        else:
            lines.append(f"- **股息率:** {dividend_yield}%")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_money_flow_data(money: Dict) -> str:
        """格式化资金流向数据为Markdown"""
        if not money:
            return ""
            
        lines = []
        lines.append("## 💸 资金流向")
        lines.append("")
        
        m2_amount = money.get('m2_amount', 'N/A')
        if isinstance(m2_amount, (int, float)):
            lines.append(f"- **M2余额:** {m2_amount/10000:.2f}万亿")
        else:
            lines.append(f"- **M2余额:** {m2_amount}")
            
        m2_growth = money.get('m2_growth', 'N/A')
        if isinstance(m2_growth, (int, float)):
            lines.append(f"- **M2同比增长:** {m2_growth:.2f}%")
        else:
            lines.append(f"- **M2同比增长:** {m2_growth}%")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_margin_data(margin_data: Dict) -> str:
        """格式化融资融券数据为Markdown"""
        if not margin_data:
            return ""
            
        lines = []
        lines.append("## 💳 融资融券")
        lines.append("")
        
        margin_balance = margin_data.get('margin_balance', 'N/A')
        if isinstance(margin_balance, (int, float)):
            lines.append(f"- **融资余额:** {margin_balance/100000000:.2f}亿")
        else:
            lines.append(f"- **融资余额:** {margin_balance}")
        
        margin_buy_balance = margin_data.get('margin_buy_balance', 'N/A')
        if isinstance(margin_buy_balance, (int, float)):
            lines.append(f"- **融资买入:** {margin_buy_balance/100000000:.2f}亿")
        else:
            lines.append(f"- **融资买入:** {margin_buy_balance}")
            
        change_ratio = margin_data.get('change_ratio', 'N/A')
        if isinstance(change_ratio, (int, float)):
            lines.append(f"- **周变化率:** {change_ratio:.2f}%")
        else:
            lines.append(f"- **周变化率:** {change_ratio}%")
        
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
    def format_report_header(report: Dict) -> str:
        """格式化报告头部为Markdown"""
        lines = []
        lines.append("# 📊 A股市场综合报告")
        lines.append("")
        lines.append(f"**🕐 报告时间:** {report.get('report_time', 'N/A')}")
        lines.append(f"**🎯 关注指数:** {report.get('focus_index', 'N/A')}")
        lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_comprehensive_report(report: Dict) -> str:
        """格式化综合报告为Markdown"""
        sections = []
        
        # 报告头部
        sections.append(MarketTextFormatter.format_report_header(report))
        
        # 各个数据部分
        sentiment_section = MarketTextFormatter.format_sentiment_data(report.get('sentiment_indicators', {}))
        if sentiment_section:
            sections.append(sentiment_section)
        
        valuation_section = MarketTextFormatter.format_valuation_data(report.get('valuation_indicators', {}))
        if valuation_section:
            sections.append(valuation_section)
        
        money_flow_section = MarketTextFormatter.format_money_flow_data(report.get('money_flow_indicators', {}))
        if money_flow_section:
            sections.append(money_flow_section)
        
        margin_section = MarketTextFormatter.format_margin_data(report.get('margin_detail', {}))
        if margin_section:
            sections.append(margin_section)
        
        news_section = MarketTextFormatter.format_news_data(report.get('market_news_data', {}))
        if news_section:
            sections.append(news_section)
        
        return '\n\n---\n\n'.join(sections)
    
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


class MarketDataCollector:
    """市场数据收集和整理工具"""
    
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
        # 统一使用report格式的样式和文字描述
        metrics = [
            ('当前点位', f"{index_data.get('current_price', 0):.2f}"),
            ('今日开盘', f"{index_data.get('open', 0):.2f}"),
            ('今日最高', f"{index_data.get('high', 0):.2f}"),
            ('今日最低', f"{index_data.get('low', 0):.2f}"),
            ('昨日收盘', f"{index_data.get('prev_close', 0):.2f}"),
            ('涨跌点数', f"{index_data.get('change_amount', 0):.2f}"),
            ('涨跌幅', f"{index_data.get('change_percent', 0):.2f}%"),
            ('成交量', format_volume(index_data.get('volume', 0)))
        ]
        
        if format_type == "analysis":
            md_content = f"## 当前分析的指数（{index_name}）：\n\n"
        else:  # format_type == "report"
            md_content = f"## {index_name} 详细信息\n\n"
        
        for label, value in metrics:
            if value and value != "0.00" and value != "0.00%":
                md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
        return md_content

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
    def collect_market_data_for_report(index_name, include_ai=False, user_opinion=""):
        """
        统一收集市场数据
        
        Args:
            index_name: 指数名称
            include_ai: 是否包含AI分析
            user_opinion: 用户观点
        
        Returns:
            dict: 包含所有市场数据的字典
        """
        # 避免循环导入，在函数内部导入
        from market.market_data_tools import get_market_tools
        
        market_tools = get_market_tools()
        report_data = {}
        
        # 收集当前指数数据
        try:
            current_indices = market_tools.get_current_indices(use_cache=True)
            if 'error' not in current_indices and current_indices:
                report_data['current_indices'] = current_indices
                # 获取特定指数信息
                if index_name in current_indices.get('indices_dict', {}):
                    report_data['focus_index_data'] = current_indices['indices_dict'][index_name]
        except Exception as e:
            report_data['current_indices'] = {'error': str(e)}
        
        # 收集技术指标数据
        try:
            tech_indicators = market_tools.get_index_technical_indicators(index_name)
            if tech_indicators:
                report_data['technical_indicators'] = tech_indicators
        except Exception as e:
            report_data['technical_indicators'] = {'error': str(e)}
        
        # 收集估值数据
        try:
            valuation_data = market_tools.get_valuation_data(use_cache=True)
            if 'error' not in valuation_data and valuation_data:
                report_data['valuation_data'] = valuation_data
        except Exception as e:
            report_data['valuation_data'] = {'error': str(e)}
        
        # 收集资金流向数据
        try:
            money_flow_data = market_tools.get_money_flow_data(use_cache=True)
            if 'error' not in money_flow_data and money_flow_data:
                report_data['money_flow_data'] = money_flow_data
        except Exception as e:
            report_data['money_flow_data'] = {'error': str(e)}
        
        # 收集融资融券数据
        try:
            margin_data = market_tools.get_margin_data(use_cache=True)
            if 'error' not in margin_data and margin_data:
                report_data['margin_data'] = margin_data
        except Exception as e:
            report_data['margin_data'] = {'error': str(e)}
        
        # 收集AI分析数据
        if include_ai:
            try:
                ai_analysis = market_tools.get_ai_analysis(
                    use_cache=True, 
                    index_name=index_name,
                    force_regenerate=bool(user_opinion.strip()),
                    user_opinion=user_opinion
                )
                if 'error' not in ai_analysis:
                    report_data['ai_analysis'] = ai_analysis
            except Exception as e:
                report_data['ai_analysis'] = {'error': str(e)}
        
        return report_data

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
                indices_text = MarketDataCollector.format_all_indices_summary(current_indices['indices_dict'])
                
                for index_name, index_data in current_indices['indices_dict'].items():
                    if index_data.get('name') == stock_name:
                        current_index_detail = MarketDataCollector.format_index_detail(index_data, stock_name, "analysis")
                        break
            else:
                indices_text = "## 当前市场指数情况：\n无法获取指数数据\n"

            if current_index_detail:
                indices_text = current_index_detail + "\n" + indices_text
                
            return indices_text
                
        except Exception as e:
            return f"## 当前市场指数情况：\n获取指数数据失败: {str(e)}\n"
