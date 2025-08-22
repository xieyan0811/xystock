#!/usr/bin/env python3
"""
XY Stock Streamlit UI 启动脚本
在8811端口启动Streamlit应用
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """启动Streamlit应用"""
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    ui_file = project_root / "ui" / "app.py"
    
    print("🚀 正在启动 XY Stock Streamlit UI...")
    print(f"📂 项目路径: {project_root}")
    print(f"🌐 访问地址: http://localhost:8811")
    print("⏹️  按 Ctrl+C 停止服务")
    print("-" * 50)
    
    # 检查streamlit是否已安装
    try:
        import streamlit
        print(f"✅ Streamlit 版本: {streamlit.__version__}")
    except ImportError:
        print("❌ 错误: 未安装 Streamlit")
        print("请运行: pip install streamlit")
        return 1
    
    # 检查应用文件是否存在
    if not ui_file.exists():
        print(f"❌ 错误: 应用文件不存在: {ui_file}")
        return 1
    
    # 构建streamlit命令
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(ui_file),
        "--server.port", "8811",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ]
    
    try:
        # 切换到项目根目录
        os.chdir(project_root)
        
        # 启动streamlit
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断，正在停止服务...")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return 1
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
