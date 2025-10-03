"""
K线数据管理器 - 统一处理指数K线数据的获取、转换和缓存
"""
import os
import sys
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import akshare as ak

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

warnings.filterwarnings('ignore')

from ui.config import INDEX_SYMBOL_MAPPING
from utils.kline_cache import cache_manager, KLineData


class KLineDataManager:
    """K线数据管理器"""
    
    def __init__(self):
        """初始化K线数据管理器"""
        self.index_mapping = INDEX_SYMBOL_MAPPING
    
    def fetch_index_kline_raw(self, index_name: str, period: int = 250) -> pd.DataFrame:
        """
        从akshare获取原始K线数据
        
        Args:
            index_name: 指数名称
            period: 获取的数据条数
            
        Returns:
            pd.DataFrame: 原始K线数据
        """
        if index_name not in self.index_mapping:
            raise ValueError(f"不支持的指数名称: {index_name}")
        
        symbol = self.index_mapping[index_name]
        df_raw = ak.stock_zh_index_daily(symbol=symbol)
        
        if df_raw.empty:
            raise ValueError(f"无法获取{index_name}数据")
        
        # 取最近的数据
        df_raw = df_raw.tail(period).copy()
        
        # 数据类型转换
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df_raw.columns:
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')
        
        # 确保date列是日期时间格式
        if 'date' in df_raw.columns:
            df_raw['date'] = pd.to_datetime(df_raw['date'])
        
        return df_raw
    
    def convert_to_kline_data_list(self, df: pd.DataFrame, index_name: str) -> List[KLineData]:
        """
        将DataFrame转换为KLineData列表
        
        Args:
            df: K线数据DataFrame
            index_name: 指数名称
            
        Returns:
            List[KLineData]: KLineData对象列表
        """
        kline_data_list = []
        
        for _, row in df.iterrows():
            # 处理日期，确保datetime字段始终是字符串
            if 'date' in df.columns:
                if pd.isna(row['date']):
                    date_str = datetime.now().strftime('%Y-%m-%d')
                elif isinstance(row['date'], str):
                    date_str = row['date']
                else:
                    date_str = row['date'].strftime('%Y-%m-%d')
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            kline_data = KLineData(
                symbol=index_name,
                datetime=date_str,
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                amount=None,
                data_type="index"
            )
            kline_data_list.append(kline_data)
        
        return kline_data_list
    
    def convert_from_kline_data_list(self, kline_data_list: List[KLineData], 
                                     for_technical_analysis: bool = False) -> pd.DataFrame:
        """
        将KLineData列表转换为DataFrame
        
        Args:
            kline_data_list: KLineData对象列表
            for_technical_analysis: 是否用于技术分析（影响索引设置）
            
        Returns:
            pd.DataFrame: K线数据DataFrame
        """
        kline_records = []
        
        for kdata in kline_data_list:
            # 安全处理datetime字段
            if isinstance(kdata.datetime, str):
                date_str = kdata.datetime.split()[0]  # 只取日期部分
                datetime_str = kdata.datetime
            else:
                # 如果是datetime对象，转换为字符串
                date_str = kdata.datetime.strftime('%Y-%m-%d')
                datetime_str = kdata.datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            record = {
                'date': date_str,
                'datetime': datetime_str,
                'open': kdata.open,
                'high': kdata.high,
                'low': kdata.low,
                'close': kdata.close,
                'volume': kdata.volume
            }
            if kdata.amount is not None:
                record['amount'] = kdata.amount
            
            kline_records.append(record)
        
        df = pd.DataFrame(kline_records)
        df['date'] = pd.to_datetime(df['date'])
        
        # 如果是用于技术分析，设置date为索引
        if for_technical_analysis:
            df = df.set_index('date')
        
        return df
    
    def get_index_kline_data(self, index_name: str, period: int = 250, 
                           use_cache: bool = True, force_refresh: bool = False,
                           for_technical_analysis: bool = False) -> Tuple[pd.DataFrame, bool]:
        """
        获取指数K线数据（统一入口）
        
        Args:
            index_name: 指数名称
            period: 获取的数据条数
            use_cache: 是否使用缓存
            force_refresh: 是否强制刷新
            for_technical_analysis: 是否用于技术分析（影响DataFrame格式）
            
        Returns:
            Tuple[pd.DataFrame, bool]: (K线数据DataFrame, 是否来自缓存)
        """
        from_cache = False
        
        # 尝试从缓存获取
        if use_cache and not force_refresh:
            cached_data = cache_manager.get_cached_index_kline(index_name, period)
            if cached_data and len(cached_data) >= min(period, 30):
                print(f"📋 使用缓存的K线数据: {index_name} ({len(cached_data)}条)")
                df = self.convert_from_kline_data_list(cached_data, for_technical_analysis)
                # 确保数据量符合要求
                df = df.tail(period)
                from_cache = True
                return df, from_cache
        
        # 从网络获取最新数据
        print(f"📡 获取最新K线数据: {index_name}")
        df_raw = self.fetch_index_kline_raw(index_name, period * 2)  # 多取一些数据以备缓存
        
        # 转换为KLineData列表并缓存
        if use_cache:
            kline_data_list = self.convert_to_kline_data_list(df_raw, index_name)
            cache_manager.cache_index_kline(index_name, kline_data_list)
        
        # 准备返回的DataFrame
        df = df_raw.tail(period).copy()
        
        # 确保DataFrame包含datetime列（用于绘图）
        if 'date' in df.columns and 'datetime' not in df.columns:
            df['datetime'] = df['date'].dt.strftime('%Y-%m-%d')
        
        if for_technical_analysis and 'date' in df.columns:
            df = df.set_index('date')
        
        return df, from_cache
    
    def update_index_cache(self, index_name: str, period: int = 250) -> bool:
        """
        更新指数缓存数据
        
        Args:
            index_name: 指数名称
            period: 获取的数据条数
            
        Returns:
            bool: 是否更新成功
        """
        try:
            print(f"🔄 更新{index_name}缓存数据...")
            
            # 获取原始数据
            df_raw = self.fetch_index_kline_raw(index_name, period)
            
            # 转换为KLineData列表
            kline_data_list = self.convert_to_kline_data_list(df_raw, index_name)
            
            # 更新缓存（智能合并）
            cache_manager.update_index_kline(index_name, kline_data_list)
            
            print(f"   ✓ 成功更新{index_name}缓存数据: {len(kline_data_list)}条")
            return True
            
        except Exception as e:
            print(f"   ❌ 更新{index_name}缓存数据失败: {e}")
            return False
    
    def batch_update_indices_cache(self, indices: Optional[List[str]] = None, 
                                 period: int = 250) -> Dict:
        """
        批量更新指数缓存数据
        
        Args:
            indices: 指数名称列表，None表示更新所有支持的指数
            period: 获取的数据条数
            
        Returns:
            Dict: 更新结果统计
        """
        if indices is None:
            from ui.config import FOCUS_INDICES
            indices = FOCUS_INDICES
        
        print(f"📊 批量更新指数缓存数据 ({len(indices)}个指数)...")
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'results': {}
        }
        
        for index_name in indices:
            success = self.update_index_cache(index_name, period)
            results['results'][index_name] = success
            if success:
                results['success_count'] += 1
            else:
                results['failed_count'] += 1
        
        print(f"   ✓ 批量更新完成: 成功 {results['success_count']} 个，失败 {results['failed_count']} 个")
        return results
    
    def add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为DataFrame添加移动平均线
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            pd.DataFrame: 添加了移动平均线的DataFrame
        """
        try:
            # 确保有close列
            if 'close' not in df.columns:
                print("❌ DataFrame中没有close列，无法计算均线")
                return df
            
            df = df.copy()
            
            # 计算移动平均线
            df['MA5'] = df['close'].rolling(window=5, min_periods=1).mean()
            df['MA10'] = df['close'].rolling(window=10, min_periods=1).mean()
            df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()
            df['MA60'] = df['close'].rolling(window=60, min_periods=1).mean()
            
            return df
            
        except Exception as e:
            print(f"❌ 计算均线失败: {e}")
            return df


# 全局K线数据管理器实例
_kline_manager = None

def get_kline_manager() -> KLineDataManager:
    """获取全局K线数据管理器实例"""
    global _kline_manager
    if _kline_manager is None:
        _kline_manager = KLineDataManager()
    return _kline_manager


if __name__ == "__main__":
    """测试K线数据管理器"""
    print("🧪 测试K线数据管理器...")
    
    manager = get_kline_manager()
    
    # 测试获取K线数据
    try:
        df, from_cache = manager.get_index_kline_data('上证指数', period=100, use_cache=True)
        print(f"✅ 获取上证指数数据成功: {len(df)}条记录, 来自缓存: {from_cache}")
        print(f"数据列: {df.columns.tolist()}")
        print(f"最新数据:\n{df.tail(3)}")
        
        # 测试添加均线
        df_with_ma = manager.add_moving_averages(df)
        print(f"✅ 添加均线成功, 新增列: {[col for col in df_with_ma.columns if col.startswith('MA')]}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("✅ 测试完成!")
