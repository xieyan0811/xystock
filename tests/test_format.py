"""
测试数字格式化工具
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.format_utils import format_large_number, format_volume, format_market_value, format_price, format_percentage, format_change

def test_format_functions():
    print("测试数字格式化函数：")
    print()
    
    # 测试 format_large_number
    print("=== format_large_number 测试 ===")
    test_numbers = [1234, 12345, 123456, 1234567, 12345678, 123456789, 1234567890, 12345678901]
    for num in test_numbers:
        print(f"{num:>12} -> {format_large_number(num)}")
    print()
    
    # 测试 format_market_value
    print("=== format_market_value 测试 ===")
    market_values = [1500000000, 2340000000, 45600000000, 123400000000]
    for val in market_values:
        print(f"原值: {val:>12} -> {format_market_value(val)}")
    print()
    
    # 测试 format_volume
    print("=== format_volume 测试 ===")
    volumes = [12345, 1234567, 123456789, 1234567890]
    for vol in volumes:
        print(f"原值: {vol:>10} -> {format_volume(vol)}")
    print()
    
    # 测试 format_price
    print("=== format_price 测试 ===")
    prices = [12.34, 123.456, 0.05, 1234.5678]
    for price in prices:
        print(f"原值: {price:>8} -> {format_price(price)}")
    print()
    
    # 测试 format_percentage
    print("=== format_percentage 测试 ===")
    percentages = [12.34, 5.67, 0.05, 123.45]
    for pct in percentages:
        print(f"原值: {pct:>6} -> {format_percentage(pct)}")
    print()
    
    # 测试 format_change
    print("=== format_change 测试 ===")
    changes = [(1.23, 2.45), (-0.56, -1.12), (0, 0), (5.67, 3.21)]
    for change, pct in changes:
        print(f"原值: {change:>6}, {pct:>6}% -> {format_change(change, pct)}")

if __name__ == "__main__":
    test_format_functions()
