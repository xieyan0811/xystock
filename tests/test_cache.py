#!/usr/bin/env python3
"""
测试缓存功能的脚本
"""

import sys
import os

# 获取项目根目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

sys.path.insert(0, PROJECT_ROOT)

from providers.stock_data_fetcher import data_manager
from providers.cache_manager import KLineType

def test_cache():
    """测试缓存功能"""
    print('=== 测试缓存功能 ===')
    
    # 第一次获取数据（应该从数据源获取并缓存）
    print('第一次获取数据（从数据源）:')
    data1 = data_manager.get_kline_data('000001', KLineType.DAY, 10)
    print(f'获取到 {len(data1)} 条数据')
    
    print()
    
    # 第二次获取数据（应该从缓存获取）
    print('第二次获取数据（从缓存）:')
    data2 = data_manager.get_kline_data('000001', KLineType.DAY, 10)
    print(f'获取到 {len(data2)} 条数据')
    
    print()
    
    # 强制获取新数据
    print('强制获取新数据（忽略缓存）:')
    data3 = data_manager.get_kline_data('000001', KLineType.DAY, 10, force=True)
    print(f'获取到 {len(data3)} 条数据')
    
    print()
    
    # 查看缓存状态
    print('缓存状态:')
    stats = data_manager.get_cache_stats()
    print(stats)
    
    print()
    
    # 测试清理缓存
    print('清理指定股票缓存:')
    data_manager.clear_cache('000001')
    
    print('清理后缓存状态:')
    stats = data_manager.get_cache_stats()
    print(stats)

if __name__ == "__main__":
    test_cache()
