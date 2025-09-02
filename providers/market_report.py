import sys
import os
import datetime

# 添加路径以便导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from providers.market_data_tools import get_market_tools
from utils.format_utils import format_volume, format_market_value, format_price, format_percentage, format_change, format_large_number
from providers.report_utils import generate_pdf_report, generate_docx_report, generate_markdown_file


def generate_market_report(index_name="上证指数", format_type="pdf", has_ai_analysis=False, user_opinion=""):
    """生成完整的市场分析报告（安全版本，完全独立于UI）"""
    try:
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
            from providers.market_data_fetcher import fetch_index_technical_indicators
            tech_indicators = fetch_index_technical_indicators(index_name)
            if tech_indicators:
                report_data['technical_indicators'] = tech_indicators
        except Exception as e:
            report_data['technical_indicators'] = {'error': str(e)}
        
        # 收集市场情绪数据
        try:
            sentiment_data = market_tools.get_market_sentiment(use_cache=True)
            if 'error' not in sentiment_data and sentiment_data:
                report_data['sentiment_data'] = sentiment_data
        except Exception as e:
            report_data['sentiment_data'] = {'error': str(e)}
        
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
        if has_ai_analysis:
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
        
        md_content = generate_markdown_market_report(index_name, report_data)
        
        if format_type == "pdf":
            return generate_pdf_report(md_content)
        elif format_type == "docx":
            return generate_docx_report(md_content)
        elif format_type == "markdown":
            return generate_markdown_file(md_content)
        else:
            return md_content
            
    except Exception as e:
        error_msg = f"生成市场报告失败: {str(e)}"
        if format_type == "pdf":
            return generate_pdf_report(f"# 错误\n\n{error_msg}")
        elif format_type == "docx":
            return generate_docx_report(f"# 错误\n\n{error_msg}")
        elif format_type == "markdown":
            return generate_markdown_file(f"# 错误\n\n{error_msg}")
        else:
            return f"# 错误\n\n{error_msg}"


def generate_markdown_market_report(index_name, report_data):
    """生成Markdown格式的市场报告"""
    
    md_content = f"""# {index_name} 市场综合分析报告

**关注指数**: {index_name}  
**报告生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    # 指数概览部分
    current_indices = report_data.get('current_indices', {})
    focus_index_data = report_data.get('focus_index_data', {})
    
    if 'error' not in current_indices and current_indices:
        md_content += """# 📊 市场指数概览

"""
        
        # 主要指数表格
        indices_dict = current_indices.get('indices_dict', {})
        if indices_dict:
            md_content += """## 主要指数

| 指数名称 | 当前点位 | 涨跌幅 | 涨跌点数 |
|---------|----------|--------|----------|
"""
            
            # 定义要显示的主要指数顺序
            main_indices = ['上证指数', '深证成指', '创业板指', '科创50', '沪深300', '中证500']
            
            for idx_name in main_indices:
                if idx_name in indices_dict:
                    idx_data = indices_dict[idx_name]
                    current = idx_data.get('current_price', 0)
                    change_pct = idx_data.get('change_percent', 0)
                    change = idx_data.get('change_amount', 0)
                    
                    # 格式化涨跌幅颜色
                    if change_pct > 0:
                        change_str = f"🔴 +{change_pct:.2f}%"
                        change_val_str = f"+{change:.2f}"
                    elif change_pct < 0:
                        change_str = f"🟢 {change_pct:.2f}%"
                        change_val_str = f"{change:.2f}"
                    else:
                        change_str = f"⚪ {change_pct:.2f}%"
                        change_val_str = f"{change:.2f}"
                    
                    md_content += f"| {idx_name} | {current:.2f} | {change_str} | {change_val_str} |\n"
            
            md_content += "\n"
        
        # 焦点指数详细信息
        if focus_index_data:
            md_content += f"""## {index_name} 详细信息

