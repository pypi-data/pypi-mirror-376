"""
方圆核心功能 - 所有语法风格的基础
包含所有基础的 GUI 创建和管理函数。
"""

import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QGraphicsDropShadowEffect, QApplication,
    QSpacerItem, QSizePolicy, QCheckBox
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap,
    QPainter, QLinearGradient, QBrush, QTextCursor
)
from PySide6.QtCore import (
    Qt, QTimer, QRect, QPoint, QSize, QUrl, QDate, QTime, QDateTime
)

from 样式.主题 import 获取主题, 获取样式, 应用主题
from 组件.高级按钮 import 高级按钮, 创建按钮
from 组件.卡片 import 卡片, 创建卡片

# --- 核心窗口和布局 ---

def 创建主窗口(标题="我的应用", 宽度=600, 高度=400):
    """
    创建并配置一个 QMainWindow 实例。
    自动处理 QApplication 实例的创建。
    """
    # 检查是否已有 QApplication 实例，如果没有则创建
    应用实例 = QApplication.instance()
    if 应用实例 is None:
        # 如果没有命令行参数，传递空列表
        try:
            import sys
            应用实例 = QApplication(sys.argv)
        except:
            # 如果 sys.argv 不可用，使用空列表
            应用实例 = QApplication([])

    窗口 = QMainWindow()
    窗口.setWindowTitle(标题)
    窗口.resize(宽度, 高度)
    return 窗口


def 为窗口设置中央区域和布局(窗口, 布局类型="垂直", 内边距=20, 间距=15):
    """
    为 QMainWindow 设置中央部件和布局管理器
    布局类型: "垂直", "水平", "网格"
    """
    if not isinstance(窗口, QMainWindow):
        raise TypeError("参数'窗口'必须是QMainWindow实例")

    中央区域 = QWidget()
    窗口.setCentralWidget(中央区域)

    if 布局类型 == "垂直":
        布局管理器 = QVBoxLayout()
    elif 布局类型 == "水平":
        布局管理器 = QHBoxLayout()
    elif 布局类型 == "网格":
        布局管理器 = QGridLayout()
    else:
        布局管理器 = QVBoxLayout()

    布局管理器.setContentsMargins(内边距, 内边距, 内边距, 内边距)
    布局管理器.setSpacing(间距)
    中央区域.setLayout(布局管理器)
    return 中央区域, 布局管理器


def 为控件设置布局(控件, 布局类型="垂直", 内边距=20, 间距=15):
    """
    为普通的 QWidget 设置布局管理器。
    布局类型: "垂直", "水平", "网格"
    """
    if 布局类型 == "垂直":
        布局管理器 = QVBoxLayout()
    elif 布局类型 == "水平":
        布局管理器 = QHBoxLayout()
    elif 布局类型 == "网格":
        布局管理器 = QGridLayout()
    else:
        布局管理器 = QVBoxLayout()

    布局管理器.setContentsMargins(内边距, 内边距, 内边距, 内边距)
    布局管理器.setSpacing(间距)
    控件.setLayout(布局管理器)
    return 控件, 布局管理器


# --- 美化和样式 ---

def 应用全局样式(窗口, 背景颜色="#F0F0F0", 字体="微软雅黑", 字号=12):
    """应用全局样式到窗口"""
    样式表 = f"""
        QMainWindow {{
            background-color: {背景颜色};
            font-family: "{字体}";
            font-size: {字号}px;
        }}
        QWidget {{
            color: #333333;
        }}
    """
    窗口.setStyleSheet(样式表)


def 使控件具有样式(控件, 样式规则):
    """为单个控件应用内联样式"""
    样式字符串 = ""
    if "背景颜色" in 样式规则:
        样式字符串 += f"background-color: {样式规则['背景颜色']};"
    if "文字颜色" in 样式规则:
        样式字符串 += f"color: {样式规则['文字颜色']};"
    if "字体大小" in 样式规则:
        样式字符串 += f"font-size: {样式规则['字体大小']};"
    if "字体" in 样式规则:
        样式字符串 += f"font-family: {样式规则['字体']};"
    if "字体粗细" in 样式规则:
        样式字符串 += f"font-weight: {样式规则['字体粗细']};"
    if "字体样式" in 样式规则:
        样式字符串 += f"font-style: {样式规则['字体样式']};"
    if "行高" in 样式规则:
        样式字符串 += f"line-height: {样式规则['行高']};"
    if "边框" in 样式规则:
        样式字符串 += f"border: {样式规则['边框']};"
    if "圆角" in 样式规则:
        样式字符串 += f"border-radius: {样式规则['圆角']};"
    if "内边距" in 样式规则:
        样式字符串 += f"padding: {样式规则['内边距']};"
    if "外边距" in 样式规则:
        样式字符串 += f"margin: {样式规则['外边距']};"
    if "最小宽度" in 样式规则:
        样式字符串 += f"min-width: {样式规则['最小宽度']};"
    if "最小高度" in 样式规则:
        样式字符串 += f"min-height: {样式规则['最小高度']};"
    if "最大宽度" in 样式规则:
        样式字符串 += f"max-width: {样式规则['最大宽度']};"
    if "最大高度" in 样式规则:
        样式字符串 += f"max-height: {样式规则['最大高度']};"
    控件.setStyleSheet(样式字符串)


