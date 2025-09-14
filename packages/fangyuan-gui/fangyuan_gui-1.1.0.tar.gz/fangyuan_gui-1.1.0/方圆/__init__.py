"""
方圆 GUI 库 - 多语法风格支持
提供多种创建 GUI 的语法风格，让编程更像写说明书。
"""

# 首先导入常用的 Qt 模块
from PySide6.QtCore import Qt, QPoint, QSize, QRect
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout

# 显式导入核心功能
from 方圆.核心 import (
    # 基础函数
    创建主窗口, 为窗口设置中央区域和布局, 为控件设置布局,
    应用全局样式, 使控件具有样式,

    # 控件创建
    添加标签到布局, 添加按钮到布局, 添加输入框到布局,
    添加文本框到布局, 添加列表框到布局, 添加复选框到布局,

    # 布局管理
    在布局中添加弹性空间, 在布局中添加间距,

    # 对话框
    显示信息, 显示警告, 显示错误, 询问是或否,

    # 高级效果
    添加带阴影的框架到布局,

    # 列表操作
    向列表添加可勾选项目, 切换列表项目状态,

    # 工具函数
    简单居中窗口, 启动应用程序_说明性, 启动应用程序, 运行应用程序,

    # 上下文管理器
    创建窗口上下文
)

# 尝试导入样式和组件功能
try:
    from 样式.主题 import 获取主题, 获取样式, 应用主题
    from 组件.高级按钮 import 高级按钮, 创建按钮
    from 组件.卡片 import 卡片, 创建卡片
except ImportError:
    # 如果模块不存在，创建占位符函数
    def 获取主题(主题名称="light"):
        """占位函数 - 样式模块未实现"""
        print("警告：样式模块未实现")
        return {}

    def 获取样式(样式名称, 主题名称="light"):
        """占位函数 - 样式模块未实现"""
        print("警告：样式模块未实现")
        return {}

    def 应用主题(窗口, 主题名称="light"):
        """占位函数 - 样式模块未实现"""
        print("警告：样式模块未实现")
        return {}

    # 占位组件类
    class 高级按钮:
        def __init__(self, *args, **kwargs):
            from PySide6.QtWidgets import QPushButton
            self.button = QPushButton(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.button, name)

    def 创建按钮(文字="", 图标=None, 样式="primary", 主题="light", 点击事件=None):
        """占位函数 - 组件模块未实现"""
        from PySide6.QtWidgets import QPushButton
        button = QPushButton(文字)
        if 点击事件:
            button.clicked.connect(点击事件)
        return button

    class 卡片:
        def __init__(self, 标题=None, 样式="card", 主题="light"):
            from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
            self.frame = QFrame()
            self.layout = QVBoxLayout(self.frame)
            if 标题:
                label = QLabel(标题)
                self.layout.addWidget(label)

        def 添加控件(self, 控件):
            self.layout.addWidget(控件)

    def 创建卡片(标题=None, 主题="light"):
        """占位函数 - 组件模块未实现"""
        return 卡片(标题, "card", 主题)

# 简写别名（向前兼容）
创建窗口 = 创建主窗口
设置布局 = 为窗口设置中央区域和布局
控件布局 = 为控件设置布局
全局样式 = 应用全局样式
控件样式 = 使控件具有样式
添加标签 = 添加标签到布局
添加按钮 = 添加按钮到布局
添加输入框 = 添加输入框到布局
添加文本框 = 添加文本框到布局
添加列表 = 添加列表框到布局
添加复选框 = 添加复选框到布局
弹性空间 = 在布局中添加弹性空间
添加间距 = 在布局中添加间距
信息框 = 显示信息
警告框 = 显示警告
错误框 = 显示错误
确认框 = 询问是或否
阴影框架 = 添加带阴影的框架到布局
列表项 = 向列表添加可勾选项目
切换状态 = 切换列表项目状态
居中窗口 = 简单居中窗口
运行应用 = 运行应用程序
启动应用 = 启动应用程序

# 从自动加载器导入智能语法系统
try:
    from 语法.自动加载 import (
        使用语法, 获取当前语法, 语法信息, 检测最佳语法
    )
except ImportError:
    # 如果自动加载模块不存在，创建占位函数
    def 使用语法(语法名称):
        print(f"警告：自动加载模块未实现，无法切换到 {语法名称} 语法")
        return False

    def 获取当前语法():
        return "传统"

    def 语法信息():
        return {"传统": "函数调用风格，向前兼容"}

    def 检测最佳语法():
        return "传统"

# 导出常用的 Qt 常量和方法
对齐方式 = {
    "居中": Qt.AlignCenter,
    "左对齐": Qt.AlignLeft | Qt.AlignVCenter,
    "右对齐": Qt.AlignRight | Qt.AlignVCenter,
    "顶部对齐": Qt.AlignTop,
    "底部对齐": Qt.AlignBottom
}

勾选状态 = {
    "已勾选": Qt.Checked,
    "未勾选": Qt.Unchecked,
    "部分勾选": Qt.PartiallyChecked
}

# 显式导出列表
__all__ = [
    # 核心功能
    '创建主窗口', '为窗口设置中央区域和布局', '为控件设置布局',
    '应用全局样式', '使控件具有样式', '添加标签到布局',
    '添加按钮到布局', '添加输入框到布局', '添加文本框到布局',
    '添加列表框到布局', '添加复选框到布局', '在布局中添加弹性空间',
    '在布局中添加间距', '显示信息', '显示警告', '显示错误',
    '询问是或否', '添加带阴影的框架到布局', '向列表添加可勾选项目',
    '切换列表项目状态', '简单居中窗口', '启动应用程序_说明性',
    '启动应用程序', '运行应用程序', '创建窗口上下文',

    # 样式和组件功能
    '获取主题', '获取样式', '应用主题',
    '高级按钮', '创建按钮',
    '卡片', '创建卡片',

    # 简写别名
    '创建窗口', '设置布局', '控件布局', '全局样式', '控件样式',
    '添加标签', '添加按钮', '添加输入框', '添加文本框', '添加列表',
    '添加复选框', '弹性空间', '添加间距', '信息框', '警告框',
    '错误框', '确认框', '阴影框架', '列表项', '切换状态',
    '居中窗口', '运行应用', '启动应用',

    # 语法控制
    '使用语法', '获取当前语法', '语法信息', '检测最佳语法',

    # Qt 相关
    'Qt', 'QPoint', 'QSize', 'QRect', 'QWidget',
    'QHBoxLayout', 'QVBoxLayout', 'QGridLayout',
    '对齐方式', '勾选状态'
]

# 动态导出功能
def __getattr__(name):
    """动态属性访问，用于处理IDE的未解析引用"""
    if name in __all__:
        # 如果名称在导出列表中，但IDE找不到，返回一个占位符
        def 占位函数(*args, **kwargs):
            print(f"警告：函数 {name} 可能未正确实现")
            return None
        return 占位函数

    raise AttributeError(f"模块 '方圆' 没有属性 '{name}'")

# 默认使用自动检测的最佳语法
print(f"方圆GUI库已加载，当前语法: {获取当前语法()}")
print("✅ 已自动导入常用 Qt 模块: Qt, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout")