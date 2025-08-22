"""
风险指标计算模块
提供核心金融风险指标的计算功能
"""

import pandas as pd
import numpy as np
from typing import Dict

class RiskCalculator:
    """风险指标计算器"""
    
    def __init__(self, trading_days_per_year: int = 252):
        """
        初始化风险计算器
        
        Args:
            trading_days_per_year: 每年交易日数量，默认252天
        """
        self.trading_days = trading_days_per_year
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """计算收益率序列"""
        return prices.pct_change().dropna()
    
    def annual_volatility(self, returns: pd.Series) -> float:
        """计算年化波动率"""
        return returns.std() * np.sqrt(self.trading_days)
    
    def max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()
    
    def sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """计算夏普比率"""
        daily_risk_free = risk_free_rate / self.trading_days
        excess_returns = returns - daily_risk_free
        return excess_returns.mean() / returns.std() * np.sqrt(self.trading_days)
    
    def value_at_risk(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """计算VaR (Value at Risk)"""
        return np.percentile(returns, confidence_level * 100)
    
    def conditional_var(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """计算CVaR (Conditional Value at Risk)"""
        var = self.value_at_risk(returns, confidence_level)
        return returns[returns <= var].mean()
        
    def calculate_all_metrics(self, 
                            prices: pd.Series, 
                            confidence_level: float = 0.05,
                            risk_free_rate: float = 0.03) -> Dict[str, float]:
        """
        计算所有风险指标
        
        Args:
            prices: 价格序列
            confidence_level: VaR/CVaR置信水平
            risk_free_rate: 无风险利率
            
        Returns:
            包含所有风险指标的字典
        """
        returns = self.calculate_returns(prices)
        
        if len(returns) == 0:
            raise ValueError("价格序列太短，无法计算收益率")
        
        metrics = {
            'annual_volatility': self.annual_volatility(returns),
            'max_drawdown': self.max_drawdown(returns),
            'sharpe_ratio': self.sharpe_ratio(returns, risk_free_rate),
            'var_95': self.value_at_risk(returns, confidence_level),
            'cvar_95': self.conditional_var(returns, confidence_level),
        }
        
        return metrics
    
    def get_risk_summary(self, 
                        prices: pd.Series,
                        confidence_level: float = 0.05,
                        risk_free_rate: float = 0.03) -> pd.DataFrame:
        """
        获取风险指标汇总表
        
        Args:
            prices: 价格序列
            confidence_level: VaR/CVaR置信水平
            risk_free_rate: 无风险利率
            
        Returns:
            风险指标汇总DataFrame
        """
        metrics = self.calculate_all_metrics(prices, confidence_level, risk_free_rate)
        
        risk_df = pd.DataFrame({
            '风险指标': [
                '年化波动率',
                '最大回撤', 
                '夏普比率',
                f'VaR ({(1-confidence_level)*100:.0f}%)',
                f'CVaR ({(1-confidence_level)*100:.0f}%)',
            ],
            '数值': [
                metrics['annual_volatility'],
                metrics['max_drawdown'],
                metrics['sharpe_ratio'],
                metrics['var_95'],
                metrics['cvar_95'],
            ]
        })
        
        # 添加百分比格式列
        risk_df['百分比形式'] = [
            f"{metrics['annual_volatility']*100:.2f}%",
            f"{metrics['max_drawdown']*100:.2f}%",
            f"{metrics['sharpe_ratio']:.4f}",
            f"{metrics['var_95']*100:.2f}%",
            f"{metrics['cvar_95']*100:.2f}%",
        ]
        
        return risk_df


def calculate_portfolio_risk(df: pd.DataFrame, 
                           price_col: str = 'close',
                           confidence_level: float = 0.05,
                           risk_free_rate: float = 0.03) -> Dict:
    """
    便捷函数：计算单个资产的风险指标
    
    Args:
        df: 包含价格数据的DataFrame
        price_col: 价格列名
        confidence_level: VaR/CVaR置信水平
        risk_free_rate: 无风险利率
        
    Returns:
        包含计算结果的字典
    """
    calculator = RiskCalculator()
    
    if price_col not in df.columns:
        raise ValueError(f"DataFrame中未找到列 '{price_col}'")
    
    prices = df[price_col].dropna()
    
    if len(prices) < 2:
        raise ValueError("价格数据不足，至少需要2个数据点")
    
    # 计算风险指标
    metrics = calculator.calculate_all_metrics(prices, confidence_level, risk_free_rate)
    risk_summary = calculator.get_risk_summary(prices, confidence_level, risk_free_rate)
    
    # 计算额外的分析数据
    returns = calculator.calculate_returns(prices)
    cumulative_returns = (1 + returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown_series = (cumulative_returns - running_max) / running_max
    
    return {
        'metrics': metrics,
        'summary_table': risk_summary,
        'returns': returns,
        'cumulative_returns': cumulative_returns,
        'drawdown_series': drawdown_series,
        'statistics': {
            'data_length': len(df),
            'returns_length': len(returns),
            'returns_mean': returns.mean(),
            'returns_std': returns.std(),
            'returns_min': returns.min(),
            'returns_max': returns.max()
        }
    }
