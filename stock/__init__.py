# 后面可能去掉

"""
xystock 数据获取模块

该模块提供了统一的股票数据获取接口，支持A股数据：
- efinance: A股数据（东方财富）

使用示例：
    # 推荐用法：使用全局实例
    from xystock.data import data_manager
    
    # 获取实时行情
    quote = data_manager.get_realtime_quote("ETF")
    quote = data_manager.get_realtime_quote("沪深A股")
    
    # 获取K线数据
    kline = data_manager.get_kline_data("600519", KLineType.DAY, 30)
    
    # 方式2：创建新实例
    from xystock.data import StockDataFetcher, KLineType
    
    fetcher = StockDataFetcher()
    fetcher.initialize()
    quote = fetcher.get_realtime_quote("ETF")
"""

from utils.kline_cache import KLineData, KLineType
from stock.stock_data_fetcher import (
    StockDataFetcher,
    RealTimeQuote, 
    DataFetcherError,
    DataFetcherNotAvailableError,
    InvalidSymbolError,
    data_manager  # 全局实例
)

__all__ = [
    # 数据结构
    "KLineData", 
    "RealTimeQuote",
    "KLineType",
    
    # 异常类
    "DataFetcherError",
    "DataFetcherNotAvailableError", 
    "InvalidSymbolError",
    
    # 具体实现
    "StockDataFetcher",
    
    # 全局实例
    "data_manager",
]

__version__ = "1.0.0"
