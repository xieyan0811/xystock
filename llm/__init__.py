"""
LLM模块 - 大语言模型相关功能
包含OpenAI客户端、使用记录等功能
"""

from .openai_client import OpenAIClient
from .usage_logger import UsageLogger

__all__ = [
    'OpenAIClient',
    'UsageLogger'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'XYStock Team'
__description__ = 'Enhanced OpenAI client with usage tracking and configuration management'
