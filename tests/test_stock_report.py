#!/usr/bin/env python3
"""
股票报告测试
"""
import sys
import os
import argparse

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from providers.stock_report import generate_stock_report


def test_stock_report(stock_code="600519", stock_name="贵州茅台", market_type="A股", 
                     format_type="markdown", use_ai=False):
    """测试生成股票报告"""
    print(f"🧪 测试股票报告生成 - {stock_name}({stock_code})...")
    if use_ai:
        print("🤖 启用AI分析模式")
    
    try:
        # AI分析开关
        has_fundamental_ai = use_ai
        has_market_ai = use_ai
        has_news_ai = use_ai
        has_chip_ai = use_ai and market_type not in ["港股", "指数"]  # 港股和指数不支持筹码分析
        has_comprehensive_ai = use_ai
        
        report = generate_stock_report(
            stock_code=stock_code,
            market_type=market_type,
            format_type=format_type,
            has_fundamental_ai=has_fundamental_ai,
            has_market_ai=has_market_ai,
            has_news_ai=has_news_ai,
            has_chip_ai=has_chip_ai,
            has_comprehensive_ai=has_comprehensive_ai
        )
        
        # 生成文件名
        if format_type == "markdown":
            ext = "md"
        else:
            ext = format_type
        
        ai_suffix = "_ai" if use_ai else ""
        filename = f"test_stock_report_{stock_name}_{stock_code}{ai_suffix}.{ext}"
        path = os.path.join(project_root, "reports", filename)
        
        # 保存报告
        mode = "wb" if isinstance(report, bytes) else "w"
        encoding = None if isinstance(report, bytes) else "utf-8"
        
        with open(path, mode, encoding=encoding) as f:
            f.write(report)
            
        print(f"✅ 报告生成成功，大小: {len(report)} 字节")
        print(f"📄 报告已保存: {path}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="股票报告测试程序")
    parser.add_argument("--stock-code", default="600519", help="股票代码 (默认: 600519)")
    parser.add_argument("--stock-name", default="贵州茅台", help="股票名称 (默认: 贵州茅台)")
    parser.add_argument("--market-type", default="A股", choices=["A股", "港股", "指数"], help="市场类型 (默认: A股)")
    parser.add_argument("--format", default="markdown", choices=["pdf", "docx", "markdown"], help="报告格式 (默认: markdown)")
    parser.add_argument("--use-ai", action="store_true", help="启用所有AI分析功能")
    
    args = parser.parse_args()
    
    test_stock_report(
        stock_code=args.stock_code,
        stock_name=args.stock_name,
        market_type=args.market_type,
        format_type=args.format,
        use_ai=args.use_ai
    )


if __name__ == "__main__":
    main()