"""
            
            focus_metrics = [
                ('当前点位', f"{focus_index_data.get('current_price', 0):.2f}"),
                ('今日开盘', f"{focus_index_data.get('open', 0):.2f}"),
                ('今日最高', f"{focus_index_data.get('high', 0):.2f}"),
                ('今日最低', f"{focus_index_data.get('low', 0):.2f}"),
                ('昨日收盘', f"{focus_index_data.get('prev_close', 0):.2f}"),
                ('涨跌点数', f"{focus_index_data.get('change_amount', 0):.2f}"),
                ('涨跌幅', f"{focus_index_data.get('change_percent', 0):.2f}%"),
                ('成交量', format_volume(focus_index_data.get('volume', 0))),
                ('成交额', format_large_number(focus_index_data.get('turnover', 0)))
            ]
            
            for label, value in focus_metrics:
                if value and value != "0.00":
                    md_content += f"- **{label}**: {value}\n"
            
            md_content += "\n"
    
    # 技术指标分析部分
    technical_indicators = report_data.get('technical_indicators', {})
    if 'error' not in technical_indicators and technical_indicators:
        md_content += """---

# 📈 技术指标分析

"""
        
        tech_metrics = [
            ('MA5', f"{technical_indicators.get('ma5', 0):.2f}"),
            ('MA10', f"{technical_indicators.get('ma10', 0):.2f}"),
            ('MA20', f"{technical_indicators.get('ma20', 0):.2f}"),
            ('MA60', f"{technical_indicators.get('ma60', 0):.2f}"),
            ('RSI(14)', f"{technical_indicators.get('rsi_14', 0):.2f}"),
            ('MACD', f"{technical_indicators.get('macd', 0):.4f}"),
            ('MACD信号线', f"{technical_indicators.get('macd_signal', 0):.4f}"),
            ('MACD柱状图', f"{technical_indicators.get('macd_histogram', 0):.4f}"),
            ('MA趋势', technical_indicators.get('ma_trend', '')),
            ('MACD趋势', technical_indicators.get('macd_trend', ''))
        ]
        
        for label, value in tech_metrics:
            if value and str(value) != "0.00":
                md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
        
        # RSI水平判断
        rsi_14 = technical_indicators.get('rsi_14', 50)
        if rsi_14:
            rsi_level = _judge_rsi_level(rsi_14)
            md_content += f"## RSI水平分析\n\n当前RSI值为 **{rsi_14:.2f}**，处于 **{rsi_level}** 状态。\n\n"
    
    # 市场情绪部分
    sentiment_data = report_data.get('sentiment_data', {})
    if 'error' not in sentiment_data and sentiment_data:
        md_content += """---

# 😊 市场情绪指标

"""
        
        sentiment_metrics = [
            ('上涨家数', sentiment_data.get('up_stocks', 0)),
            ('下跌家数', sentiment_data.get('down_stocks', 0)),
            ('平盘家数', sentiment_data.get('flat_stocks', 0)),
            ('上涨占比', f"{sentiment_data.get('up_ratio', 0) * 100:.1f}%"),
            ('下跌占比', f"{sentiment_data.get('down_ratio', 0) * 100:.1f}%"),
            ('涨停家数', sentiment_data.get('limit_up', 0)),
            ('跌停家数', sentiment_data.get('limit_down', 0))
        ]
        
        for label, value in sentiment_metrics:
            if value and str(value) != "0":
                md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
        
        # 市场情绪总结
        up_ratio = sentiment_data.get('up_ratio', 0)
        if up_ratio > 0.6:
            mood = "积极乐观"
        elif up_ratio > 0.4:
            mood = "中性偏多"
        elif up_ratio > 0.3:
            mood = "中性偏空"
        else:
            mood = "悲观谨慎"
        
        md_content += f"## 市场情绪总结\n\n当前市场整体情绪：**{mood}**\n\n"
    
    # 估值水平部分
    valuation_data = report_data.get('valuation_data', {})
    if 'error' not in valuation_data and valuation_data:
        md_content += """---

# 💰 估值水平分析

"""
        
        valuation_metrics = [
            ('沪深300 PE', f"{valuation_data.get('hs300_pe', 0):.2f}"),
            ('沪深300 PB', f"{valuation_data.get('hs300_pb', 0):.2f}"),
            ('沪深300股息率', f"{valuation_data.get('hs300_dividend_yield', 0):.2f}%"),
            ('中证500 PE', f"{valuation_data.get('zz500_pe', 0):.2f}"),
            ('中证500 PB', f"{valuation_data.get('zz500_pb', 0):.2f}"),
            ('创业板指 PE', f"{valuation_data.get('cyb_pe', 0):.2f}"),
            ('创业板指 PB', f"{valuation_data.get('cyb_pb', 0):.2f}")
        ]
        
        for label, value in valuation_metrics:
            if value and value != "0.00" and value != "0.00%":
                md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
    
    # 资金流向部分
    money_flow_data = report_data.get('money_flow_data', {})
    if 'error' not in money_flow_data and money_flow_data:
        md_content += """---

