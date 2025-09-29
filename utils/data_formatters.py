"""股票数据格式化模块"""

import os
import sys
from typing import Dict, Any, List

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from utils.format_utils import format_large_number, format_market_value, format_price, format_percentage, format_volume, judge_rsi_level


def format_technical_indicators(tech_indicators):
    """
    为市场报告格式化技术指标数据（固定格式）
    
    Args:
        tech_indicators: 技术指标数据
    
    Returns:
        str: 格式化后的技术指标Markdown文本
    """
    if 'error' in tech_indicators or not tech_indicators:
        return ""
        
    md_content = """---

# 📈 技术指标分析
（注意：使用的 K线数据截至上一交易日）

"""
    
    tech_metrics = [
        ('MA5', f"{tech_indicators.get('ma5', 0):.2f}"),
        ('MA10', f"{tech_indicators.get('ma10', 0):.2f}"),
        ('MA20', f"{tech_indicators.get('ma20', 0):.2f}"),
        ('MA60', f"{tech_indicators.get('ma60', 0):.2f}"),
        ('MACD', f"{tech_indicators.get('macd', 0):.4f}"),
        ('MACD信号线', f"{tech_indicators.get('macd_signal', 0):.4f}"),
        ('MACD柱状图', f"{tech_indicators.get('macd_histogram', 0):.4f}"),
        ('MA趋势', tech_indicators.get('ma_trend', '')),
        ('MACD趋势', tech_indicators.get('macd_trend', '')),
        ('KDJ_K', f"{tech_indicators.get('kdj_k', 0):.2f}"),
        ('KDJ_D', f"{tech_indicators.get('kdj_d', 0):.2f}"),
        ('KDJ_J', f"{tech_indicators.get('kdj_j', 0):.2f}"),
        ('BOLL上轨', f"{tech_indicators.get('boll_upper', 0):.2f}"),
        ('BOLL中轨', f"{tech_indicators.get('boll_middle', 0):.2f}"),
        ('BOLL下轨', f"{tech_indicators.get('boll_lower', 0):.2f}"),
        ('WR(14)', f"{tech_indicators.get('wr_14', 0):.2f}"),
        ('CCI(14)', f"{tech_indicators.get('cci_14', 0):.2f}")
    ]
    
    for label, value in tech_metrics:
        if value and str(value) != "0.00":
            md_content += f"- **{label}**: {value}\n"
    
    md_content += "\n"
    
    # RSI水平判断
    rsi_14 = tech_indicators.get('rsi_14', 50)
    if rsi_14:
        rsi_level = judge_rsi_level(rsi_14)
        md_content += f"## RSI水平分析\n\n当前RSI值为 **{rsi_14:.2f}**，处于 **{rsi_level}** 状态。\n\n"
    
    return md_content


def format_market_news(market_report_data, max_news_count=10):
    """
    为AI分析格化市场新闻数据
    
    Args:
        market_report_data: 市场报告数据
        max_news_count: 最大新闻数量，默认10条
    
    Returns:
        str: 格式化后的市场新闻文本
    """
    news_text = ""
    
    try:
        news_data = market_report_data.get('market_news_data', {})
        if news_data and news_data.get('market_news'):
            market_news = news_data['market_news']
            news_summary = news_data.get('news_summary', {})
            
            news_text += f"""

**市场新闻资讯：**
数据源：{news_summary.get('data_source', '财新网')}
新闻数量：{news_summary.get('total_market_news_count', len(market_news))}条

重要资讯摘要："""
            
            # 添加前N条重要新闻
            for idx, news in enumerate(market_news[:max_news_count]):
                title = news.get('新闻标题', '无标题')
                time_info = news.get('发布时间', '')
                relative_time = news.get('相对时间', '')
                content = news.get('新闻内容', '')
                
                time_display = f"{time_info} ({relative_time})" if relative_time else time_info
                news_text += f"\n{idx+1}. {title}"
                if time_display:
                    news_text += f" - {time_display}"
                
                # 添加新闻内容摘要（前150字符）
                if content:
                    content_preview = content[:150] + "..." if len(content) > 150 else content
                    news_text += f"\n   {content_preview}"
                    
    except Exception as e:
        print(f"⚠️ 格式化新闻信息失败: {e}")
        news_text = f"\n\n**市场新闻资讯：**\n获取新闻数据失败: {str(e)}"
    
    return news_text


