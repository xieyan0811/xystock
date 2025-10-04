"""
回测结果可视化模块
提供各种图表绘制功能，支持策略对比和详细分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
import subprocess
import os
from typing import Dict, List, Optional


class BacktestVisualizer:
    """回测结果可视化工具"""
    
    def __init__(self):
        """初始化可视化工具，配置字体"""
        self._setup_fonts()
        self._font_initialized = True
    
    def _setup_fonts(self):
        """设置中文字体配置"""
        # 忽略字体警告
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
        warnings.filterwarnings('ignore', category=UserWarning, message='.*font.*')
        warnings.filterwarnings('ignore', category=UserWarning, message='.*findfont.*')
        
        # 获取系统所有字体名称
        available_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        # 常见中文字体列表（按优先级排序）
        chinese_fonts = [
            'WenQuanYi Micro Hei',  # 文泉驿微米黑
            'SimHei',               # 黑体
            'Microsoft YaHei',      # 微软雅黑
            'Noto Sans CJK SC',     # Google Noto字体
            'Source Han Sans CN',   # 思源黑体
            'DejaVu Sans'           # 备用英文字体
        ]
        
        # 找到第一个可用的中文字体
        found_font = None
        for font in chinese_fonts:
            if font in available_fonts:
                found_font = font
                break
        
        # 设置字体配置
        if found_font and found_font != 'DejaVu Sans':
            plt.rcParams['font.sans-serif'] = [found_font, 'DejaVu Sans']
            self.font_available = True
            self.current_font = found_font
        else:
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            self.font_available = False
            self.current_font = 'DejaVu Sans'
        
        plt.rcParams['axes.unicode_minus'] = False
        
        # 刷新字体缓存
        fm._load_fontmanager(try_read_cache=False)
    
    def _ensure_font_setup(self):
        """确保字体已正确设置（内部使用）"""
        if not hasattr(self, '_font_initialized'):
            self._setup_fonts()
            self._font_initialized = True
    
    def install_chinese_fonts(self):
        """自动安装中文字体（仅Linux系统）"""
        print("=== 检测系统并安装中文字体 ===")
        
        try:
            # 检测操作系统
            import platform
            system = platform.system()
            
            if system == "Linux":
                print("检测到Linux系统，尝试安装中文字体...")
                
                # 检查是否有 apt 包管理器
                result = subprocess.run(['which', 'apt-get'], capture_output=True)
                if result.returncode == 0:
                    print("正在安装文泉驿微米黑字体...")
                    try:
                        # 安装字体包
                        subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
                        subprocess.run(['apt-get', 'install', '-y', 'fonts-wqy-microhei'], 
                                     check=True, capture_output=True)
                        
                        # 刷新字体缓存
                        subprocess.run(['fc-cache', '-fv'], check=True, capture_output=True)
                        
                        print("✅ 中文字体安装成功！")
                        
                        # 重新初始化字体设置
                        self._setup_fonts()
                        return True
                        
                    except subprocess.CalledProcessError as e:
                        print(f"❌ 字体安装失败: {e}")
                        print("请手动执行: sudo apt-get install fonts-wqy-microhei")
                        return False
                else:
                    print("❌ 未找到apt包管理器，请手动安装中文字体")
                    return False
            else:
                print(f"检测到{system}系统，请手动安装中文字体")
                if system == "Darwin":  # macOS
                    print("macOS建议: brew install font-wqy-microhei")
                elif system == "Windows":
                    print("Windows系统通常已包含中文字体")
                return False
                
        except Exception as e:
            print(f"字体安装过程出错: {e}")
            return False
    
    def test_font_display(self):
        """测试字体显示效果并生成测试图表"""
        print("=== 字体显示测试 ===")
        
        # 获取系统所有字体名称
        available_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        # 常见中文字体列表
        test_fonts = [
            'WenQuanYi Micro Hei',
            'SimHei',
            'Microsoft YaHei',
            'Noto Sans CJK SC',
            'Source Han Sans CN',
            'DejaVu Sans'
        ]
        
        # 创建测试图表
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Font Display Test / 字体显示测试', fontsize=16)
        
        for i, font_name in enumerate(test_fonts):
            row = i // 3
            col = i % 3
            ax = axes[row, col]
            
            # 测试字体是否可用
            if font_name in available_fonts:
                status = "✅ 可用"
                test_text = f"字体测试: {font_name}\nFont Test: {font_name}\n数字: 123456\nNumbers: 123456"
                color = 'green'
                
                # 临时设置字体
                original_font = plt.rcParams['font.sans-serif']
                plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
                
                ax.text(0.5, 0.5, test_text, ha='center', va='center', 
                       fontsize=10, transform=ax.transAxes, color=color)
                
                # 恢复原字体设置
                plt.rcParams['font.sans-serif'] = original_font
            else:
                status = "❌ 不可用"
                test_text = f"Font not available: {font_name}"
                color = 'red'
                
                ax.text(0.5, 0.5, test_text, ha='center', va='center',
                       fontsize=10, transform=ax.transAxes, color=color)
            
            ax.set_title(f"{font_name}\n{status}", fontsize=8)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        
        plt.tight_layout()
        plt.show()
        
        # 输出当前字体配置信息
        print(f"\n当前字体配置:")
        print(f"  主字体: {self.current_font}")
        print(f"  中文支持: {'是' if self.font_available else '否'}")
        print(f"  matplotlib字体设置: {plt.rcParams['font.sans-serif']}")
        
        return available_fonts
    
    def get_system_fonts_info(self):
        """获取系统字体详细信息"""
        print("=== 系统字体信息 ===")
        
        # 获取所有字体
        all_fonts = fm.fontManager.ttflist
        
        # 按字体名称分组
        font_families = {}
        for font in all_fonts:
            family = font.name
            if family not in font_families:
                font_families[family] = []
            font_families[family].append({
                'file': font.fname,
                'style': font.style,
                'weight': font.weight
            })
        
        # 查找中文字体
        chinese_keywords = ['Chinese', 'CJK', 'Han', 'Hei', 'Micro', 'YaHei', 'SimHei', 'WenQuanYi']
        chinese_fonts = []
        
        for family_name, fonts in font_families.items():
            for keyword in chinese_keywords:
                if keyword.lower() in family_name.lower():
                    chinese_fonts.append(family_name)
                    break
        
        print(f"总共找到 {len(font_families)} 个字体族")
        print(f"疑似中文字体 {len(chinese_fonts)} 个:")
        
        for font in sorted(chinese_fonts):
            print(f"  - {font}")
        
        # 推荐的中文字体
        recommended_fonts = [
            'WenQuanYi Micro Hei',
            'SimHei', 
            'Microsoft YaHei',
            'Noto Sans CJK SC',
            'Source Han Sans CN'
        ]
        
        print(f"\n推荐中文字体安装状态:")
        for font in recommended_fonts:
            status = "✅" if font in font_families else "❌"
            print(f"  {status} {font}")
        
        return font_families, chinese_fonts
    
    def set_custom_font(self, font_name: str):
        """设置自定义字体"""
        print(f"=== 设置自定义字体: {font_name} ===")
        
        # 检查字体是否可用
        available_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        if font_name in available_fonts:
            plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
            self.current_font = font_name
            self.font_available = True
            print(f"✅ 成功设置字体: {font_name}")
            
            # 测试显示效果
            plt.figure(figsize=(8, 4))
            plt.text(0.5, 0.7, f'当前字体: {font_name}', ha='center', va='center', fontsize=16)
            plt.text(0.5, 0.5, '中文显示测试: 回测分析图表', ha='center', va='center', fontsize=14)
            plt.text(0.5, 0.3, 'English Display Test: Backtest Analysis', ha='center', va='center', fontsize=12)
            plt.title(f'Custom Font Test - {font_name}')
            plt.xlim(0, 1)
            plt.ylim(0, 1)
            plt.axis('off')
            plt.tight_layout()
            plt.show()
            
            return True
        else:
            print(f"❌ 字体不可用: {font_name}")
            print("可用的字体列表:")
            for font in sorted(available_fonts):
                if any(keyword in font.lower() for keyword in ['chinese', 'cjk', 'han', 'hei', 'micro']):
                    print(f"  - {font}")
            return False
    
    def plot_single_strategy(self, results: Dict, strategy_name: str = "策略", 
                           benchmark_data: Optional[pd.DataFrame] = None):
        """
        绘制单个策略的详细分析图表
        
        Args:
            results: 回测结果字典
            strategy_name: 策略名称
            benchmark_data: 基准数据（用于对比）
        """
        self._ensure_font_setup()
        
        if results['history'].empty:
            print("没有历史数据可绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        title = f'{strategy_name} 回测结果分析' if self.font_available else f'{strategy_name} Backtest Analysis'
        fig.suptitle(title, fontsize=16)
        
        history = results['history']
        
        # 1. 资产曲线
        ax1 = axes[0, 0]
        ax1.plot(history['total_value'], label=strategy_name, color='blue', linewidth=2)
        
        # 添加基准线（买入持有策略）
        if benchmark_data is not None:
            initial_value = results['initial_cash']
            buy_hold_value = initial_value * (benchmark_data['close'] / benchmark_data['close'].iloc[0])
            ax1.plot(buy_hold_value.values[:len(history)], 
                    label='买入持有' if self.font_available else 'Buy & Hold', 
                    color='red', linestyle='--', alpha=0.7)
        
        title1 = '资产价值变化曲线' if self.font_available else 'Portfolio Value'
        ylabel1 = '资产价值 (元)' if self.font_available else 'Value'
        ax1.set_title(title1)
        ax1.set_ylabel(ylabel1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 回撤曲线
        ax2 = axes[0, 1]
        ax2.fill_between(range(len(history)), -history['drawdown'], 0, 
                        alpha=0.3, color='red', label='回撤' if self.font_available else 'Drawdown')
        title2 = '回撤曲线' if self.font_available else 'Drawdown'
        ylabel2 = '回撤率' if self.font_available else 'Drawdown Rate'
        ax2.set_title(title2)
        ax2.set_ylabel(ylabel2)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 收益分布
        ax3 = axes[1, 0]
        if len(history) > 1:
            returns = history['total_value'].pct_change().dropna()
            ax3.hist(returns, bins=30, alpha=0.7, color='green')
            title3 = '日收益分布' if self.font_available else 'Daily Returns Distribution'
            xlabel3 = '收益率' if self.font_available else 'Return Rate'
            ax3.set_title(title3)
            ax3.set_xlabel(xlabel3)
            ax3.grid(True, alpha=0.3)
        
        # 4. 持仓变化
        ax4 = axes[1, 1]
        ax4.plot(history['position'], color='orange', linewidth=2)
        title4 = '持仓变化' if self.font_available else 'Position Changes'
        ylabel4 = '持仓数量' if self.font_available else 'Position Size'
        ax4.set_title(title4)
        ax4.set_ylabel(ylabel4)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_strategy_comparison(self, all_results: Dict[str, Dict], 
                               benchmark_data: Optional[pd.DataFrame] = None):
        """
        绘制多个策略的对比分析图表
        
        Args:
            all_results: 所有策略的回测结果字典
            benchmark_data: 基准数据
        """
        self._ensure_font_setup()
        
        if not all_results:
            print("没有策略结果可绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        title = '策略对比分析' if self.font_available else 'Strategy Comparison'
        fig.suptitle(title, fontsize=16)
        
        # 颜色列表
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        # 1. 资产曲线对比
        ax1 = axes[0, 0]
        for i, (strategy_name, results) in enumerate(all_results.items()):
            if not results['history'].empty:
                ax1.plot(results['history']['total_value'], 
                        label=strategy_name, color=colors[i % len(colors)], linewidth=2)
        
        # 添加基准线
        if benchmark_data is not None:
            first_result = next(iter(all_results.values()))
            initial_value = first_result['initial_cash']
            max_len = max(len(results['history']) for results in all_results.values())
            buy_hold_value = initial_value * (benchmark_data['close'] / benchmark_data['close'].iloc[0])
            ax1.plot(buy_hold_value.values[:max_len], 
                    label='买入持有' if self.font_available else 'Buy & Hold', 
                    color='black', linestyle='--', alpha=0.7)
        
        title1 = '资产价值变化曲线' if self.font_available else 'Portfolio Value Comparison'
        ylabel1 = '资产价值 (元)' if self.font_available else 'Value'
        ax1.set_title(title1)
        ax1.set_ylabel(ylabel1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 回撤对比
        ax2 = axes[0, 1]
        for i, (strategy_name, results) in enumerate(all_results.items()):
            if not results['history'].empty:
                ax2.fill_between(range(len(results['history'])), 
                               -results['history']['drawdown'], 
                               0, alpha=0.3, color=colors[i % len(colors)], 
                               label=strategy_name)
        title2 = '回撤曲线对比' if self.font_available else 'Drawdown Comparison'
        ylabel2 = '回撤率' if self.font_available else 'Drawdown Rate'
        ax2.set_title(title2)
        ax2.set_ylabel(ylabel2)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 收益率对比柱状图
        ax3 = axes[1, 0]
        strategy_names = list(all_results.keys())
        returns = [results['total_return'] for results in all_results.values()]
        bars = ax3.bar(strategy_names, returns, color=colors[:len(strategy_names)])
        title3 = '总收益率对比' if self.font_available else 'Total Return Comparison'
        ylabel3 = '收益率' if self.font_available else 'Return Rate'
        ax3.set_title(title3)
        ax3.set_ylabel(ylabel3)
        ax3.tick_params(axis='x', rotation=45)
        
        # 在柱状图上添加数值标签
        for bar, return_val in zip(bars, returns):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{return_val:.2%}', ha='center', va='bottom')
        
        # 4. 风险收益散点图
        ax4 = axes[1, 1]
        for i, (strategy_name, results) in enumerate(all_results.items()):
            ax4.scatter(results['max_drawdown'], results['annual_return'], 
                       s=100, color=colors[i % len(colors)], label=strategy_name, alpha=0.7)
        xlabel4 = '最大回撤' if self.font_available else 'Max Drawdown'
        ylabel4 = '年化收益率' if self.font_available else 'Annual Return'
        title4 = '风险收益分析' if self.font_available else 'Risk-Return Analysis'
        ax4.set_xlabel(xlabel4)
        ax4.set_ylabel(ylabel4)
        ax4.set_title(title4)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_trade_analysis(self, results: Dict, strategy_name: str = "策略"):
        """
        绘制交易分析图表
        
        Args:
            results: 回测结果字典
            strategy_name: 策略名称
        """
        self._ensure_font_setup()
        
        if results['trades'].empty:
            print("没有交易记录可分析")
            return
        
        trades_df = results['trades']
        history_df = results['history']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        title = f'{strategy_name} 交易分析' if self.font_available else f'{strategy_name} Trade Analysis'
        fig.suptitle(title, fontsize=16)
        
        # 1. 价格和交易点位
        ax1 = axes[0, 0]
        ax1.plot(history_df['current_price'], label='价格' if self.font_available else 'Price', alpha=0.7)
        
        buy_trades = trades_df[trades_df['action'] == 'buy']
        sell_trades = trades_df[trades_df['action'] == 'sell']
        
        if not buy_trades.empty:
            buy_indices = [i for i, date in enumerate(history_df['date']) 
                          if date in buy_trades['date'].values]
            ax1.scatter(buy_indices, [history_df.iloc[i]['current_price'] for i in buy_indices], 
                       color='green', marker='^', s=100, label='买入' if self.font_available else 'Buy')
        
        if not sell_trades.empty:
            sell_indices = [i for i, date in enumerate(history_df['date']) 
                           if date in sell_trades['date'].values]
            ax1.scatter(sell_indices, [history_df.iloc[i]['current_price'] for i in sell_indices], 
                       color='red', marker='v', s=100, label='卖出' if self.font_available else 'Sell')
        
        title1 = '价格与交易点位' if self.font_available else 'Price & Trade Points'
        ylabel1 = '价格' if self.font_available else 'Price'
        ax1.set_title(title1)
        ax1.set_ylabel(ylabel1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 交易频率分析
        ax2 = axes[0, 1]
        if not trades_df.empty:
            trades_df['date'] = pd.to_datetime(trades_df['date'])
            monthly_trades = trades_df.groupby(trades_df['date'].dt.to_period('M')).size()
            monthly_trades.plot(kind='bar', ax=ax2, color='skyblue')
            title2 = '月度交易频率' if self.font_available else 'Monthly Trade Frequency'
            ylabel2 = '交易次数' if self.font_available else 'Number of Trades'
            ax2.set_title(title2)
            ax2.set_ylabel(ylabel2)
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. 持仓时间分析
        ax3 = axes[1, 0]
        if len(buy_trades) > 0 and len(sell_trades) > 0:
            holding_periods = []
            for i in range(min(len(buy_trades), len(sell_trades))):
                buy_date = pd.to_datetime(buy_trades.iloc[i]['date'])
                sell_date = pd.to_datetime(sell_trades.iloc[i]['date'])
                holding_period = (sell_date - buy_date).days
                holding_periods.append(holding_period)
            
            if holding_periods:
                ax3.hist(holding_periods, bins=20, alpha=0.7, color='lightgreen')
                title3 = '持仓时间分布' if self.font_available else 'Holding Period Distribution'
                xlabel3 = '天数' if self.font_available else 'Days'
                ylabel3 = '频次' if self.font_available else 'Frequency'
                ax3.set_title(title3)
                ax3.set_xlabel(xlabel3)
                ax3.set_ylabel(ylabel3)
                ax3.grid(True, alpha=0.3)
        
        # 4. 盈亏分析
        ax4 = axes[1, 1]
        if len(buy_trades) > 0 and len(sell_trades) > 0:
            trade_profits = []
            for i in range(min(len(buy_trades), len(sell_trades))):
                buy_price = buy_trades.iloc[i]['price']
                sell_price = sell_trades.iloc[i]['price']
                profit_rate = (sell_price - buy_price) / buy_price
                trade_profits.append(profit_rate)
            
            if trade_profits:
                colors_pnl = ['green' if p > 0 else 'red' for p in trade_profits]
                ax4.bar(range(len(trade_profits)), trade_profits, color=colors_pnl, alpha=0.7)
                title4 = '单笔交易盈亏' if self.font_available else 'Individual Trade P&L'
                xlabel4 = '交易序号' if self.font_available else 'Trade Number'
                ylabel4 = '收益率' if self.font_available else 'Return Rate'
                ax4.set_title(title4)
                ax4.set_xlabel(xlabel4)
                ax4.set_ylabel(ylabel4)
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_monthly_analysis(self, results: Dict, strategy_name: str = "策略"):
        """
        绘制月度分析图表
        
        Args:
            results: 回测结果字典
            strategy_name: 策略名称
        """
        self._ensure_font_setup()
        
        if results['history'].empty:
            print("没有历史数据可分析")
            return
        
        history_df = results['history'].copy()
        history_df['date'] = pd.to_datetime(history_df['date'])
        history_df['month'] = history_df['date'].dt.to_period('M')
        
        # 计算月度收益
        monthly_returns = history_df.groupby('month')['total_value'].agg(['first', 'last'])
        monthly_returns['return'] = (monthly_returns['last'] - monthly_returns['first']) / monthly_returns['first']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        title = f'{strategy_name} 月度分析' if self.font_available else f'{strategy_name} Monthly Analysis'
        fig.suptitle(title, fontsize=16)
        
        # 1. 月度收益率
        ax1 = axes[0, 0]
        colors_monthly = ['green' if r > 0 else 'red' for r in monthly_returns['return']]
        monthly_returns['return'].plot(kind='bar', ax=ax1, color=colors_monthly, alpha=0.7)
        title1 = '月度收益率' if self.font_available else 'Monthly Returns'
        ylabel1 = '收益率' if self.font_available else 'Return Rate'
        ax1.set_title(title1)
        ax1.set_ylabel(ylabel1)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # 2. 累计收益曲线
        ax2 = axes[0, 1]
        cumulative_returns = (1 + monthly_returns['return']).cumprod() - 1
        cumulative_returns.plot(ax=ax2, color='blue', linewidth=2)
        title2 = '累计收益率曲线' if self.font_available else 'Cumulative Returns'
        ylabel2 = '累计收益率' if self.font_available else 'Cumulative Return'
        ax2.set_title(title2)
        ax2.set_ylabel(ylabel2)
        ax2.grid(True, alpha=0.3)
        
        # 3. 收益率分布
        ax3 = axes[1, 0]
        monthly_returns['return'].hist(bins=15, ax=ax3, alpha=0.7, color='skyblue')
        title3 = '月度收益率分布' if self.font_available else 'Monthly Returns Distribution'
        xlabel3 = '收益率' if self.font_available else 'Return Rate'
        ylabel3 = '频次' if self.font_available else 'Frequency'
        ax3.set_title(title3)
        ax3.set_xlabel(xlabel3)
        ax3.set_ylabel(ylabel3)
        ax3.grid(True, alpha=0.3)
        
        # 4. 胜率统计
        ax4 = axes[1, 1]
        positive_months = (monthly_returns['return'] > 0).sum()
        negative_months = (monthly_returns['return'] <= 0).sum()
        labels = ['盈利月份', '亏损月份'] if self.font_available else ['Profitable Months', 'Loss Months']
        sizes = [positive_months, negative_months]
        colors_pie = ['green', 'red']
        ax4.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
        title4 = '月度胜率统计' if self.font_available else 'Monthly Win Rate'
        ax4.set_title(title4)
        
        plt.tight_layout()
        plt.show()
    
    def check_font_display(self):
        """检查字体显示效果"""
        print("=== 检查系统字体配置 ===")
        
        # 获取系统所有字体名称
        available_fonts = set([f.name for f in fm.fontManager.ttflist])
        
        # 常见中文字体列表
        chinese_fonts = [
            'WenQuanYi Micro Hei',  # 文泉驿微米黑
            'SimHei',               # 黑体
            'Microsoft YaHei',      # 微软雅黑
            'Noto Sans CJK SC',     # Google Noto字体
            'Source Han Sans CN'    # 思源黑体
        ]
        
        # 找到可用的中文字体
        found_fonts = []
        for font in chinese_fonts:
            if font in available_fonts:
                found_fonts.append(font)
                print(f"✅ 找到可用中文字体: {font}")
        
        if not found_fonts:
            print("⚠️  未找到中文字体，将使用英文显示")
            print("建议安装中文字体：sudo apt-get install fonts-wqy-microhei")
        
        # 测试字体显示
        plt.figure(figsize=(8, 3))
        if self.font_available:
            plt.text(0.5, 0.7, '测试中文显示效果', ha='center', va='center', fontsize=16)
            plt.text(0.5, 0.3, 'Test Chinese Display', ha='center', va='center', fontsize=14)
        else:
            plt.text(0.5, 0.5, 'English Display Mode', ha='center', va='center', fontsize=16)
        
        plt.title(f'Font Test - Using: {plt.rcParams["font.sans-serif"][0]}')
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.axis('off')
        plt.tight_layout()
        plt.show()
        
        return found_fonts


# 全局可视化实例
visualizer = BacktestVisualizer()


def plot_backtest_results(all_results: Dict[str, Dict], benchmark_data: Optional[pd.DataFrame] = None):
    """
    便捷函数：绘制回测结果对比图表
    
    Args:
        all_results: 所有策略的回测结果字典
        benchmark_data: 基准数据
    """
    visualizer.plot_strategy_comparison(all_results, benchmark_data)


def plot_single_strategy_analysis(results: Dict, strategy_name: str = "策略", 
                                benchmark_data: Optional[pd.DataFrame] = None):
    """
    便捷函数：绘制单个策略的详细分析
    
    Args:
        results: 回测结果字典
        strategy_name: 策略名称
        benchmark_data: 基准数据
    """
    visualizer.plot_single_strategy(results, strategy_name, benchmark_data)


def plot_trade_details(results: Dict, strategy_name: str = "策略"):
    """
    便捷函数：绘制交易详细分析
    
    Args:
        results: 回测结果字典
        strategy_name: 策略名称
    """
    visualizer.plot_trade_analysis(results, strategy_name)


def plot_monthly_performance(results: Dict, strategy_name: str = "策略"):
    """
    便捷函数：绘制月度表现分析
    
    Args:
        results: 回测结果字典
        strategy_name: 策略名称
    """
    visualizer.plot_monthly_analysis(results, strategy_name)


def check_font_setup():
    """便捷函数：检查字体配置（可选使用）"""
    return visualizer.check_font_display()


def get_font_info():
    """便捷函数：获取当前字体信息"""
    return {
        'current_font': visualizer.current_font,
        'chinese_support': visualizer.font_available,
        'matplotlib_fonts': plt.rcParams['font.sans-serif']
    }
