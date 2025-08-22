#!/usr/bin/env python3
"""
UI功能测试脚本
测试股票数据提供者的基本功能
"""

from ui.stock_provider import stock_data_provider
from ui.config import MARKET_TYPES, STOCK_CODE_EXAMPLES

def test_stock_provider():
    """测试股票数据提供者"""
    
    print("=" * 60)
    print("🧪 UI 股票数据提供者功能测试")
    print("=" * 60)
    
    # 测试各种市场类型
    for market_type in MARKET_TYPES:
        print(f"\n📊 测试 {market_type} 数据获取...")
        
        # 获取该市场的示例代码
        if market_type in STOCK_CODE_EXAMPLES:
            test_codes = STOCK_CODE_EXAMPLES[market_type][:2]  # 取前两个测试
        else:
            test_codes = ["TEST001"]
        
        for code in test_codes:
            print(f"\n🔍 查询代码: {code}")
            try:
                result = stock_data_provider.get_stock_info(code, market_type)
                print("✅ 查询成功!")
                print("-" * 40)
                print(result)
                print("-" * 40)
            except Exception as e:
                print(f"❌ 查询失败: {e}")
    
    print("\n🎉 测试完成!")

def main():
    """主函数"""
    test_stock_provider()

if __name__ == "__main__":
    main()
