import sys
import os
import datetime

# 添加路径以便导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.report_utils import generate_pdf_report, generate_docx_report, generate_markdown_file, generate_html_report
from ui.config import FOCUS_INDICES
from market.market_formatters import MarketDataCollector
from utils.data_formatters import format_technical_indicators, format_risk_metrics
from version import get_full_version


def write_market_report(index_name="上证指数", format_type="pdf", has_ai_analysis=False, user_opinion=""):
    """生成完整的市场分析报告（安全版本，完全独立于UI）"""
    try:
        # 使用统一的数据收集工具
        report_data = MarketDataCollector.collect_market_data_for_report(index_name, has_ai_analysis, user_opinion)
        
        md_content = generate_markdown_market_report(index_name, report_data)
        
        if format_type == "pdf":
            return generate_pdf_report(md_content)
        elif format_type == "docx":
            return generate_docx_report(md_content)
        elif format_type == "html":
            return generate_html_report(md_content)
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
        elif format_type == "html":
            return generate_html_report(f"# 错误\n\n{error_msg}")
        elif format_type == "markdown":
            return generate_markdown_file(f"# 错误\n\n{error_msg}")
        else:
            return f"# 错误\n\n{error_msg}"


def generate_markdown_market_report(index_name, report_data):
    """生成Markdown格式的市场报告"""
    
    md_content = f"# 📊 {index_name} 市场分析报告\n\n"
    
    # 添加版本信息和生成时间
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md_content += f"**📅 报告生成时间:** {current_time}  \n"
    md_content += f"**🔧 生成工具:** {get_full_version()}  \n\n"

    # AI分析部分
    ai_analysis = report_data.get('ai_analysis', {})
    if 'error' not in ai_analysis and ai_analysis and 'report' in ai_analysis:
        md_content += """
# 🤖 AI市场分析

"""
        
        report_text = ai_analysis['report']
        report_time = ai_analysis.get('timestamp', '')
        user_opinion = ai_analysis.get('user_opinion', '')
        
        if user_opinion:
            md_content += f"**用户观点**: {user_opinion}\n\n"
        
        md_content += f"""{report_text}

*AI分析生成时间: {report_time}*

*以下为参考数据: 当前指数数据, 技术指标, 市场情绪, 估值水平, 资金流向, 融资融券*

""" 
    
    # 指数概览部分
    current_indices = report_data.get('current_indices', {})
    focus_index_data = report_data.get('focus_index_data', {})
    
    if 'error' not in current_indices and current_indices:
        md_content += """---

# 参考数据

## 📊 市场指数概览

"""
        
        # 主要指数列表
        indices_dict = current_indices.get('indices_dict', {})
        if indices_dict:
            md_content += """## 主要指数

"""
            

            for idx_name in FOCUS_INDICES:
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
                    
                    md_content += f"### {arrow} {idx_name}\n"
                    md_content += f"- **当前点位**: {current:.2f}\n"
                    md_content += f"- **涨跌幅**: {change_str}\n"
                    md_content += f"- **涨跌点数**: {change_val_str}\n\n"
        
        # 焦点指数详细信息
        if focus_index_data:
            md_content += MarketDataCollector.format_index_detail(focus_index_data, index_name)
    
    # 技术指标分析部分
    tech_indicators = report_data.get('technical_indicators', {})
    md_content += format_technical_indicators(tech_indicators)
    if tech_indicators.get('risk_metrics'):
        md_content += "\n" + format_risk_metrics(tech_indicators.get('risk_metrics'))
    
    # 市场情绪部分

    sentiment_data = report_data.get('sentiment_data', {})
    if 'error' not in sentiment_data and sentiment_data:
        md_content += """---

## 😊 市场情绪指标

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

## 💰 估值水平分析

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

## 💸 资金流向分析

"""
        
        money_metrics = [
            ('M2货币供应量', f"{money_flow_data.get('m2_amount', 0) / 10000:.2f}万亿元"),
            ('M2同比增长', f"{money_flow_data.get('m2_growth', 0):.2f}%"),
            ('社会融资规模', f"{money_flow_data.get('social_financing', 0) / 10000:.2f}万亿元"),
            ('新增人民币贷款', f"{money_flow_data.get('new_loans', 0) / 10000:.2f}万亿元"),
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

## 💳 融资融券分析

"""
        
        margin_metrics = [
            ('融资余额', f"{margin_data.get('margin_buy_balance', 0) / 100000000:.2f}亿元"),
            ('融券余额', f"{margin_data.get('margin_sell_balance', 0) / 100000000:.2f}亿元"),
            ('融资融券总额', f"{margin_data.get('margin_balance', 0) / 100000000:.2f}亿元"),
            ('周变化率', f"{margin_data.get('change_ratio', 0):.2f}%"),
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
        
        md_content += f"## 融资融券趋势\n\n融资融券余额较上周 **{trend}** ({change_ratio:.2f}%)\n\n"

    md_content += f"""---

**关注指数**: {index_name}  
**报告生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*本报告由XYStock市场分析系统自动生成，仅供参考，不构成任何投资建议*
"""
    
    return md_content


if __name__ == "__main__":
    # 测试用例
    print("🧪 测试市场报告生成模块...")
    
    # 测试生成Markdown报告
    print("\n1. 生成上证指数Markdown报告:")
    try:
        md_report = write_market_report(
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
