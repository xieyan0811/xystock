"""
A股市场工具 - 统一的数据获取和缓存管理

所有数据都支持智能缓存，避免重复请求
"""

import os
import sys
import warnings
from datetime import datetime
from typing import Dict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

warnings.filterwarnings('ignore')

import akshare as ak
from stock.stock_utils import get_indicators
from ui.config import FOCUS_INDICES, INDEX_SYMBOL_MAPPING
from market.kline_data_manager import get_kline_manager

def fetch_market_sentiment() -> tuple:
    """获取市场情绪数据 - 优化版本，避免频繁请求导致IP被封"""
    sentiment_data = {}
    ret = False  # 默认失败，成功时设为True
    
    # 方法1：使用乐咕乐股的市场活跃度数据（推荐）
    try:
        print("   获取市场活跃度数据...")
        df_activity = ak.stock_market_activity_legu()
        
        if not df_activity.empty:
            # 转换为字典格式便于处理
            activity_dict = dict(zip(df_activity['item'], df_activity['value']))
            
            up_count = int(activity_dict.get('上涨', 0))
            down_count = int(activity_dict.get('下跌', 0))
            flat_count = int(activity_dict.get('平盘', 0))
            limit_up = int(activity_dict.get('涨停', 0))
            limit_down = int(activity_dict.get('跌停', 0))
            real_limit_up = int(activity_dict.get('真实涨停', 0))
            real_limit_down = int(activity_dict.get('真实跌停', 0))
            suspended = int(activity_dict.get('停牌', 0))
            
            total_count = up_count + down_count + flat_count
            
            sentiment_data.update({
                'up_stocks': up_count,
                'down_stocks': down_count,
                'flat_stocks': flat_count,
                'limit_up_stocks': limit_up,
                'limit_down_stocks': limit_down,
                'real_limit_up_stocks': real_limit_up,
                'real_limit_down_stocks': real_limit_down,
                'suspended_stocks': suspended,
                'total_stocks': total_count,
                'up_ratio': float(up_count / total_count) if total_count > 0 else 0,
                'down_ratio': float(down_count / total_count) if total_count > 0 else 0,
                'limit_up_ratio': float(limit_up / total_count) if total_count > 0 else 0,
                'data_source': '乐咕乐股-市场活跃度'
            })
            
            print(f"      上涨: {up_count} | 下跌: {down_count} | 平盘: {flat_count}")
            print(f"      涨停: {limit_up} | 跌停: {limit_down} | 停牌: {suspended}")
            ret = True  # 成功获取数据
            
    except Exception as e:
        print(f"   ❌ 获取市场活跃度数据失败: {e}")
        
        # 方法2：备用方案 - 从概念板块汇总数据中获取（速度更快）
        try:
            print("   使用备用方案：概念板块数据汇总...")
            df_concept = ak.stock_board_concept_name_em()
            
            if not df_concept.empty:
                # 汇总所有板块的上涨下跌家数
                total_up = df_concept['上涨家数'].sum()
                total_down = df_concept['下跌家数'].sum()
                
                # 估算总股票数（可能有重复计算，但能给出大致比例）
                total_estimated = total_up + total_down
                
                sentiment_data.update({
                    'up_stocks': int(total_up),
                    'down_stocks': int(total_down),
                    'flat_stocks': 0,  # 板块数据中没有平盘信息
                    'total_stocks': int(total_estimated),
                    'up_ratio': float(total_up / total_estimated) if total_estimated > 0 else 0,
                    'down_ratio': float(total_down / total_estimated) if total_estimated > 0 else 0,
                    'data_source': '东方财富-概念板块汇总'
                })
                
                print(f"      上涨: {total_up} | 下跌: {total_down} (来自板块汇总)")
                ret = True  # 成功获取数据
                
        except Exception as e2:
            print(f"   ❌ 备用方案也失败: {e2}")
            
            # 方法3：最后备用方案 - 从大盘资金流向推断市场情绪
            try:
                print("   使用最后备用方案：大盘资金流向数据...")
                df_fund = ak.stock_market_fund_flow()
                
                if not df_fund.empty:
                    latest_fund = df_fund.iloc[-1]
                    main_net_inflow = float(latest_fund.get('主力净流入-净额', 0))
                    main_net_ratio = float(latest_fund.get('主力净流入-净占比', 0))
                    
                    # 根据资金流向推断市场情绪
                    if main_net_ratio > 1:
                        market_mood = 'bullish'
                    elif main_net_ratio < -1:
                        market_mood = 'bearish' 
                    else:
                        market_mood = 'neutral'
                    
                    sentiment_data.update({
                        'main_net_inflow': main_net_inflow,
                        'main_net_ratio': main_net_ratio,
                        'market_mood': market_mood,
                        'data_source': '东方财富-大盘资金流向'
                    })
                    
                    print(f"      主力净流入: {main_net_inflow/1e8:.2f}亿 ({main_net_ratio:.2f}%)")
                    ret = True  # 成功获取数据
                    
            except Exception as e3:
                print(f"   ❌ 所有备用方案都失败: {e3}")
                sentiment_data['error'] = f"所有数据源都失败: {str(e)}, {str(e2)}, {str(e3)}"
                # ret 保持 False
    
    sentiment_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return ret, sentiment_data


