"""
配置管理器
"""
import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.toml"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            logging.warning(f"配置文件 {self.config_file} 不存在，使用默认配置")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = toml.load(f)
            logging.info(f"成功加载配置文件: {self.config_file}")
            return config
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'LLM_OPENAI': {
                'API_KEY': os.getenv('OPENAI_API_KEY', 'sk-'),
                'BASE_URL': 'https://api.deepseek.com',
                'TIMEOUT': 60,
                'MAX_RETRIES': 3,
                'DEFAULT_MODEL': 'deepseek-chat',
                'INFERENCE_MODEL': 'deepseek-chat',
                'DEFAULT_TEMPERATURE': 0.7
            },
            'LLM_LOGGING': {
                'USAGE_LOG_FILE': 'data/logs/openai_usage.csv',
                'ENABLE_LOGGING': True,
                'LOG_LEVEL': 'INFO'
            },
            'LLM_CACHE': {
                'ENABLE_CACHE': False,
                'CACHE_TTL': 3600
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的键路径
        
        Args:
            key: 配置键，支持 'section.key' 格式
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持 'section.key' 格式
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 创建嵌套字典结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                toml.dump(self.config, f)
            logging.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
    
    def get_openai_config(self) -> Dict[str, Any]:
        """获取OpenAI相关配置"""
        return self.get('LLM_OPENAI', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志相关配置"""
        return self.get('LLM_LOGGING', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存相关配置"""
        return self.get('LLM_CACHE', {})
    
    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        logging.info("配置已重新加载")

# 全局配置实例
XYSTOCK_DIR = Path(__file__).resolve().parent
config = ConfigManager(os.path.join(XYSTOCK_DIR, 'config.toml'))
