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
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date, time
from typing import Dict, Optional, Any


class NumpyJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理numpy、pandas和datetime数据类型"""
    
    @staticmethod
    def clean_data(obj):
        """递归清理数据中的NaN和无穷大值"""
        if isinstance(obj, dict):
            return {k: NumpyJSONEncoder.clean_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [NumpyJSONEncoder.clean_data(item) for item in obj]
        elif isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        elif isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif hasattr(obj, '__module__') and 'numpy' in str(obj.__module__):
            # 处理其他numpy类型
            if hasattr(obj, 'item'):
                try:
                    item_val = obj.item()
                    if isinstance(item_val, float) and (np.isnan(item_val) or np.isinf(item_val)):
                        return None
                    return item_val
                except:
                    return None
        return obj
    
    def default(self, obj):
        # 处理Python原生float中的特殊值
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.generic):  # numpy scalar types
            return obj.item()
        
        # 处理pandas数据类型
        elif isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        elif isinstance(obj, pd.DataFrame):
            # 将DataFrame转换为可序列化的格式，替换NaN和无穷大
            df_clean = obj.replace([np.nan, np.inf, -np.inf], None)
            return df_clean.to_dict('records')
        elif isinstance(obj, pd.Series):
            # 将Series转换为列表，替换NaN和无穷大
            series_clean = obj.replace([np.nan, np.inf, -np.inf], None)
            return series_clean.tolist()
        elif isinstance(obj, (pd.Index, pd.RangeIndex)):
            # 处理pandas索引对象
            return obj.tolist()
        # 对于标量pandas对象，安全地检查是否为NaN
        elif hasattr(obj, '__module__') and obj.__module__ == 'pandas._libs.missing':
            # 处理pandas的NA/NaT等特殊值
            return None
        elif hasattr(obj, '__array__') and hasattr(obj, 'size') and obj.size == 1:
            # 处理单元素的pandas对象
            try:
                if pd.isna(obj):
                    return None
                return obj.item() if hasattr(obj, 'item') else obj
            except (ValueError, TypeError):
                pass  # 如果pd.isna()失败，继续其他处理
        
        # 处理Python原生datetime类型
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        
        # 处理pandas日期相关类型
        elif hasattr(obj, 'to_pydatetime'):  # pandas datetime-like objects
            try:
                return obj.to_pydatetime().isoformat()
            except:
                return str(obj)
        elif hasattr(obj, 'date'):  # objects with date method
            try:
                return obj.date().isoformat()
            except:
                return str(obj)
        
        return super().default(obj)


class MarketDataCache:
    """市场数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化缓存管理器"""
        self.cache_dir = cache_dir
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_file = os.path.join(project_dir, cache_dir, "market_data.json")
        
        os.makedirs(cache_dir, exist_ok=True)
        
        # 缓存配置
        self.cache_configs = {
            'market_sentiment': {'expire_minutes': 15, 'description': '市场情绪指标', 'index_specific': False},
            'valuation_data': {'expire_minutes': 1440, 'description': '估值指标', 'index_specific': False},
            'money_flow_data': {'expire_minutes': 43200, 'description': '资金流向指标', 'index_specific': False},
            'margin_data': {'expire_minutes': 60, 'description': '融资融券数据', 'index_specific': False},
            'current_indices': {'expire_minutes': 5, 'description': '当前指数实时数据', 'index_specific': False},
            'ai_analysis': {'expire_minutes': 180, 'description': 'AI大盘分析', 'index_specific': True},
            'technical_indicators': {'expire_minutes': 60, 'description': '技术指标数据', 'index_specific': True}
        }
    
    def load_cache(self) -> Dict:
        """加载缓存文件"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return self._clean_loaded_data(data)
            return {}
        except Exception:
            return {}
    
    def _clean_loaded_data(self, data):
        """清理从JSON加载的数据，处理特殊值"""
        if isinstance(data, dict):
            return {k: self._clean_loaded_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_loaded_data(item) for item in data]
        elif isinstance(data, float):
            if np.isnan(data) or np.isinf(data):
                return None
            return data
        else:
            return data
    
    def save_cache(self, cache_data: Dict):
        """保存缓存文件"""
        try:
            # 预清理数据，确保所有NaN和无穷大值都被处理
            cleaned_data = NumpyJSONEncoder.clean_data(cache_data)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2, cls=NumpyJSONEncoder, allow_nan=False)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ 保存缓存失败: {e}")
    
    def _get_cache_key(self, data_type: str, index_name: str = None) -> str:
        """生成缓存键名"""
        if data_type not in self.cache_configs:
            return data_type
        
        config = self.cache_configs[data_type]
        if config.get('index_specific', False) and index_name:
            # 对于指数相关的数据，添加指数名称后缀
            return f"{data_type}_{index_name}"
        else:
            return data_type
    
    def is_cache_valid(self, data_type: str, index_name: str = None) -> bool:
        """检查缓存是否有效"""
        try:
            cache_key = self._get_cache_key(data_type, index_name)
            cache_data = self.load_cache()
            if cache_key not in cache_data:
                return False
            
            cache_meta = cache_data[cache_key].get('cache_meta', {})
            cache_time = datetime.fromisoformat(cache_meta['timestamp'])
            expire_minutes = self.cache_configs[data_type]['expire_minutes']
            expire_time = cache_time + timedelta(minutes=expire_minutes)
            
            return datetime.now() < expire_time
        except Exception:
            return False
    
    def get_cached_data(self, data_type: str, index_name: str = None) -> Dict:
        """获取缓存数据"""
        try:
            cache_key = self._get_cache_key(data_type, index_name)
            cache_data = self.load_cache()
            return cache_data.get(cache_key, {}).get('data', {})
        except Exception:
            return {}
    
    def save_cached_data(self, data_type: str, data: Dict, index_name: str = None):
        """保存数据到缓存"""
        try:
            cache_key = self._get_cache_key(data_type, index_name)
            cache_data = self.load_cache()
            
            cache_meta = {
                'timestamp': datetime.now().isoformat(),
                'data_type': data_type,
                'expire_minutes': self.cache_configs[data_type]['expire_minutes']
            }
            
            # 如果是指数相关数据，记录指数名称
            if index_name and self.cache_configs[data_type].get('index_specific', False):
                cache_meta['index_name'] = index_name
            
            cache_data[cache_key] = {
                'cache_meta': cache_meta,
                'data': data
            }
            self.save_cache(cache_data)
            description = self.cache_configs.get(data_type, {}).get('description', data_type)
            if index_name and self.cache_configs[data_type].get('index_specific', False):
                print(f"💾 {description}({index_name})已缓存")
            else:
                print(f"💾 {description}已缓存")
        except Exception as e:
            print(f"❌ 缓存数据失败: {e}")
    
    def clear_cache(self, data_type: Optional[str] = None, index_name: str = None):
        """清理缓存"""
        if data_type:
            if data_type not in self.cache_configs:
                print(f"❌ 未知的数据类型: {data_type}")
                return
            
            try:
                cache_data = self.load_cache()
                config = self.cache_configs[data_type]
                
                if config.get('index_specific', False) and index_name:
                    # 清理特定指数的缓存
                    cache_key = self._get_cache_key(data_type, index_name)
                    if cache_key in cache_data:
                        del cache_data[cache_key]
                        print(f"✅ 已清理{config['description']}({index_name})缓存")
                    else:
                        print(f"ℹ️ {config['description']}({index_name})缓存不存在")
                elif config.get('index_specific', False):
                    # 清理该数据类型所有指数的缓存
                    keys_to_delete = [k for k in cache_data.keys() if k.startswith(f"{data_type}_")]
                    for key in keys_to_delete:
                        del cache_data[key]
                    if keys_to_delete:
                        print(f"✅ 已清理{len(keys_to_delete)}个{config['description']}缓存")
                    else:
                        print(f"ℹ️ 没有{config['description']}缓存需要清理")
                else:
                    # 非指数相关数据，直接清理
                    if data_type in cache_data:
                        del cache_data[data_type]
                        print(f"✅ 已清理{config['description']}缓存")
                    else:
                        print(f"ℹ️ {config['description']}缓存不存在")
                
                self.save_cache(cache_data)
            except Exception as e:
                print(f"❌ 清理缓存失败: {e}")
        else:
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
            if config.get('index_specific', False):
                # 指数相关数据，需要检查所有指数的缓存
                index_caches = {}
                found_any = False
                
                # 检查所有可能的指数缓存
                from ui.config import FOCUS_INDICES
                for index_name in FOCUS_INDICES:
                    cache_key = self._get_cache_key(data_type, index_name)
                    if cache_key in cache_data:
                        found_any = True
                        is_valid = self.is_cache_valid(data_type, index_name)
                        
                        try:
                            cache_meta = cache_data[cache_key].get('cache_meta', {})
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
                        
                        index_caches[index_name] = {
                            'valid': is_valid,
                            'cache_time': cache_time_str,
                            'remaining': remaining_text
                        }
                
                status[data_type] = {
                    'description': config['description'],
                    'exists': found_any,
                    'valid': any(cache['valid'] for cache in index_caches.values()),
                    'expire_minutes': config['expire_minutes'],
                    'index_specific': True,
                    'index_caches': index_caches
                }
            else:
                # 非指数相关数据，按原逻辑处理
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
                        'remaining': remaining_text,
                        'index_specific': False
                    }
                else:
                    status[data_type] = {
                        'description': config['description'],
                        'exists': False,
                        'valid': False,
                        'cache_time': None,
                        'expire_minutes': config['expire_minutes'],
                        'remaining': "无缓存",
                        'index_specific': False
                    }
        
        return status
    
    def print_cache_status(self):
        """打印缓存状态"""
        status = self.get_cache_status()
        
        print("=" * 80)
        print("📊 市场数据缓存状态")
        print(f"📁 缓存文件: {self.cache_file}")
        print("=" * 80)
        
        for data_type, info in status.items():
            if info.get('index_specific', False):
                status_icon = "✅" if info['valid'] else ("📋" if info['exists'] else "❌")
                print(f"{status_icon} {info['description']:<15} | 过期时间: {info['expire_minutes']}分钟")
                
                # 显示各个指数的缓存状态
                index_caches = info.get('index_caches', {})
                if index_caches:
                    for index_name, cache_info in index_caches.items():
                        sub_icon = "  ✅" if cache_info['valid'] else "  ❌"
                        print(f"{sub_icon} {index_name:<12} | {cache_info['remaining']:<15}")
                else:
                    print(f"  ❌ 无指数缓存")
            else:
                status_icon = "✅" if info['valid'] else ("📋" if info['exists'] else "❌")
                remaining = info.get('remaining', '无缓存')
                print(f"{status_icon} {info['description']:<15} | {remaining:<15} | 过期时间: {info['expire_minutes']}分钟")
        
        try:
            if os.path.exists(self.cache_file):
                file_size = os.path.getsize(self.cache_file)
                size_text = f"{file_size/1024:.1f}KB" if file_size > 1024 else f"{file_size}B"
                print(f"\n📦 缓存文件大小: {size_text}")
            else:
                print(f"\n📦 缓存文件不存在")
        except Exception:
            pass
        
        print("=" * 80)


# 全局缓存管理器实例
_cache_manager = None

def get_cache_manager() -> MarketDataCache:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MarketDataCache()
    return _cache_manager
