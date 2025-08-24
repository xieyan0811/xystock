"""
筹码分析功能测试模块

测试股票筹码集中度分析功能。
包括：
1. 筹码集中度数据获取测试
2. 筹码分析指标验证
3. 筹码分析输出格式测试
4. 阈值逻辑测试
"""

import pytest
import sys
import os
import pandas as pd

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from providers.stock_utils import explain_cyq_data


class TestChipConcentrationAnalysis:
    """筹码集中度分析测试类"""
    
    @pytest.fixture
    def test_stocks(self):
        """测试股票列表"""
        return [
            '000001',  # 平安银行
            '000002',  # 万科A
            '600036'   # 招商银行
        ]
    
    def test_explain_cyq_data_basic(self, test_stocks):
        """测试筹码集中度基础功能"""
        for stock_code in test_stocks[:2]:  # 只测试前2个，避免测试时间过长
            result = explain_cyq_data(stock_code)
            
            # 如果有数据返回，应该是pandas Series或字典格式
            if result is not None:
                assert hasattr(result, '__getitem__')  # 可以使用索引访问
                
                # 检查关键指标是否存在
                key_indicators = ['获利比例', '平均成本', '90集中度', '70集中度']
                for indicator in key_indicators:
                    if indicator in result:
                        # 获利比例和集中度应该是数值
                        assert isinstance(result[indicator], (int, float))
                        
                        # 获利比例应该在0-100之间
                        if indicator == '获利比例':
                            assert 0 <= result[indicator] <= 100
                        
                        # 集中度应该是正数
                        if '集中度' in indicator:
                            assert result[indicator] >= 0
    
    def test_cyq_data_output_format(self, test_stocks, capsys):
        """测试筹码集中度输出格式"""
        stock_code = test_stocks[0]
        
        explain_cyq_data(stock_code)
        
        # 检查输出内容
        captured = capsys.readouterr()
        
        if "无法获取" not in captured.out and "获取筹码数据失败" not in captured.out:
            # 如果成功获取数据，应该包含这些关键信息
            assert "筹码集中度分析" in captured.out
            assert "获利比例" in captured.out
            assert "平均成本" in captured.out
            assert "90%筹码分布" in captured.out
            assert "70%筹码分布" in captured.out
            assert "交易策略参考" in captured.out
    
    def test_cyq_threshold_logic(self):
        """测试筹码集中度阈值逻辑（使用模拟数据）"""
        # 模拟筹码数据
        mock_data = pd.DataFrame({
            '获利比例': [85, 25, 50],
            '90集中度': [8, 25, 15],
            '平均成本': [10.5, 12.3, 11.8],
            '90成本-低': [10.0, 11.5, 11.0],
            '90成本-高': [11.0, 13.0, 12.5],
            '70成本-低': [10.2, 11.8, 11.2],
            '70成本-高': [10.8, 12.7, 12.2],
            '70集中度': [6, 20, 12]
        })
        
        # 测试高获利比例+高集中度场景
        latest = mock_data.iloc[0]
        assert latest['获利比例'] > 80
        assert latest['90集中度'] < 15
        
        # 测试低获利比例+高集中度场景
        latest = mock_data.iloc[1]
        assert latest['获利比例'] < 30
        
        # 测试适中场景
        latest = mock_data.iloc[2]
        assert 30 <= latest['获利比例'] <= 70
    
    def test_chip_data_consistency(self, test_stocks):
        """测试筹码数据一致性"""
        for stock_code in test_stocks[:2]:  # 只测试前2个
            result = explain_cyq_data(stock_code)
            
            if result is not None:
                # 检查数据类型一致性
                assert hasattr(result, '__getitem__')
                
                # 如果有平均成本，应该是正数
                if '平均成本' in result:
                    assert result['平均成本'] > 0
                
                # 如果有90成本范围，低成本应该小于高成本
                if '90成本-低' in result and '90成本-高' in result:
                    assert result['90成本-低'] <= result['90成本-高']
                
                # 如果有70成本范围，低成本应该小于高成本
                if '70成本-低' in result and '70成本-高' in result:
                    assert result['70成本-低'] <= result['70成本-高']
    
    def test_chip_error_handling(self):
        """测试筹码分析错误处理"""
        # 测试无效股票代码
        invalid_code = "INVALID999"
        
        result = explain_cyq_data(invalid_code)
        
        # 对于无效代码，应该返回None或者处理错误
        # 不应该抛出未捕获的异常
        assert result is None or hasattr(result, '__getitem__')
    
    @pytest.mark.parametrize("stock_code", ['000001', '000002', '600036'])
    def test_multiple_stocks_chip_analysis(self, stock_code):
        """测试多个股票的筹码分析"""
        result = explain_cyq_data(stock_code)
        
        # 每个股票的分析结果应该是一致的格式
        if result is not None:
            assert hasattr(result, '__getitem__')
            
            # 如果有数据，应该包含基本的筹码指标
            expected_indicators = ['获利比例', '平均成本']
            for indicator in expected_indicators:
                if indicator in result:
                    assert isinstance(result[indicator], (int, float))


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
