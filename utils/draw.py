"""
股票数据可视化模块
专注于K线图绘制功能
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def plot_kline(df, title="K线图", figsize=(15, 8)):
    """
    绘制K线图
    
    Args:
        df: DataFrame，包含股票数据，需要有 open, high, low, close, volume 列
        title: str，图表标题
        figsize: tuple，图表大小
    """
    # 创建数据副本，避免修改原数据
    df = df.copy()
    
    # 确保日期列为datetime类型
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
    
    # K线图
    for i, (idx, row) in enumerate(df.iterrows()):
        open_price = row['open']
        high_price = row['high']
        low_price = row['low']
        close_price = row['close']
        
        # 判断涨跌
        color = 'red' if close_price >= open_price else 'green'
        
        # 绘制上下影线
        ax1.plot([i, i], [low_price, high_price], color='black', linewidth=1)
        
        # 绘制实体
        body_height = abs(close_price - open_price)
        body_bottom = min(open_price, close_price)
        
        rect = Rectangle((i-0.3, body_bottom), 0.6, body_height, 
                        facecolor=color, edgecolor='black', alpha=0.8)
        ax1.add_patch(rect)
    
    ax1.set_title(f'{title} - K线图', fontsize=14, fontweight='bold')
    ax1.set_ylabel('价格', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # 设置x轴标签
    x_labels = [idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx) 
                for idx in df.index[::len(df)//10]]  # 显示10个标签
    x_positions = list(range(0, len(df), len(df)//10))
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(x_labels, rotation=45)
    
    # 成交量图
    volumes = df['volume'] if 'volume' in df.columns else [0] * len(df)
    colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' 
              for i in range(len(df))]
    
    ax2.bar(range(len(df)), volumes, color=colors, alpha=0.7)
    ax2.set_title('成交量', fontsize=12)
    ax2.set_ylabel('成交量', fontsize=10)
    ax2.set_xticks(x_positions)
    ax2.set_xticklabels(x_labels, rotation=45)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
