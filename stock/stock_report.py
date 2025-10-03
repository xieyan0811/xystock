import sys
import os
import datetime
from typing import Dict, Any

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from stock.stock_data_tools import get_stock_tools
from utils.report_utils import generate_pdf_report, generate_docx_report, generate_markdown_file, generate_html_report
from utils.data_formatters import get_stock_formatter
from version import get_version, get_full_version


def generate_stock_report(stock_identity: Dict[str, Any], 
                          format_type="pdf",
                          has_fundamental_ai=False, has_market_ai=False,
                          has_news_ai=False, has_chip_ai=False,
                          has_company_ai=False, has_comprehensive_ai=False):
    """生成完整的股票分析报告（安全版本，完全独立于Streamlit）"""
    try:
        stock_tools = get_stock_tools()
        report_data = {}
        
        # 收集基本信息
        try:
            basic_info = stock_tools.get_basic_info(stock_identity, use_cache=True, include_ai_analysis=has_fundamental_ai, include_company_analysis=has_company_ai)
            if 'error' not in basic_info and basic_info:
                report_data['basic_info'] = basic_info
        except Exception as e:
            report_data['basic_info'] = {'error': str(e)}
        
        # 收集行情数据
        try:
            kline_info = stock_tools.get_stock_kline_data(stock_identity, period=160, use_cache=True, include_ai_analysis=has_market_ai)
            if 'error' not in kline_info and kline_info:
                report_data['kline_info'] = kline_info
        except Exception as e:
            report_data['kline_info'] = {'error': str(e)}
        
        # 收集新闻数据
        try:
            news_info = stock_tools.get_stock_news_data(stock_identity, use_cache=True, include_ai_analysis=has_news_ai)
            if 'error' not in news_info and news_info:
                report_data['news_data'] = news_info
        except Exception as e:
            report_data['news_data'] = {'error': str(e)}
        
        # 收集筹码数据（仅A股和基金）
        if stock_identity.get('market_name', "") != '港股':
            try:
                chip_data = stock_tools.get_stock_chip_data(stock_identity, use_cache=True, include_ai_analysis=has_chip_ai)
                if 'error' not in chip_data and chip_data:
                    report_data['chip_data'] = chip_data
            except Exception as e:
                report_data['chip_data'] = {'error': str(e)}
        
        # 收集综合分析
        if has_comprehensive_ai:
            try:
                comprehensive_analysis = stock_tools.get_comprehensive_ai_analysis(stock_identity, use_cache=True)
                if 'error' not in comprehensive_analysis:
                    report_data['comprehensive_analysis'] = comprehensive_analysis
            except Exception as e:
                pass
                
        final_ai_reports = {}
        
        # 整理AI分析报告
        if has_fundamental_ai:
            if 'ai_analysis' in report_data.get('basic_info', {}):
                final_ai_reports['fundamental'] = report_data['basic_info']['ai_analysis']
        
        if has_company_ai:
            if 'company_analysis' in report_data.get('basic_info', {}):
                final_ai_reports['company'] = report_data['basic_info']['company_analysis']
        
        if has_market_ai:
            if 'ai_analysis' in report_data.get('kline_info', {}):
                final_ai_reports['market'] = report_data['kline_info']['ai_analysis']

        if has_news_ai:
            if 'ai_analysis' in report_data.get('news_data', {}):
                final_ai_reports['news'] = report_data['news_data']['ai_analysis']
        
        if has_chip_ai:
            if 'ai_analysis' in report_data.get('chip_data', {}):
                final_ai_reports['chip'] = report_data['chip_data']['ai_analysis']
        
        if has_comprehensive_ai:
            if 'comprehensive_analysis' in report_data:
                final_ai_reports['comprehensive'] = report_data['comprehensive_analysis']
        
        report_data['ai_reports'] = final_ai_reports
        
        md_content = generate_markdown_report(stock_identity, report_data)
        
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
        error_msg = f"生成报告失败: {str(e)}"
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


