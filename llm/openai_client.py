"""
OpenAI API 增强封装
包含 token 使用记录、配置管理、错误处理等功能
"""
import time
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
from openai.types.chat import ChatCompletion

# 添加项目根目录到路径，以便导入配置管理器
sys.path.append(str(Path(__file__).parent.parent))
from config_manager import config
from .usage_logger import UsageLogger

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.get('LLM_LOGGING.LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OpenAIClient:
    """增强的 OpenAI API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, usage_logger: Optional[UsageLogger] = None):
        """
        初始化 OpenAI 客户端
        
        Args:
            api_key: API 密钥，如果为空则从配置文件读取
            usage_logger: 使用记录器，如果为空则自动创建
        """
        # 从配置获取API密钥
        self.api_key = api_key or config.get('LLM_OPENAI.API_KEY')
        if not self.api_key:
            raise ValueError("API密钥未设置，请在配置文件中设置 LLM_OPENAI.API_KEY")
        
        # 获取其他配置
        openai_config = config.get_openai_config()
        base_url = openai_config.get('BASE_URL')
        timeout = openai_config.get('TIMEOUT', 60)
        max_retries = openai_config.get('MAX_RETRIES', 3)
        
        # 初始化 OpenAI 客户端
        kwargs = {'api_key': self.api_key, 'timeout': timeout, 'max_retries': max_retries}
        if base_url:
            kwargs['base_url'] = base_url
        
        self.client = OpenAI(**kwargs)
        
        # 初始化使用记录器
        if config.get('LLM_LOGGING.ENABLE_LOGGING', True):
            log_file = config.get('LLM_LOGGING.USAGE_LOG_FILE', 'data/logs/openai_usage.csv')
            if not Path(log_file).is_absolute():
                project_root = Path(__file__).parent.parent
                log_file = project_root / log_file
            self.usage_logger = usage_logger or UsageLogger(str(log_file))
        else:
            self.usage_logger = None
        
        # 默认参数
        self.default_model = openai_config.get('DEFAULT_MODEL', 'gpt-4o')
        self.default_temperature = openai_config.get('DEFAULT_TEMPERATURE', 0.7)
        
        logger.info("OpenAI 客户端初始化完成")
    
    def ask(self, 
            prompt: str, 
            model: Optional[str] = None, 
            temperature: Optional[float] = None, 
            max_tokens: Optional[int] = None,
            system_message: Optional[str] = None,
            messages: Optional[List[Dict[str, str]]] = None,
            json_mode: bool = False,
            debug: bool = False) -> str:
        """
        发送聊天请求
        
        Args:
            prompt: 用户输入
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            system_message: 系统消息
            messages: 完整的消息列表（如果提供，将覆盖prompt和system_message）
            json_mode: 是否强制返回JSON格式
            debug: 是否打印调试信息
            
        Returns:
            AI回复内容
        """
        start_time = time.time()
        
        # 使用默认值
        model = model or self.default_model
        temperature = temperature or self.default_temperature
        
        try:
            # 构建消息列表
            if messages is None:
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
            
            # 构建请求参数
            kwargs = {
                'model': model,
                'messages': messages,
                'temperature': temperature
            }
            if max_tokens:
                kwargs['max_tokens'] = max_tokens
            
            # 如果启用了JSON模式，设置response_format
            if json_mode:
                kwargs['response_format'] = {"type": "json_object"}
                # 在JSON模式下，确保系统消息中包含JSON指令
                if not any(msg.get('role') == 'system' for msg in messages):
                    messages.insert(0, {"role": "system", "content": "You must respond with valid JSON."})
                elif not any('json' in msg.get('content', '').lower() for msg in messages if msg.get('role') == 'system'):
                    # 如果已有系统消息但不包含JSON指令，则追加
                    for msg in messages:
                        if msg.get('role') == 'system':
                            msg['content'] += " You must respond with valid JSON."
                            break
            
            # 发送请求
            response: ChatCompletion = self.client.chat.completions.create(**kwargs)
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 获取回复内容
            content = response.choices[0].message.content
            
            # 记录使用情况
            if self.usage_logger:
                usage_data = response.usage.model_dump() if response.usage else {}
                input_text = prompt if not messages else str(messages)
                
                self.usage_logger.log_usage(
                    model=model,
                    usage_data=usage_data,
                    input_text=input_text,
                    output_text=content,
                    response_time=response_time,
                    temperature=temperature,
                    success=True
                )
            
            # 调试输出
            if debug:
                print(f"模型: {model}")
                print(f"输入: {prompt}")
                print(f"输出: {content}")
                print(f"Token使用: {response.usage.model_dump() if response.usage else 'N/A'}")
                print(f"响应时间: {response_time:.2f}秒")
            
            logger.info(f"API调用成功，模型: {model}, tokens: {response.usage.total_tokens if response.usage else 'N/A'}")
            
            return content
            
        except Exception as e:
            response_time = time.time() - start_time
            error_message = str(e)
            
            # 记录错误
            if self.usage_logger:
                input_text = prompt if not messages else str(messages)
                self.usage_logger.log_usage(
                    model=model,
                    usage_data={},
                    input_text=input_text,
                    output_text="",
                    response_time=response_time,
                    temperature=temperature,
                    success=False,
                    error_message=error_message
                )
            
            logger.error(f"API调用失败: {error_message}")
            raise
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             model: Optional[str] = None, 
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None,
             json_mode: bool = False,
             debug: bool = False) -> str:
        """
        多轮对话
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            json_mode: 是否强制返回JSON格式
            debug: 是否打印调试信息
            
        Returns:
            AI回复内容
        """
        return self.ask(
            prompt="",  # 这里prompt为空，因为使用messages
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
            json_mode=json_mode,
            debug=debug
        )
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        获取使用统计
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息
        """
        if self.usage_logger:
            return self.usage_logger.get_usage_stats(days)
        return {}
    
    def export_usage_report(self, output_file: str = "reports/usage_report.html"):
        """
        导出使用报告
        
        Args:
            output_file: 输出文件路径
        """
        if self.usage_logger:
            self.usage_logger.export_usage_report(output_file)

# 示例和测试
if __name__ == "__main__":
    try:
        # 创建客户端
        client = OpenAIClient()
        
        # 简单问答
        print("=== 简单问答测试 ===")
        response = client.ask("用一句话评价AAPL股票", debug=True)
        print(f"回复: {response}")
        
        # 多轮对话测试
        print("\n=== 多轮对话测试 ===")
        messages = [
            {"role": "system", "content": "你是一个专业的股票分析师"},
            {"role": "user", "content": "分析一下苹果公司的投资价值"},
            {"role": "assistant", "content": "苹果公司作为科技巨头..."},
            {"role": "user", "content": "那它的主要风险是什么？"}
        ]
        response = client.chat(messages, debug=True)
        print(f"回复: {response}")
        
        # 获取使用统计
        print("\n=== 使用统计 ===")
        stats = client.get_usage_stats()
        if stats:
            print(f"总请求数: {stats.get('total_requests', 0)}")
            print(f"总Token数: {stats.get('total_tokens', 0)}")
            print(f"总成本: ${stats.get('total_cost', 0):.4f}")
        
        # 导出使用报告
        client.export_usage_report()
        print("使用报告已导出")
        
    except Exception as e:
        print(f"测试失败: {e}")
