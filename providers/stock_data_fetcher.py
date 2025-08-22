"""
基于 efinance 的A股数据获取器（集成缓存管理）
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from providers.cache_manager import cache_manager, KLineData, KLineType


@dataclass
class RealTimeQuote:
    """实时行情数据结构"""
    symbol: str            # 股票代码
    name: str              # 股票名称
    current_price: float   # 当前价格
    change: float          # 涨跌额
    change_percent: float  # 涨跌幅(%)
    volume: int            # 成交量
    amount: float          # 成交额
    high: float            # 最高价
    low: float             # 最低价
    open: float            # 开盘价
    prev_close: float      # 昨收价
    timestamp: str         # 时间戳


@dataclass
class StockInfo:
    """股票基本信息数据结构"""
    symbol: str                    # 股票代码
    name: str                      # 股票名称
    net_profit: Optional[str]      # 净利润
    total_market_value: Optional[float]  # 总市值
    circulating_market_value: Optional[float]  # 流通市值
    industry: Optional[str]        # 所处行业
    pe_ratio: Optional[str]        # 市盈率(动)
    pb_ratio: Optional[str]        # 市净率
    roe: Optional[str]             # ROE
    gross_profit_margin: Optional[str]  # 毛利率
    net_profit_margin: Optional[str]    # 净利率
    sector_code: Optional[str]     # 板块编号


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
    """efinance 数据获取器，专门用于A股数据"""
    
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
        """
        获取A股实时行情数据
        
        Args:
            symbol: 股票范围（如：沪深A股，可转债，期货……）
            max_retry: 最大重试次数
            
        Returns:
            RealTimeQuote: 实时行情数据
        """
        if not self._is_initialized:
            raise DataFetcherNotAvailableError("efinance 未初始化")
        
        formatted_symbol = self.format_symbol(symbol)
        
        for attempt in range(1, max_retry + 1):
            try:
                # 获取实时行情
                quotes_df = self._ef.stock.get_latest_quote(formatted_symbol)
                
                if quotes_df is not None and not quotes_df.empty:
                    # 处理DataFrame数据
                    if hasattr(quotes_df, "to_dict"):
                        if hasattr(quotes_df, "shape") and len(quotes_df.shape) > 1:
                            # DataFrame
                            records = quotes_df.to_dict(orient="records")
                            if records:
                                data = records[0]
                            else:
                                continue
                        else:
                            # Series
                            data = quotes_df.to_dict()
                        
                        # 转换为标准格式
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
                      count: int = 30,
                      force: bool = False) -> List[KLineData]:
        """
        获取K线数据（支持缓存）
        
        Args:
            symbol: 股票代码（如:600519, AAPL, 微软，ETF Code）
            kline_type: K线类型
            count: 获取条数
            force: 是否强制从数据源获取新数据，忽略缓存
            
        Returns:
            List[KLineData]: K线数据列表
        """
        if not self._is_initialized:
            raise DataFetcherNotAvailableError("efinance 未初始化")
        
        if kline_type not in self._kline_type_mapping:
            raise DataFetcherError(f"不支持的K线类型: {kline_type}")
        
        symbol = symbol.upper().strip()
        
        # 如果不强制刷新，先尝试从缓存获取
        if not force:
            cached_data = cache_manager.get_cached_kline(symbol, kline_type, count)
            if cached_data:
                print(f"📦 从缓存获取K线数据: {symbol} {kline_type.value} {len(cached_data)}条")
                return cached_data

        try:
            formatted_symbol = self.format_symbol(symbol)
            klt = self._kline_type_mapping[kline_type]
            
            # 获取K线数据
            kline_df = self._ef.stock.get_quote_history(formatted_symbol, klt=klt)
            
            if kline_df is not None and not kline_df.empty:
                # 保留最近count条记录
                if len(kline_df) > count:
                    kline_df = kline_df.tail(count)
                
                # 转换为标准格式
                kline_list = []
                if hasattr(kline_df, "to_dict"):
                    records = kline_df.to_dict(orient="records")
                    for record in records:
                        kline_data = self._convert_to_kline_data(record, symbol)
                        if kline_data:
                            kline_list.append(kline_data)
                
                # 如果成功获取到数据，则缓存
                if kline_list:
                    cache_manager.cache_kline(symbol, kline_type, count, kline_list)
                    print(f"🔄 从数据源获取K线数据: {symbol} {kline_type.value} {len(kline_list)}条")
                
                return kline_list
            
            return []
            
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return []
    
    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码或名称（如：'600519', '贵州茅台', '上证指数'）
            
        Returns:
            StockInfo: 股票基本信息
        """
        if not self._is_initialized:
            raise DataFetcherNotAvailableError("efinance 未初始化")
        
        try:
            # 获取股票基本信息
            info = self._ef.stock.get_base_info(symbol)
            
            if info is not None and hasattr(info, 'to_dict'):
                # 将Series转换为字典
                data = info.to_dict()
                
                # 转换为标准格式
                return self._convert_to_stock_info(data, symbol)
            
            return None
            
        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
            return None
    
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
        """
        格式化股票代码为数据源要求的格式
        
        Args:
            symbol: 原始股票代码
            
        Returns:
            str: 格式化后的股票代码
        """
        return symbol
    
    def is_available(self) -> bool:
        """
        检查数据源是否可用
        
        Returns:
            bool: 是否可用
        """
        return self._is_initialized
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        清理K线数据缓存
        
        Args:
            symbol: 指定股票代码，不指定则清理所有缓存
        """
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
    def _convert_to_stock_info(self, data: Dict[str, Any], original_symbol: str) -> StockInfo:
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
                """安全转换为字符串，处理'-'值"""
                if value == '-' or value is None:
                    return None
                return str(value).strip() if str(value).strip() else None
            
            return StockInfo(
                symbol=data.get('股票代码', original_symbol),
                name=data.get('股票名称', ''),
                net_profit=safe_convert_str(data.get('净利润')),
                total_market_value=safe_convert_float(data.get('总市值')),
                circulating_market_value=safe_convert_float(data.get('流通市值')),
                industry=safe_convert_str(data.get('所处行业')),
                pe_ratio=safe_convert_str(data.get('市盈率(动)')),
                pb_ratio=safe_convert_str(data.get('市净率')),
                roe=safe_convert_str(data.get('ROE')),
                gross_profit_margin=safe_convert_str(data.get('毛利率')),
                net_profit_margin=safe_convert_str(data.get('净利率')),
                sector_code=safe_convert_str(data.get('板块编号'))
            )
        except Exception as e:
            raise DataFetcherError(f"股票信息转换失败: {e}")


# 全局数据获取器实例
data_manager = StockDataFetcher()
# 自动初始化
if data_manager.initialize():
    print(f"✅ {data_manager.name} 初始化成功")
else:
    print(f"❌ {data_manager.name} 初始化失败")
