"""
通用工具模块
包含各种通用的工具函数

主要功能：
- remove_markdown_format: 去除markdown格式，将markdown文本转换为纯文本
- clean_text: 清理文本中的多余空格和换行
- normalize_whitespace: 标准化空白字符

使用示例：
    from common_utils import remove_markdown_format
    
    markdown_text = "这是**粗体**和*斜体*文本"
    plain_text = remove_markdown_format(markdown_text)
    print(plain_text)  # 输出: 这是粗体和斜体文本
"""

import re


def remove_markdown_format(text: str) -> str:
    """
    去除markdown文本的格式，输入字符串，输出纯文本字符串
    
    Args:
        text (str): 包含markdown格式的文本
        
    Returns:
        str: 去除markdown格式后的纯文本
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 移除代码块 ```
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # 移除行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # 移除粗体 **text** 或 __text__
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    
    # 移除斜体 *text* 或 _text_
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # 移除删除线 ~~text~~
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    
    # 移除标题 # ## ### 等
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # 移除图片 ![alt](url) - 需要在链接处理之前
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    
    # 移除链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # 移除引用 >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    
    # 移除水平线 --- 或 ***
    text = re.sub(r'^(-{3,}|\*{3,})$', '', text, flags=re.MULTILINE)
    
    # 移除列表标记
    # 无序列表 - * +
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    # 有序列表 1. 2. 等
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # 移除表格分隔符
    text = re.sub(r'\|', '', text)
    text = re.sub(r'^[-\s:]+$', '', text, flags=re.MULTILINE)
    
    # 清理多余的空行
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 去除首尾空白
    text = text.strip()
    
    return text


def clean_text(text: str) -> str:
    """
    清理文本，去除多余的空格和换行
    
    Args:
        text (str): 需要清理的文本
        
    Returns:
        str: 清理后的文本
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 将多个空格替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 去除首尾空白
    text = text.strip()
    
    return text


def normalize_whitespace(text: str) -> str:
    """
    标准化空白字符，将各种空白字符统一为普通空格
    
    Args:
        text (str): 需要标准化的文本
        
    Returns:
        str: 标准化后的文本
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 将各种空白字符（制表符、换行符等）替换为空格
    text = re.sub(r'[\t\r\n\f\v]', ' ', text)
    
    # 将多个连续空格替换为单个空格
    text = re.sub(r' +', ' ', text)
    
    # 去除首尾空白
    text = text.strip()
    
    return text
