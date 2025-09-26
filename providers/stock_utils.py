import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Dict
from stockstats import wrap

def get_chip_analysis_data(stock_code):
    """获取股票筹码分析数据"""
    try:
        cyq_data = ak.stock_cyq_em(stock_code)
        
        if cyq_data is None or cyq_data.empty:
            return {"error": f"无法获取 {stock_code} 的筹码数据"}
        
        latest = cyq_data.iloc[-1]
        profit_ratio = latest['获利比例']
        concentration_90 = latest['90集中度']
        
        cyq_data_for_cache = cyq_data.copy()
        cyq_data_for_cache['日期'] = cyq_data_for_cache['日期'].astype(str)
        
        chip_data = {
            "latest_date": str(latest['日期']),
            "profit_ratio": profit_ratio,
            "avg_cost": latest['平均成本'],
            "cost_90_low": latest['90成本-低'],
            "cost_90_high": latest['90成本-高'],
            "concentration_90": concentration_90,
            "cost_70_low": latest['70成本-低'],
            "cost_70_high": latest['70成本-高'],
            "concentration_70": latest['70集中度'],
            "support_level": latest['90成本-低'],
            "resistance_level": latest['90成本-高'],
            "cost_center": latest['平均成本'],
            "raw_data": cyq_data_for_cache.to_dict('records'),
        }
        
        # 添加分析指标
        chip_data["analysis"] = {
            "profit_status": "高获利" if profit_ratio > 0.7 else ("低获利" if profit_ratio < 0.3 else "中性获利"),
            "concentration_status": "高度集中" if concentration_90 < 0.1 else ("分散" if concentration_90 > 0.2 else "适中"),
            "risk_level": "高" if profit_ratio > 0.8 and concentration_90 < 0.15 else ("低" if profit_ratio < 0.2 and concentration_90 < 0.15 else "中"),
        }
        
        return chip_data
        
    except Exception as e:
        print(f"获取筹码数据失败: {str(e)}")
        return {"error": f"该股票暂不支持获取筹码数据"}

def _judge_ma_trend(stock_data) -> str:
    """判断移动平均线趋势"""
    try:
        ma5 = stock_data['close_5_sma'].iloc[-1]
        ma10 = stock_data['close_10_sma'].iloc[-1]
        ma20 = stock_data['close_20_sma'].iloc[-1]
        current_price = stock_data['close'].iloc[-1]
        
        if current_price > ma5 > ma10 > ma20:
            return "多头排列"
        elif current_price < ma5 < ma10 < ma20:
            return "空头排列"
        else:
            return "震荡整理"
    except:
        return "无法判断"

def _judge_macd_trend(stock_data) -> str:
    """判断MACD趋势"""
    try:
        macd = stock_data['macd'].iloc[-1]
        macd_signal = stock_data['macds'].iloc[-1]
        macd_hist = stock_data['macdh'].iloc[-1]
        
        if macd > macd_signal and macd_hist > 0:
            return "金叉向上"
        elif macd < macd_signal and macd_hist < 0:
            return "死叉向下"
        else:
            return "震荡调整"
    except:
        return "无法判断"
    

def get_indicators(df):
    """使用stockstats计算技术指标"""
    stock = wrap(df)
    stock_len = len(stock)
    
    indicators = {
        # 移动平均线
        'ma_5': stock['close_5_sma'].iloc[-1] if stock_len > 5 else None,
        'ma_10': stock['close_10_sma'].iloc[-1] if stock_len > 10 else None,
        'ma_20': stock['close_20_sma'].iloc[-1] if stock_len > 20 else None,
        'ma_60': stock['close_60_sma'].iloc[-1] if stock_len > 60 else None,
        
        # 指数移动平均
        'ema_12': stock['close_12_ema'].iloc[-1] if stock_len > 12 else None,
        'ema_26': stock['close_26_ema'].iloc[-1] if stock_len > 26 else None,
        
        # MACD指标
        'macd': stock['macd'].iloc[-1] if stock_len > 26 else None,
        'macd_signal': stock['macds'].iloc[-1] if stock_len > 26 else None,
        'macd_histogram': stock['macdh'].iloc[-1] if stock_len > 26 else None,
        
        # KDJ指标
        'kdj_k': stock['kdjk'].iloc[-1] if stock_len > 9 else None,
        'kdj_d': stock['kdjd'].iloc[-1] if stock_len > 9 else None,
        'kdj_j': stock['kdjj'].iloc[-1] if stock_len > 9 else None,
        
        # RSI指标
        'rsi_14': stock['rsi_14'].iloc[-1] if stock_len > 14 else None,
        
        # 布林带
        'boll_upper': stock['boll_ub'].iloc[-1] if stock_len > 20 else None,
        'boll_middle': stock['boll'].iloc[-1] if stock_len > 20 else None,
        'boll_lower': stock['boll_lb'].iloc[-1] if stock_len > 20 else None,
        
        # 威廉指标
        'wr_14': stock['wr_14'].iloc[-1] if stock_len > 14 else None,
        
        # CCI指标
        'cci_14': stock['cci_14'].iloc[-1] if stock_len > 14 else None,
                
        # 趋势判断
        'ma_trend': _judge_ma_trend(stock),
        'macd_trend': _judge_macd_trend(stock),
    }
    
    return indicators

