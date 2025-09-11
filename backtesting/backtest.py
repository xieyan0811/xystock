"""
简单回测框架
支持基本的买卖策略回测、绩效计算和可视化
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable
from datetime import datetime, timedelta


class SimpleBacktest:
    """简单回测引擎"""
    
    def __init__(self, initial_cash: float = 100000):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.position = 0  # 持仓数量
        self.total_value = initial_cash  # 总资产
        
        # 记录历史
        self.history = []
        self.trades = []
        
        # 统计指标
        self.max_drawdown = 0
        self.max_value = initial_cash
        
    def reset(self):
        """重置回测状态"""
        self.cash = self.initial_cash
        self.position = 0
        self.total_value = self.initial_cash
        self.history = []
        self.trades = []
        self.max_drawdown = 0
        self.max_value = self.initial_cash
        
    def buy(self, price: float, volume: int, date: str):
        """买入操作"""
        cost = price * volume
        if cost <= self.cash:
            self.cash -= cost
            self.position += volume
            self.trades.append({
                'date': date,
                'action': 'buy',
                'price': price,
                'volume': volume,
                'cost': cost
            })
            return True
        return False
    
    def sell(self, price: float, volume: int, date: str):
        """卖出操作"""
        if volume <= self.position:
            self.cash += price * volume
            self.position -= volume
            self.trades.append({
                'date': date,
                'action': 'sell',
                'price': price,
                'volume': volume,
                'revenue': price * volume
            })
            return True
        return False
    
    def update_value(self, current_price: float, date: str):
        """更新总资产"""
        self.total_value = self.cash + self.position * current_price
        
        # 更新最大回撤
        if self.total_value > self.max_value:
            self.max_value = self.total_value
        
        drawdown = (self.max_value - self.total_value) / self.max_value
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # 记录历史
        self.history.append({
            'date': date,
            'cash': self.cash,
            'position': self.position,
            'current_price': current_price,
            'total_value': self.total_value,
            'drawdown': drawdown
        })
    
    def run_backtest(self, data: pd.DataFrame, strategy: Callable):
        """
        运行回测
        
        Args:
            data: 包含日期、价格等信息的DataFrame
            strategy: 策略函数，接收(index, row, backtest)参数，返回交易信号
        """
        print("开始回测...")
        
        for i, row in data.iterrows():
            # 执行策略
            signal = strategy(i, row, self)
            
            # 处理交易信号
            if signal == 'buy' and self.cash > 0:
                # 全仓买入
                max_shares = int(self.cash / row['close'])
                if max_shares > 0:
                    self.buy(row['close'], max_shares, str(row['date']))
            
            elif signal == 'sell' and self.position > 0:
                # 全部卖出
                self.sell(row['close'], self.position, str(row['date']))
            
            # 更新资产价值
            self.update_value(row['close'], str(row['date']))
        
        print("回测完成!")
        return self.get_results()
    
    def get_results(self) -> Dict:
        """获取回测结果"""
        if not self.history:
            return {}
        
        history_df = pd.DataFrame(self.history)
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        
        # 计算收益率
        total_return = (self.total_value - self.initial_cash) / self.initial_cash
        
        # 计算年化收益率（假设250个交易日）
        days = len(history_df)
        annual_return = (1 + total_return) ** (250 / days) - 1 if days > 0 else 0
        
        # 计算夏普比率
        returns = history_df['total_value'].pct_change().dropna()
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(250) if len(returns) > 1 else 0
        
        # 胜率计算
        if len(trades_df) > 0:
            buy_trades = trades_df[trades_df['action'] == 'buy']
            sell_trades = trades_df[trades_df['action'] == 'sell']
            
            win_count = 0
            total_trades = min(len(buy_trades), len(sell_trades))
            
            for i in range(total_trades):
                if sell_trades.iloc[i]['price'] > buy_trades.iloc[i]['price']:
                    win_count += 1
            
            win_rate = win_count / total_trades if total_trades > 0 else 0
        else:
            win_rate = 0
            total_trades = 0
        
        results = {
            'initial_cash': self.initial_cash,
            'final_value': self.total_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'history': history_df,
            'trades': trades_df
        }
        
        return results
    
    def print_summary(self, results: Dict):
        """打印回测摘要"""
        print("\n" + "="*50)
        print("回测结果摘要")
        print("="*50)
        print(f"初始资金: {results['initial_cash']:,.2f}")
        print(f"最终资产: {results['final_value']:,.2f}")
        print(f"总收益率: {results['total_return']:.2%}")
        print(f"年化收益率: {results['annual_return']:.2%}")
        print(f"最大回撤: {results['max_drawdown']:.2%}")
        print(f"夏普比率: {results['sharpe_ratio']:.3f}")
        print(f"交易次数: {results['total_trades']}")
        print(f"胜率: {results['win_rate']:.2%}")
        print("="*50)


# 示例策略函数
def simple_ma_strategy(index: int, row: pd.Series, backtest: SimpleBacktest) -> str:
    """
    简单移动平均策略示例
    当价格上穿5日均线时买入，下穿时卖出
    """
    # 需要足够的历史数据计算均线
    if index < 5:
        return 'hold'
    
    # 假设数据包含ma5字段，或者在这里计算
    # 这里简化处理，实际使用时需要传入包含技术指标的数据
    if hasattr(row, 'ma5'):
        if row['close'] > row['ma5'] and backtest.position == 0:
            return 'buy'
        elif row['close'] < row['ma5'] and backtest.position > 0:
            return 'sell'
    
    return 'hold'


def momentum_strategy(index: int, row: pd.Series, backtest: SimpleBacktest) -> str:
    """
    动量策略示例
    当日涨幅超过2%时买入，跌幅超过1%时卖出
    """
    if hasattr(row, 'pct_change'):
        if row['pct_change'] > 0.02 and backtest.position == 0:
            return 'buy'
        elif row['pct_change'] < -0.01 and backtest.position > 0:
            return 'sell'
    
    return 'hold'


# 示例用法
if __name__ == "__main__":
    # 创建示例数据
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'pct_change': np.random.randn(len(dates)) * 0.02  # 模拟涨跌幅
    })
    
    # 运行回测
    bt = SimpleBacktest(initial_cash=100000)
    results = bt.run_backtest(data, momentum_strategy)
    
    # 展示结果
    bt.print_summary(results)
    
    # 使用可视化模块绘制图表
    # from backtesting.visualizer import plot_single_strategy_analysis
    # plot_single_strategy_analysis(results, "动量策略", data)