def fetch_limit_stocks_data() -> Dict:
    """获取涨跌停股票详细数据"""
    limit_data = {}
    
    try:
        print("   获取涨跌停股票详情...")
        
        # 获取涨停股票
        try:
            df_limit_up = ak.stock_zt_pool_em(date=datetime.now().strftime('%Y%m%d'))
            limit_up_count = len(df_limit_up) if not df_limit_up.empty else 0
            
            # 分析涨停原因分布
            if not df_limit_up.empty and '涨停原因' in df_limit_up.columns:
                reason_counts = df_limit_up['涨停原因'].value_counts().head(5).to_dict()
                limit_data['limit_up_reasons'] = {str(k): int(v) for k, v in reason_counts.items()}
            
            limit_data['limit_up_detail_count'] = limit_up_count
            print(f"      详细涨停股票: {limit_up_count}只")
            
        except Exception as e:
            print(f"      ⚠️ 获取涨停详情失败: {e}")
            limit_data['limit_up_detail_count'] = 0
        
        # 获取跌停股票  
        try:
            df_limit_down = ak.stock_zt_pool_dtgc_em(date=datetime.now().strftime('%Y%m%d'))
            limit_down_count = len(df_limit_down) if not df_limit_down.empty else 0
            limit_data['limit_down_detail_count'] = limit_down_count
            print(f"      详细跌停股票: {limit_down_count}只")
            
        except Exception as e:
            print(f"      ⚠️ 获取跌停详情失败: {e}")
            limit_data['limit_down_detail_count'] = 0
            
    except Exception as e:
        print(f"   ❌ 获取涨跌停数据失败: {e}")
        limit_data['error'] = str(e)
    
    limit_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return limit_data


