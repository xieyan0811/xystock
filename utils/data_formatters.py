"""股票数据格式化模块"""

import os
import sys
from typing import Dict, Any, List

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from utils.format_utils import format_large_number, format_market_value, format_price, format_percentage, format_volume, judge_rsi_level


def format_numeric_value(value, decimal_places=2):
    """
    格式化数值，处理字符串类型的数值
    
    Args:
        value: 要格式化的值，可能是数值或字符串类型的数值
        decimal_places: 保留的小数位数
    
    Returns:
        str: 格式化后的数值字符串
    """
    if value is None:
        return "0.00"
    
    # 如果是字符串，尝试转换为浮点数
    if isinstance(value, str):
        try:
            # 去除可能的百分号和空格
            clean_value = value.strip().rstrip('%')
            numeric_value = float(clean_value)
            return f"{numeric_value:.{decimal_places}f}"
        except (ValueError, TypeError):
            # 如果转换失败，返回原始字符串
            return value
    elif isinstance(value, (int, float)):
        return f"{value:.{decimal_places}f}"
    else:
        return str(value)


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

## 📈 技术指标分析
（注意：交易日17:00前数据截至上一交易日，17:00后包含当日数据）

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


def format_risk_metrics(risk_metrics, with_header = True):
    """
    为市场报告格式化风险指标数据（中文化格式）
    
    Args:
        risk_metrics: 风险指标数据字典
    
    Returns:
        str: 格式化后的风险指标Markdown文本
    """
    if not risk_metrics or 'error' in risk_metrics:
        return ""
        
    if with_header:
        md_content = """---

## ⚠️ 风险指标分析
（注意：交易日17:00前数据截至上一交易日，17:00后包含当日数据）

"""
    else:
        md_content = """（注意：交易日17:00前数据截至上一交易日，17:00后包含当日数据）

"""
    
    # 周期分析
    if 'period_analysis' in risk_metrics:
        period = risk_metrics['period_analysis']
        md_content += "### 数据周期分析\n\n"
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
        md_content += "### 波动率分析\n\n"
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
        md_content += "### 核心风险指标\n\n"
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
        md_content += "### 收益统计\n\n"
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
        md_content += "### 风险评估\n\n"
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
    
    def format_basic_info(self, basic_info: Dict[str, Any], stock_identity: Dict[str, Any], include_dividend: bool = False) -> str:
        """格式化基本信息为Markdown格式的文本 - 处理中文字段名"""
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
        
        # 市值信息 - 使用中文字段名
        if '总市值' in basic_info and basic_info['总市值']:
            md_content += f"- 总市值: {format_market_value(basic_info['总市值'])}{currency_symbol}\n"
        if '流通市值' in basic_info and basic_info['流通市值']:
            md_content += f"- 流通市值: {format_market_value(basic_info['流通市值'])}{currency_symbol}\n"
        
        # 基本财务比率（直接使用中文字段名）
        profitability_section = ""
        profitability_indicators = ['净资产收益率(ROE)', '总资产报酬率(ROA)', '毛利率', '销售净利率', '营业利润率']
        
        for field_name in profitability_indicators:
            if field_name in basic_info and basic_info[field_name] is not None and str(basic_info[field_name]).strip():
                value = basic_info[field_name]
                formatted_value = format_numeric_value(value, 2)
                profitability_section += f"- {field_name}: {formatted_value}%\n"
        
        if profitability_section:
            md_content += "\n### 📊 盈利能力指标\n" + profitability_section
        
        solvency_section = ""
        solvency_indicators = ['资产负债率', '流动比率', '速动比率', '现金比率', '权益乘数']
        
        for field_name in solvency_indicators:
            if field_name in basic_info and basic_info[field_name] is not None and str(basic_info[field_name]).strip():
                value = basic_info[field_name]
                if field_name == '资产负债率':
                    formatted_value = format_numeric_value(value, 2)
                    solvency_section += f"- {field_name}: {formatted_value}%\n"
                else:
                    formatted_value = format_numeric_value(value, 2)
                    solvency_section += f"- {field_name}: {formatted_value}\n"
        
        if solvency_section:
            md_content += "\n### 💰 偿债能力指标\n" + solvency_section
        
        efficiency_section = ""
        efficiency_indicators = ['总资产周转率', '应收账款周转率', '存货周转率', '流动资产周转率']
        
        for field_name in efficiency_indicators:
            if field_name in basic_info and basic_info[field_name] is not None and str(basic_info[field_name]).strip():
                value = basic_info[field_name]
                formatted_value = format_numeric_value(value, 2)
                efficiency_section += f"- {field_name}: {formatted_value}\n"
        
        if efficiency_section:
            md_content += "\n### 🔄 营运能力指标\n" + efficiency_section
        
        growth_section = ""
        growth_indicators = ['营业总收入增长率', '归属母公司净利润增长率']
        
        for field_name in growth_indicators:
            if field_name in basic_info and basic_info[field_name] is not None and str(basic_info[field_name]).strip():
                value = basic_info[field_name]
                formatted_value = format_numeric_value(value, 2)
                growth_section += f"- {field_name}: {formatted_value}%\n"
        
        if growth_section:
            md_content += "\n### 📈 成长能力指标\n" + growth_section
        
        valuation_section = ""
        if '市盈率' in basic_info and basic_info['市盈率'] is not None and str(basic_info['市盈率']).strip():
            formatted_pe = format_numeric_value(basic_info['市盈率'], 2)
            valuation_section += f"- 市盈率: {formatted_pe}\n"
        if '市净率' in basic_info and basic_info['市净率'] is not None and str(basic_info['市净率']).strip():
            formatted_pb = format_numeric_value(basic_info['市净率'], 2)
            valuation_section += f"- 市净率: {formatted_pb}\n"
        
        if valuation_section:
            md_content += "\n### 📋 估值指标\n" + valuation_section
        
        # 每股指标
        per_share_section = ""
        per_share_indicators = ['基本每股收益', '每股净资产', '每股经营现金流', '每股营业收入']
        
        for field_name in per_share_indicators:
            if field_name in basic_info and basic_info[field_name] is not None and str(basic_info[field_name]).strip():
                value = basic_info[field_name]
                formatted_value = format_numeric_value(value, 2)
                per_share_section += f"- {field_name}: {formatted_value}元\n"
        
        if per_share_section:
            md_content += "\n### 💎 每股指标\n" + per_share_section
        
        # 股息分红信息（仅在 include_dividend=True 时显示）
        if include_dividend:
            dividend_section = ""
            dividend_indicators = [
                '最新分红公告日期', '最新分红类型', '最新派息比例', '最新送股比例', '最新转增比例',
                '最新股权登记日', '最新除权日', '最新派息日', '近年平均派息比例', '近年分红次数'
            ]
            
            for field_name in dividend_indicators:
                if field_name in basic_info and basic_info[field_name] is not None and str(basic_info[field_name]).strip():
                    value = basic_info[field_name]
                    if field_name in ['最新派息比例', '近年平均派息比例']:
                        formatted_value = format_numeric_value(value, 2)
                        dividend_section += f"- {field_name}: {formatted_value}元/10股\n"
                    elif field_name in ['最新送股比例', '最新转增比例']:
                        formatted_value = format_numeric_value(value, 2)
                        dividend_section += f"- {field_name}: {formatted_value}股/10股\n"
                    else:
                        dividend_section += f"- {field_name}: {value}\n"
            
            # 显示近年分红详情（最多显示3条）
            if '近年分红详情' in basic_info and basic_info['近年分红详情']:
                dividend_section += "\n#### 近年分红记录（最近3次）\n"
                for i, record in enumerate(basic_info['近年分红详情'][:3]):
                    year = record.get('年份', '')
                    dividend_type = record.get('分红类型', '')
                    dividend_ratio = record.get('派息比例', 0)
                    send_ratio = record.get('送股比例', 0)
                    bonus_ratio = record.get('转增比例', 0)
                    
                    record_text = f"- {year}年 {dividend_type}"
                    if dividend_ratio > 0:
                        record_text += f" 派息{dividend_ratio:.2f}元/10股"
                    if send_ratio > 0:
                        record_text += f" 送股{send_ratio:.2f}股/10股"
                    if bonus_ratio > 0:
                        record_text += f" 转增{bonus_ratio:.2f}股/10股"
                    
                    dividend_section += record_text + "\n"
            
            if dividend_section:
                md_content += "\n### 💰 股息分红信息\n" + dividend_section
        
        md_content += "\n### 🏢 公司信息\n"
        if '所处行业' in basic_info and basic_info['所处行业']:
            md_content += f"- 所属行业: {basic_info['所处行业']}\n"
        if '净利润' in basic_info and basic_info['净利润']:
            md_content += f"- 净利润: {format_large_number(basic_info['净利润'])}\n"
        
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
        
    def format_stock_news_data(self, news_data: List[Dict[str, Any]], has_content: bool, max_item: int = -1) -> str:
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
            if 'high' in basic_info: 
                parts.append(f"- 最高价: {format_price(basic_info['high'])}{currency_symbol}")
            if 'low' in basic_info:
                parts.append(f"- 最低价: {format_price(basic_info['low'])}{currency_symbol}")
            if 'open' in basic_info:
                parts.append(f"- 今开: {format_price(basic_info['open'])}{currency_symbol}")
            if 'volume' in basic_info and basic_info['volume'] is not None:
                parts.append(f"- 成交量: {format_volume(basic_info['volume'])}")
        
        return "\n".join(parts)
    
    def format_etf_holdings(self, holdings_data: Dict[str, Any], max_display: int = 20) -> str:
        """格式化ETF持仓数据为Markdown格式的文本"""
        if not holdings_data or 'error' in holdings_data:
            return f"获取ETF持仓数据时出错: {holdings_data.get('error', '未知错误')}\n"
        
        etf_code = holdings_data['etf_code']
        holdings = holdings_data['holdings']
        statistics = holdings_data.get('statistics', {})
        
        md_content = f"\n## 📊 ETF {etf_code} 持仓分析\n\n"
        
        # 基本信息
        md_content += f"- 数据日期: {holdings_data.get('data_date', '')}\n"
        md_content += f"- 持仓股票总数: {holdings_data.get('total_holdings_count', 0)}\n"
        
        # 集中度分析
        if statistics and 'concentration_analysis' in statistics:
            conc = statistics['concentration_analysis']
            md_content += f"- 集中度分析: {conc.get('analysis', '')}\n"
            md_content += f"- 前5大持仓占比: {conc.get('top_5_weight', 0)}%\n"
            md_content += f"- 前10大持仓占比: {conc.get('top_10_weight', 0)}%\n"
            md_content += f"- 前20大持仓占比: {conc.get('top_20_weight', 0)}%\n"
        
        md_content += "\n### 主要持仓股票\n\n"
        
        # 显示持仓明细
        display_count = min(len(holdings), max_display)
        for i in range(display_count):
            holding = holdings[i]
            md_content += f"{holding['序号']:2d}. **{holding['股票代码']}** {holding['股票名称']} - {holding['占净值比例']:.2f}%\n"
        
        if len(holdings) > max_display:
            md_content += f"\n*还有 {len(holdings) - max_display} 只股票...*\n"
        
        md_content += f"\n*数据更新时间: {holdings_data.get('update_time', '')}*\n"
        
        return md_content
    
    def format_etf_holdings_for_ai(self, holdings_data: Dict[str, Any], max_stocks: int = 30) -> str:
        """为AI分析格式化ETF持仓数据为文本"""
        if not holdings_data or 'error' in holdings_data:
            return f"暂无ETF持仓数据: {holdings_data.get('error', '未知错误')}"
        
        etf_code = holdings_data['etf_code']
        holdings = holdings_data['holdings']
        statistics = holdings_data.get('statistics', {})
        
        text_parts = []
        text_parts.append(f"ETF {etf_code} 持仓分析:")
        text_parts.append(f"- 持仓股票总数: {holdings_data.get('total_holdings_count', 0)}")
        text_parts.append(f"- 数据年份: {holdings_data.get('data_date', '')}")
        text_parts.append(f"- 最新季度: {holdings_data.get('latest_quarter', '')}")
        
        # 集中度分析
        if statistics and 'concentration_analysis' in statistics:
            conc = statistics['concentration_analysis']
            text_parts.append(f"- 集中度水平: {conc.get('concentration_level', '')}集中度")
            text_parts.append(f"- 前10大持仓占比: {conc.get('top_10_weight', 0)}%")
        
        # 主要持仓
        text_parts.append(f"\n前{min(len(holdings), max_stocks)}大持仓:")
        for i, holding in enumerate(holdings[:max_stocks]):
            text_parts.append(f"{holding['序号']:2d}. {holding['股票代码']} {holding['股票名称']} {holding['占净值比例']:.2f}%")
        
        if len(holdings) > max_stocks:
            text_parts.append(f"... 另有 {len(holdings) - max_stocks} 只股票")
        
        return "\n".join(text_parts)


def get_indicator_value(basic_info: Dict[str, Any], indicator_key: str) -> Any:
    """获取指标值的统一函数 - 简化版，直接返回字段值"""
    return basic_info.get(indicator_key)


_formatter = None

def get_stock_formatter() -> StockDataFormatter:
    """获取全局股票数据格式化器实例"""
    global _formatter
    if _formatter is None:
        _formatter = StockDataFormatter()
    return _formatter

