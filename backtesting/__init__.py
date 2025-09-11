"""
Backtesting module
Provides backtesting framework and visualization tools
"""

from .backtest import SimpleBacktest
from .visualizer import (
    BacktestVisualizer,
    plot_backtest_results,
    plot_single_strategy_analysis,
    plot_trade_details,
    plot_monthly_performance,
    check_font_setup
)

__all__ = [
    'SimpleBacktest',
    'BacktestVisualizer',
    'plot_backtest_results',
    'plot_single_strategy_analysis',
    'plot_trade_details',
    'plot_monthly_performance',
    'check_font_setup'
]