def fetch_stock_basic_info(stock_code: str) -> Dict:
    """获取股票基本信息的具体实现"""
    from providers.stock_data_fetcher import data_manager
    
    basic_info = {}
    
    try:
        if not data_manager.is_available() and not data_manager.initialize():
            raise Exception("数据提供者初始化失败")
                
        realtime_data = data_manager.get_realtime_quote(stock_code)
        stock_info = data_manager.fetch_stock_info(stock_code)
        
        if realtime_data:
            basic_info.update({
                'current_price': float(realtime_data.current_price),
                'change': float(realtime_data.change),
                'change_percent': float(realtime_data.change_percent),
                'volume': int(realtime_data.volume),
                'amount': float(realtime_data.amount),
                'high': float(realtime_data.high),
                'low': float(realtime_data.low),
                'open': float(realtime_data.open),
                'prev_close': float(realtime_data.prev_close),
                'timestamp': str(realtime_data.timestamp),
            })
        
        if stock_info:
            basic_info.update(stock_info)
        
    except Exception as e:
        basic_info['error'] = str(e)
    
    basic_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return basic_info

def fetch_stock_technical_indicators(stock_code: str, period: int = 160) -> Dict:
    """获取股票技术指标的具体实现（K线数据不缓存，只缓存计算结果）"""
    from providers.stock_data_fetcher import data_manager, KLineType
    from providers.risk_metrics import calculate_portfolio_risk_summary
    
    indicators_info = {}
    
    try:
        kline_data = data_manager.get_kline_data(stock_code, KLineType.DAY, period)
        
        if not kline_data:
            indicators_info['error'] = f"未获取到股票 {stock_code} 的K线数据"
        else:
            df = pd.DataFrame([k.__dict__ for k in kline_data]).sort_values('datetime')
            
            # 计算移动平均线
            for period in [5, 10, 20]:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            
            indicators = get_indicators(df)
            
            # 风险指标计算
            risk_metrics = {}
            if len(df) >= 5:
                try:
                    risk_metrics = calculate_portfolio_risk_summary(df, price_col='close')                            
                except Exception as e:
                    risk_metrics['error'] = str(e)

            # 获取最新数据摘要
            latest_row = df.iloc[-1]
            latest_data = {
                'date': latest_row['datetime'].isoformat() if hasattr(latest_row['datetime'], 'isoformat') else str(latest_row['datetime']),
                'open': float(latest_row['open']) if pd.notna(latest_row['open']) else None,
                'high': float(latest_row['high']) if pd.notna(latest_row['high']) else None,
                'low': float(latest_row['low']) if pd.notna(latest_row['low']) else None,
                'close': float(latest_row['close']) if pd.notna(latest_row['close']) else None,
                'volume': int(latest_row['volume']) if pd.notna(latest_row['volume']) else None,
            }
            
            indicators_info.update({
                'indicators': indicators,
                'risk_metrics': risk_metrics,
                'data_length': len(df),
                'latest_data': latest_data,
                'has_ma_data': True
            })
            
    except Exception as e:
        indicators_info['error'] = str(e)
    
    indicators_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return indicators_info

def fetch_stock_news_data(stock_code: str, day=7) -> Dict:
    """获取股票新闻数据的具体实现"""
    from providers.news_tools import get_stock_news_by_akshare
    
    news_info = {}
    
    try:
        stock_data = get_stock_news_by_akshare(stock_code, day=day)
        
        if stock_data and 'company_news' in stock_data:
            news_data = stock_data['company_news']
            news_info.update({
                'news_data': news_data,
                'news_count': len(news_data),
                'latest_news': news_data[:5] if len(news_data) >= 5 else news_data
            })
        else:
            news_info['error'] = "未能获取到相关新闻"
            
    except Exception as e:
        news_info['error'] = str(e)
    
    news_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return news_info

def fetch_stock_chip_data(stock_code: str) -> Dict:
    """获取股票筹码数据的具体实现"""
    chip_info = {}
    
    try:
        chip_data = get_chip_analysis_data(stock_code)
        chip_info.update(chip_data if "error" not in chip_data else {'error': chip_data["error"]})
    except Exception as e:
        chip_info['error'] = str(e)
    
    chip_info['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return chip_info

