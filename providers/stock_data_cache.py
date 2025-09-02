"""
股票数据缓存管理器
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


class StockDataCache:
    """股票数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_file = os.path.join(project_dir, cache_dir, "stock_data.json")
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        self.cache_configs = {
            'basic_info': {'expire_minutes': 5, 'description': '股票基本信息'},
            'technical_indicators': {'expire_minutes': 30, 'description': '技术指标和风险指标'},
            'news_data': {'expire_minutes': 60, 'description': '新闻资讯数据'},
            'chip_data': {'expire_minutes': 1440, 'description': '筹码分析数据'},
            'ai_analysis': {'expire_minutes': 180, 'description': 'AI分析报告'},
        }
    
    def _make_json_safe(self, obj):
        """对象转为JSON安全格式"""
        import numpy as np
        import pandas as pd
        
        if isinstance(obj, dict):
            return {key: self._make_json_safe(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return obj
    
    def load_cache(self) -> Dict:
        """加载缓存文件"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def save_cache(self, cache_data: Dict):
        """保存缓存文件"""
        try:
            safe_cache_data = self._make_json_safe(cache_data)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(safe_cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存股票数据缓存失败: {e}")
    
    def get_cache_key(self, data_type: str, stock_code: str) -> str:
        """生成缓存键"""
        return f"{data_type}_{stock_code}"
    
    def is_cache_valid(self, data_type: str, stock_code: str) -> bool:
        """检查缓存是否有效"""
        try:
            cache_data = self.load_cache()
            cache_key = self.get_cache_key(data_type, stock_code)
            if cache_key not in cache_data:
                return False
            cache_meta = cache_data[cache_key].get('cache_meta', {})
            cache_time = datetime.fromisoformat(cache_meta['timestamp'])
            expire_minutes = self.cache_configs[data_type]['expire_minutes']
            expire_time = cache_time + timedelta(minutes=expire_minutes)
            return datetime.now() < expire_time
        except Exception:
            return False
    
    def get_cached_data(self, data_type: str, stock_code: str) -> Dict:
        """获取缓存数据"""
        try:
            cache_data = self.load_cache()
            cache_key = self.get_cache_key(data_type, stock_code)
            return cache_data.get(cache_key, {}).get('data', {})
        except Exception:
            return {}
    
    def save_cached_data(self, data_type: str, stock_code: str, data: Dict):
        """保存数据到缓存"""
        try:
            cache_data = self.load_cache()
            cache_key = self.get_cache_key(data_type, stock_code)
            cache_data[cache_key] = {
                'cache_meta': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': data_type,
                    'stock_code': stock_code,
                    'expire_minutes': self.cache_configs[data_type]['expire_minutes']
                },
                'data': data
            }
            self.save_cache(cache_data)
            print(f"💾 {stock_code} {self.cache_configs[data_type]['description']}已缓存")
        except Exception as e:
            print(f"❌ 缓存股票数据失败: {e}")
    
    def clear_cache(self, stock_code: Optional[str] = None, data_type: Optional[str] = None):
        """清理缓存"""
        try:
            cache_data = self.load_cache()
            cache_cleared = False
            
            if stock_code and data_type:
                # 清理特定股票的特定数据类型
                cache_key = self.get_cache_key(data_type, stock_code)
                if cache_key in cache_data:
                    del cache_data[cache_key]
                    self.save_cache(cache_data)
                    cache_cleared = True
                    print(f"✅ 已清理 {stock_code} {self.cache_configs.get(data_type, {}).get('description', data_type)} 缓存")
                else:
                    print(f"ℹ️  {stock_code} {data_type} 缓存不存在")
                    
            elif stock_code:
                # 清理特定股票的所有缓存
                keys_to_remove = [key for key in cache_data.keys() if key.endswith(f"_{stock_code}")]
                for key in keys_to_remove:
                    del cache_data[key]
                if keys_to_remove:
                    self.save_cache(cache_data)
                    cache_cleared = True
                    print(f"✅ 已清理 {stock_code} 所有缓存 ({len(keys_to_remove)}项)")
                else:
                    print(f"ℹ️  {stock_code} 无缓存数据")
                    
            elif data_type:
                # 清理特定数据类型的所有缓存
                keys_to_remove = [key for key in cache_data.keys() if key.startswith(f"{data_type}_")]
                for key in keys_to_remove:
                    del cache_data[key]
                if keys_to_remove:
                    self.save_cache(cache_data)
                    cache_cleared = True
                    print(f"✅ 已清理所有 {self.cache_configs.get(data_type, {}).get('description', data_type)} 缓存 ({len(keys_to_remove)}项)")
                else:
                    print(f"ℹ️  无 {data_type} 缓存数据")
                    
            else:
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
                    cache_cleared = True
                    print("✅ 已清理所有股票数据缓存")
                else:
                    print("ℹ️  缓存文件不存在")
            
            if cache_cleared:
                self.load_cache()
                    
        except Exception as e:
            print(f"❌ 清理缓存失败: {e}")
    
    def get_cache_status(self, stock_code: Optional[str] = None) -> Dict:
        """获取缓存状态"""
        status = {}
        current_time = datetime.now()
        cache_data = self.load_cache()
        
        for cache_key, cache_info in cache_data.items():
            try:
                cache_meta = cache_info.get('cache_meta', {})
                cached_stock_code = cache_meta.get('stock_code', '')
                data_type = cache_meta.get('data_type', '')
                analysis_type = cache_meta.get('analysis_type', '')
                if stock_code and cached_stock_code != stock_code:
                    continue
                cache_time = datetime.fromisoformat(cache_meta['timestamp'])
                expire_minutes = cache_meta.get('expire_minutes', 60)
                expire_time = cache_time + timedelta(minutes=expire_minutes)
                is_valid = current_time < expire_time
                remaining_minutes = (expire_time - current_time).total_seconds() / 60
                if remaining_minutes > 0:
                    remaining_text = f"剩余 {int(remaining_minutes)} 分钟"
                else:
                    remaining_text = "已过期"
                display_key = cache_key
                if analysis_type:
                    display_key = f"{cached_stock_code}_{analysis_type}_AI分析"
                status[display_key] = {
                    'stock_code': cached_stock_code,
                    'data_type': data_type,
                    'analysis_type': analysis_type,
                    'description': self.cache_configs.get(data_type, {}).get('description', data_type),
                    'valid': is_valid,
                    'cache_time': cache_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'expire_minutes': expire_minutes,
                    'remaining': remaining_text
                }
            except Exception:
                continue
        
        return status
    
    def print_cache_status(self, stock_code: Optional[str] = None):
        """打印缓存状态"""
        status = self.get_cache_status(stock_code)
        
        print("=" * 70)
        if stock_code:
            print(f"📊 股票 {stock_code} 数据缓存状态")
        else:
            print("📊 股票数据缓存状态")
        print(f"📁 缓存文件: {self.cache_file}")
        print("=" * 70)
        
        if not status:
            if stock_code:
                print(f"ℹ️  股票 {stock_code} 无缓存数据")
            else:
                print("ℹ️  无缓存数据")
        else:
            for key, info in status.items():
                status_icon = "✅" if info['valid'] else "❌"
                print(f"{status_icon} {info['stock_code']:<8} | {info['description']:<12} | {info['remaining']:<15} | 过期: {info['expire_minutes']}分钟")
        
        try:
            if os.path.exists(self.cache_file):
                file_size = os.path.getsize(self.cache_file) / 1024  # KB
                print(f"💾 缓存文件大小: {file_size:.1f} KB")
            else:
                print("💾 缓存文件: 不存在")
        except Exception:
            pass
        
        print("=" * 70)


# 全局缓存管理器实例
_cache_manager = None

def get_cache_manager() -> StockDataCache:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = StockDataCache()
    return _cache_manager
