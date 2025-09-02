#!/usr/bin/env python3
"""
市场报告测试
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from providers.market_report import generate_market_report


def test_market_ai_report():
    """测试生成带AI分析的市场报告"""
    print("🧪 测试市场AI报告生成...")
    
    try:
        report = generate_market_report(
            index_name="上证指数",
            format_type="markdown", 
            has_ai_analysis=True,
            user_opinion="当前市场处于调整期，建议关注政策面变化"
        )
        
        path = os.path.join(project_root, "reports", "test_market_ai_report.md")
        with open(path, "wb") as f:
            f.write(report)
            
        print(f"✅ 报告生成成功，大小: {len(report)} 字节")
        print(f"📄 报告已保存: {path}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    test_market_ai_report()
