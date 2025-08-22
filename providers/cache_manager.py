"""
基于CSV的K线数据缓存管理器
支持智能缓存策略：历史数据永久保存，近期数据智能过期
"""

import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class KLineType(Enum):
    """K线类型枚举"""
    MIN_1 = "1m"      # 1分钟
    MIN_5 = "5m"      # 5分钟
    MIN_15 = "15m"    # 15分钟
    MIN_30 = "30m"    # 30分钟
    MIN_60 = "60m"    # 60分钟
    HOUR_1 = "1h"     # 1小时
    DAY = "1d"        # 日K
    WEEK = "1w"       # 周K
    MONTH = "1M"      # 月K


@dataclass
class KLineData:
    """K线数据结构"""
    symbol: str             # 股票代码
    datetime: str           # 股票数据时间
    open: float            # 开盘价
    high: float            # 最高价
    low: float             # 最低价
    close: float           # 收盘价
    volume: int            # 成交量
    amount: Optional[float] = None  # 成交额
    fetch_time: Optional[str] = None  # 数据拉取时间
    
    def __post_init__(self):
        """数据验证和默认值设置"""
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("K线数据不合理：最高价应大于等于开盘价和收盘价，最低价应小于等于开盘价和收盘价")
        
        # 如果没有设置fetch_time，使用当前时间
        if self.fetch_time is None:
            self.fetch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class KLineCacheManager:
    """基于CSV的K线数据缓存管理器"""
    
    def __init__(self, cache_dir: str = None):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: CSV文件存储目录，默认为项目data/cache目录
        """
        if cache_dir is None:
            # 获取当前文件所在目录，然后构建cache路径
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.cache_dir = os.path.join(project_dir, "data", "cache")
        else:
            self.cache_dir = cache_dir
        
        # 确保目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"✅ CSV缓存目录: {self.cache_dir}")
    
    def _get_csv_path(self, kline_type: KLineType) -> str:
        """获取CSV文件路径（按时间周期存储）"""
        filename = f"kline_{kline_type.value}.csv"
        return os.path.join(self.cache_dir, filename)
    
    def _is_data_fresh(self, stock_data_time: str, fetch_time: str, kline_type: KLineType) -> bool:
        """
        判断数据是否需要更新
        
        Args:
            stock_data_time: 股票数据的时间（如"2024-01-15 09:30:00"）
            fetch_time: 拉取时间（如"2024-01-15 14:30:00"）
            kline_type: K线类型
        
        Returns:
            bool: True表示数据仍然有效，False表示需要更新
        """
        try:
            # 解析时间
            if kline_type == KLineType.DAY:
                # 日线只比较日期部分
                data_date = datetime.strptime(stock_data_time.split()[0], '%Y-%m-%d').date()
                fetch_datetime = datetime.strptime(fetch_time, '%Y-%m-%d %H:%M:%S')
            else:
                # 分钟线比较完整时间
                data_datetime = datetime.strptime(stock_data_time, '%Y-%m-%d %H:%M:%S')
                fetch_datetime = datetime.strptime(fetch_time, '%Y-%m-%d %H:%M:%S')
            
            now = datetime.now()
            
            # 历史数据判断：如果数据时间是T-2之前，认为是历史数据，永久有效
            if kline_type == KLineType.DAY:
                if data_date < (now - timedelta(days=2)).date():
                    return True  # 历史数据，永久有效
                
                # 近期数据判断：只有当拉取时间在数据时间范围内时，才考虑过期
                if data_date != fetch_datetime.date():
                    return True  # 不在同一天拉取的，认为有效
            else:
                # 分钟线：如果数据时间是1小时之前，认为是历史数据
                if data_datetime < now - timedelta(hours=1):
                    return True
                
                # 近期数据：只有当拉取时间接近数据时间时，才考虑过期
                time_diff = abs((data_datetime - fetch_datetime).total_seconds())
                if time_diff > 3600:  # 如果拉取时间和数据时间差距超过1小时，认为有效
                    return True
            
            # 当日/当前数据过期判断
            time_since_fetch = now - fetch_datetime
            
            if kline_type == KLineType.DAY:
                # 当日日线：4小时后过期
                return time_since_fetch < timedelta(hours=4)
            elif kline_type == KLineType.MIN_1:
                return time_since_fetch < timedelta(minutes=1)
            elif kline_type == KLineType.MIN_5:
                return time_since_fetch < timedelta(minutes=5)
            elif kline_type == KLineType.MIN_15:
                return time_since_fetch < timedelta(minutes=15)
            elif kline_type == KLineType.MIN_30:
                return time_since_fetch < timedelta(minutes=30)
            elif kline_type in [KLineType.MIN_60, KLineType.HOUR_1]:
                return time_since_fetch < timedelta(hours=1)
            elif kline_type == KLineType.WEEK:
                return time_since_fetch < timedelta(days=1)
            elif kline_type == KLineType.MONTH:
                return time_since_fetch < timedelta(days=1)
            else:
                return time_since_fetch < timedelta(hours=1)
                
        except Exception as e:
            print(f"判断数据新鲜度失败: {e}")
            return False
    
    def _load_all_data(self, kline_type: KLineType) -> pd.DataFrame:
        """加载指定类型的所有数据"""
        csv_path = self._get_csv_path(kline_type)
        
        if not os.path.exists(csv_path):
            return pd.DataFrame()
        
        try:
            # 指定symbol列为字符串类型，避免类型转换问题
            df = pd.read_csv(csv_path, dtype={'symbol': str})
            return df
        except Exception as e:
            print(f"加载数据失败 {csv_path}: {e}")
            return pd.DataFrame()
    
    def _save_all_data(self, kline_type: KLineType, df: pd.DataFrame):
        """保存所有数据到CSV文件"""
        csv_path = self._get_csv_path(kline_type)
        
        try:
            df.to_csv(csv_path, index=False, encoding='utf-8')
        except Exception as e:
            print(f"保存数据失败 {csv_path}: {e}")
    
    def get_cached_kline(self, symbol: str, kline_type: KLineType, count: int) -> Optional[List[KLineData]]:
        """
        获取缓存的K线数据
        
        Args:
            symbol: 股票代码
            kline_type: K线类型
            count: 数据条数
            
        Returns:
            Optional[List[KLineData]]: 缓存的K线数据，如果不存在或已过期则返回None
        """
        try:
            # 加载所有数据
            df = self._load_all_data(kline_type)
            
            if df.empty:
                return None
            
            # 筛选指定股票的数据
            symbol_df = df[df['symbol'] == symbol].copy()
            
            if symbol_df.empty:
                return None
            
            # 按时间排序
            symbol_df = symbol_df.sort_values('datetime')
            
            # 检查数据新鲜度，过滤掉过期的数据
            fresh_data = []
            for _, row in symbol_df.iterrows():
                if pd.notna(row.get('fetch_time')):
                    if self._is_data_fresh(row['datetime'], row['fetch_time'], kline_type):
                        fresh_data.append(row)
                else:
                    # 如果没有fetch_time，认为是历史数据，保留
                    fresh_data.append(row)
            
            if not fresh_data:
                return None
            
            # 取最后count条数据
            fresh_df = pd.DataFrame(fresh_data).tail(count)
            
            # 转换为KLineData对象
            kline_data = []
            for _, row in fresh_df.iterrows():
                kline_data.append(KLineData(
                    symbol=row['symbol'],
                    datetime=row['datetime'],
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                    amount=float(row['amount']) if pd.notna(row['amount']) else None,
                    fetch_time=row.get('fetch_time')
                ))
            
            return kline_data
            
        except Exception as e:
            print(f"获取缓存数据失败: {e}")
            return None
    
    def cache_kline(self, symbol: str, kline_type: KLineType, count: int, kline_data: List[KLineData]):
        """
        缓存K线数据（替换指定股票的所有数据）
        
        Args:
            symbol: 股票代码
            kline_type: K线类型
            count: 数据条数（为了保持接口兼容性，实际不使用）
            kline_data: K线数据
        """
        if not kline_data:
            return
        
        try:
            # 加载现有数据
            df = self._load_all_data(kline_type)
            
            # 移除指定股票的旧数据
            if not df.empty:
                df = df[df['symbol'] != symbol]
            else:
                df = pd.DataFrame()
            
            # 准备新数据
            new_data_list = []
            for kdata in kline_data:
                new_data_list.append({
                    'symbol': kdata.symbol,
                    'datetime': kdata.datetime,
                    'open': kdata.open,
                    'high': kdata.high,
                    'low': kdata.low,
                    'close': kdata.close,
                    'volume': kdata.volume,
                    'amount': kdata.amount,
                    'fetch_time': kdata.fetch_time
                })
            
            new_df = pd.DataFrame(new_data_list)
            
            # 合并数据
            if not df.empty:
                df = pd.concat([df, new_df], ignore_index=True)
            else:
                df = new_df
            
            # 按股票代码和时间排序
            df = df.sort_values(['symbol', 'datetime'])
            
            # 保存数据
            self._save_all_data(kline_type, df)
            
            print(f"✅ 缓存K线数据: {symbol} {kline_type.value} {len(kline_data)}条")
            
        except Exception as e:
            print(f"缓存K线数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_kline_data(self, symbol: str, kline_type: KLineType, new_data: List[KLineData]):
        """
        智能更新K线数据（增量更新，合并新旧数据）
        
        Args:
            symbol: 股票代码
            kline_type: K线类型
            new_data: 新的K线数据
        """
        if not new_data:
            return
        
        try:
            # 加载现有数据
            df = self._load_all_data(kline_type)
            
            # 获取指定股票的现有数据
            existing_symbol_df = df[df['symbol'] == symbol].copy() if not df.empty else pd.DataFrame()
            other_symbols_df = df[df['symbol'] != symbol].copy() if not df.empty else pd.DataFrame()
            
            # 转换现有数据为字典，便于查找和更新
            existing_data = {}
            if not existing_symbol_df.empty:
                for _, row in existing_symbol_df.iterrows():
                    existing_data[row['datetime']] = row.to_dict()
            
            # 处理新数据
            for new_item in new_data:
                existing_data[new_item.datetime] = {
                    'symbol': new_item.symbol,
                    'datetime': new_item.datetime,
                    'open': new_item.open,
                    'high': new_item.high,
                    'low': new_item.low,
                    'close': new_item.close,
                    'volume': new_item.volume,
                    'amount': new_item.amount,
                    'fetch_time': new_item.fetch_time
                }
            
            # 重建该股票的DataFrame
            updated_symbol_df = pd.DataFrame(list(existing_data.values()))
            
            # 合并所有数据
            if not other_symbols_df.empty:
                df = pd.concat([other_symbols_df, updated_symbol_df], ignore_index=True)
            else:
                df = updated_symbol_df
            
            # 按股票代码和时间排序
            df = df.sort_values(['symbol', 'datetime'])
            
            # 保存数据
            self._save_all_data(kline_type, df)
            
            print(f"✅ 更新K线数据: {symbol} {kline_type.value} 新增/更新 {len(new_data)}条")
            
        except Exception as e:
            print(f"更新K线数据失败: {e}")
    
    def analyze_missing_ranges(self, symbol: str, kline_type: KLineType, count: int) -> List[Tuple[str, str]]:
        """
        分析缺失的时间范围
        
        Args:
            symbol: 股票代码
            kline_type: K线类型
            count: 需要的数据条数
            
        Returns:
            List[Tuple[str, str]]: 缺失的时间范围列表 [(start_time, end_time), ...]
        """
        try:
            # 获取现有数据
            cached_data = self.get_cached_kline(symbol, kline_type, count * 2)  # 多获取一些用于分析
            
            if not cached_data:
                # 没有缓存数据，需要全部拉取
                end_time = datetime.now()
                if kline_type == KLineType.DAY:
                    start_time = end_time - timedelta(days=count + 10)  # 多拉取一些天数，考虑周末
                    return [(start_time.strftime('%Y-%m-%d'), end_time.strftime('%Y-%m-%d'))]
                else:
                    # 分钟线数据
                    if kline_type == KLineType.MIN_1:
                        start_time = end_time - timedelta(minutes=count)
                    elif kline_type == KLineType.MIN_5:
                        start_time = end_time - timedelta(minutes=count * 5)
                    elif kline_type == KLineType.MIN_15:
                        start_time = end_time - timedelta(minutes=count * 15)
                    elif kline_type == KLineType.MIN_30:
                        start_time = end_time - timedelta(minutes=count * 30)
                    else:
                        start_time = end_time - timedelta(hours=count)
                    
                    return [(start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                            end_time.strftime('%Y-%m-%d %H:%M:%S'))]
            
            # 如果有足够的数据，返回空列表
            if len(cached_data) >= count:
                return []
            
            # 数据不足，计算需要补充的范围
            latest_time = cached_data[-1].datetime
            end_time = datetime.now()
            
            missing_ranges = []
            if kline_type == KLineType.DAY:
                latest_date = datetime.strptime(latest_time.split()[0], '%Y-%m-%d')
                if latest_date.date() < end_time.date():
                    next_day = latest_date + timedelta(days=1)
                    missing_ranges.append((next_day.strftime('%Y-%m-%d'), 
                                         end_time.strftime('%Y-%m-%d')))
            else:
                latest_datetime = datetime.strptime(latest_time, '%Y-%m-%d %H:%M:%S')
                if latest_datetime < end_time:
                    missing_ranges.append((latest_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                                         end_time.strftime('%Y-%m-%d %H:%M:%S')))
            
            return missing_ranges
            
        except Exception as e:
            print(f"分析缺失范围失败: {e}")
            return []
    
    def clear_cache(self, symbol: Optional[str] = None, kline_type: Optional[KLineType] = None):
        """
        清理缓存
        
        Args:
            symbol: 指定股票代码，不指定则清理所有股票
            kline_type: 指定K线类型，不指定则清理所有类型
        """
        try:
            if kline_type:
                # 清理指定类型的缓存
                if symbol:
                    # 清理指定股票的指定类型数据
                    df = self._load_all_data(kline_type)
                    if not df.empty:
                        df = df[df['symbol'] != symbol]
                        self._save_all_data(kline_type, df)
                    print(f"✅ 清理股票 {symbol} 的 {kline_type.value} 缓存数据")
                else:
                    # 清理指定类型的所有数据
                    csv_path = self._get_csv_path(kline_type)
                    if os.path.exists(csv_path):
                        os.remove(csv_path)
                    print(f"✅ 清理所有 {kline_type.value} 缓存文件")
            else:
                # 清理所有缓存
                if symbol:
                    # 清理指定股票的所有数据
                    for ktype in KLineType:
                        df = self._load_all_data(ktype)
                        if not df.empty:
                            df = df[df['symbol'] != symbol]
                            self._save_all_data(ktype, df)
                    print(f"✅ 清理股票 {symbol} 的所有缓存数据")
                else:
                    # 清理所有数据
                    for file in os.listdir(self.cache_dir):
                        if file.startswith('kline_') and file.endswith('.csv'):
                            os.remove(os.path.join(self.cache_dir, file))
                    print("✅ 清理所有缓存文件")
                
        except Exception as e:
            print(f"清理缓存失败: {e}")
    
    def clear_expired_cache(self):
        """清理过期的缓存数据"""
        try:
            expired_count = 0
            
            for kline_type in KLineType:
                df = self._load_all_data(kline_type)
                if df.empty:
                    continue
                
                fresh_data = []
                for _, row in df.iterrows():
                    if pd.notna(row.get('fetch_time')):
                        if self._is_data_fresh(row['datetime'], row['fetch_time'], kline_type):
                            fresh_data.append(row)
                        else:
                            expired_count += 1
                    else:
                        # 没有fetch_time的数据保留
                        fresh_data.append(row)
                
                if len(fresh_data) != len(df):
                    # 保存清理后的数据
                    if fresh_data:
                        fresh_df = pd.DataFrame(fresh_data)
                        self._save_all_data(kline_type, fresh_df)
                    else:
                        # 如果没有数据了，删除文件
                        csv_path = self._get_csv_path(kline_type)
                        if os.path.exists(csv_path):
                            os.remove(csv_path)
            
            if expired_count > 0:
                print(f"✅ 清理过期缓存数据: {expired_count}条")
                
        except Exception as e:
            print(f"清理过期缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        try:
            csv_files = [f for f in os.listdir(self.cache_dir) if f.startswith('kline_') and f.endswith('.csv')]
            
            stats = {
                "cache_dir": self.cache_dir,
                "total_files": len(csv_files),
                "files": []
            }
            
            total_size = 0
            symbol_stats = {}
            total_records = 0
            
            for file in csv_files:
                file_path = os.path.join(self.cache_dir, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # 解析文件名获取K线类型
                kline_type = file.replace('kline_', '').replace('.csv', '')
                
                # 统计记录数和股票数
                df = pd.read_csv(file_path)
                record_count = len(df)
                total_records += record_count
                
                if not df.empty:
                    symbols = df['symbol'].nunique()
                    for symbol in df['symbol'].unique():
                        if symbol not in symbol_stats:
                            symbol_stats[symbol] = {}
                        symbol_stats[symbol][kline_type] = len(df[df['symbol'] == symbol])
                else:
                    symbols = 0
                
                stats["files"].append({
                    "filename": file,
                    "kline_type": kline_type,
                    "size_bytes": file_size,
                    "size_kb": round(file_size / 1024, 2),
                    "record_count": record_count,
                    "symbol_count": symbols
                })
            
            stats["total_size_bytes"] = total_size
            stats["total_size_kb"] = round(total_size / 1024, 2)
            stats["total_records"] = total_records
            stats["symbol_count"] = len(symbol_stats)
            stats["symbol_stats"] = symbol_stats
            
            return stats
            
        except Exception as e:
            return {"error": f"获取统计信息失败: {e}"}


# 全局缓存管理器实例
cache_manager = KLineCacheManager()
