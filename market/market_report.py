import sys
import os

# 添加路径以便导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.report_utils import generate_pdf_report, generate_docx_report, generate_markdown_file, generate_html_report
from version import get_full_version


def write_market_report(index_name="上证指数", format_type="pdf", has_ai_analysis=False, user_opinion=""):
    """生成完整的市场分析报告（优化版本，复用AI分析数据）"""
    try:
        from market.market_data_tools import get_market_tools
        
        market_tools = get_market_tools()
        
        # 获取AI分析（如果需要）
        ai_analysis = None
        if has_ai_analysis:
            ai_analysis = market_tools.get_ai_analysis(
                use_cache=True, 
                index_name=index_name,
                force_regenerate=bool(user_opinion.strip()),
                user_opinion=user_opinion
            )
        
        # 获取综合市场数据（两种情况都需要）
        comprehensive_report = market_tools.get_comprehensive_market_report(
            use_cache=True, 
            index_name=index_name
        )
        
        # 获取当前指数数据
        current_indices = market_tools.get_current_indices(use_cache=True)
        
        # 获取焦点指数数据
        focus_index_data = None
        if index_name in current_indices.get('indices_dict', {}):
            focus_index_data = current_indices['indices_dict'][index_name]
        
        # 构建报告数据
        report_data = {
            'ai_analysis': ai_analysis,
            'technical_indicators': comprehensive_report.get('technical_indicators', {}),
            'sentiment_indicators': comprehensive_report.get('sentiment_indicators', {}),
            'valuation_indicators': comprehensive_report.get('valuation_indicators', {}),
            'money_flow_indicators': comprehensive_report.get('money_flow_indicators', {}),
            'margin_detail': comprehensive_report.get('margin_detail', {}),
            'market_news_data': comprehensive_report.get('market_news_data', []),
            'current_indices': current_indices,
            'focus_index_data': focus_index_data
        }
        
        from market.market_formatters import MarketTextFormatter
        
        md_content = MarketTextFormatter.format_data_for_report(
            index_name, 
            report_data, 
            get_full_version(),
            use_gray_section=(format_type == "markdown")
        )
        
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
