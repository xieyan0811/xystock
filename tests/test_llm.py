"""
OpenAI 客户端测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def main():
    print("OpenAI 客户端测试")
    print("-" * 30)
    
    # 1. 测试配置加载
    try:
        from config_manager import config
        api_key = config.get('LLM_OPENAI.API_KEY')
        model = config.get('LLM_OPENAI.DEFAULT_MODEL')
        print(f"✓ 配置加载成功")
        print(f"  API Key: {'已设置' if api_key else '未设置'}")
        print(f"  默认模型: {model}")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return
    
    # 2. 测试模块导入
    try:
        from llm import OpenAIClient, UsageLogger
        print("✓ 模块导入成功")
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return
    
    # 3. 测试客户端创建
    try:
        if not api_key:
            print("⚠ API密钥未设置，跳过客户端测试")
            return
        
        client = OpenAIClient()
        print("✓ 客户端创建成功")
        
        # 4. 简单测试调用（如果API密钥有效）
        try:
            response = client.ask("说一句话", debug=False)
            print("✓ API调用成功")
            print(f"  回复: {response[:50]}...")
            
            # 5. 测试使用统计
            stats = client.get_usage_stats(days=1)
            if stats:
                print(f"✓ 统计功能正常")
                print(f"  今日请求: {stats.get('total_requests', 0)}")
                print(f"  今日tokens: {stats.get('total_tokens', 0)}")
        except Exception as e:
            print(f"⚠ API调用失败: {e}")
            
    except Exception as e:
        print(f"✗ 客户端创建失败: {e}")
    
    print("-" * 30)
    print("测试完成")

if __name__ == "__main__":
    main()
