#!/usr/bin/env python3
"""
用于验证股票数据获取和数据管理器功能的测试用例。

测试覆盖范围：
1. 数据管理器初始化和配置
2. EFinance数据获取器功能
3. K线数据获取和验证
4. 实时行情数据获取
5. 缓存管理功能
6. 自动选择数据获取器
7. 多种股票代码支持
8. 数据格式和有效性验证
"""

import sys
import os
import unittest
import warnings
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目根目录到路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
XYSTOCK_DIR = os.path.dirname(CURRENT_DIR)
if XYSTOCK_DIR not in sys.path:
    sys.path.insert(0, XYSTOCK_DIR)

# 清理代理设置，避免网络问题
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

# 忽略警告
warnings.filterwarnings('ignore')

# 导入数据获取相关模块
from providers.stock_data_fetcher import data_manager
from providers.cache_manager import KLineType


class TestDataManager(unittest.TestCase):
    """数据管理器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.test_stocks = {
            'A股股票': ['600300', '000001', '300015'],  # 维维股份、平安银行、爱尔眼科
            'A股指数': ['上证指数', '深证成指', '创业板指']
        }
        print(f"\n🚀 开始测试股票数据获取模块...")
        print(f"📊 测试股票: {cls.test_stocks}")
        print("=" * 60)
    
    def test_data_manager_initialization(self):
        """测试数据管理器初始化"""
        print(f"\n🔧 测试数据管理器初始化...")
        
        # 检查数据管理器状态
        status = data_manager.get_status()
        
        assert isinstance(status, dict), "状态信息应为字典类型"
        assert 'efinance' in status, "应包含efinance获取器"
        
        # 检查可用的获取器
        assert data_manager.is_available(), "数据获取器应可用"
        
        print(f"   ✓ 数据获取器可用")
        
        # 检查获取器的状态
        fetcher_status = status.get("efinance", {})
        available = fetcher_status.get('available', False)
        fetcher_desc = fetcher_status.get('description', 'N/A')
        print(f"   ✓ efinance: {fetcher_desc} ({'可用' if available else '不可用'})")
        
        print(f"   ✓ 数据管理器初始化成功")
    
    def test_efinance_fetcher_direct(self):
        """测试直接使用EFinance获取器"""
        print(f"\n💹 测试EFinance获取器...")
        
        # 现在 data_manager 本身就是获取器
        assert data_manager is not None, "应能获取到数据获取器"
        assert data_manager.is_available(), "数据获取器应可用"
        
        print(f"   ✓ 获取器名称: {data_manager.name}")
        print(f"   ✓ 获取器描述: {data_manager.description}")
        print(f"   ✓ 获取器状态: {'可用' if data_manager.is_available() else '不可用'}")
    
    def test_auto_fetcher_selection(self):
        """测试数据获取器可用性"""
        print(f"\n🤖 测试数据获取器可用性...")
        
        if data_manager.is_available():
            print(f"   ✓ 数据获取器可用")
        else:
            print(f"   ⚠️ 数据获取器不可用")
    
    def test_kline_data_retrieval(self):
        """测试K线数据获取"""
        print(f"\n📈 测试K线数据获取...")
        
        # 测试A股股票K线数据
        for stock_code in self.test_stocks['A股股票'][:2]:  # 只测试前两个，节省时间
            print(f"   测试股票: {stock_code}")
            
            # 获取日线数据
            kline_data = data_manager.get_kline_data(
                symbol=stock_code, 
                kline_type=KLineType.DAY, 
                count=30
            )
            
            if kline_data:
                assert len(kline_data) > 0, f"{stock_code}应返回K线数据"
                
                # 验证数据结构
                first_data = kline_data[0]
                required_fields = ['datetime', 'open', 'high', 'low', 'close', 'volume']
                
                for field in required_fields:
                    assert hasattr(first_data, field), f"K线数据应包含{field}字段"
                
                # 验证数据合理性
                assert first_data.high >= first_data.low, "最高价应大于等于最低价"
                assert first_data.high >= first_data.open, "最高价应大于等于开盘价"
                assert first_data.high >= first_data.close, "最高价应大于等于收盘价"
                assert first_data.low <= first_data.open, "最低价应小于等于开盘价"
                assert first_data.low <= first_data.close, "最低价应小于等于收盘价"
                assert first_data.volume >= 0, "成交量应大于等于0"
                
                print(f"      ✓ 获取到 {len(kline_data)} 条K线数据")
                print(f"      ✓ 最新价格: {first_data.close:.2f}")
                print(f"      ✓ 最新日期: {first_data.datetime}")
                print(f"      ✓ 成交量: {first_data.volume}")
            else:
                print(f"      ⚠️  {stock_code} 未获取到K线数据")
    
    def test_index_kline_data(self):
        """测试指数K线数据获取"""
        print(f"\n📊 测试指数K线数据获取...")
        
        # 专门测试上证指数
        test_index = '上证指数'
        print(f"   测试指数: {test_index}")
        
        kline_data = data_manager.get_kline_data(
            symbol=test_index,
            kline_type=KLineType.DAY,
            count=10
        )
        
        if kline_data:
            assert len(kline_data) > 0, f"{test_index}应返回K线数据"
            
            # 验证指数数据
            latest_data = kline_data[0]
            assert latest_data.close > 2000, "上证指数应大于2000点"  # 合理范围检查
            assert latest_data.close < 6000, "上证指数应小于6000点"  # 合理范围检查
            
            print(f"      ✓ 获取到 {len(kline_data)} 条指数数据")
            print(f"      ✓ 当前点位: {latest_data.close:.2f}")
            print(f"      ✓ 日期: {latest_data.datetime}")
            
            # 转换为DataFrame进行分析
            df_data = []
            for item in kline_data:
                df_data.append({
                    'date': item.datetime,
                    'open': item.open,
                    'high': item.high,
                    'low': item.low,
                    'close': item.close,
                    'volume': item.volume
                })
            
            df = pd.DataFrame(df_data)
            print(f"      ✓ DataFrame形状: {df.shape}")
            print(f"      ✓ 平均收盘价: {df['close'].mean():.2f}")
            print(f"      ✓ 价格波动范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
        else:
            print(f"      ⚠️  {test_index} 未获取到K线数据")
    
    def test_realtime_quote(self):
        """测试实时行情获取"""
        print(f"\n⚡ 测试实时行情获取...")
        
        # 测试股票实时行情
        test_stock = '600300'
        print(f"   测试股票实时行情: {test_stock}")
        
        quote = data_manager.get_realtime_quote(
            symbol=test_stock
        )
        
        if quote:
            # 验证实时行情数据结构
            required_fields = ['symbol', 'name', 'current_price', 'change', 'change_percent']
            
            for field in required_fields:
                assert hasattr(quote, field), f"实时行情应包含{field}字段"
            
            # 验证数据合理性
            assert quote.current_price > 0, "当前价格应大于0"
            assert -20 < quote.change_percent < 20, "涨跌幅应在合理范围内"
            
            print(f"      ✓ 股票名称: {quote.name}")
            print(f"      ✓ 当前价格: {quote.current_price:.2f}")
            print(f"      ✓ 涨跌额: {quote.change:+.2f}")
            print(f"      ✓ 涨跌幅: {quote.change_percent:+.2f}%")
        else:
            print(f"      ⚠️  {test_stock} 未获取到实时行情")
    
    def test_different_kline_types(self):
        """测试不同K线类型"""
        print(f"\n📋 测试不同K线类型...")
        
        test_symbol = '600300'
        kline_types = [
            (KLineType.DAY, "日线"),
            (KLineType.WEEK, "周线"),
            (KLineType.MONTH, "月线")
        ]
        
        for kline_type, type_name in kline_types:
            print(f"   测试{type_name}数据...")
            
            kline_data = data_manager.get_kline_data(
                symbol=test_symbol,
                kline_type=kline_type,
                count=5
            )
            
            if kline_data:
                print(f"      ✓ {type_name}数据: {len(kline_data)} 条")
                
                # 验证时间间隔合理性
                if len(kline_data) >= 2:
                    date1 = datetime.strptime(kline_data[0].datetime, '%Y-%m-%d')
                    date2 = datetime.strptime(kline_data[1].datetime, '%Y-%m-%d')
                    days_diff = abs((date1 - date2).days)
                    
                    if kline_type == KLineType.DAY:
                        assert days_diff <= 7, "日线数据时间间隔应合理"
                    elif kline_type == KLineType.WEEK:
                        assert days_diff >= 6 and days_diff <= 8, "周线数据时间间隔应约为7天"
                    elif kline_type == KLineType.MONTH:
                        assert days_diff >= 25 and days_diff <= 35, "月线数据时间间隔应约为30天"
            else:
                print(f"      ⚠️  {type_name}数据获取失败")
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        print(f"\n💾 测试缓存功能...")
        
        test_symbol = '600300'
        
        # 清理缓存
        data_manager.clear_cache(test_symbol)
        print(f"   清理缓存: {test_symbol}")
        
        # 第一次获取（应从数据源获取）
        print(f"   第一次获取数据...")
        start_time = datetime.now()
        kline_data1 = data_manager.get_kline_data(
            symbol=test_symbol,
            kline_type=KLineType.DAY,
            count=30,
            force=False
        )
        first_duration = (datetime.now() - start_time).total_seconds()
        
        # 第二次获取（应从缓存获取）
        print(f"   第二次获取数据...")
        start_time = datetime.now()
        kline_data2 = data_manager.get_kline_data(
            symbol=test_symbol,
            kline_type=KLineType.DAY,
            count=30,
            force=False
        )
        second_duration = (datetime.now() - start_time).total_seconds()
        
        if kline_data1 and kline_data2:
            # 验证数据一致性
            assert len(kline_data1) == len(kline_data2), "缓存数据长度应一致"
            assert kline_data1[0].close == kline_data2[0].close, "缓存数据内容应一致"
            
            print(f"      ✓ 第一次获取耗时: {first_duration:.2f}秒")
            print(f"      ✓ 第二次获取耗时: {second_duration:.2f}秒")
            print(f"      ✓ 数据长度: {len(kline_data1)} 条")
            
            # 获取缓存统计
            cache_stats = data_manager.get_cache_stats()
            print(f"      ✓ 缓存统计: {cache_stats}")
        else:
            print(f"      ⚠️  缓存测试失败，数据获取失败")
    
    def test_forced_refresh(self):
        """测试强制刷新功能"""
        print(f"\n🔄 测试强制刷新功能...")
        
        test_symbol = '000001'
        
        # 获取缓存数据
        cached_data = data_manager.get_kline_data(
            symbol=test_symbol,
            kline_type=KLineType.DAY,
            count=5,
            force=False
        )
        
        # 强制刷新
        fresh_data = data_manager.get_kline_data(
            symbol=test_symbol,
            kline_type=KLineType.DAY,
            count=5,
            force=True
        )
        
        if cached_data and fresh_data:
            print(f"      ✓ 缓存数据: {len(cached_data)} 条")
            print(f"      ✓ 刷新数据: {len(fresh_data)} 条")
            
            # 数据应该基本一致（除非是交易时间内）
            assert len(cached_data) == len(fresh_data), "强制刷新后数据长度应一致"
        else:
            print(f"      ⚠️  强制刷新测试失败")
    
    def test_data_validation_and_format(self):
        """测试数据验证和格式"""
        print(f"\n🧪 测试数据验证和格式...")
        
        test_symbol = '上证指数'
        
        kline_data = data_manager.get_kline_data(
            symbol=test_symbol,
            kline_type=KLineType.DAY,
            count=20
        )
        
        if kline_data:
            print(f"   验证 {len(kline_data)} 条数据...")
            
            # 检查数据排序（需要检查实际的排序方式）
            if len(kline_data) >= 2:
                date1 = datetime.strptime(kline_data[0].datetime, '%Y-%m-%d')
                date2 = datetime.strptime(kline_data[1].datetime, '%Y-%m-%d')
                if date1 >= date2:
                    print(f"      ✓ 数据按时间倒序排列")
                elif date1 <= date2:
                    print(f"      ✓ 数据按时间正序排列")
                else:
                    print(f"      ⚠️  数据排序异常")
            
            # 检查数据完整性
            complete_data_count = 0
            for i, data in enumerate(kline_data):
                if (data.open > 0 and data.high > 0 and data.low > 0 and 
                    data.close > 0 and data.volume >= 0):
                    complete_data_count += 1
                
                # 验证OHLC关系
                if not (data.low <= data.open <= data.high and 
                       data.low <= data.close <= data.high):
                    print(f"      ⚠️  数据{i}的OHLC关系不合理")
            
            completeness_ratio = complete_data_count / len(kline_data)
            print(f"      ✓ 数据完整性: {completeness_ratio:.1%}")
            assert completeness_ratio >= 0.8, "数据完整性应大于80%"
            
            # 检查数据格式
            sample_data = kline_data[0]
            print(f"      ✓ 样本数据:")
            print(f"         日期: {sample_data.datetime}")
            print(f"         开盘: {sample_data.open:.2f}")
            print(f"         最高: {sample_data.high:.2f}")
            print(f"         最低: {sample_data.low:.2f}")
            print(f"         收盘: {sample_data.close:.2f}")
            print(f"         成交量: {sample_data.volume}")
        else:
            print(f"      ⚠️  数据验证失败，未获取到数据")
    
    def test_error_handling(self):
        """测试错误处理"""
        print(f"\n❌ 测试错误处理...")
        
        # 测试无效股票代码
        invalid_symbols = ['INVALID123', '999999', 'XXXYYY']
        
        for invalid_symbol in invalid_symbols:
            print(f"   测试无效代码: {invalid_symbol}")
            
            kline_data = data_manager.get_kline_data(
                symbol=invalid_symbol,
                kline_type=KLineType.DAY,
                count=5
            )
            
            # 无效代码应返回空列表而不是抛出异常
            assert isinstance(kline_data, list), "无效代码应返回列表类型"
            print(f"      ✓ 返回数据长度: {len(kline_data)}")
        
        # 测试无效获取器名称（这个测试现在不再适用）
        result = data_manager.get_kline_data(
            symbol='600300'
        )
        assert isinstance(result, list), "应返回列表"
        print(f"   ✓ 正常获取器处理正常")
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        print("\n" + "=" * 60)
        print("✅ 股票数据获取模块测试完成!")
        print(f"📊 测试股票: {cls.test_stocks}")
        print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


class TestDataConversion(unittest.TestCase):
    """数据转换测试类"""
    
    def setUp(self):
        """每个测试的初始化"""
        self.test_symbol = '600300'
    
    def test_kline_to_dataframe(self):
        """测试K线数据转DataFrame"""
        print(f"\n📊 测试K线数据转DataFrame...")
        
        kline_data = data_manager.get_kline_data(
            symbol=self.test_symbol,
            kline_type=KLineType.DAY,
            count=10
        )
        
        if kline_data:
            # 转换为DataFrame
            df_data = []
            for item in kline_data:
                df_data.append({
                    'date': item.datetime,
                    'open': item.open,
                    'high': item.high,
                    'low': item.low,
                    'close': item.close,
                    'volume': item.volume
                })
            
            df = pd.DataFrame(df_data)
            
            # 验证DataFrame结构
            expected_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            for col in expected_columns:
                assert col in df.columns, f"DataFrame应包含{col}列"
            
            # 验证数据类型
            assert df['open'].dtype in ['float64', 'int64'], "开盘价应为数值类型"
            assert df['volume'].dtype in ['float64', 'int64'], "成交量应为数值类型"
            
            print(f"   ✓ DataFrame形状: {df.shape}")
            print(f"   ✓ 列名: {list(df.columns)}")
            print(f"   ✓ 数据类型检查通过")
            
            # 计算技术指标示例
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            
            valid_ma5_count = df['ma5'].notna().sum()
            print(f"   ✓ MA5有效数据: {valid_ma5_count} 条")
            
            if valid_ma5_count > 0:
                latest_ma5 = df['ma5'].iloc[0]
                latest_close = df['close'].iloc[0]
                print(f"   ✓ 最新收盘: {latest_close:.2f}")
                print(f"   ✓ 最新MA5: {latest_ma5:.2f}")
        else:
            print(f"   ⚠️  DataFrame转换测试失败，未获取到数据")
    
    def test_data_analysis_capabilities(self):
        """测试数据分析能力"""
        print(f"\n📈 测试数据分析能力...")
        
        kline_data = data_manager.get_kline_data(
            symbol=self.test_symbol,
            kline_type=KLineType.DAY,
            count=30
        )
        
        if kline_data and len(kline_data) >= 10:
            # 转换为DataFrame
            df_data = [{
                'date': item.datetime,
                'open': item.open,
                'high': item.high,
                'low': item.low,
                'close': item.close,
                'volume': item.volume
            } for item in kline_data]
            
            df = pd.DataFrame(df_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            # 基本统计分析
            price_stats = df['close'].describe()
            print(f"   ✓ 价格统计:")
            print(f"      平均价: {price_stats['mean']:.2f}")
            print(f"      最高价: {price_stats['max']:.2f}")
            print(f"      最低价: {price_stats['min']:.2f}")
            print(f"      标准差: {price_stats['std']:.2f}")
            
            # 计算波动率
            df['returns'] = df['close'].pct_change()
            volatility = df['returns'].std() * (252**0.5)  # 年化波动率
            print(f"   ✓ 年化波动率: {volatility:.2%}")
            
            # 计算技术指标
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            
            # 判断趋势
            latest_close = df['close'].iloc[-1]
            latest_sma5 = df['sma_5'].iloc[-1]
            latest_sma20 = df['sma_20'].iloc[-1]
            
            if pd.notna(latest_sma5) and pd.notna(latest_sma20):
                if latest_close > latest_sma5 > latest_sma20:
                    trend = "上升趋势"
                elif latest_close < latest_sma5 < latest_sma20:
                    trend = "下降趋势"
                else:
                    trend = "震荡趋势"
                
                print(f"   ✓ 当前趋势: {trend}")
                print(f"   ✓ 当前价格: {latest_close:.2f}")
                print(f"   ✓ 5日均线: {latest_sma5:.2f}")
                print(f"   ✓ 20日均线: {latest_sma20:.2f}")
            
            # 成交量分析
            volume_stats = df['volume'].describe()
            print(f"   ✓ 平均成交量: {volume_stats['mean']:,.0f}")
            print(f"   ✓ 最大成交量: {volume_stats['max']:,.0f}")
        else:
            print(f"   ⚠️  数据分析测试失败，数据不足")


def run_stock_data_tests():
    """运行所有股票数据测试的主函数"""
    print("🚀 开始运行 stock.ipynb 替代测试程序")
    print("=" * 80)
    
    # 环境设置检查
    print("🔧 环境设置检查...")
    print(f"   Python路径: {XYSTOCK_DIR}")
    print(f"   当前目录: {CURRENT_DIR}")
    
    # 导入检查
    try:
        from data.stock_data_fetcher import data_manager
        print("   ✓ 数据管理器导入成功")
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False
    
    print("   ✓ 环境设置完成")
    print("=" * 80)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDataManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDataConversion))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=False)
    result = runner.run(suite)
    
    print("=" * 80)
    if result.wasSuccessful():
        print("✅ 所有测试通过!")
        print(f"✓ 运行了 {result.testsRun} 个测试")
    else:
        print(f"❌ 测试失败!")
        print(f"✓ 运行了 {result.testsRun} 个测试")
        print(f"❌ 失败: {len(result.failures)} 个")
        print(f"❌ 错误: {len(result.errors)} 个")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    """直接运行时的入口点"""
    success = run_stock_data_tests()
    sys.exit(0 if success else 1)
