import sys
import os
import datetime
import pandas as pd
import tempfile

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from providers.stock_data_tools import get_stock_tools
from utils.format_utils import format_volume, format_market_value, format_price, format_percentage, format_change
from providers.stock_utils import get_stock_name

# 导入PDF生成相关库
try:
    import pypandoc
    # 检查pandoc是否可用
    try:
        pypandoc.get_pandoc_version()
        PANDOC_AVAILABLE = True
        print("✅ pandoc可用")
    except OSError:
        print("⚠️ 未找到pandoc，正在尝试自动下载...")
        try:
            pypandoc.download_pandoc()
            PANDOC_AVAILABLE = True
            print("✅ pandoc下载成功！")
        except Exception as download_error:
            print(f"❌ pandoc下载失败: {download_error}")
            PANDOC_AVAILABLE = False
except ImportError:
    PANDOC_AVAILABLE = False
    print("❌ pypandoc未安装，PDF功能不可用")

# 检查weasyprint是否可用
def check_weasyprint_available():
    """检查weasyprint是否可用"""
    try:
        import shutil
        import subprocess
        
        if shutil.which('weasyprint'):
            try:
                result = subprocess.run(['weasyprint', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ weasyprint命令行工具可用")
                    return True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
        
        print("❌ weasyprint不可用")
        return False
    except Exception as e:
        print(f"❌ 检查weasyprint时出错: {e}")
        return False

WEASYPRINT_AVAILABLE = check_weasyprint_available()

# PDF支持状态
PDF_SUPPORT_AVAILABLE = PANDOC_AVAILABLE and WEASYPRINT_AVAILABLE


def _clean_markdown_for_pandoc(content):
    """清理Markdown内容避免pandoc YAML解析问题"""
    if not content:
        return ""

    # 确保内容不以可能被误认为YAML的字符开头
    content = content.strip()

    # 如果第一行看起来像YAML分隔符，添加空行
    lines = content.split('\n')
    if lines and (lines[0].startswith('---') or lines[0].startswith('...')):
        content = '\n' + content

    # 替换可能导致YAML解析问题的字符序列，但保护表格分隔符
    # 先保护表格分隔符
    content = content.replace('|------|------|', '|TABLESEP|TABLESEP|')
    content = content.replace('|------|', '|TABLESEP|')

    # 然后替换其他的三连字符
    content = content.replace('---', '—')  # 替换三个连字符
    content = content.replace('...', '…')  # 替换三个点

    # 恢复表格分隔符
    content = content.replace('|TABLESEP|TABLESEP|', '|------|------|')
    content = content.replace('|TABLESEP|', '|------|')

    # 清理特殊引号
    content = content.replace('"', '"')  # 左双引号
    content = content.replace('"', '"')  # 右双引号
    content = content.replace(''', "'")  # 左单引号
    content = content.replace(''', "'")  # 右单引号

    # 确保内容以标准Markdown标题开始
    if not content.startswith('#'):
        content = '# 分析报告\n\n' + content

    return content


def generate_complete_report_safe(stock_code, market_type, format_type="pdf",
                                 has_fundamental_ai=False, has_market_ai=False, 
                                 has_news_ai=False, has_chip_ai=False, 
                                 has_comprehensive_ai=False):
    """
    生成完整的股票分析报告（安全版本，完全独立于Streamlit）
    
    Args:
        stock_code: 股票代码
        market_type: 市场类型
        format_type: 输出格式 ("markdown"、"pdf" 或 "docx")
        has_fundamental_ai: 是否包含基本面AI分析
        has_market_ai: 是否包含行情AI分析
        has_news_ai: 是否包含新闻AI分析
        has_chip_ai: 是否包含筹码AI分析
        has_comprehensive_ai: 是否包含综合AI分析
    
    Returns:
        报告内容字符串(markdown)或字节数据(pdf/docx)
    """
    try:
        stock_tools = get_stock_tools()

        # 获取股票名称
        stock_name = get_stock_name(stock_code, 'index' if market_type == "指数" else 'stock')
        
        # 收集所有数据
        report_data = {}
        
        # 1. 基本信息（仅当界面有AI分析时才包含AI分析）
        try:
            basic_info = stock_tools.get_stock_basic_info(stock_code, use_cache=True, include_ai_analysis=has_fundamental_ai)
            if 'error' not in basic_info and basic_info:
                report_data['basic_info'] = basic_info
        except Exception as e:
            report_data['basic_info'] = {'error': str(e)}
        
        # 2. 行情数据（仅当界面有AI分析时才包含AI分析）
        try:
            kline_info = stock_tools.get_stock_kline_data(stock_code, period=160, use_cache=True, include_ai_analysis=has_market_ai)
            if 'error' not in kline_info and kline_info:
                report_data['market_data'] = kline_info
        except Exception as e:
            report_data['market_data'] = {'error': str(e)}
        
        # 3. 新闻数据（仅当界面有AI分析时才包含AI分析）
        try:
            news_info = stock_tools.get_stock_news_data(stock_code, use_cache=True, include_ai_analysis=has_news_ai)
            if 'error' not in news_info and news_info:
                report_data['news_data'] = news_info
        except Exception as e:
            report_data['news_data'] = {'error': str(e)}
        
        # 4. 筹码数据（仅A股和基金，仅当界面有AI分析时才包含AI分析）
        if market_type not in ["港股", "指数"]:
            try:
                chip_data = stock_tools.get_stock_chip_data(stock_code, use_cache=True, include_ai_analysis=has_chip_ai)
                if 'error' not in chip_data and chip_data:
                    report_data['chip_data'] = chip_data
            except Exception as e:
                report_data['chip_data'] = {'error': str(e)}
        
        # 5. 综合分析（仅当界面有AI分析时才包含）
        if has_comprehensive_ai:
            try:
                comprehensive_analysis = stock_tools.get_comprehensive_ai_analysis(stock_code, "", use_cache=True)
                if 'error' not in comprehensive_analysis:
                    report_data['comprehensive_analysis'] = comprehensive_analysis
            except Exception as e:
                # 综合分析失败不影响整体报告生成
                pass
                
        final_ai_reports = {}
        
        # 基本面分析
        if has_fundamental_ai:
            if 'ai_analysis' in report_data.get('basic_info', {}):
                final_ai_reports['fundamental'] = report_data['basic_info']['ai_analysis']
        
        # 行情分析
        if has_market_ai:
            if 'ai_analysis' in report_data.get('market_data', {}):
                final_ai_reports['market'] = report_data['market_data']['ai_analysis']
        
        # 新闻分析
        if has_news_ai:
            if 'ai_analysis' in report_data.get('news_data', {}):
                final_ai_reports['news'] = report_data['news_data']['ai_analysis']
        
        # 筹码分析
        if has_chip_ai:
            if 'ai_analysis' in report_data.get('chip_data', {}):
                final_ai_reports['chip'] = report_data['chip_data']['ai_analysis']
        
        # 综合分析
        if has_comprehensive_ai:
            if 'comprehensive_analysis' in report_data:
                final_ai_reports['comprehensive'] = report_data['comprehensive_analysis']
        
        report_data['ai_reports'] = final_ai_reports
        
        #print('@@@@@@@@@@@@@@@@@@ report_data', report_data)
        
        # 生成markdown内容
        md_content = generate_markdown_report(stock_code, stock_name, market_type, report_data)
        
        # 根据格式类型返回相应内容
        if format_type == "pdf":
            return generate_pdf_report(md_content)
        elif format_type == "docx":
            return generate_docx_report(md_content)
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
        elif format_type == "markdown":
            return generate_markdown_file(f"# 错误\n\n{error_msg}")
        else:
            return f"# 错误\n\n{error_msg}"


def generate_pdf_report(md_content):
    """将Markdown内容转换为PDF"""
    
    print("📊 开始生成PDF文档...")
    
    if not PANDOC_AVAILABLE:
        print("❌ Pandoc不可用")
        raise Exception("Pandoc不可用，无法生成PDF文档。请安装pandoc或使用Markdown格式导出。")

    print(f"✅ Markdown内容生成完成，长度: {len(md_content)} 字符")

    pdf_engines = [
        ('weasyprint', '现代HTML转PDF引擎'),
        (None, '使用pandoc默认引擎')  # 不指定引擎，让pandoc自己选择
    ]

    last_error = None

    for engine_info in pdf_engines:
        engine, description = engine_info
        try:
            # 创建临时文件用于PDF输出
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                output_file = tmp_file.name

            # 使用禁用YAML解析的参数
            extra_args = ['--from=markdown-yaml_metadata_block']

            # 如果指定了引擎，添加引擎参数
            if engine:
                extra_args.append(f'--pdf-engine={engine}')
                print(f"🔧 使用PDF引擎: {engine}")
            else:
                print(f"🔧 使用默认PDF引擎")

            print(f"🔧 PDF参数: {extra_args}")

            # 清理内容避免YAML解析问题
            cleaned_content = _clean_markdown_for_pandoc(md_content)

            # 使用pypandoc将markdown转换为PDF - 禁用YAML解析
            pypandoc.convert_text(
                cleaned_content,
                'pdf',
                format='markdown',  # 基础markdown格式
                outputfile=output_file,
                extra_args=extra_args
            )

            # 检查文件是否生成且有内容
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                # 读取生成的PDF文件
                with open(output_file, 'rb') as f:
                    pdf_content = f.read()

                # 清理临时文件
                os.unlink(output_file)

                print(f"✅ PDF生成成功，使用引擎: {engine or '默认'}")
                return pdf_content
            else:
                raise Exception("PDF文件生成失败或为空")

        except Exception as e:
            last_error = str(e)
            print(f"PDF引擎 {engine or '默认'} 失败: {e}")

            # 清理可能存在的临时文件
            try:
                if 'output_file' in locals() and os.path.exists(output_file):
                    os.unlink(output_file)
            except:
                pass

            continue

    # 如果所有引擎都失败，提供详细的错误信息和解决方案
    error_msg = f"""PDF生成失败，最后错误: {last_error}

可能的解决方案:
1. 安装wkhtmltopdf (推荐):
   Windows: choco install wkhtmltopdf
   macOS: brew install wkhtmltopdf
   Linux: sudo apt-get install wkhtmltopdf

2. 安装LaTeX:
   Windows: choco install miktex
   macOS: brew install mactex
   Linux: sudo apt-get install texlive-full

3. 使用Markdown格式导出作为替代方案
"""
    raise Exception(error_msg)


def generate_docx_report(md_content):
    """将Markdown内容转换为Word文档"""
    
    print("📄 开始生成Word文档...")
    
    if not PANDOC_AVAILABLE:
        print("❌ Pandoc不可用")
        raise Exception("Pandoc不可用，无法生成Word文档。请安装pandoc或使用Markdown格式导出。")

    print(f"✅ Markdown内容生成完成，长度: {len(md_content)} 字符")

    try:
        # 创建临时文件用于Word输出
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            output_file = tmp_file.name

        # 使用禁用YAML解析的参数
        extra_args = [
            '--from=markdown-yaml_metadata_block',
            '--reference-doc=/app/templates/reference.docx' if os.path.exists('/app/templates/reference.docx') else None
        ]
        
        # 过滤掉None值
        extra_args = [arg for arg in extra_args if arg is not None]

        print(f"🔧 Word转换参数: {extra_args}")

        # 清理内容避免YAML解析问题
        cleaned_content = _clean_markdown_for_pandoc(md_content)

        # 使用pypandoc将markdown转换为Word文档
        pypandoc.convert_text(
            cleaned_content,
            'docx',
            format='markdown',
            outputfile=output_file,
            extra_args=extra_args
        )

        # 检查文件是否生成且有内容
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            # 读取生成的Word文件
            with open(output_file, 'rb') as f:
                docx_content = f.read()

            # 清理临时文件
            os.unlink(output_file)

            print(f"✅ Word文档生成成功")
            return docx_content
        else:
            raise Exception("Word文档生成失败或为空")

    except Exception as e:
        error_msg = str(e)
        print(f"Word文档生成失败: {error_msg}")

        # 清理可能存在的临时文件
        try:
            if 'output_file' in locals() and os.path.exists(output_file):
                os.unlink(output_file)
        except:
            pass

        # 提供详细的错误信息和解决方案
        detailed_error = f"""Word文档生成失败: {error_msg}

可能的解决方案:
1. 确保pandoc已正确安装:
   Windows: choco install pandoc
   macOS: brew install pandoc
   Linux: sudo apt-get install pandoc

2. 检查系统权限，确保可以创建临时文件

3. 使用Markdown或PDF格式导出作为替代方案
"""
        raise Exception(detailed_error)


def generate_markdown_file(md_content):
    """将Markdown内容转换为文件字节数据"""
    
    print("📝 开始生成Markdown文件...")
    
    try:
        # 将字符串内容编码为UTF-8字节数据
        markdown_bytes = md_content.encode('utf-8')
        
        print(f"✅ Markdown文件生成成功，大小: {len(markdown_bytes)} 字节")
        return markdown_bytes
        
    except Exception as e:
        error_msg = str(e)
        print(f"Markdown文件生成失败: {error_msg}")
        
        # 生成错误信息的字节数据
        error_content = f"# Markdown文件生成失败\n\n{error_msg}\n"
        return error_content.encode('utf-8')


def generate_markdown_report(stock_code, stock_name, market_type, report_data):
    """生成Markdown格式报告"""
    
    md_content = f"""# {stock_name}({stock_code}) 完整分析报告

**市场类型**: {market_type}  
**报告生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    # 1. 基本信息部分
    basic_info = report_data.get('basic_info', {})
    if 'error' not in basic_info and basic_info:
        md_content += """# 📊 基本信息

"""
        
        metrics = [
            ('股票名称', basic_info.get('name', '')),
            ('所属行业', basic_info.get('industry', '')),
            ('当前价格', format_price(basic_info.get('current_price', 0))),
            ('涨跌幅', format_change(basic_info.get('change', 0), basic_info.get('change_percent', 0))),
            ('总市值', format_market_value(basic_info.get('total_market_value', 0))),
            ('流通市值', format_market_value(basic_info.get('circulating_market_value', 0))),
            ('成交量', format_volume(basic_info.get('volume', 0))),
            ('市盈率', basic_info.get('pe_ratio', '')),
            ('市净率', basic_info.get('pb_ratio', '')),
            ('ROE', basic_info.get('roe', ''))
        ]
        
        for label, value in metrics:
            if value:
                md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
        
        # AI基本面分析
        if 'fundamental' in report_data['ai_reports']:
            fundamental_report = report_data['ai_reports']['fundamental']
            report_text = fundamental_report['report']
            report_time = fundamental_report.get('timestamp', '')
            
            md_content += f"""## 🤖 AI基本面分析

{report_text}

*分析生成时间: {report_time}*

"""
    
    # 2. 行情走势部分
    market_data = report_data.get('market_data', {})
    if 'error' not in market_data and market_data and market_data.get('kline_data'):
        df = pd.DataFrame(market_data['kline_data'])
        last_row = df.iloc[-1]
        
        md_content += """
---

# 📈 行情走势

## 最新价格信息

"""
        
        price_metrics = [
            ('开盘价', format_price(last_row['open'])),
            ('最高价', format_price(last_row['high'])),
            ('最低价', format_price(last_row['low'])),
            ('收盘价', format_price(last_row['close'])),
            ('成交量', format_volume(last_row['volume']))
        ]
        
        for label, value in price_metrics:
            md_content += f"- **{label}**: {value}\n"
        
        # 技术指标
        indicators = market_data.get('indicators', {})
        if indicators:
            md_content += "\n## 技术指标\n\n"
            for indicator_name, indicator_data in indicators.items():
                if isinstance(indicator_data, dict) and 'current' in indicator_data:
                    value = str(indicator_data['current'])
                else:
                    value = str(indicator_data)
                md_content += f"- **{indicator_name}**: {value}\n"
        
        md_content += "\n"
        
        # AI行情分析
        if 'market' in report_data['ai_reports']:
            market_report = report_data['ai_reports']['market']
            report_text = market_report['report']
            report_time = market_report.get('timestamp', '')
            
            md_content += f"""## 🤖 AI行情分析

{report_text}

*分析生成时间: {report_time}*

"""
    
    # 3. 新闻资讯部分
    news_data = report_data.get('news_data', {})
    if 'error' not in news_data and news_data and news_data.get('news_data'):
        news_list = news_data['news_data']
        md_content += f"""
---

# 📰 新闻资讯

共获取到 {len(news_list)} 条相关新闻

"""
        
        for i, news in enumerate(news_list[:10], 1):  # 只显示前10条
            title = news.get('新闻标题', '')
            time = news.get('发布时间', '')
            #content = news.get('新闻内容', '')
            url = news.get('新闻链接', '')
            
            md_content += f"#### {i}. {title}\n\n"
            md_content += f"**发布时间**: {time}\n\n"
            
            #if content:
            #    truncated_content = content[:300] + '...' if len(content) > 300 else content
            #    md_content += f"{truncated_content}\n\n"
            
            if url:
                md_content += f"[阅读原文]({url})\n\n"
            
            md_content += "---\n\n"
        
        # AI新闻分析
        if 'news' in report_data['ai_reports']:
            news_report = report_data['ai_reports']['news']
            report_text = news_report['report']
            report_time = news_report.get('timestamp', '')
            
            md_content += f"""## 🤖 AI新闻分析

{report_text}

*分析生成时间: {report_time}*

"""
    
    # 4. 筹码分析部分（仅A股）
    chip_data = report_data.get('chip_data', {})
    if 'error' not in chip_data and chip_data:
        md_content += """
---

# 🧮 筹码分析

"""
        
        chip_metrics = [
            ('获利比例', format_percentage(chip_data['profit_ratio'] * 100)),
            ('平均成本', f"{format_price(chip_data['avg_cost'])}元"),
            ('90%成本区间', f"{format_price(chip_data['cost_90_low'])}-{format_price(chip_data['cost_90_high'])}"),
            ('70%成本区间', f"{format_price(chip_data['cost_70_low'])}-{format_price(chip_data['cost_70_high'])}"),
            ('支撑位', f"{format_price(chip_data['support_level'])}元"),
            ('阻力位', f"{format_price(chip_data['resistance_level'])}元"),
            ('成本中枢', f"{format_price(chip_data['cost_center'])}元")
        ]
        
        for label, value in chip_metrics:
            md_content += f"- **{label}**: {value}\n"
        
        md_content += "\n"
        
        # AI筹码分析
        if 'chip' in report_data['ai_reports']:
            chip_report = report_data['ai_reports']['chip']
            report_text = chip_report['report']
            report_time = chip_report.get('timestamp', '')
            
            md_content += f"""## 🤖 AI筹码分析

{report_text}

*分析生成时间: {report_time}*

"""
    
    # 5. 综合分析部分
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
    
    # 结束
    md_content += """---

*本报告由XYStock股票分析系统自动生成，仅供参考，不构成任何投资建议*
"""
    
    return md_content