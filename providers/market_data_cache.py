"""
市场数据缓存管理器

本模块提供市场基础数据的缓存管理功能，包括：
1. 市场情绪指标缓存
2. 估值指标缓存
3. 资金流向指标缓存
4. 融资融券详细数据缓存

支持不同数据类型的差异化过期策略
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


class MarketDataCache:
    """市场数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化缓存管理器"""
        self.cache_dir = cache_dir
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_file = os.path.join(project_dir, cache_dir, "market_data.json")
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 缓存配置
        self.cache_configs = {
            'market_sentiment': {'expire_minutes': 15, 'description': '市场情绪指标'},
            'valuation_data': {'expire_minutes': 1440, 'description': '估值指标'},
            'money_flow_data': {'expire_minutes': 43200, 'description': '资金流向指标'},
            'margin_data': {'expire_minutes': 60, 'description': '融资融券数据'},
            'current_indices': {'expire_minutes': 5, 'description': '当前指数实时数据'},
            'ai_analysis': {'expire_minutes': 180, 'description': 'AI大盘分析'},
        }
    
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
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存缓存失败: {e}")
    
    def is_cache_valid(self, data_type: str) -> bool:
        """检查缓存是否有效"""
        try:
            cache_data = self.load_cache()
            if data_type not in cache_data:
                return False
            
            cache_meta = cache_data[data_type].get('cache_meta', {})
            cache_time = datetime.fromisoformat(cache_meta['timestamp'])
            expire_minutes = self.cache_configs[data_type]['expire_minutes']
            expire_time = cache_time + timedelta(minutes=expire_minutes)
            
            return datetime.now() < expire_time
        except Exception:
            return False
    
    def get_cached_data(self, data_type: str) -> Dict:
        """获取缓存数据"""
        try:
            cache_data = self.load_cache()
            return cache_data.get(data_type, {}).get('data', {})
        except Exception:
            return {}
    
    def save_cached_data(self, data_type: str, data: Dict):
        """保存数据到缓存"""
        try:
            cache_data = self.load_cache()
            cache_data[data_type] = {
                'cache_meta': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': data_type,
                    'expire_minutes': self.cache_configs[data_type]['expire_minutes']
                },
                'data': data
            }
            self.save_cache(cache_data)
            print(f"💾 {self.cache_configs[data_type]['description']}已缓存")
        except Exception as e:
            print(f"❌ 缓存数据失败: {e}")
    
    def clear_cache(self, data_type: Optional[str] = None):
        """清理缓存"""
        if data_type:
            if data_type not in self.cache_configs:
                print(f"❌ 未知的数据类型: {data_type}")
                return
            
            try:
                cache_data = self.load_cache()
                if data_type in cache_data:
                    del cache_data[data_type]
                    self.save_cache(cache_data)
                    print(f"✅ 已清理{self.cache_configs[data_type]['description']}缓存")
                else:
                    print(f"ℹ️ {self.cache_configs[data_type]['description']}缓存不存在")
            except Exception as e:
                print(f"❌ 清理缓存失败: {e}")
        else:
            # 清理所有缓存
            try:
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
                    print("✅ 已清理所有缓存数据")
                else:
                    print("ℹ️ 缓存文件不存在")
            except Exception as e:
                print(f"❌ 清理缓存失败: {e}")
    
    def get_cache_status(self) -> Dict:
        """获取缓存状态"""
        status = {}
        current_time = datetime.now()
        cache_data = self.load_cache()
        
        for data_type, config in self.cache_configs.items():
            if data_type in cache_data:
                is_valid = self.is_cache_valid(data_type)
                
                try:
                    cache_meta = cache_data[data_type].get('cache_meta', {})
                    cache_time_str = cache_meta.get('timestamp', '')
                    cache_time = datetime.fromisoformat(cache_time_str)
                    expire_time = cache_time + timedelta(minutes=config['expire_minutes'])
                    
                    if is_valid:
                        remaining_minutes = int((expire_time - current_time).total_seconds() / 60)
                        remaining_text = f"{remaining_minutes}分钟后过期"
                    else:
                        overdue_minutes = int((current_time - expire_time).total_seconds() / 60)
                        remaining_text = f"已过期{overdue_minutes}分钟"
                        
                except Exception:
                    cache_time_str = "解析失败"
                    remaining_text = "未知"
                
                status[data_type] = {
                    'description': config['description'],
                    'exists': True,
                    'valid': is_valid,
                    'cache_time': cache_time_str,
                    'expire_minutes': config['expire_minutes'],
                    'remaining': remaining_text
                }
            else:
                status[data_type] = {
                    'description': config['description'],
                    'exists': False,
                    'valid': False,
                    'cache_time': None,
                    'expire_minutes': config['expire_minutes'],
                    'remaining': "无缓存"
                }
        
        return status
    
    def print_cache_status(self):
        """打印缓存状态"""
        status = self.get_cache_status()
        
        print("=" * 70)
        print("📊 市场数据缓存状态")
        print(f"📁 缓存文件: {self.cache_file}")
        print("=" * 70)
        
        for data_type, info in status.items():
            status_icon = "✅" if info['valid'] else ("📋" if info['exists'] else "❌")
            print(f"{status_icon} {info['description']:<12} | {info['remaining']:<15} | 过期时间: {info['expire_minutes']}分钟")
        
        # 显示缓存文件大小
        try:
            if os.path.exists(self.cache_file):
                file_size = os.path.getsize(self.cache_file)
                size_text = f"{file_size/1024:.1f}KB" if file_size > 1024 else f"{file_size}B"
                print(f"\n📦 缓存文件大小: {size_text}")
            else:
                print(f"\n📦 缓存文件不存在")
        except Exception:
            pass
        
        print("=" * 70)


# 全局缓存管理器实例
_cache_manager = None

def get_cache_manager() -> MarketDataCache:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MarketDataCache()
    return _cache_manager