# --- 控件创建 ---

def 添加标签到布局(布局, 文字="", 对齐方式="居中"):
    """添加一个标签到布局"""
    标签 = QLabel(文字)
    if 对齐方式 == "居中":
        标签.setAlignment(Qt.AlignCenter)
    elif 对齐方式 == "左对齐":
        标签.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    elif 对齐方式 == "右对齐":
        标签.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    布局.addWidget(标签)
    return 标签


def 添加按钮到布局(布局, 文字="点击我", 点击时执行=None, 样式=None):
    """添加一个按钮到布局"""
    按钮 = QPushButton(文字)
    if 点击时执行:
        按钮.clicked.connect(点击时执行)
    if 样式:
        使控件具有样式(按钮, 样式)
    布局.addWidget(按钮)
    return 按钮


def 添加输入框到布局(布局, 提示文字="", 样式=None):
    """添加一个单行输入框到布局"""
    输入框 = QLineEdit()
    if 提示文字:
        输入框.setPlaceholderText(提示文字)
    if 样式:
        使控件具有样式(输入框, 样式)
    布局.addWidget(输入框)
    return 输入框


def 添加文本框到布局(布局, 提示文字="", 只读=False, 样式=None):
    """添加一个多行文本框到布局"""
    文本框 = QTextEdit()
    if 提示文字:
        文本框.setPlaceholderText(提示文字)
    if 只读:
        文本框.setReadOnly(True)
    if 样式:
        使控件具有样式(文本框, 样式)
    布局.addWidget(文本框)
    return 文本框


def 添加列表框到布局(布局, 样式=None):
    """添加一个列表框到布局"""
    列表框 = QListWidget()
    if 样式:
        使控件具有样式(列表框, 样式)
    布局.addWidget(列表框)
    return 列表框


def 添加复选框到布局(布局, 文字="", 初始状态=False, 样式=None):
    """添加一个复选框到布局"""
    复选框 = QCheckBox(文字)
    复选框.setChecked(初始状态)
    if 样式:
        使控件具有样式(复选框, 样式)
    布局.addWidget(复选框)
    return 复选框


# --- 布局管理 ---

def 在布局中添加弹性空间(布局, 方向="垂直"):
    """在布局中添加弹性空间"""
    if 方向 == "垂直":
        布局.addStretch()
    elif 方向 == "水平" and isinstance(布局, QHBoxLayout):
        布局.addStretch()


def 在布局中添加间距(布局, 大小=10):
    """在布局中添加固定间距"""
    布局.addSpacing(大小)


# --- 对话框 ---

def 显示信息(父窗口, 标题, 内容):
    """显示信息对话框"""
    QMessageBox.information(父窗口, 标题, 内容)


def 显示警告(父窗口, 标题, 内容):
    """显示警告对话框"""
    QMessageBox.warning(父窗口, 标题, 内容)


def 显示错误(父窗口, 标题, 内容):
    """显示错误对话框"""
    QMessageBox.critical(父窗口, 标题, 内容)


def 询问是或否(父窗口, 标题, 问题):
    """显示是/否确认对话框"""
    回复 = QMessageBox.question(父窗口, 标题, 问题, QMessageBox.Yes | QMessageBox.No)
    return 回复 == QMessageBox.Yes


# --- 高级控件和效果 ---

