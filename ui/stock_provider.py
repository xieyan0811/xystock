"""
股票数据获取模块 - 简化版本用于UI测试
"""

import datetime
import random
from typing import Dict, Any

class SimpleStockDataProvider:
    """简单的股票数据提供者，用于UI测试"""
    
    def __init__(self):
        # 模拟数据字典
        self.mock_data = {
            # A股示例
            "000001": {"name": "平安银行", "price": 13.45, "change": 0.23},
            "000002": {"name": "万科A", "price": 18.67, "change": -0.15},
            "600000": {"name": "浦发银行", "price": 9.12, "change": 0.08},
            "600036": {"name": "招商银行", "price": 42.35, "change": 0.56},
            
            # 港股示例
            "00700": {"name": "腾讯控股", "price": 380.20, "change": 5.60},
            "00941": {"name": "中国移动", "price": 52.40, "change": -0.80},
            
            # 指数示例
            "399001": {"name": "深证成指", "price": 9876.54, "change": 123.45},
            "000001": {"name": "上证指数", "price": 3234.56, "change": -12.34},
        }
    
    def get_stock_info(self, stock_code: str, market_type: str) -> str:
        """
        获取股票信息
        
        Args:
            stock_code: 股票代码
            market_type: 市场类型 (A股/港股/指数/基金)
            
        Returns:
            格式化的股票信息字符串
        """
        try:
            # 检查是否有模拟数据
            if stock_code in self.mock_data:
                data = self.mock_data[stock_code]
                return self._format_stock_info(stock_code, market_type, data)
            else:
                # 生成随机模拟数据
                data = self._generate_mock_data()
                return self._format_stock_info(stock_code, market_type, data)
                
        except Exception as e:
            return f"获取股票信息失败: {str(e)}"
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """生成随机模拟数据"""
        base_price = random.uniform(10, 200)
        change_percent = random.uniform(-10, 10)
        change_amount = base_price * (change_percent / 100)
        
        return {
            "name": f"股票{random.randint(1000, 9999)}",
            "price": round(base_price, 2),
            "change": round(change_amount, 2),
            "change_percent": round(change_percent, 2)
        }
    
    def _format_stock_info(self, stock_code: str, market_type: str, data: Dict[str, Any]) -> str:
        """格式化股票信息显示"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算涨跌幅百分比
        if "change_percent" not in data and "price" in data and "change" in data:
            if data["price"] != 0:
                data["change_percent"] = round((data["change"] / (data["price"] - data["change"])) * 100, 2)
            else:
                data["change_percent"] = 0.0
        
        # 涨跌标识
        if data["change"] > 0:
            trend = "📈 上涨"
            change_symbol = "+"
        elif data["change"] < 0:
            trend = "📉 下跌" 
            change_symbol = ""
        else:
            trend = "➡️ 平盘"
            change_symbol = ""
        
        info = f"""
╔═══════════════════════════════════════════════════════════════╗
║                        股票信息查询结果                          ║
╠═══════════════════════════════════════════════════════════════╣
║ 市场类型: {market_type:<10} │ 查询时间: {current_time}    ║
║ 股票代码: {stock_code:<10} │ 股票名称: {data.get('name', '未知'):<15} ║
╠═══════════════════════════════════════════════════════════════╣
║ 当前价格: {data['price']:<10.2f} │ 涨跌金额: {change_symbol}{data['change']:<10.2f} ║
║ 涨跌幅度: {change_symbol}{data.get('change_percent', 0):<8.2f}% │ 走势状态: {trend:<10} ║
╠═══════════════════════════════════════════════════════════════╣
║ 更多信息:                                                      ║
║ • 成交量: {random.randint(1000000, 99999999):,} 手                    ║
║ • 成交额: {random.randint(100000000, 9999999999):,} 元                ║
║ • 换手率: {random.uniform(0.1, 15):.2f}%                                ║
║ • 市盈率: {random.uniform(5, 50):.2f}                                   ║
╚═══════════════════════════════════════════════════════════════╝

💡 提示: 以上数据为模拟数据，仅用于系统演示
⚠️  免责声明: 股市有风险，投资需谨慎
        """
        
        return info.strip()

# 创建全局实例
stock_data_provider = SimpleStockDataProvider()
