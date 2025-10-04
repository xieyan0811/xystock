"""
XY Stock 版本信息配置
"""

__version__ = "1.2.0"
__app_name__ = "XY Stock"
__full_version__ = f"{__app_name__} v{__version__}"

def get_version():
    """获取版本号"""
    return __version__

def get_app_name():
    """获取应用名称"""
    return __app_name__

def get_full_version():
    """获取完整版本信息"""
    return __full_version__
