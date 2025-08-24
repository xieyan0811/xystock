#!/usr/bin/env python3
"""
测试融资融券数据获取功能
"""

import sys
import os
sys.path.append('/app')

from providers.market_tools import get_market_tools

def test_margin_data():
    """测试融资融券数据获取"""
    print("=" * 60)
    print("测试融资融券数据获取（沪深两市）")
    print("=" * 60)
    
    market = get_market_tools()
    
    # 测试市场情绪指标中的融资融券数据
    print("\n1. 测试市场情绪指标中的融资融券数据...")
    sentiment = market.get_market_sentiment_indicators()
    
    if sentiment:
        print(f"   融资融券余额: {sentiment.get('margin_balance', 0):.2f}亿")
        print(f"   融资余额: {sentiment.get('margin_buy_balance', 0):.2f}亿")
        print(f"   融券余额: {sentiment.get('margin_sell_balance', 0):.2f}亿")
        print(f"   上交所融资余额: {sentiment.get('margin_sh_buy', 0):.2f}亿")
        print(f"   深交所融资余额: {sentiment.get('margin_sz_buy', 0):.2f}亿")
        print(f"   数据日期: {sentiment.get('margin_date', 'N/A')}")
    
    # 测试详细融资融券数据
    print("\n2. 测试详细融资融券数据...")
    detailed = market.get_detailed_margin_data()
    
    if detailed:
        print(f"   两市合计融资余额: {detailed.get('margin_buy_balance', 0):.2f}亿")
        print(f"   两市合计周变化: {detailed.get('weekly_change', 0):+.2f}亿")
        print(f"   变化比例: {detailed.get('change_ratio', 0):+.2f}%")
        
        if 'shanghai' in detailed and detailed['shanghai']:
            sh = detailed['shanghai']
            print(f"   上交所融资余额: {sh.get('margin_buy_balance', 0):.2f}亿")
            print(f"   上交所周变化: {sh.get('weekly_change', 0):+.2f}亿")
        
        if 'shenzhen' in detailed and detailed['shenzhen']:
            sz = detailed['shenzhen']
            print(f"   深交所融资余额: {sz.get('margin_buy_balance', 0):.2f}亿")
            print(f"   深交所周变化: {sz.get('weekly_change', 0):+.2f}亿")
        
        print(f"   数据日期: {detailed.get('latest_date', 'N/A')}")

if __name__ == "__main__":
    test_margin_data()
