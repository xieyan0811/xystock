"""
XY Stock 股票分析系统 - 设置界面
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 导入配置管理器
from config_manager import config

def save_config(section, key, value):
    """保存单个配置项到配置文件"""
    config.set(f'{section}.{key}', value)
    config.save()
    return True

def main():
    """显示设置界面"""
    st.header("⚙️ 系统设置")
    
    with st.container():
        st.subheader("OpenAI API 设置")
        
        # API 基本设置
        api_key = st.text_input(
            "API Key", 
            value=config.get('LLM_OPENAI.API_KEY', ''),
            type="password",
            help="输入您的OpenAI API密钥"
        )
        
        base_url = st.text_input(
            "API Base URL", 
            value=config.get('LLM_OPENAI.BASE_URL', 'https://api.openai.com/v1'),
            help="输入API基础URL，使用替代服务时需要修改"
        )
        
        # 模型设置
        col1, col2 = st.columns(2)
        with col1:
            analysis_model = st.text_input(
                "分析模型", 
                value=config.get('LLM_OPENAI.DEFAULT_MODEL', 'gpt-4o'),
                help="用于详细分析的高级模型"
            )
        
        with col2:
            inference_model = st.text_input(
                "推理模型", 
                value=config.get('LLM_OPENAI.INFERENCE_MODEL', 'gpt-4o-mini'),
                help="用于快速推理的轻量模型"
            )
        
        # 高级设置
        with st.expander("高级设置", expanded=False):
            timeout = st.number_input(
                "超时时间(秒)", 
                min_value=10, 
                max_value=300, 
                value=int(config.get('LLM_OPENAI.TIMEOUT', 60)),
                help="API请求超时时间"
            )
            
            max_retries = st.number_input(
                "最大重试次数", 
                min_value=0, 
                max_value=10, 
                value=int(config.get('LLM_OPENAI.MAX_RETRIES', 3)),
                help="API请求失败时最大重试次数"
            )
            
            temperature = st.slider(
                "温度参数", 
                min_value=0.0, 
                max_value=2.0, 
                value=float(config.get('LLM_OPENAI.DEFAULT_TEMPERATURE', 0.7)),
                step=0.1,
                help="控制生成文本的随机性，值越高越有创意，值越低越确定"
            )
        
        # 缓存设置
        with st.expander("缓存设置", expanded=False):
            enable_cache = st.toggle(
                "启用缓存", 
                value=config.get('LLM_CACHE.ENABLE_CACHE', False),
                help="是否启用API响应缓存"
            )
            
            cache_ttl = st.number_input(
                "缓存有效期(秒)", 
                min_value=60, 
                max_value=86400, 
                value=int(config.get('LLM_CACHE.CACHE_TTL', 3600)),
                help="缓存数据的有效期"
            )
        
        # 保存按钮
        if st.button("💾 保存设置", type="primary"):
            try:
                # 保存基本设置
                save_config('LLM_OPENAI', 'API_KEY', api_key)
                save_config('LLM_OPENAI', 'BASE_URL', base_url)
                save_config('LLM_OPENAI', 'DEFAULT_MODEL', analysis_model)
                save_config('LLM_OPENAI', 'INFERENCE_MODEL', inference_model)
                
                # 保存高级设置
                save_config('LLM_OPENAI', 'TIMEOUT', timeout)
                save_config('LLM_OPENAI', 'MAX_RETRIES', max_retries)
                save_config('LLM_OPENAI', 'DEFAULT_TEMPERATURE', temperature)
                
                # 保存缓存设置
                save_config('LLM_CACHE', 'ENABLE_CACHE', enable_cache)
                save_config('LLM_CACHE', 'CACHE_TTL', cache_ttl)
                
                st.success("设置已保存！")
            except Exception as e:
                st.error(f"保存失败: {str(e)}")
    
    # 测试连接区域
    st.subheader("测试连接")
    if st.button("🔄 测试API连接"):
        with st.spinner("正在测试连接..."):
            try:
                from llm.openai_client import OpenAIClient
                
                # 使用临时客户端测试连接
                client = OpenAIClient(api_key=api_key)
                response = client.ask("这是一个API连接测试，请回复'连接成功'", model_type="inference")
                
                if "连接成功" in response:
                    st.success(f"API连接测试成功！响应：{response}")
                else:
                    st.warning(f"API连接成功但响应不符合预期：{response}")
            except Exception as e:
                st.error(f"API连接测试失败：{str(e)}")
    
    # 页面底部信息
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <small>XY Stock 配置管理 | 重启应用后设置生效</small>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
