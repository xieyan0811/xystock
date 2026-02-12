"""基于CSV的K线数据缓存管理器，支持智能缓存策略：历史数据永久保存，近期数据智能过期"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class KLineType(Enum):
    MIN_1 = "1m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_30 = "30m"
    MIN_60 = "60m"
    HOUR_1 = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"
    INDEX_DAY = "index_1d"  # 指数日线数据


@dataclass
class KLineData:
    """K线数据结构"""
    symbol: str
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: Optional[float] = None
    fetch_time: Optional[str] = None
    data_type: str = "stock"  # "stock" 或 "index"
    
    def __post_init__(self):
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("K线数据不合理：最高价应大于等于开盘价和收盘价，最低价应小于等于开盘价和收盘价")
        
        if self.fetch_time is None:
            self.fetch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class KLineCacheManager:
    """基于CSV的K线数据缓存管理器"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.cache_dir = os.path.join(project_dir, "data", "cache")
        else:
            self.cache_dir = cache_dir
        
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"✅ CSV缓存目录: {self.cache_dir}")
    
    def _get_csv_path(self, kline_type: KLineType) -> str:
        filename = f"kline_{kline_type.value}.csv"
        return os.path.join(self.cache_dir, filename)
    
    def _is_data_fresh(self, stock_data_time: str, fetch_time: str, kline_type: KLineType) -> bool:
        """判断数据是否需要更新"""
        try:
            if kline_type in [KLineType.DAY, KLineType.INDEX_DAY]:
                data_date = datetime.strptime(stock_data_time.split()[0], '%Y-%m-%d').date()
                fetch_datetime = datetime.strptime(fetch_time, '%Y-%m-%d %H:%M:%S')
            else:
                data_datetime = datetime.strptime(stock_data_time, '%Y-%m-%d %H:%M:%S')
                fetch_datetime = datetime.strptime(fetch_time, '%Y-%m-%d %H:%M:%S')
            
            now = datetime.now()
            
            # 历史数据判断：T-2之前的数据永久有效
            if kline_type in [KLineType.DAY, KLineType.INDEX_DAY]:
                if data_date < (now - timedelta(days=2)).date():
                    return True
                
                if data_date != fetch_datetime.date():
                    return True  # 不在同一天拉取的，认为有效
            else:
                # 分钟线：1小时之前的数据永久有效
                if data_datetime < now - timedelta(hours=1):
                    return True
                
                time_diff = abs((data_datetime - fetch_datetime).total_seconds())
                if time_diff > 3600:  # 如果拉取时间和数据时间差距超过1小时，认为有效
                    return True
            
            # 当日/当前数据过期判断
            time_since_fetch = now - fetch_datetime
            
            if kline_type in [KLineType.DAY, KLineType.INDEX_DAY]:
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
        csv_path = self._get_csv_path(kline_type)
        
        if not os.path.exists(csv_path):
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_path, dtype={'symbol': str})
            return df
        except Exception as e:
            print(f"加载数据失败 {csv_path}: {e}")
            return pd.DataFrame()
    
    def _save_all_data(self, kline_type: KLineType, df: pd.DataFrame):
        csv_path = self._get_csv_path(kline_type)
        
        try:
            df.to_csv(csv_path, index=False, encoding='utf-8')
        except Exception as e:
            print(f"保存数据失败 {csv_path}: {e}")
    
    def get_cached_kline(self, symbol: str, kline_type: KLineType, count: int) -> Optional[List[KLineData]]:
        """获取缓存的K线数据"""
        try:
            df = self._load_all_data(kline_type)
            
            if df.empty:
                return None
            
            symbol_df = df[df['symbol'] == symbol].copy()
            
            if symbol_df.empty:
                return None
            
            symbol_df = symbol_df.sort_values('datetime')
            
            # 检查数据新鲜度，过滤掉过期的数据
            fresh_data = []
            for _, row in symbol_df.iterrows():
                if pd.notna(row.get('fetch_time')):
                    if self._is_data_fresh(row['datetime'], row['fetch_time'], kline_type):
                        fresh_data.append(row)
                else:
                    fresh_data.append(row)
            
            if not fresh_data:
                return None
            
            fresh_df = pd.DataFrame(fresh_data).tail(count)
            
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
                    fetch_time=row.get('fetch_time'),
                    data_type=row.get('data_type', 'stock')
                ))
            
            # 检查是否包含前一个交易日的数据（仅对日线和指数日线进行检查）
            if kline_type in [KLineType.DAY, KLineType.INDEX_DAY]:
                from stock.stock_data_tools import get_valid_trading_day
                previous_trading_day = get_valid_trading_day()
                has_previous_trading_day_data = any(
                    kline.datetime.startswith(previous_trading_day) for kline in kline_data
                )
                
                if not has_previous_trading_day_data:
                    print(f"⚠️  缓存不包含前一个交易日数据({previous_trading_day})，需要重新拉取: {symbol} {kline_type.value}")
                    return None
                else:
                    print(f"✅ 缓存包含前一个交易日数据({previous_trading_day}): {symbol} {kline_type.value}")
            
            return kline_data
            
        except Exception as e:
            print(f"获取缓存数据失败: {e}")
            return None
    
    def cache_kline(self, symbol: str, kline_type: KLineType, count: int, kline_data: List[KLineData]):
        """缓存K线数据（替换指定股票的所有数据）"""
        if not kline_data:
            return
        
        try:
            df = self._load_all_data(kline_type)
            
            if not df.empty:
                df = df[df['symbol'] != symbol]
            else:
                df = pd.DataFrame()
            
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
                    'fetch_time': kdata.fetch_time,
                    'data_type': kdata.data_type
                })
            
            new_df = pd.DataFrame(new_data_list)
            
            if not df.empty:
                df = pd.concat([df, new_df], ignore_index=True)
            else:
                df = new_df
            
            df = df.sort_values(['symbol', 'datetime'])
            
            self._save_all_data(kline_type, df)
            
            print(f"✅ 缓存K线数据: {symbol} {kline_type.value} {len(kline_data)}条")
            
        except Exception as e:
            print(f"缓存K线数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_kline_data(self, symbol: str, kline_type: KLineType, new_data: List[KLineData]):
        """智能更新K线数据（增量更新，合并新旧数据）"""
        if not new_data:
            return
        
        try:
            df = self._load_all_data(kline_type)
            
            existing_symbol_df = df[df['symbol'] == symbol].copy() if not df.empty else pd.DataFrame()
            other_symbols_df = df[df['symbol'] != symbol].copy() if not df.empty else pd.DataFrame()
            
            existing_data = {}
            if not existing_symbol_df.empty:
                for _, row in existing_symbol_df.iterrows():
                    existing_data[row['datetime']] = row.to_dict()
            
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
                    'fetch_time': new_item.fetch_time,
                    'data_type': new_item.data_type
                }
            
            updated_symbol_df = pd.DataFrame(list(existing_data.values()))
            
            if not other_symbols_df.empty:
                df = pd.concat([other_symbols_df, updated_symbol_df], ignore_index=True)
            else:
                df = updated_symbol_df
            
            df = df.sort_values(['symbol', 'datetime'])
            
            self._save_all_data(kline_type, df)
            
            print(f"✅ 更新K线数据: {symbol} {kline_type.value} 新增/更新 {len(new_data)}条")
            
        except Exception as e:
            print(f"更新K线数据失败: {e}")
    
    def analyze_missing_ranges(self, symbol: str, kline_type: KLineType, count: int) -> List[Tuple[str, str]]:
        """分析缺失的时间范围"""
        try:
            cached_data = self.get_cached_kline(symbol, kline_type, count * 2)
            
            if not cached_data:
                end_time = datetime.now()
                if kline_type == KLineType.DAY:
                    start_time = end_time - timedelta(days=count + 10)
                    return [(start_time.strftime('%Y-%m-%d'), end_time.strftime('%Y-%m-%d'))]
                else:
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
        """清理缓存"""
        try:
            if kline_type:
                if symbol:
                    df = self._load_all_data(kline_type)
                    if not df.empty:
                        df = df[df['symbol'] != symbol]
                        self._save_all_data(kline_type, df)
                    print(f"✅ 清理股票 {symbol} 的 {kline_type.value} 缓存数据")
                else:
                    csv_path = self._get_csv_path(kline_type)
                    if os.path.exists(csv_path):
                        os.remove(csv_path)
                    print(f"✅ 清理所有 {kline_type.value} 缓存文件")
            else:
                if symbol:
                    for ktype in KLineType:
                        df = self._load_all_data(ktype)
                        if not df.empty:
                            df = df[df['symbol'] != symbol]
                            self._save_all_data(ktype, df)
                    print(f"✅ 清理股票 {symbol} 的所有缓存数据")
                else:
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
                    if fresh_data:
                        fresh_df = pd.DataFrame(fresh_data)
                        self._save_all_data(kline_type, fresh_df)
                    else:
                        csv_path = self._get_csv_path(kline_type)
                        if os.path.exists(csv_path):
                            os.remove(csv_path)
            
            if expired_count > 0:
                print(f"✅ 清理过期缓存数据: {expired_count}条")
                
        except Exception as e:
            print(f"清理过期缓存失败: {e}")
    
    def cache_index_kline(self, index_name: str, kline_data: List[KLineData]):
        """缓存指数K线数据的便捷方法"""
        # 确保所有数据都标记为指数类型
        for kdata in kline_data:
            kdata.data_type = "index"
        
        self.cache_kline(index_name, KLineType.INDEX_DAY, len(kline_data), kline_data)
    
    def get_cached_index_kline(self, index_name: str, count: int = 30) -> Optional[List[KLineData]]:
        """获取缓存的指数K线数据的便捷方法"""
        return self.get_cached_kline(index_name, KLineType.INDEX_DAY, count)
    
    def update_index_kline(self, index_name: str, new_data: List[KLineData]):
        """更新指数K线数据的便捷方法"""
        # 确保所有数据都标记为指数类型
        for kdata in new_data:
            kdata.data_type = "index"
        
        self.update_kline_data(index_name, KLineType.INDEX_DAY, new_data)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
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
                
                kline_type = file.replace('kline_', '').replace('.csv', '')
                
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
