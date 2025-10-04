"""
筹码数据专用缓存管理器 - 独立存储筹码原始数据
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional


class ChipDataCache:
    """筹码数据专用缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_file = os.path.join(project_dir, cache_dir, "chip_raw_data.json")
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # 筹码数据缓存配置：24小时过期
        self.expire_hours = 24
    
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
        """加载筹码缓存文件"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ 读取筹码缓存文件失败: {e}")
            return {}
    
    def save_cache(self, cache_data: Dict):
        """保存筹码缓存文件"""
        try:
            safe_cache_data = self._make_json_safe(cache_data)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(safe_cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存筹码缓存文件失败: {e}")
    
    def is_cache_valid(self, stock_code: str) -> bool:
        """检查筹码缓存是否有效"""
        try:
            cache_data = self.load_cache()
            if stock_code not in cache_data:
                return False
            
            cache_time_str = cache_data[stock_code].get('cache_time')
            if not cache_time_str:
                return False
            
            cache_time = datetime.fromisoformat(cache_time_str)
            expire_time = cache_time + timedelta(hours=self.expire_hours)
            
            return datetime.now() < expire_time
        except Exception:
            return False
    
    def get_cached_raw_data(self, stock_code: str) -> Optional[list]:
        """获取缓存的筹码原始数据"""
        try:
            if not self.is_cache_valid(stock_code):
                return None
            
            cache_data = self.load_cache()
            return cache_data.get(stock_code, {}).get('raw_data')
        except Exception:
            return None
    
    def save_raw_data(self, stock_code: str, raw_data: list):
        """保存筹码原始数据到缓存"""
        try:
            cache_data = self.load_cache()
            
            cache_data[stock_code] = {
                'stock_code': stock_code,
                'raw_data': raw_data,
                'cache_time': datetime.now().isoformat(),
                'data_count': len(raw_data) if raw_data else 0,
                'expire_hours': self.expire_hours
            }
            
            self.save_cache(cache_data)
            print(f"💾 {stock_code} 筹码原始数据已缓存 ({len(raw_data) if raw_data else 0}条记录)")
        except Exception as e:
            print(f"❌ 缓存筹码原始数据失败: {e}")
    
    def clear_cache(self, stock_code: Optional[str] = None):
        """清理筹码缓存"""
        try:
            if stock_code:
                # 清理特定股票的筹码缓存
                cache_data = self.load_cache()
                if stock_code in cache_data:
                    del cache_data[stock_code]
                    self.save_cache(cache_data)
                    print(f"✅ 已清理 {stock_code} 筹码缓存")
                else:
                    print(f"ℹ️  {stock_code} 筹码缓存不存在")
            else:
                # 清理所有筹码缓存
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
                    print("✅ 已清理所有筹码缓存")
                else:
                    print("ℹ️  筹码缓存文件不存在")
        except Exception as e:
            print(f"❌ 清理筹码缓存失败: {e}")
    
    def get_cache_status(self, stock_code: Optional[str] = None) -> Dict:
        """获取筹码缓存状态"""
        status = {}
        current_time = datetime.now()
        cache_data = self.load_cache()
        
        for cached_stock_code, cache_info in cache_data.items():
            if stock_code and cached_stock_code != stock_code:
                continue
            
            try:
                cache_time = datetime.fromisoformat(cache_info['cache_time'])
                expire_time = cache_time + timedelta(hours=self.expire_hours)
                is_valid = current_time < expire_time
                remaining_hours = (expire_time - current_time).total_seconds() / 3600
                
                if remaining_hours > 0:
                    remaining_text = f"剩余 {int(remaining_hours)} 小时"
                else:
                    remaining_text = "已过期"
                
                status[cached_stock_code] = {
                    'stock_code': cached_stock_code,
                    'data_count': cache_info.get('data_count', 0),
                    'valid': is_valid,
                    'cache_time': cache_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'expire_hours': self.expire_hours,
                    'remaining': remaining_text
                }
            except Exception:
                continue
        
        return status
    
    def print_cache_status(self, stock_code: Optional[str] = None):
        """打印筹码缓存状态"""
        status = self.get_cache_status(stock_code)
        
        print("=" * 70)
        if stock_code:
            print(f"📊 股票 {stock_code} 筹码数据缓存状态")
        else:
            print("📊 筹码数据缓存状态")
        print(f"📁 缓存文件: {self.cache_file}")
        print("=" * 70)
        
        if not status:
            if stock_code:
                print(f"ℹ️  股票 {stock_code} 无筹码缓存数据")
            else:
                print("ℹ️  无筹码缓存数据")
        else:
            for stock_code, info in status.items():
                status_icon = "✅" if info['valid'] else "❌"
                print(f"{status_icon} {info['stock_code']:<8} | 数据:{info['data_count']:<4}条 | {info['remaining']:<15} | 过期: {info['expire_hours']}小时")
        
        try:
            if os.path.exists(self.cache_file):
                file_size = os.path.getsize(self.cache_file) / 1024  # KB
                print(f"💾 缓存文件大小: {file_size:.1f} KB")
            else:
                print("💾 缓存文件: 不存在")
        except Exception:
            pass
        
        print("=" * 70)


# 全局筹码缓存管理器实例
_chip_cache_manager = None

def get_chip_cache_manager() -> ChipDataCache:
    """获取全局筹码缓存管理器实例"""
    global _chip_cache_manager
    if _chip_cache_manager is None:
        _chip_cache_manager = ChipDataCache()
    return _chip_cache_manager
