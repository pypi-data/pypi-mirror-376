# -*- coding: utf-8 -*-
"""
EmuTrader 版本信息

采用语义化版本控制 (Semantic Versioning)
格式：MAJOR.MINOR.PATCH[-prerelease][+buildmetadata]

版本号说明:
- MAJOR: 不兼容的API修改
- MINOR: 向下兼容的新功能  
- PATCH: 向下兼容的问题修正
"""

__version_info__ = (0, 1, 1)
__version__ = ".".join(map(str, __version_info__))

# 详细版本信息
VERSION_INFO = {
    "version": __version__,
    "version_info": __version_info__,
    "release_name": "Alpha",  # 版本代号
    "build_date": "2024-01-15",
    "python_requires": ">=3.8",
    "api_version": "0.1",
}

# 兼容性信息
COMPATIBILITY = {
    "joinquant_api": "2.0+",
    "qmt_api": "1.0+", 
    "python_min": "3.6.0",
    "python_tested": ["3.6", "3.7", "3.8", "3.9", "3.10", "3.11"],
}

# 功能特性信息
FEATURES = {
    "jq_compatibility": True,      # JoinQuant完全兼容
    "multi_account": True,         # 多账户支持  
    "cache_optimization": True,    # 缓存优化
    "sqlite_storage": True,        # SQLite存储
    "memory_storage": True,        # 内存存储
    "thread_safe": True,          # 线程安全
    "risk_management": True,       # 风险管理
    "performance_tracking": True,  # 性能追踪
}

def get_version():
    """获取版本字符串"""
    return __version__

def get_version_info():
    """获取详细版本信息"""
    return VERSION_INFO.copy()

def print_version():
    """打印版本信息"""
    print(f"EmuTrader v{__version__} ({VERSION_INFO['release_name']})")
    print(f"Build Date: {VERSION_INFO['build_date']}")
    print(f"Python: {VERSION_INFO['python_requires']}")
    print(f"API Version: {VERSION_INFO['api_version']}")

if __name__ == "__main__":
    print_version()