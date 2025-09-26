"""
市场数据收集和格式化的统一工具
"""
from market.market_data_tools import get_market_tools
from utils.format_utils import format_volume, judge_rsi_level


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
            indices_text = format_all_indices_summary(current_indices['indices_dict'])
            
            for index_name, index_data in current_indices['indices_dict'].items():
                if index_data.get('name') == stock_name:
                    current_index_detail = format_index_detail(index_data, stock_name, "analysis")
                    break
        else:
            indices_text = "## 当前市场指数情况：\n无法获取指数数据\n"

        if current_index_detail:
            indices_text = current_index_detail + "\n" + indices_text
            
        return indices_text
            
    except Exception as e:
        return f"## 当前市场指数情况：\n获取指数数据失败: {str(e)}\n"

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
