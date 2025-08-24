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
    便捷函数：计算单个资产的风险指标（完整版本，包含时间序列）
    
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


def calculate_portfolio_risk_summary(df: pd.DataFrame, 
                                   price_col: str = 'close',
                                   confidence_level: float = 0.05,
                                   risk_free_rate: float = 0.03) -> Dict:
    """
    计算单个资产的风险指标摘要（精简版本，仅统计信息，用于缓存）
    
    Args:
        df: 包含价格数据的DataFrame
        price_col: 价格列名
        confidence_level: VaR/CVaR置信水平
        risk_free_rate: 无风险利率
        
    Returns:
        包含关键统计信息的字典，适合缓存和给大模型分析
    """
    calculator = RiskCalculator()
    
    if price_col not in df.columns:
        raise ValueError(f"DataFrame中未找到列 '{price_col}'")
    
    prices = df[price_col].dropna()
    
    if len(prices) < 2:
        raise ValueError("价格数据不足，至少需要2个数据点")
    
    # 计算风险指标（只保留关键统计数据）
    metrics = calculator.calculate_all_metrics(prices, confidence_level, risk_free_rate)
    returns = calculator.calculate_returns(prices)
    
    # 计算价格趋势
    price_change = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
    recent_volatility = returns.tail(20).std() * np.sqrt(252) if len(returns) >= 20 else returns.std() * np.sqrt(252)
    
    # 构建适合大模型分析的风险摘要
    risk_analysis = {
        'period_analysis': {
            'data_length': len(df),
            'price_change_pct': float(price_change * 100),  # 期间涨跌幅
            'trend_direction': 'up' if price_change > 0 else 'down',
        },
        'volatility_analysis': {
            'annual_volatility': float(metrics['annual_volatility']),
            'recent_volatility': float(recent_volatility),
            'volatility_trend': 'increasing' if recent_volatility > metrics['annual_volatility'] else 'decreasing',
        },
        'risk_metrics': {
            'max_drawdown': float(metrics['max_drawdown']),
            'sharpe_ratio': float(metrics['sharpe_ratio']),
            'var_5pct': float(metrics['var_95']),
            'cvar_5pct': float(metrics['cvar_95']),
        },
        'return_statistics': {
            'daily_return_mean': float(returns.mean()),
            'daily_return_std': float(returns.std()),
            'positive_days_ratio': float((returns > 0).mean()),
            'max_single_day_gain': float(returns.max()),
            'max_single_day_loss': float(returns.min()),
        },
        'risk_assessment': {
            'risk_level': _assess_risk_level(metrics['annual_volatility'], metrics['max_drawdown']),
            'stability': _assess_stability(returns),
            'trend_strength': _assess_trend_strength(price_change, metrics['annual_volatility']),
        }
    }
    
    return risk_analysis


def _assess_risk_level(volatility: float, max_drawdown: float) -> str:
    """评估风险水平"""
    if volatility > 0.3 or abs(max_drawdown) > 0.2:
        return 'high'
    elif volatility > 0.2 or abs(max_drawdown) > 0.1:
        return 'medium'
    else:
        return 'low'


def _assess_stability(returns: pd.Series) -> str:
    """评估稳定性"""
    volatility = returns.std()
    skewness = returns.skew()
    
    if abs(skewness) > 1 or volatility > returns.mean() * 3:
        return 'unstable'
    elif abs(skewness) > 0.5 or volatility > returns.mean() * 2:
        return 'moderate'
    else:
        return 'stable'


def _assess_trend_strength(price_change: float, volatility: float) -> str:
    """评估趋势强度"""
    if abs(price_change) > volatility * 2:
        return 'strong'
    elif abs(price_change) > volatility:
        return 'moderate'
    else:
        return 'weak'