def fetch_valuation_data(debug=False) -> tuple:
    """获取多个指数的估值指标"""
    print("💰 获取多指数估值指标...")
    
    valuation_data = {}
    ret = True
    
    # 支持估值数据的指数代码映射（主要是中证指数系列）
    valuation_indices = {
        '沪深300': '000300',
        '中证500': '000905', 
        '中证1000': '000852',
        '中证2000': '932000',
        '上证50': '000016',
        '科创50': '000688',         # 科创板代表
        '沪深300成长': '000918',    # 成长风格
        '中证信息技术': '000935',   # 科技行业
    }
    
    for index_name, index_code in valuation_indices.items():
        try:
            print(f"   获取{index_name}估值...")
            df_index = ak.stock_zh_index_value_csindex(index_code)
            if not df_index.empty:
                if debug:
                    print(f"{index_name}数据:")
                    print(df_index.tail(3))
                    
                latest_data = df_index.iloc[-1]
                
                # 生成统一的数据key
                index_key = index_name.lower().replace('沪深', 'hs').replace('中证', 'zz')
                
                pe_value = latest_data.get('市盈率1', 0)
                dividend_yield = latest_data.get('股息率1', 0)
                date_value = latest_data.get('日期', datetime.now().strftime('%Y-%m-%d'))
                
                # 存储指数估值数据
                valuation_data[f'{index_key}_pe'] = float(pe_value) if pe_value else 0
                valuation_data[f'{index_key}_dividend_yield'] = float(dividend_yield) if dividend_yield else 0
                valuation_data[f'{index_key}_date'] = str(date_value)
                
                # 同时保留原有的hs300格式以兼容现有代码
                if index_name == '沪深300':
                    valuation_data.update({
                        'hs300_pe': float(pe_value) if pe_value else 0,
                        'hs300_dividend_yield': float(dividend_yield) if dividend_yield else 0,
                        'hs300_date': str(date_value),
                    })
                
                print(f"      {index_name} PE: {pe_value:.2f}")
                
        except Exception as e:
            print(f"   ❌ 获取{index_name}估值失败: {e}")
            ret = False
            continue
    
    # 如果没有获取到任何估值数据，标记为失败
    if not any(key.endswith('_pe') for key in valuation_data.keys()):
        ret = False
    
    valuation_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("   ✓ 多指数估值指标获取完成")
    return ret, valuation_data


def fetch_money_flow_data(debug=False) -> tuple:
    """获取资金流向数据"""
    print("💸 获取资金流向指标...")
    
    ret = True
    money_flow_data = {}
    
    try:
        print("   获取M2数据...")
        df_m2 = ak.macro_china_money_supply()
        if debug:
            print(df_m2.head())
        if not df_m2.empty:
            latest_m2 = df_m2.iloc[0]
            if debug:
                print(latest_m2)
            money_flow_data.update({
                'm2_amount': float(latest_m2.get('货币和准货币(M2)-数量(亿元)', 0)),
                'm2_growth': float(latest_m2.get('货币和准货币(M2)-同比增长', 0)),
                'm1_amount': float(latest_m2.get('货币(M1)-数量(亿元)', 0)),
                'm1_growth': float(latest_m2.get('货币(M1)-同比增长', 0)),
                'm2_date': str(latest_m2.get('月份', datetime.now().strftime('%Y-%m'))),
            })
            print(f"      M2余额: {money_flow_data['m2_amount']/10000:.2f}万亿 | 同比增长: {money_flow_data['m2_growth']:.2f}%")
        else:
            print("   ⚠️ M2数据为空")
            ret = False

    except Exception as e:
        print(f"   ❌ 获取M2数据失败: {e}")
        ret = False
    
    money_flow_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("   ✓ 资金流向指标获取完成")
    return ret, money_flow_data