def format_risk_metrics(risk_metrics):
    """
    为市场报告格式化风险指标数据（中文化格式）
    
    Args:
        risk_metrics: 风险指标数据字典
    
    Returns:
        str: 格式化后的风险指标Markdown文本
    """
    if not risk_metrics or 'error' in risk_metrics:
        return ""
        
    md_content = """---

# ⚠️ 风险指标分析
（注意：使用的 K线数据截至上一交易日）

"""
    
    # 周期分析
    if 'period_analysis' in risk_metrics:
        period = risk_metrics['period_analysis']
        md_content += "## 数据周期分析\n\n"
        if 'data_length' in period:
            md_content += f"- **数据天数**: {int(period['data_length'])}天\n"
        if 'price_change_pct' in period:
            md_content += f"- **期间涨跌幅**: {period['price_change_pct']:.2f}%\n"
        if 'trend_direction' in period:
            trend_cn = {'up': '上涨', 'down': '下跌', 'sideways': '横盘'}.get(period['trend_direction'], period['trend_direction'])
            md_content += f"- **趋势方向**: {trend_cn}\n"
        md_content += "\n"
    
    # 波动率分析
    if 'volatility_analysis' in risk_metrics:
        volatility = risk_metrics['volatility_analysis']
        md_content += "## 波动率分析\n\n"
        if 'annual_volatility' in volatility:
            md_content += f"- **年化波动率**: {volatility['annual_volatility']:.2f} ({volatility['annual_volatility']*100:.2f}%)\n"
        if 'recent_volatility' in volatility:
            md_content += f"- **近期波动率**: {volatility['recent_volatility']:.2f} ({volatility['recent_volatility']*100:.2f}%)\n"
        if 'volatility_trend' in volatility:
            trend_cn = {'increasing': '递增', 'decreasing': '递减', 'stable': '稳定'}.get(volatility['volatility_trend'], volatility['volatility_trend'])
            md_content += f"- **波动趋势**: {trend_cn}\n"
        md_content += "\n"
    
    # 核心风险指标
    if 'risk_metrics' in risk_metrics:
        risk_core = risk_metrics['risk_metrics']
        md_content += "## 核心风险指标\n\n"
        if 'max_drawdown' in risk_core:
            md_content += f"- **最大回撤**: {risk_core['max_drawdown']:.2f} ({risk_core['max_drawdown']*100:.2f}%)\n"
        if 'sharpe_ratio' in risk_core:
            md_content += f"- **夏普比率**: {risk_core['sharpe_ratio']:.3f}\n"
        if 'var_5pct' in risk_core:
            md_content += f"- **风险价值VaR(5%)**: {risk_core['var_5pct']:.3f} ({risk_core['var_5pct']*100:.2f}%)\n"
        if 'cvar_5pct' in risk_core:
            md_content += f"- **条件风险价值CVaR(5%)**: {risk_core['cvar_5pct']:.3f} ({risk_core['cvar_5pct']*100:.2f}%)\n"
        md_content += "\n"
    
    # 收益统计
    if 'return_statistics' in risk_metrics:
        returns = risk_metrics['return_statistics']
        md_content += "## 收益统计\n\n"
        if 'daily_return_mean' in returns:
            md_content += f"- **日均收益率**: {returns['daily_return_mean']:.4f} ({returns['daily_return_mean']*100:.2f}%)\n"
        if 'daily_return_std' in returns:
            md_content += f"- **日收益标准差**: {returns['daily_return_std']:.4f} ({returns['daily_return_std']*100:.2f}%)\n"
        if 'positive_days_ratio' in returns:
            md_content += f"- **上涨日占比**: {returns['positive_days_ratio']:.2f} ({returns['positive_days_ratio']*100:.1f}%)\n"
        if 'max_single_day_gain' in returns:
            md_content += f"- **单日最大涨幅**: {returns['max_single_day_gain']:.3f} ({returns['max_single_day_gain']*100:.2f}%)\n"
        if 'max_single_day_loss' in returns:
            md_content += f"- **单日最大跌幅**: {returns['max_single_day_loss']:.3f} ({returns['max_single_day_loss']*100:.2f}%)\n"
        md_content += "\n"
    
    # 风险评估
    if 'risk_assessment' in risk_metrics:
        assessment = risk_metrics['risk_assessment']
        md_content += "## 风险评估\n\n"
        if 'risk_level' in assessment:
            risk_level_cn = {'low': '低风险', 'medium': '中等风险', 'high': '高风险'}.get(assessment['risk_level'], assessment['risk_level'])
            md_content += f"- **风险等级**: {risk_level_cn}\n"
        if 'stability' in assessment:
            stability_cn = {'stable': '稳定', 'unstable': '不稳定', 'volatile': '高波动'}.get(assessment['stability'], assessment['stability'])
            md_content += f"- **稳定性**: {stability_cn}\n"
        if 'trend_strength' in assessment:
            strength_cn = {'weak': '弱', 'moderate': '中等', 'strong': '强'}.get(assessment['trend_strength'], assessment['trend_strength'])
            md_content += f"- **趋势强度**: {strength_cn}\n"
        md_content += "\n"
    
    return md_content


