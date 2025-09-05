import os
import tempfile
import subprocess
import shutil

try:
    import pypandoc
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

def check_weasyprint_available():
    """检查weasyprint是否可用"""
    try:
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
PDF_SUPPORT_AVAILABLE = PANDOC_AVAILABLE and WEASYPRINT_AVAILABLE


def _clean_markdown_for_pandoc(content):
    """清理Markdown内容避免pandoc YAML解析问题"""
    if not content:
        return ""

    content = content.strip()

    # 处理可能被误认为YAML的内容
    lines = content.split('\n')
    if lines and (lines[0].startswith('---') or lines[0].startswith('...')):
        content = '\n' + content

    # 保护表格分隔符，然后替换其他问题字符
    content = content.replace('|------|------|', '|TABLESEP|TABLESEP|')
    content = content.replace('|------|', '|TABLESEP|')
    content = content.replace('---', '—')
    content = content.replace('...', '…')
    content = content.replace('|TABLESEP|TABLESEP|', '|------|------|')
    content = content.replace('|TABLESEP|', '|------|')

    # 清理特殊引号
    content = content.replace('"', '"')
    content = content.replace('"', '"')
    content = content.replace(''', "'")
    content = content.replace(''', "'")

    if not content.startswith('#'):
        content = '# 分析报告\n\n' + content

    return content


def generate_pdf_report(md_content):
    """将Markdown内容转换为PDF"""
    
    print("📊 开始生成PDF文档...")
    
    if not PANDOC_AVAILABLE:
        print("❌ Pandoc不可用")
        raise Exception("Pandoc不可用，无法生成PDF文档。请安装pandoc或使用Markdown格式导出。")

    print(f"✅ Markdown内容生成完成，长度: {len(md_content)} 字符")

    pdf_engines = [
        ('weasyprint', '现代HTML转PDF引擎'),
        (None, '使用pandoc默认引擎')
    ]

    last_error = None

    for engine_info in pdf_engines:
        engine, description = engine_info
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                output_file = tmp_file.name

            extra_args = ['--from=markdown-yaml_metadata_block']

            if engine:
                extra_args.append(f'--pdf-engine={engine}')
                print(f"🔧 使用PDF引擎: {engine}")
            else:
                print(f"🔧 使用默认PDF引擎")

            print(f"🔧 PDF参数: {extra_args}")

            # 清理内容避免YAML解析问题
            cleaned_content = _clean_markdown_for_pandoc(md_content)

            pypandoc.convert_text(
                cleaned_content,
                'pdf',
                format='markdown',
                outputfile=output_file,
                extra_args=extra_args
            )

            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                with open(output_file, 'rb') as f:
                    pdf_content = f.read()

                os.unlink(output_file)

                print(f"✅ PDF生成成功，使用引擎: {engine or '默认'}")
                return pdf_content
            else:
                raise Exception("PDF文件生成失败或为空")

        except Exception as e:
            last_error = str(e)
            print(f"PDF引擎 {engine or '默认'} 失败: {e}")

            try:
                if 'output_file' in locals() and os.path.exists(output_file):
                    os.unlink(output_file)
            except:
                pass

            continue

    # 所有引擎都失败时的错误信息
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
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            output_file = tmp_file.name

        extra_args = [
            '--from=markdown-yaml_metadata_block',
            '--reference-doc=/app/templates/reference.docx' if os.path.exists('/app/templates/reference.docx') else None
        ]
        
        extra_args = [arg for arg in extra_args if arg is not None]

        print(f"🔧 Word转换参数: {extra_args}")

        # 清理内容避免YAML解析问题
        cleaned_content = _clean_markdown_for_pandoc(md_content)

        pypandoc.convert_text(
            cleaned_content,
            'docx',
            format='markdown',
            outputfile=output_file,
            extra_args=extra_args
        )

        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            with open(output_file, 'rb') as f:
                docx_content = f.read()

            os.unlink(output_file)

            print(f"✅ Word文档生成成功")
            return docx_content
        else:
            raise Exception("Word文档生成失败或为空")

    except Exception as e:
        error_msg = str(e)
        print(f"Word文档生成失败: {error_msg}")

        try:
            if 'output_file' in locals() and os.path.exists(output_file):
                os.unlink(output_file)
        except:
            pass

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


def generate_html_report(md_content):
    """将Markdown内容转换为HTML"""
    
    print("🌐 开始生成HTML文档...")
    
    if not PANDOC_AVAILABLE:
        print("❌ Pandoc不可用")
        raise Exception("Pandoc不可用，无法生成HTML文档。请安装pandoc或使用Markdown格式导出。")

    print(f"✅ Markdown内容生成完成，长度: {len(md_content)} 字符")

    try:
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_file:
            output_file = tmp_file.name

        extra_args = [
            '--from=markdown-yaml_metadata_block',
            '--standalone',
            '--css=/app/templates/style.css' if os.path.exists('/app/templates/style.css') else None,
            '--metadata', 'title=分析报告',
            '--template=/app/templates/template.html' if os.path.exists('/app/templates/template.html') else None
        ]
        
        extra_args = [arg for arg in extra_args if arg is not None]

        print(f"🔧 HTML转换参数: {extra_args}")

        cleaned_content = _clean_markdown_for_pandoc(md_content)

        pypandoc.convert_text(
            cleaned_content,
            'html',
            format='markdown',
            outputfile=output_file,
            extra_args=extra_args
        )

        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            with open(output_file, 'rb') as f:
                html_content = f.read()

            os.unlink(output_file)

            print(f"✅ HTML文档生成成功")
            return html_content
        else:
            raise Exception("HTML文档生成失败或为空")

    except Exception as e:
        error_msg = str(e)
        print(f"HTML文档生成失败: {error_msg}")

        try:
            if 'output_file' in locals() and os.path.exists(output_file):
                os.unlink(output_file)
        except:
            pass

        detailed_error = f"""HTML文档生成失败: {error_msg}

可能的解决方案:
1. 确保pandoc已正确安装:
   Windows: choco install pandoc
   macOS: brew install pandoc
   Linux: sudo apt-get install pandoc

2. 检查系统权限，确保可以创建临时文件

3. 使用Markdown格式导出作为替代方案
"""
        raise Exception(detailed_error)
