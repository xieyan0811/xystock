#!/usr/bin/env python3
"""
市场报告测试
"""
import sys
import os
import argparse

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from providers.market_report import generate_market_report


def test_market_report(index_name="上证指数", format_type="markdown", has_ai_analysis=True, user_opinion=None):
    """测试生成市场报告"""
    print(f"🧪 测试市场报告生成 - {index_name}...")
    if has_ai_analysis:
        print("🤖 启用AI分析模式")
    
    try:
        default_opinion = "当前市场处于调整期，建议关注政策面变化"
        
        report = generate_market_report(
            index_name=index_name,
            format_type=format_type, 
            has_ai_analysis=has_ai_analysis,
            user_opinion=user_opinion or default_opinion
        )
        
        if format_type == "markdown":
            ext = "md"
        else:
            ext = format_type
        
        ai_suffix = "_ai" if has_ai_analysis else ""
        filename = f"market_report_{index_name}{ai_suffix}.{ext}"
        path = os.path.join(project_root, "reports", filename)
        
        mode = "wb" if isinstance(report, bytes) else "w"
        encoding = None if isinstance(report, bytes) else "utf-8"
        
        with open(path, mode, encoding=encoding) as f:
            f.write(report)
            
        print(f"✅ 报告生成成功，大小: {len(report)} 字节")
        print(f"📄 报告已保存: {path}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="市场报告测试程序")
    parser.add_argument("--index-name", default="上证指数", help="指数名称 (默认: 上证指数)")
    parser.add_argument("--format", default="markdown", choices=["pdf", "docx", "markdown", "html"], help="报告格式 (默认: markdown)")
    parser.add_argument("--disable-ai", action="store_true", help="禁用AI分析功能")
    parser.add_argument("--user-opinion", help="用户观点 (可选)")
    
    args = parser.parse_args()
    
    test_market_report(
        index_name=args.index_name,
        format_type=args.format,
        has_ai_analysis=not args.disable_ai,
        user_opinion=args.user_opinion
    )


if __name__ == "__main__":
    main()
