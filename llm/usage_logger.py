"""
OpenAI API 使用记录管理器
"""
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

class UsageLogger:
    """OpenAI API 使用记录器"""
    
    def __init__(self, log_file: str = "data/logs/openai_usage.csv"):
        """
        初始化使用记录器
        
        Args:
            log_file: 日志文件路径
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化CSV文件（如果不存在）
        if not self.log_file.exists():
            self._init_csv()
    
    def _init_csv(self):
        """初始化CSV文件，创建列标题"""
        df = pd.DataFrame(columns=[
            'timestamp',
            'model',
            'prompt_tokens',
            'completion_tokens', 
            'total_tokens',
            'cost_estimate',
            'temperature',
            'input_text',
            'output_text',
            'response_time',
            'success',
            'error_message'
        ])
        df.to_csv(self.log_file, index=False)
    
    def log_usage(self, 
                  model: str,
                  usage_data: Dict[str, Any],
                  input_text: str,
                  output_text: str,
                  response_time: float,
                  temperature: float = 0.7,
                  success: bool = True,
                  error_message: str = ""):
        """
        记录API使用情况
        
        Args:
            model: 使用的模型名称
            usage_data: 使用数据（token信息）
            input_text: 输入文本
            output_text: 输出文本
            response_time: 响应时间
            temperature: 温度参数
            success: 是否成功
            error_message: 错误信息
        """
        # 估算成本（基于OpenAI定价，仅供参考）
        cost_estimate = self._estimate_cost(model, usage_data)
        
        # 创建记录
        record = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'prompt_tokens': usage_data.get('prompt_tokens', 0),
            'completion_tokens': usage_data.get('completion_tokens', 0),
            'total_tokens': usage_data.get('total_tokens', 0),
            'cost_estimate': cost_estimate,
            'temperature': temperature,
            'input_text': self._truncate_text(input_text, 500),  # 截断长文本
            'output_text': self._truncate_text(output_text, 500),
            'response_time': response_time,
            'success': success,
            'error_message': error_message
        }
        
        # 追加到CSV文件
        df = pd.DataFrame([record])
        df.to_csv(self.log_file, mode='a', header=False, index=False)
        
        logging.info(f"记录API使用: {model}, tokens: {usage_data.get('total_tokens', 0)}, 成本: ${cost_estimate:.4f}")
    
    def _estimate_cost(self, model: str, usage_data: Dict[str, Any]) -> float:
        """
        估算API调用成本
        
        Args:
            model: 模型名称
            usage_data: 使用数据
            
        Returns:
            估算成本（美元）
        """
        # OpenAI定价（2024年8月参考价格，实际价格可能变化）
        pricing = {
            'gpt-4o': {'input': 0.005 / 1000, 'output': 0.015 / 1000},
            'gpt-4o-mini': {'input': 0.00015 / 1000, 'output': 0.0006 / 1000},
            'gpt-4': {'input': 0.03 / 1000, 'output': 0.06 / 1000},
            'gpt-3.5-turbo': {'input': 0.0015 / 1000, 'output': 0.002 / 1000},
        }
        
        if model not in pricing:
            return 0.0
        
        input_cost = usage_data.get('prompt_tokens', 0) * pricing[model]['input']
        output_cost = usage_data.get('completion_tokens', 0) * pricing[model]['output']
        
        return input_cost + output_cost
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本以节省存储空间"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        获取使用统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        try:
            df = pd.read_csv(self.log_file)
            if df.empty:
                return {}
            
            # 过滤最近N天的数据
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            recent_df = df[df['timestamp'] >= cutoff_date]
            
            if recent_df.empty:
                return {}
            
            stats = {
                'total_requests': len(recent_df),
                'total_tokens': recent_df['total_tokens'].sum(),
                'total_cost': recent_df['cost_estimate'].sum(),
                'avg_response_time': recent_df['response_time'].mean(),
                'success_rate': recent_df['success'].mean(),
                'model_distribution': recent_df['model'].value_counts().to_dict(),
                'daily_usage': recent_df.groupby(recent_df['timestamp'].dt.date)['total_tokens'].sum().to_dict()
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"获取使用统计失败: {e}")
            return {}
    
    def export_usage_report(self, output_file: str = "reports/usage_report.html"):
        """
        导出使用报告
        
        Args:
            output_file: 输出文件路径
        """
        try:
            df = pd.read_csv(self.log_file)
            if df.empty:
                return
            
            # 创建输出目录
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # 生成HTML报告
            html_content = f"""
            <html>
            <head><title>OpenAI API 使用报告</title></head>
            <body>
            <h1>OpenAI API 使用报告</h1>
            <h2>总体统计</h2>
            <p>总请求数: {len(df)}</p>
            <p>总Token数: {df['total_tokens'].sum()}</p>
            <p>总成本: ${df['cost_estimate'].sum():.4f}</p>
            <p>平均响应时间: {df['response_time'].mean():.2f}秒</p>
            
            <h2>详细数据</h2>
            {df.to_html(index=False)}
            </body>
            </html>
            """
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logging.info(f"使用报告已导出到: {output_file}")
            
        except Exception as e:
            logging.error(f"导出使用报告失败: {e}")