def 添加带阴影的框架到布局(布局, 背景颜色="#FFFFFF", 圆角=10, 阴影模糊=15, 阴影偏移Y=5):
    """添加一个带阴影效果的框架"""
    框架 = QFrame()
    框架.setStyleSheet(f"QFrame {{ background-color: {背景颜色}; border-radius: {圆角}px; }}")

    阴影 = QGraphicsDropShadowEffect()
    阴影.setBlurRadius(阴影模糊)
    阴影.setXOffset(0)
    阴影.setYOffset(阴影偏移Y)
    阴影.setColor(QColor(0, 0, 0, 50))
    框架.setGraphicsEffect(阴影)

    框架布局 = QVBoxLayout(框架)
    框架布局.setContentsMargins(20, 20, 20, 20)
    布局.addWidget(框架)
    return 框架, 框架布局


# --- 列表操作 ---

def 向列表添加可勾选项目(列表框, 文字, 已完成=False):
    """向列表添加一个可勾选的项目"""
    项目 = QListWidgetItem(文字)
    项目.setCheckState(Qt.Checked if 已完成 else Qt.Unchecked)
    列表框.addItem(项目)
    return 项目


def 切换列表项目状态(项目):
    """切换列表项目的勾选状态"""
    项目.setCheckState(Qt.Unchecked if 项目.checkState() == Qt.Checked else Qt.Checked)


# --- 实用工具函数 ---