def fetch_current_indices() -> tuple:
    """获取当前指数实时数据"""
    print("📊 获取当前指数实时数据...")
    
    indices_data = {}
    ret = True
    
    try:
        print("   获取沪深重要指数...")
        df_indices = ak.stock_zh_index_spot_em('沪深重要指数')
        
        if not df_indices.empty:
            indices_list = []

            for _, row in df_indices.iterrows():
                if str(row.get('名称', '')) not in FOCUS_INDICES:
                    continue
                index_info = {
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'current_price': float(row.get('最新价', 0)),
                    'change_percent': float(row.get('涨跌幅', 0)),
                    'change_amount': float(row.get('涨跌额', 0)),
                    'volume': float(row.get('成交量', 0)),
                    'turnover': float(row.get('成交额', 0)),
                    'amplitude': float(row.get('振幅', 0)),
                    'high': float(row.get('最高', 0)),
                    'low': float(row.get('最低', 0)),
                    'open': float(row.get('今开', 0)),
                    'prev_close': float(row.get('昨收', 0)),
                    'volume_ratio': float(row.get('量比', 0))
                }
                indices_list.append(index_info)
            
            indices_dict = {}
            for index in indices_list:
                indices_dict[index['name']] = index
            
            indices_data = {
                'indices_dict': indices_dict,
                'total_count': len(indices_dict),
                'data_source': '东方财富-沪深重要指数',
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"      成功获取 {len(indices_dict)} 个指数数据")
            
            for name in FOCUS_INDICES:
                if name in indices_dict:
                    idx = indices_dict[name]
                    change_sign = '+' if idx['change_percent'] >= 0 else ''
                    print(f"      - {name}: {idx['current_price']:.2f} ({change_sign}{idx['change_percent']:.2f}%)")
        else:
            print("   ⚠️ 指数数据为空")
            indices_data = {
                'error': '指数数据为空',
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            ret = False
        
    except Exception as e:
        print(f"   ❌ 获取指数数据失败: {e}")
        indices_data = {
            'error': str(e),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        ret = False
    
    print("   ✓ 指数数据获取完成")
    return ret, indices_data


def fetch_margin_data_unified(include_historical: bool = False) -> tuple:
    """统一的融资融券数据获取方法"""
    result = {
        'margin_balance': 0,
        'margin_buy_balance': 0,
        'margin_sell_balance': 0,
        'margin_sh_balance': 0,
        'margin_sh_buy': 0,
        'margin_sh_sell': 0,
        'margin_sz_balance': 0,
        'margin_sz_buy': 0,
        'margin_sz_sell': 0,
        'margin_date': datetime.now().strftime('%Y-%m-%d'),
    }
    ret = True
    
    sh_data = {}
    sz_data = {}
    
    try:
        df_margin_sh = ak.macro_china_market_margin_sh()
        if not df_margin_sh.empty:
            latest_sh = df_margin_sh.iloc[-1]
            result.update({
                'margin_sh_balance': float(latest_sh.get('融资融券余额', 0)),
                'margin_sh_buy': float(latest_sh.get('融资余额', 0)),
                'margin_sh_sell': float(latest_sh.get('融券余额', 0)),
                'margin_date': str(latest_sh.get('日期', datetime.now().strftime('%Y-%m-%d'))),
            })
            
            # 计算一周变化
            if include_historical and len(df_margin_sh) >= 7:
                week_ago_sh = df_margin_sh.iloc[-7]
                weekly_change_sh = result['margin_sh_buy'] - float(week_ago_sh.get('融资余额', 0))
                sh_data = {
                    'weekly_change': float(weekly_change_sh),
                    'change_ratio': float(weekly_change_sh / (result['margin_sh_buy'] - weekly_change_sh) * 100) if (result['margin_sh_buy'] - weekly_change_sh) > 0 else 0
                }
            
    except Exception as e:
        import traceback
        traceback.print_exc()               
        print(f"      ❌ 获取上交所融资融券失败: {e}")
        ret = False
    
    try:
        df_margin_sz = ak.macro_china_market_margin_sz()
        if not df_margin_sz.empty:
            latest_sz = df_margin_sz.iloc[-1]
            result.update({
                'margin_sz_balance': float(latest_sz.get('融资融券余额', 0)),
                'margin_sz_buy': float(latest_sz.get('融资余额', 0)),
                'margin_sz_sell': float(latest_sz.get('融券余额', 0)),
            })
            
            if include_historical and len(df_margin_sz) >= 7:
                week_ago_sz = df_margin_sz.iloc[-7]
                weekly_change_sz = result['margin_sz_buy'] - float(week_ago_sz.get('融资余额', 0))
                sz_data = {
                    'weekly_change': float(weekly_change_sz),
                    'change_ratio': float(weekly_change_sz / (result['margin_sz_buy'] - weekly_change_sz) * 100) if (result['margin_sz_buy'] - weekly_change_sz) > 0 else 0
                }
            
    except Exception as e:
        print(f"      ❌ 获取深交所融资融券失败: {e}")
        ret = False
    
    total_margin_balance = result['margin_sh_balance'] + result['margin_sz_balance']
    total_margin_buy = result['margin_sh_buy'] + result['margin_sz_buy']
    total_margin_sell = result['margin_sh_sell'] + result['margin_sz_sell']
    
    result.update({
        'margin_balance': float(total_margin_balance),
        'margin_buy_balance': float(total_margin_buy),
        'margin_sell_balance': float(total_margin_sell),
    })
    
    if include_historical:
        total_weekly_change = sh_data.get('weekly_change', 0) + sz_data.get('weekly_change', 0)
        result.update({
            'weekly_change': float(total_weekly_change),
            'change_ratio': float(total_weekly_change / (total_margin_buy - total_weekly_change) * 100) if (total_margin_buy - total_weekly_change) > 0 else 0,
            'shanghai': sh_data,
            'shenzhen': sz_data,
        })
    
    # 检查是否有有效数据
    if total_margin_balance == 0 and total_margin_buy == 0:
        ret = False
        
    result['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return ret, result

def update_index_cache_data(index_name: str = '上证指数', period: int = 250) -> bool:
    """更新指数缓存数据（用于定期更新缓存）"""
    manager = get_kline_manager()
    return manager.update_index_cache(index_name, period)


def batch_update_indices_cache(indices: list = None, period: int = 250) -> Dict:
    """批量更新指数缓存数据"""
    manager = get_kline_manager()
    return manager.batch_update_indices_cache(indices, period)


def fetch_comprehensive_market_sentiment() -> tuple:
    """获取综合市场情绪分析数据"""
    print("🎯 获取综合市场情绪分析...")
    
    comprehensive_data = {
        'sentiment_score': 0,  # 情绪评分 -100到100
        'sentiment_level': 'neutral',  # 情绪等级: bearish, neutral, bullish
        'confidence': 0,  # 数据可信度 0-100
    }
    ret = True
    
    # 1. 基础涨跌家数数据
    ret_sentiment, sentiment_data = fetch_market_sentiment()
    comprehensive_data['basic_sentiment'] = sentiment_data
    if not ret_sentiment:
        ret = False
    
    # 2. 涨跌停详细数据  
    limit_data = fetch_limit_stocks_data()
    comprehensive_data['limit_analysis'] = limit_data
    
    # 3. 大盘资金流向数据
    try:
        print("   获取资金流向数据...")
        df_fund = ak.stock_market_fund_flow()
        if not df_fund.empty:
            latest_fund = df_fund.iloc[-1]
            fund_data = {
                'main_net_inflow': float(latest_fund.get('主力净流入-净额', 0)),
                'main_net_ratio': float(latest_fund.get('主力净流入-净占比', 0)),
                'super_large_inflow': float(latest_fund.get('超大单净流入-净额', 0)),
                'large_inflow': float(latest_fund.get('大单净流入-净额', 0)),
                'date': str(latest_fund.get('日期', datetime.now().strftime('%Y-%m-%d')))
            }
            comprehensive_data['fund_flow'] = fund_data
            print(f"      主力净流入: {fund_data['main_net_inflow']/1e8:.2f}亿 ({fund_data['main_net_ratio']:.2f}%)")
    except Exception as e:
        print(f"   ❌ 获取资金流向失败: {e}")
        comprehensive_data['fund_flow'] = {}
    
    # 4. 计算综合情绪评分
    try:
        score_components = []
        
        # 基于涨跌比例的评分 (-40到40分)
        if sentiment_data.get('up_ratio', 0) > 0:
            up_ratio = sentiment_data['up_ratio']
            ratio_score = (up_ratio - 0.5) * 80  # 50%为中性，转换为-40到40分
            score_components.append(('ratio', ratio_score))
        
        # 基于涨停跌停比例的评分 (-20到20分)
        limit_up = sentiment_data.get('limit_up_stocks', 0)
        limit_down = sentiment_data.get('limit_down_stocks', 0)
        total_stocks = sentiment_data.get('total_stocks', 1)
        
        if total_stocks > 0:
            limit_score = ((limit_up - limit_down) / total_stocks) * 1000  # 放大1000倍
            limit_score = max(-20, min(20, limit_score))  # 限制在-20到20分
            score_components.append(('limit', limit_score))
        
        # 基于资金流向的评分 (-40到40分)
        if 'fund_flow' in comprehensive_data and comprehensive_data['fund_flow']:
            main_ratio = comprehensive_data['fund_flow'].get('main_net_ratio', 0)
            fund_score = max(-40, min(40, main_ratio * 10))  # 4%主力净流入为满分
            score_components.append(('fund', fund_score))
        
        # 计算总分
        total_score = sum(score for _, score in score_components)
        comprehensive_data['sentiment_score'] = round(total_score, 2)
        comprehensive_data['score_components'] = dict(score_components)
        
        # 确定情绪等级
        if total_score > 20:
            comprehensive_data['sentiment_level'] = 'bullish'
        elif total_score < -20:
            comprehensive_data['sentiment_level'] = 'bearish' 
        else:
            comprehensive_data['sentiment_level'] = 'neutral'
        
        # 计算数据可信度
        data_sources = 0
        if sentiment_data.get('data_source'):
            data_sources += 1
        if comprehensive_data.get('fund_flow'):
            data_sources += 1
        if limit_data.get('limit_up_detail_count', 0) > 0:
            data_sources += 1
            
        comprehensive_data['confidence'] = min(100, data_sources * 30 + 10)
        
        print(f"   ✓ 综合情绪评分: {total_score:.1f} ({comprehensive_data['sentiment_level']})")
        
    except Exception as e:
        print(f"   ❌ 计算情绪评分失败: {e}")
        comprehensive_data['sentiment_score'] = 0
        comprehensive_data['sentiment_level'] = 'unknown'
        comprehensive_data['confidence'] = 0
        ret = False
    
    comprehensive_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("   ✓ 综合市场情绪分析完成")
    
    return ret, comprehensive_data


def fetch_index_technical_indicators(index_name: str = '上证指数', period: int = 100) -> tuple:
    """获取指数技术指标（使用智能缓存）"""
    print(f"📊 获取{index_name}技术指标...")
        
    try:
        if index_name not in INDEX_SYMBOL_MAPPING:
            raise ValueError(f"不支持的指数名称: {index_name}")
        
        # 使用统一的K线数据管理器获取数据
        manager = get_kline_manager()
        df, from_cache = manager.get_index_kline_data(
            index_name, 
            period=period, 
            use_cache=True, 
            force_refresh=False, 
            for_technical_analysis=True
        )
        
        # 计算技术指标
        indicators = get_indicators(df)
        
        # 风险指标计算
        risk_metrics = {}
        if len(df) >= 5:
            try:
                from utils.risk_metrics import calculate_portfolio_risk_summary
                risk_metrics = calculate_portfolio_risk_summary(df, price_col='close')
                if risk_metrics:
                    indicators['risk_metrics'] = risk_metrics
            except ImportError:
                print("   ⚠️  风险指标模块未找到，跳过风险计算")
            except Exception as e:
                print(f"   ⚠️  风险指标计算失败: {e}")

        print(f"   ✓ 成功获取{index_name}技术指标")
        return True, indicators
        
    except Exception as e:
        print(f"   ❌ 获取{index_name}技术指标失败: {e}")
        return False, {}