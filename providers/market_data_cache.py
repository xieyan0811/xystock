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
    """市场基础数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self._market_indicators = None  # 延迟初始化
        self.cache_file = os.path.join(cache_dir, "market_data_unified.json")  # 统一缓存文件
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 定义数据类型和过期时间
        self.data_configs = {
            'market_sentiment': {
                'expire_minutes': 60,  # 60分钟过期
                'fetch_method': 'get_market_sentiment_indicators',
                'description': '市场情绪指标'
            },
            'valuation': {
                'expire_minutes': 1440,  # 1天过期
                'fetch_method': 'get_valuation_indicators',
                'description': '估值指标'
            },
            'money_flow': {
                'expire_minutes': 43200,  # 30天过期
                'fetch_method': 'get_money_flow_indicators',
                'description': '资金流向指标'
            },
            'margin_detail': {
                'expire_minutes': 60,  # 1小时过期
                'fetch_method': 'get_detailed_margin_data',
                'description': '融资融券详细数据'
            },
            'ai_analysis': {
                'expire_minutes': 180,  # 3小时过期
                'fetch_method': None,  # 将来实现AI分析方法
                'description': 'AI市场分析'
            }
        }
    
    @property
    def market_indicators(self):
        """延迟初始化 MarketIndicators 实例"""
        if self._market_indicators is None:
            from market_tools import MarketIndicators
            self._market_indicators = MarketIndicators()
        return self._market_indicators
    
    def get_market_sentiment(self, force_refresh: bool = False) -> Dict:
        """获取市场情绪数据"""
        return self._get_cached_data('market_sentiment', force_refresh)
    
    def get_valuation_data(self, force_refresh: bool = False) -> Dict:
        """获取估值数据"""
        return self._get_cached_data('valuation', force_refresh)
    
    def get_money_flow_data(self, force_refresh: bool = False) -> Dict:
        """获取资金流向数据"""
        return self._get_cached_data('money_flow', force_refresh)
    
    def get_margin_data(self, force_refresh: bool = False) -> Dict:
        """获取融资融券详细数据"""
        return self._get_cached_data('margin_detail', force_refresh)
    
    def get_ai_analysis(self, force_refresh: bool = False) -> Dict:
        """获取AI市场分析数据"""
        return self._get_cached_data('ai_analysis', force_refresh)
    
    def set_ai_analysis(self, analysis_data: Dict):
        """手动设置AI分析数据"""
        self._save_data_block('ai_analysis', analysis_data)
        print(f"💾 AI市场分析已缓存")
    
    def _get_cached_data(self, data_type: str, force_refresh: bool = False) -> Dict:
        """通用缓存数据获取方法"""
        config = self.data_configs[data_type]
        
        # 检查是否需要刷新
        if not force_refresh and self._is_data_valid(data_type, config['expire_minutes']):
            print(f"📋 使用缓存的{config['description']}")
            return self._load_data_block(data_type)
        
        # 对于AI分析，如果没有获取方法，返回空数据
        if config['fetch_method'] is None:
            cached_data = self._load_data_block(data_type)
            if cached_data:
                print(f"📋 使用现有的{config['description']}")
            return cached_data
        
        # 获取新数据
        try:
            print(f"📡 刷新{config['description']}...")
            method = getattr(self.market_indicators, config['fetch_method'])
            new_data = method()
            
            # 保存到缓存
            self._save_data_block(data_type, new_data)
            return new_data
            
        except Exception as e:
            print(f"❌ 获取{config['description']}失败: {e}")
            # 返回旧缓存数据（如果存在）
            cached_data = self._load_data_block(data_type)
            if cached_data:
                print(f"📋 使用过期的{config['description']}缓存")
            return cached_data
    
    def _is_data_valid(self, data_type: str, expire_minutes: int) -> bool:
        """检查指定数据块是否有效"""
        try:
            cache_data = self._load_cache_file()
            if not cache_data or data_type not in cache_data:
                return False
            
            data_block = cache_data[data_type]
            if 'cache_meta' not in data_block:
                return False
            
            cache_time = datetime.fromisoformat(data_block['cache_meta']['timestamp'])
            expire_time = cache_time + timedelta(minutes=expire_minutes)
            
            return datetime.now() < expire_time
            
        except Exception:
            return False
    
    def _load_data_block(self, data_type: str) -> Dict:
        """加载指定数据块"""
        try:
            cache_data = self._load_cache_file()
            if cache_data and data_type in cache_data:
                return cache_data[data_type].get('data', {})
            return {}
        except Exception:
            return {}
    
    def _save_data_block(self, data_type: str, data: Dict):
        """保存指定数据块"""
        try:
            # 加载现有缓存文件
            cache_data = self._load_cache_file()
            if cache_data is None:
                cache_data = {}
            
            # 更新指定数据块
            cache_data[data_type] = {
                'cache_meta': {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': data_type,
                    'expire_minutes': self.data_configs[data_type]['expire_minutes'],
                    'version': '1.0'
                },
                'data': data
            }
            
            # 保存整个缓存文件
            self._save_cache_file(cache_data)
            print(f"💾 {self.data_configs[data_type]['description']}已缓存")
            
        except Exception as e:
            print(f"❌ 保存缓存失败: {e}")
    
    def _load_cache_file(self) -> Optional[Dict]:
        """加载整个缓存文件"""
        try:
            if not os.path.exists(self.cache_file):
                return {}
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_cache_file(self, cache_data: Dict):
        """保存整个缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存缓存文件失败: {e}")
    
    def clear_cache(self, data_type: Optional[str] = None):
        """清理缓存"""
        cache_cleared = False
        
        if data_type:
            if data_type not in self.data_configs:
                print(f"❌ 未知的数据类型: {data_type}")
                return
            
            try:
                cache_data = self._load_cache_file()
                if cache_data and data_type in cache_data:
                    del cache_data[data_type]
                    self._save_cache_file(cache_data)
                    cache_cleared = True
                    print(f"✅ 已清理{self.data_configs[data_type]['description']}缓存")
                else:
                    print(f"ℹ️ {self.data_configs[data_type]['description']}缓存不存在")
            except Exception as e:
                print(f"❌ 清理缓存失败: {e}")
        else:
            # 清理所有缓存
            try:
                if os.path.exists(self.cache_file):
                    os.remove(self.cache_file)
                    cache_cleared = True
                    print("✅ 已清理所有缓存数据")
                else:
                    print("ℹ️ 缓存文件不存在")
            except Exception as e:
                print(f"❌ 清理缓存失败: {e}")
        
        # 如果清理了缓存，强制重新加载以确保内存中的缓存也被清空
        if cache_cleared:
            # 通过重新读取文件来刷新内存缓存
            self._load_cache_file()
    
    def get_cache_status(self) -> Dict:
        """获取缓存状态"""
        status = {}
        current_time = datetime.now()
        cache_data = self._load_cache_file()
        
        for data_type, config in self.data_configs.items():
            if cache_data and data_type in cache_data:
                data_block = cache_data[data_type]
                is_valid = self._is_data_valid(data_type, config['expire_minutes'])
                
                try:
                    cache_time_str = data_block['cache_meta']['timestamp']
                    cache_time = datetime.fromisoformat(cache_time_str)
                    expire_time = cache_time + timedelta(minutes=config['expire_minutes'])
                    
                    # 计算剩余时间
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
                    'remaining': remaining_text,
                    'file_path': self.cache_file
                }
            else:
                status[data_type] = {
                    'description': config['description'],
                    'exists': False,
                    'valid': False,
                    'cache_time': None,
                    'expire_minutes': config['expire_minutes'],
                    'remaining': "无缓存",
                    'file_path': self.cache_file
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
                if file_size > 1024:
                    size_text = f"{file_size/1024:.1f}KB"
                else:
                    size_text = f"{file_size}B"
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