# 💸 资金流向分析

"""
        
        money_metrics = [
            ('M2货币供应量', f"{money_flow_data.get('m2_amount', 0) / 10000:.2f}万亿元"),
            ('M2同比增长', f"{money_flow_data.get('m2_growth', 0):.2f}%"),
            ('社会融资规模', f"{money_flow_data.get('social_financing', 0) / 10000:.2f}万亿元"),
            ('新增人民币贷款', f"{money_flow_data.get('new_loans', 0) / 10000:.2f}万亿元"),
            ('央行逆回购', f"{money_flow_data.get('reverse_repo', 0):.0f}亿元"),
            ('北向资金净流入', f"{money_flow_data.get('northbound_flow', 0):.2f}亿元")
        ]
        
        for label, value in money_metrics:
            if value and value != "0.00万亿元" and value != "0.00亿元" and value != "0.00%":
                md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
    
    # 融资融券部分
    margin_data = report_data.get('margin_data', {})
    if 'error' not in margin_data and margin_data:
        md_content += """---

# 💳 融资融券分析

"""
        
        margin_metrics = [
            ('融资余额', f"{margin_data.get('margin_buy_balance', 0) / 100000000:.2f}亿元"),
            ('融券余额', f"{margin_data.get('margin_sell_balance', 0) / 100000000:.2f}亿元"),
            ('融资融券总额', f"{margin_data.get('margin_balance', 0) / 100000000:.2f}亿元"),
            ('较前日变化', f"{margin_data.get('change_ratio', 0):.2f}%"),
            ('融资买入额', f"{margin_data.get('margin_buy_amount', 0) / 100000000:.2f}亿元"),
            ('融资偿还额', f"{margin_data.get('margin_repay_amount', 0) / 100000000:.2f}亿元")
        ]
        
        for label, value in margin_metrics:
            if value and value != "0.00亿元" and value != "0.00%":
                md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
        
        # 融资融券趋势分析
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
        
        md_content += f"## 融资融券趋势\n\n融资融券余额较前日 **{trend}** ({change_ratio:.2f}%)\n\n"
    
    # AI分析部分
    ai_analysis = report_data.get('ai_analysis', {})
    if 'error' not in ai_analysis and ai_analysis and 'report' in ai_analysis:
        md_content += """---

# 🤖 AI市场分析

"""
        
        report_text = ai_analysis['report']
        report_time = ai_analysis.get('timestamp', '')
        user_opinion = ai_analysis.get('user_opinion', '')
        
        if user_opinion:
            md_content += f"**用户观点**: {user_opinion}\n\n"
        
        md_content += f"""{report_text}

*AI分析生成时间: {report_time}*

"""
    
    md_content += """---

*本报告由XYStock市场分析系统自动生成，仅供参考，不构成任何投资建议*
"""
    
    return md_content


def _judge_rsi_level(rsi: float) -> str:
    """判断RSI水平"""
    if rsi >= 80:
        return "超买"
    elif rsi >= 70:
        return "强势"
    elif rsi >= 30:
        return "正常"
    elif rsi >= 20:
        return "弱势"
    else:
        return "超卖"


if __name__ == "__main__":
    # 测试用例
    print("🧪 测试市场报告生成模块...")
    
    # 测试生成Markdown报告
    print("\n1. 生成上证指数Markdown报告:")
    try:
        md_report = generate_market_report(
            index_name="上证指数",
            format_type="markdown",
            has_ai_analysis=False
        )
        
        if isinstance(md_report, bytes):
            print(f"   ✅ Markdown报告生成成功，大小: {len(md_report)} 字节")
            # 显示前500个字符的预览
            preview = md_report.decode('utf-8')[:500]
            print(f"   📄 内容预览:\n{preview}...")
        else:
            print(f"   ❌ 报告格式错误: {type(md_report)}")
            
    except Exception as e:
        print(f"   ❌ 报告生成失败: {e}")
    
    print("\n✅ 测试完成!")
