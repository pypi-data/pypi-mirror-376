"""
自动加载器 - 智能检测和加载最适合的语法风格
"""

import os
import sys
from pathlib import Path

# 导入所有语法风格
from .传统 import *
from .上下文 import *
from .链式 import *
from .装饰器 import *


# 检测最佳语法风格的函数
def 检测最佳语法():
    """
    自动检测最适合的语法风格
    基于代码分析和用户偏好
    """
    # 检查环境变量
    首选语法 = os.environ.get('方圆_语法', '').lower()

    if 首选语法 in ['上下文', 'with', 'block']:
        return '上下文'
    elif 首选语法 in ['链式', '链', 'chained']:
        return '链式'
    elif 首选语法 in ['装饰器', '装饰', 'decorator']:
        return '装饰器'
    else:
        # 默认使用传统语法保持兼容
        return '传统'


# 当前激活的语法
当前语法 = 检测最佳语法()


def 使用语法(语法名称):
    """切换到指定的语法风格"""
    global 当前语法
    可用语法 = ['传统', '上下文', '链式', '装饰器']

    if 语法名称 in 可用语法:
        当前语法 = 语法名称
        print(f"已切换到 {语法名称} 语法")
        return True
    else:
        print(f"未知语法: {语法名称}，可用语法: {可用语法}")
        return False


def 获取当前语法():
    """获取当前使用的语法风格"""
    return 当前语法


def 语法信息():
    """显示所有可用的语法信息"""
    return {
        '传统': '函数调用风格，向前兼容',
        '上下文': 'with 块状语法，结构清晰',
        '链式': '链式调用，类似大括号风格',
        '装饰器': '装饰器语法，函数式编程'
    }


# 根据当前语法动态导出相应的函数
def __getattr__(name):
    """
    动态属性访问，根据当前语法返回相应的函数
    """
    if 当前语法 == '上下文':
        from .上下文 import __dict__ as 上下文字典
        if name in 上下文字典:
            return 上下文字典[name]
    elif 当前语法 == '链式':
        from .链式 import __dict__ as 链式字典
        if name in 链式字典:
            return 链式字典[name]
    elif 当前语法 == '装饰器':
        from .装饰器 import __dict__ as 装饰器字典
        if name in 装饰器字典:
            return 装饰器字典[name]

    # 默认回退到传统语法
    from .传统 import __dict__ as 传统字典
    if name in 传统字典:
        return 传统字典[name]

    raise AttributeError(f"模块 '方圆.语法.自动加载' 没有属性 '{name}'")


# 导出列表（动态生成）
def __dir__():
    """返回所有可用的属性"""
    所有属性 = set()
    for 语法模块 in ['传统', '上下文', '链式', '装饰器']:
        try:
            module = __import__(f'.{语法模块}', fromlist=['*'])
            所有属性.update(getattr(module, '__all__', []))
        except ImportError:
            continue

    所有属性.update(['使用语法', '获取当前语法', '语法信息', '检测最佳语法'])
    return sorted(所有属性)


__all__ = [
    '使用语法',
    '获取当前语法',
    '语法信息',
    '检测最佳语法'
]

# 添加传统语法的所有导出
from .传统 import __all__ as 传统全部

__all__.extend(传统全部)