class StockDataFormatter:
    """股票数据格式化器"""
    
    def __init__(self):
        pass
    
    def format_basic_info(self, basic_info: Dict[str, Any], stock_identity: Dict[str, Any]) -> str:
        """格式化基本信息为Markdown格式的文本"""
        if not basic_info or 'error' in basic_info:
            return "## 获取基本信息时出错: 暂无基本信息数据\n"
        
        md_content = ""
        stock_code = stock_identity['code']
        stock_name = stock_identity.get('name', '')
        market_name = stock_identity.get('market_name', '未知')
        currency_symbol = stock_identity.get('currency_symbol', '¥')
                
        # 股票信息
        md_content += f"- 股票名称: {stock_name}\n"
        md_content += f"- 股票代码: {stock_code}\n"
        md_content += f"- 所属市场: {market_name}\n"
        
        # 价格信息
        if 'current_price' in basic_info:
            md_content += f"- 当前价格: {format_price(basic_info['current_price'])}{currency_symbol}\n"
        if 'change_amount' in basic_info:
            md_content += f"- 涨跌额: {format_price(basic_info['change_amount'])}{currency_symbol}\n"
        if 'change_percent' in basic_info:
            md_content += f"- 涨跌幅: {format_percentage(basic_info['change_percent'])}\n"
        
        # 市值信息
        if 'total_market_value' in basic_info and basic_info['total_market_value']:
            md_content += f"- 总市值: {format_market_value(basic_info['total_market_value'])}{currency_symbol}\n"
        if 'circulating_market_value' in basic_info and basic_info['circulating_market_value']:
            md_content += f"- 流通市值: {format_market_value(basic_info['circulating_market_value'])}{currency_symbol}\n"
        
        # 财务比率
        ratio_labels = {
            'pe_ratio': '市盈率',
            'pb_ratio': '市净率',
            'roe': 'ROE',
            'gross_profit_margin': '毛利率',
            'net_profit_margin': '净利率',
            'debt_to_asset_ratio': '资产负债率'
        }
        
        for ratio_key, ratio_label in ratio_labels.items():
            if ratio_key in basic_info and basic_info[ratio_key] is not None and str(basic_info[ratio_key]).strip():
                md_content += f"- {ratio_label}: {basic_info[ratio_key]}\n"
        
        # 公司信息
        if 'industry' in basic_info and basic_info['industry']:
            md_content += f"- 所属行业: {basic_info['industry']}\n"
        if 'net_profit' in basic_info and basic_info['net_profit']:
            md_content += f"- 净利润: {format_large_number(basic_info['net_profit'])}\n"
        
        return md_content


    def format_kline_data(self, kline_info: Dict[str, Any]) -> str:
        """为AI分析格式化K线数据为文本"""
        """
        if not kline_data or 'error' in kline_data:
            return "暂无K线数据"
        """
        text_parts = []
        indicators = kline_info.get('indicators')
        risk_metrics = kline_info.get('risk_metrics')
        if indicators:
            indicators_text = format_technical_indicators(indicators)
            text_parts.append(indicators_text)
        
        if risk_metrics:
            risk_text = format_risk_metrics(risk_metrics)
            text_parts.append(risk_text)

        if 'data_length' in kline_info:
            text_parts.append(f"- 数据周期: {kline_info['data_length']}天")
        if 'update_time' in kline_info:
            text_parts.append(f"- 更新时间: {kline_info['update_time']}")
            
        return "\n\n".join(text_parts)
        
    def format_news_data(self, news_data: List[Dict[str, Any]], has_content: bool, max_item: int = -1) -> str:
        """为AI分析格式化新闻数据为文本"""
        if not news_data or len(news_data) == 0:
            return "暂无相关新闻数据"

        text_parts = [f"共获取到 {len(news_data)} 条相关新闻:\n"]

        for i, news in enumerate(news_data):
            title = news.get('新闻标题', '无标题')
            if has_content:
                text_parts.append(f"{i+1}. 新闻标题: {title}")
                if '发布时间' in news:
                    text_parts.append(f"   发布时间: {news['发布时间']}")
                if has_content and '新闻内容' in news and news['新闻内容']:
                    content = news['新闻内容'][:200] + "..." if len(news['新闻内容']) > 200 else news['新闻内容']
                    text_parts.append(f"   新闻内容: {content}")
            else:
                text_parts.append(f"- [{title}]({news['新闻链接']}) - {news.get('发布时间', '')}")
            text_parts.append("")
            if max_item > 0 and i + 1 >= max_item:
                break

        return "\n".join(text_parts)
        
    def format_chip_data(self, chip_data: Dict[str, Any]) -> str:
        """格式化筹码数据为Markdown格式的文本"""
        if not chip_data or 'error' in chip_data:
            return "获取筹码数据时出错: 暂无筹码数据\n"
        
        md_content = ""
        md_content += "\n筹码概况:\n"
        if 'latest_date' in chip_data:
            md_content += f"- 最新日期: {chip_data['latest_date']}\n"
        if 'profit_ratio' in chip_data:
            md_content += f"- 获利比例: {format_percentage(chip_data['profit_ratio'] * 100)}\n"
        if 'avg_cost' in chip_data:
            md_content += f"- 平均成本: {format_price(chip_data['avg_cost'])}\n"
        
        # 筹码分布
        if 'cost_90_low' in chip_data and 'cost_90_high' in chip_data:
            md_content += f"- 90%筹码区间: {format_price(chip_data['cost_90_low'])} - {format_price(chip_data['cost_90_high'])}元\n"
        if 'concentration_90' in chip_data:
            md_content += f"- 90%集中度: {format_percentage(chip_data['concentration_90']*100)}\n"
        
        if 'cost_70_low' in chip_data and 'cost_70_high' in chip_data:
            md_content += f"- 70%筹码区间: {format_price(chip_data['cost_70_low'])} - {format_price(chip_data['cost_70_high'])}元\n"
        if 'concentration_70' in chip_data:
            md_content += f"- 70%集中度: {format_percentage(chip_data['concentration_70']*100)}\n"
        
        # 分析指标
        if 'analysis' in chip_data:
            analysis = chip_data['analysis']
            md_content += "\n分析指标:\n"
            if 'profit_status' in analysis:
                md_content += f"- 获利状态: {analysis['profit_status']}\n"
            if 'concentration_status' in analysis:
                md_content += f"- 集中度状态: {analysis['concentration_status']}\n"
            if 'risk_level' in analysis:
                md_content += f"- 风险水平: {analysis['risk_level']}\n"
        
        # 技术参考位
        reference_added = False
        if 'support_level' in chip_data:
            if not reference_added:
                md_content += "\n技术参考位:\n"
                reference_added = True
            md_content += f"- 支撑位: {format_price(chip_data['support_level'])}\n"
        if 'resistance_level' in chip_data:
            if not reference_added:
                md_content += "\n技术参考位:\n"
                reference_added = True
            md_content += f"- **阻力位**: {format_price(chip_data['resistance_level'])}\n"
        if 'cost_center' in chip_data:
            if not reference_added:
                md_content += "\n技术参考位:\n"
                reference_added = True
            md_content += f"- 成本中枢: {format_price(chip_data['cost_center'])}\n"

        return md_content
    
    def format_stock_overview(self, stock_identity: Dict[str, Any], basic_info: Dict[str, Any] = None) -> str:
        """为AI分析格式化股票概览信息"""
        parts = []       
        currency_symbol = stock_identity.get('currency_symbol', '元')
        
        parts.append(f"股票概览:")
        parts.append(f"- 股票代码: {stock_identity['code']}")
        parts.append(f"- 股票名称: {stock_identity.get('name', '')}")
        parts.append(f"- 所属市场: {stock_identity.get('market_name', '未知市场')}")
        parts.append(f"- 计价货币: {stock_identity.get('currency_name', '人民币')}({currency_symbol})")
        
        if basic_info and 'error' not in basic_info:
            if 'current_price' in basic_info:
                parts.append(f"- 当前价格: {format_price(basic_info['current_price'])}{currency_symbol}")
            if 'change_percent' in basic_info:
                parts.append(f"- 涨跌幅: {format_percentage(basic_info['change_percent'])}")
        
        return "\n".join(parts)


_formatter = None

def get_stock_formatter() -> StockDataFormatter:
    """获取全局股票数据格式化器实例"""
    global _formatter
    if _formatter is None:
        _formatter = StockDataFormatter()
    return _formatter

