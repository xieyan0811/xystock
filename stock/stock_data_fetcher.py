"""
基于 efinance 的A股数据获取器
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from utils.kline_cache import cache_manager, KLineData, KLineType
import akshare as ak

@dataclass
class RealTimeQuote:
    """实时行情数据结构"""
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    amount: float
    high: float
    low: float
    open: float
    prev_close: float
    timestamp: str


class DataFetcherError(Exception):
    """数据获取异常"""
    pass


class DataFetcherNotAvailableError(DataFetcherError):
    """数据源不可用异常"""
    pass


class InvalidSymbolError(DataFetcherError):
    """无效股票代码异常"""
    pass


class StockDataFetcher:
    """efinance 数据获取器"""
    
    def __init__(self):
        self.name = "EFinance"
        self.description = "东方财富A股数据接口，支持实时行情和K线数据"
        self._ef = None
        self._is_initialized = False
        self._kline_type_mapping = {
            KLineType.MIN_1: 1,
            KLineType.MIN_5: 5,
            KLineType.MIN_15: 15,
            KLineType.MIN_30: 30,
            KLineType.MIN_60: 60,
            KLineType.DAY: 101,
            KLineType.WEEK: 102,
            KLineType.MONTH: 103,
        }
    
    def _get_previous_trading_day(self) -> str:
        """计算前一个交易日"""
        today = datetime.now()
        weekday = today.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
        
        if weekday == 0:
            # 周一，前一个交易日是上周五
            prev_trading_day = today - timedelta(days=3)
        elif weekday == 6:
            # 周日，前一个交易日是上周五
            prev_trading_day = today - timedelta(days=2)
        else:
            # 周二到周六，前一个交易日是前一天
            prev_trading_day = today - timedelta(days=1)
        
        return prev_trading_day.strftime("%Y-%m-%d")
    
    def initialize(self) -> bool:
        """初始化 efinance 模块"""
        try:
            import efinance as ef
            self._ef = ef
            self._is_initialized = True
            return True
        except ImportError:
            print("需要安装 efinance: pip install efinance")
            self._is_initialized = False
            return False
        except Exception as e:
            print(f"初始化 efinance 失败: {e}")
            self._is_initialized = False
            return False
    
    def get_realtime_quote(self, symbol: str, max_retry: int = 3) -> Optional[RealTimeQuote]:
        """获取A股实时行情数据"""
        if not self._is_initialized:
            raise DataFetcherNotAvailableError("efinance 未初始化")
        
        formatted_symbol = self.format_symbol(symbol)
        
        for attempt in range(1, max_retry + 1):
            try:
                quotes_df = self._ef.stock.get_latest_quote(formatted_symbol)
                
                if quotes_df is not None and not quotes_df.empty:
                    # 处理DataFrame/Series数据格式差异
                    if hasattr(quotes_df, "to_dict"):
                        if hasattr(quotes_df, "shape") and len(quotes_df.shape) > 1:
                            records = quotes_df.to_dict(orient="records")
                            if records:
                                data = records[0]
                            else:
                                continue
                        else:
                            data = quotes_df.to_dict()
                        
                        return self._convert_to_realtime_quote(data, symbol)
                
                print(f"第{attempt}次尝试获取{symbol}数据为空")
                
            except Exception as e:
                print(f"第{attempt}次获取股票{symbol}数据失败: {e}")
                if attempt < max_retry:
                    print(f"等待1秒后重试...")
                    time.sleep(1)
                else:
                    print(f"达到最大重试次数({max_retry})，获取失败")
                    return None
        
        return None
    
    def get_kline_data(self, 
                      symbol: str, 
                      kline_type: KLineType = KLineType.DAY, 
                      count: int = 30) -> List[KLineData]:
        """获取K线数据（支持缓存）"""
        if not self._is_initialized:
            raise DataFetcherNotAvailableError("efinance 未初始化")
        
        if kline_type not in self._kline_type_mapping:
            raise DataFetcherError(f"不支持的K线类型: {kline_type}")
        
        symbol = symbol.upper().strip()
        
        cached_data = cache_manager.get_cached_kline(symbol, kline_type, count)
        if cached_data:
            # 检查是否包含前一个交易日的数据
            previous_trading_day = self._get_previous_trading_day()
            has_previous_trading_day_data = any(
                kline.datetime.startswith(previous_trading_day) for kline in cached_data
            )
            
            if not has_previous_trading_day_data:
                print(f"⚠️  缓存不包含前一个交易日数据，需要重新拉取: {symbol} {kline_type.value}")
            else:
                print(f"📦 从缓存获取K线数据: {symbol} {kline_type.value} {len(cached_data)}条")
                return cached_data

        # 从数据源获取数据
        try:
            formatted_symbol = self.format_symbol(symbol)
            klt = self._kline_type_mapping[kline_type]
            
            kline_df = self._ef.stock.get_quote_history(formatted_symbol, klt=klt)

            if kline_df is not None and not kline_df.empty:
                kline_list = []
                if hasattr(kline_df, "to_dict"):
                    records = kline_df.to_dict(orient="records")
                    for record in records:
                        kline_data = self._convert_to_kline_data(record, symbol)
                        if kline_data:
                            kline_list.append(kline_data)
                
                if kline_list:
                    # 判断是否保存当日K线数据：仅对日K线应用16:30收盘判断
                    now = datetime.now()
                    today = now.strftime("%Y-%m-%d")
                    
                    if kline_type == KLineType.DAY:
                        # 日K线：判断是否过了16:30收盘时间
                        market_close_time = now.replace(hour=16, minute=30, second=0, microsecond=0)
                        
                        if now >= market_close_time:
                            # 已收盘，保存包含当日在内的所有数据
                            filtered_kline_list = kline_list
                            log_message = f"🔄 从数据源获取K线数据: {symbol} {kline_type.value} {len(filtered_kline_list)}条 (已收盘，包含当日数据)"
                        else:
                            # 未收盘，去掉当日数据，避免保存盘中价格
                            filtered_kline_list = [
                                kline for kline in kline_list 
                                if not kline.datetime.startswith(today)
                            ]
                            log_message = f"🔄 从数据源获取K线数据: {symbol} {kline_type.value} {len(filtered_kline_list)}条 (未收盘，已去除当日数据)"
                    else:
                        # 分钟级K线：直接去掉当日数据（实时数据变化频繁）
                        filtered_kline_list = [
                            kline for kline in kline_list 
                            if not kline.datetime.startswith(today)
                        ]
                        log_message = f"🔄 从数据源获取K线数据: {symbol} {kline_type.value} {len(filtered_kline_list)}条 (分钟线，已去除当日数据)"
                    
                    # 保留最近count条记录
                    if len(filtered_kline_list) > count:
                        filtered_kline_list = filtered_kline_list[-count:]
                    
                    cache_manager.cache_kline(symbol, kline_type, count, filtered_kline_list)
                    print(log_message)
                    
                    return filtered_kline_list
            
            return []
            
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            # 如果拉取失败且有缓存数据，返回缓存数据
            if cached_data:
                print(f"⚠️  拉取失败，返回缓存数据: {symbol} {kline_type.value} {len(cached_data)}条")
                return cached_data
            return []
    
    def fetch_stock_info(self, symbol: str, detail = True):
        """获取股票基本信息"""
        if not self._is_initialized:
            raise DataFetcherNotAvailableError("efinance 未初始化")
        
        try:
            info = self._ef.stock.get_base_info(symbol)
            
            if info is not None and hasattr(info, 'to_dict'):
                data = info.to_dict()
                
                if detail:
                    ret2 = self.get_more_stock_info(symbol, ['资产负债率'])
                data.update(ret2)
                ret = self._convert_to_stock_info(data, symbol)
                return ret

            return None
            
        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
            return None

    def get_more_stock_info(self, symbol, key_list = None):
        ret_dic = {}
        try:
            ret = ak.stock_financial_abstract(symbol=symbol)
            for idx,item in ret.iterrows():
                if key_list is None or item['指标'] in key_list:
                    ret_dic[item.iloc[1]] = item.iloc[2]
        except Exception as e:
            print(f"获取更多股票信息失败: {e}")
        return ret_dic

    def _convert_to_realtime_quote(self, data: Dict[str, Any], original_symbol: str) -> RealTimeQuote:
        """将efinance返回的数据转换为标准实时行情格式"""
        try:
            return RealTimeQuote(
                symbol=original_symbol,
                name=data.get('股票名称', data.get('name', '')),
                current_price=float(data.get('最新价', data.get('current_price', 0))),
                change=float(data.get('涨跌额', data.get('change', 0))),
                change_percent=float(data.get('涨跌幅', data.get('change_percent', 0))),
                volume=int(data.get('成交量', data.get('volume', 0))),
                amount=float(data.get('成交额', data.get('amount', 0))),
                high=float(data.get('最高', data.get('high', 0))),
                low=float(data.get('最低', data.get('low', 0))),
                open=float(data.get('今开', data.get('open', 0))),
                prev_close=float(data.get('昨收', data.get('prev_close', 0))),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
        except (ValueError, KeyError) as e:
            raise DataFetcherError(f"数据转换失败: {e}")
    
    def _convert_to_kline_data(self, data: Dict[str, Any], symbol: str) -> Optional[KLineData]:
        """将efinance返回的K线数据转换为标准格式"""
        try:
            return KLineData(
                symbol=symbol,
                datetime=str(data.get('日期', data.get('date', ''))),
                open=float(data.get('开盘', data.get('open', 0))),
                high=float(data.get('最高', data.get('high', 0))),
                low=float(data.get('最低', data.get('low', 0))),
                close=float(data.get('收盘', data.get('close', 0))),
                volume=int(data.get('成交量', data.get('volume', 0))),
                amount=data.get('成交额', data.get('amount'))
            )
        except (ValueError, KeyError) as e:
            print(f"K线数据转换失败: {e}")
            return None
    
    def format_symbol(self, symbol: str) -> str:
        """格式化股票代码为数据源要求的格式"""
        return symbol
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self._is_initialized
    
    def clear_cache(self, symbol: Optional[str] = None):
        """清理K线数据缓存"""
        cache_manager.clear_cache(symbol)
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        return cache_manager.get_cache_stats()
    
    def get_status(self) -> Dict[str, Dict[str, any]]:
        """
        获取数据获取器的状态
        
        Returns:
            Dict: 状态信息
        """
        status = {
            "efinance": {
                "name": self.name,
                "description": self.description,
                "available": self.is_available(),
                "class": self.__class__.__name__
            },
            "cache": self.get_cache_stats()
        }
        
        return status
    
    def __str__(self) -> str:
        return f"{self.name} - {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', available={self.is_available()})>"
    
    def _convert_to_stock_info(self, data: Dict[str, Any], original_symbol: str) -> Dict[str, Any]:
        """将efinance返回的股票基本信息转换为标准格式"""
        try:
            def safe_convert_float(value):
                """安全转换为浮点数，处理'-'和None值"""
                if value == '-' or value is None or str(value).strip() == '':
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            def safe_convert_str(value):
                """安全转换为字符串，处理'-'和'0.0'值"""
                if value == '-' or value is None or str(value).strip() == '0.0':
                    return None
                return str(value).strip() if str(value).strip() else None
            
            return {
                'symbol': data.get('股票代码', original_symbol),
                'name': data.get('股票名称', ''),
                'net_profit': safe_convert_str(data.get('净利润')),
                'total_market_value': safe_convert_float(data.get('总市值')),
                'circulating_market_value': safe_convert_float(data.get('流通市值')),
                'industry': safe_convert_str(data.get('所处行业')),
                'pe_ratio': safe_convert_str(data.get('市盈率(动)')),
                'pb_ratio': safe_convert_str(data.get('市净率')),
                'roe': safe_convert_str(data.get('ROE')),
                'gross_profit_margin': safe_convert_str(data.get('毛利率')),
                'net_profit_margin': safe_convert_str(data.get('净利率')),
                'sector_code': safe_convert_str(data.get('板块编号')),
                'debt_to_asset_ratio': safe_convert_str(data.get('资产负债率'))
            }
        except Exception as e:
            raise DataFetcherError(f"股票信息转换失败: {e}")


# 全局数据获取器实例
data_manager = StockDataFetcher()
if data_manager.initialize():
    print(f"✅ {data_manager.name} 初始化成功")
else:
    print(f"❌ {data_manager.name} 初始化失败")