def generate_markdown_report(stock_identity: Dict[str, Any], report_data: Dict[str, Any]) -> str:
    """生成Markdown格式报告"""
    stock_code = stock_identity['code']
    stock_name = stock_identity['name']
    market_type = stock_identity['market_name']

    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    md_content = f"""# {stock_name}({stock_code}) 完整分析报告

**市场类型**: {market_type}  
**报告生成时间**: {current_time}  
**生成工具**: {get_full_version()}

"""

    # 综合分析部分
    if 'comprehensive' in report_data['ai_reports']:
        analysis_data = report_data['ai_reports']['comprehensive']
        md_content += """
---

# 🎯 综合分析

"""
        
        if 'analysis_info' in analysis_data:
            info = analysis_data['analysis_info']
            md_content += f"""## 分析信息

- **分析时间**: {info.get('analysis_time', '未知')}
- **数据来源**: {info.get('data_sources_count', 0)}个数据源

"""
        
        if 'report' in analysis_data:
            report_text = analysis_data['report']
            report_time = analysis_data.get('timestamp', '')
            
            md_content += f"""## 🤖 AI综合分析报告

{report_text}

*分析生成时间: {report_time}*

"""

    # 基本信息部分
    basic_info = report_data.get('basic_info', {})
    if 'error' not in basic_info and basic_info:
        md_content += """
---
        
# 📊 基本信息

"""
        
        # 使用统一格式化器
        formatter = get_stock_formatter()
        basic_info_text = formatter.format_basic_info(basic_info, stock_identity)

        md_content += basic_info_text + "\n\n"
        
        md_content += "\n"
        
        if 'company' in report_data['ai_reports']:
            company_report = report_data['ai_reports']['company']
            report_text = company_report['report']
            report_time = company_report.get('timestamp', '')
            
            md_content += f"""## 🏢 AI公司分析

{report_text}

*分析生成时间: {report_time}*

"""
        
        if 'fundamental' in report_data['ai_reports']:
            fundamental_report = report_data['ai_reports']['fundamental']
            report_text = fundamental_report['report']
            report_time = fundamental_report.get('timestamp', '')
            
            md_content += f"""## 🤖 AI基本面分析

{report_text}

*分析生成时间: {report_time}*

"""
    
    # 行情走势部分
    kline_info = report_data.get('kline_info', {})
    if 'error' not in kline_info and kline_info:
        formatter = get_stock_formatter()
        kline_text = formatter.format_kline_data(kline_info)

        #df = pd.DataFrame(kline_info['kline_data']) # later remove
        #last_row = df.iloc[-1]
        
        md_content += """
---

# 📈 行情走势

"""
        
        md_content += kline_text + "\n\n"

        if 'market' in report_data['ai_reports']:
            market_report = report_data['ai_reports']['market']
            report_text = market_report['report']
            report_time = market_report.get('timestamp', '')

            md_content += f"""## 🤖 AI行情分析

{report_text}

*分析生成时间: {report_time}*

"""
    
    # 新闻资讯部分
    news_data = report_data.get('news_data', {})
    if 'error' not in news_data and news_data and news_data.get('news_data'):
        news_list = news_data['news_data']
        md_content += f"""
---

# 📰 新闻资讯

"""
        
        # 使用统一格式化器
        formatter = get_stock_formatter()
        news_text = formatter.format_stock_news_data(news_list, has_content=False)
        
        md_content += news_text + "\n\n"
        
        if 'news' in report_data['ai_reports']:
            news_report = report_data['ai_reports']['news']
            report_text = news_report['report']
            report_time = news_report.get('timestamp', '')
            
            md_content += f"""## 🤖 AI新闻分析

{report_text}

*分析生成时间: {report_time}*

"""
    
    # 筹码分析部分（仅A股）
    chip_data = report_data.get('chip_data', {})
    if 'error' not in chip_data and chip_data:
        md_content += """
---

# 🧮 筹码分析

"""
        
        # 使用统一格式化器
        formatter = get_stock_formatter()
        chip_text = formatter.format_chip_data(chip_data)

        md_content += chip_text + "\n\n"
        
        md_content += "\n"
        
        if 'chip' in report_data['ai_reports']:
            chip_report = report_data['ai_reports']['chip']
            report_text = chip_report['report']
            report_time = chip_report.get('timestamp', '')
            
            md_content += f"""## 🤖 AI筹码分析

{report_text}

*分析生成时间: {report_time}*

"""
        
    md_content += """---

*本报告由XYStock股票分析系统自动生成，仅供参考，不构成任何投资建议*
"""
    
    return md_content