def 简单居中窗口(窗口):
    """一个简单的窗口居中函数"""
    桌面 = QApplication.primaryScreen().availableGeometry()
    窗口大小 = 窗口.frameGeometry()
    中心点 = 桌面.center()
    窗口.move(中心点 - QPoint(窗口大小.width() // 2, 窗口大小.height() // 2))


def 启动应用程序_说明性(创建界面函数):
    """
    启动 Qt 应用程序的辅助函数。
    自动处理应用程序实例的创建。
    """
    # 确保有 QApplication 实例
    应用实例 = QApplication.instance()
    if 应用实例 is None:
        try:
            import sys
            应用 = QApplication(sys.argv)
        except:
            应用 = QApplication([])
    else:
        应用 = 应用实例

    窗口 = 创建界面函数()
    窗口.show()

    # 返回应用实例以便进一步使用
    return 应用.exec()


# --- 上下文管理器支持 ---

class _布局上下文:
    def __init__(self, 布局):
        self.布局 = 布局
        self.当前布局 = 布局

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def 垂直布局(self, 内边距=20, 间距=15):
        """进入垂直布局上下文"""
        容器 = QWidget()
        容器.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        布局管理器 = QVBoxLayout(容器)
        布局管理器.setContentsMargins(内边距, 内边距, 内边距, 内边距)
        布局管理器.setSpacing(间距)
        self.当前布局.addWidget(容器)
        return _布局上下文(布局管理器)

    def 水平布局(self, 内边距=20, 间距=15):
        """进入水平布局上下文"""
        容器 = QWidget()
        容器.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        布局管理器 = QHBoxLayout(容器)
        布局管理器.setContentsMargins(内边距, 内边距, 内边距, 内边距)
        布局管理器.setSpacing(间距)
        self.当前布局.addWidget(容器)
        return _布局上下文(布局管理器)

    def 标签(self, 文字="", 对齐方式="居中", **样式):
        标签控件 = 添加标签到布局(self.当前布局, 文字, 对齐方式)
        if 样式:
            使控件具有样式(标签控件, 样式)
        return 标签控件

    def 按钮(self, 文字="点击我", 点击时执行=None, **样式):
        按钮控件 = 添加按钮到布局(self.当前布局, 文字, 点击时执行)
        if 样式:
            使控件具有样式(按钮控件, 样式)
        return 按钮控件

    def 输入框(self, 提示文字="", **样式):
        输入框控件 = 添加输入框到布局(self.当前布局, 提示文字)
        if 样式:
            使控件具有样式(输入框控件, 样式)
        return 输入框控件

    def 文本框(self, 提示文字="", 只读=False, **样式):
        文本框控件 = 添加文本框到布局(self.当前布局, 提示文字, 只读)
        if 样式:
            使控件具有样式(文本框控件, 样式)
        return 文本框控件

    def 列表框(self, **样式):
        列表框控件 = 添加列表框到布局(self.当前布局)
        if 样式:
            使控件具有样式(列表框控件, 样式)
        return 列表框控件

    def 复选框(self, 文字="", 初始状态=False, **样式):
        复选框控件 = 添加复选框到布局(self.当前布局, 文字, 初始状态)
        if 样式:
            使控件具有样式(复选框控件, 样式)
        return 复选框控件

    def 阴影框(self, 背景颜色="#FFFFFF", 圆角=10, 阴影模糊=15, 阴影偏移Y=5):
        框架, 框架布局 = 添加带阴影的框架到布局(self.当前布局, 背景颜色, 圆角, 阴影模糊, 阴影偏移Y)
        return _布局上下文(框架布局)

    def 弹性空间(self, 方向="垂直"):
        if 方向 == "垂直":
            self.当前布局.addStretch()
        elif 方向 == "水平" and isinstance(self.当前布局, QHBoxLayout):
            self.当前布局.addStretch()

    def 间距(self, 大小=10):
        self.当前布局.addSpacing(大小)

    def 添加项目(self, 文字, 已完成=False):
        """向列表添加可勾选项目"""
        return 向列表添加可勾选项目(self.当前布局, 文字, 已完成)


def 创建窗口上下文(标题="我的应用", 宽度=600, 高度=400):
    """创建窗口并返回上下文管理器"""
    窗口 = 创建主窗口(标题, 宽度, 高度)
    中央区域, 布局 = 为窗口设置中央区域和布局(窗口)
    return 窗口, _布局上下文(布局)


def 启动应用程序(创建界面函数=None, 命令行参数=None):
    """
    启动 Qt 应用程序的高级函数。
    支持多种使用方式。
    """
    # 获取或创建 QApplication 实例
    应用实例 = QApplication.instance()
    if 应用实例 is None:
        if 命令行参数 is None:
            try:
                import sys
                应用 = QApplication(sys.argv)
            except:
                应用 = QApplication([])
        else:
            应用 = QApplication(命令行参数 or [])
    else:
        应用 = 应用实例

    # 如果提供了创建界面函数，创建并显示窗口
    if 创建界面函数:
        窗口 = 创建界面函数()
        if 窗口:
            窗口.show()

    return 应用


def 运行应用程序(创建界面函数=None):
    """
    运行应用程序并进入主循环 - 修复版
    """
    import sys
    from PySide6.QtWidgets import QApplication

    # 获取或创建 QApplication 实例
    应用实例 = QApplication.instance()
    if 应用实例 is None:
        try:
            应用 = QApplication(sys.argv)
        except:
            应用 = QApplication([])
    else:
        应用 = 应用实例

    # 如果提供了创建界面函数，创建并显示窗口
    窗口 = None
    if 创建界面函数:
        try:
            窗口 = 创建界面函数()
            if 窗口:
                # 确保窗口显示
                窗口.show()
                # 立即处理事件，确保窗口显示
                QApplication.processEvents()
                print(f"✅ 窗口已显示，可见: {窗口.isVisible()}")
        except Exception as e:
            print(f"❌ 创建界面失败: {e}")
            import traceback
            traceback.print_exc()

    # 进入主事件循环
    if 应用:
        print("✅ 进入主事件循环...")
        return 应用.exec()
    else:
        print("❌ 没有可用的QApplication实例")
        return 1


# --- 导出列表 ---
__all__ = [
    # 基础函数
    '创建主窗口', '为窗口设置中央区域和布局', '为控件设置布局',
    '应用全局样式', '使控件具有样式',

    # 控件创建
    '添加标签到布局', '添加按钮到布局', '添加输入框到布局',
    '添加文本框到布局', '添加列表框到布局', '添加复选框到布局',

    # 布局管理
    '在布局中添加弹性空间', '在布局中添加间距',

    # 对话框
    '显示信息', '显示警告', '显示错误', '询问是或否',

    # 高级效果
    '添加带阴影的框架到布局',

    # 列表操作
    '向列表添加可勾选项目', '切换列表项目状态',

    # 工具函数
    '简单居中窗口', '启动应用程序_说明性',

    # 上下文管理器
    '创建窗口上下文', '_布局上下文',

    # 新增的样式和组件功能
    '获取主题', '获取样式', '应用主题',
    '高级按钮', '创建按钮',
    '卡片', '创建卡片'
]

# 确保所有导出名称都存在
# 如果某些模块没有导入，需要添加导入语句
try:
    from 样式.主题 import 获取主题, 获取样式, 应用主题
    from 组件.高级按钮 import 高级按钮, 创建按钮
    from 组件.卡片 import 卡片, 创建卡片
except ImportError:
    # 如果子模块还不存在，先定义为None
    获取主题 = 获取样式 = 应用主题 = None
    高级按钮 = 创建按钮 = None
    卡片 = 创建卡片 = None
    print("警告：样式和组件模块尚未完全实现")