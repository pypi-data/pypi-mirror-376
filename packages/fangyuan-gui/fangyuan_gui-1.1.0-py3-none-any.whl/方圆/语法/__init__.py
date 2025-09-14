"""
方圆语法模块 - 提供多种 GUI 语法风格
"""

# 导出所有语法模块
from . import 传统
from . import 上下文
from . import 链式
from . import 装饰器

# 导出列表
__all__ = ['传统', '上下文', '链式', '装饰器']