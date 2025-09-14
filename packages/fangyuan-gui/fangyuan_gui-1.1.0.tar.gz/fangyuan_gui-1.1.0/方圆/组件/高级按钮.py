"""
高级按钮组件 - 提供丰富的按钮样式和功能
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize


class 高级按钮(QPushButton):
    """增强的按钮组件，支持图标、加载状态等"""

    def __init__(self, 文字="", 图标路径=None, 样式名称="primary_button", 主题="light"):
        super().__init__(文字)

        from ..样式.主题 import 获取样式
        样式 = 获取样式(样式名称, 主题)

        # 设置图标
        if 图标路径:
            self.setIcon(QIcon(图标路径))
            self.setIconSize(QSize(16, 16))

        # 应用样式
        self.应用样式(样式)

        # 添加点击动画效果
        self.pressed.connect(self._按下效果)
        self.released.connect(self._释放效果)

    def 应用样式(self, 样式规则):
        """应用样式到按钮"""
        样式字符串 = ""
        for 键, 值 in 样式规则.items():
            样式字符串 += f"{键.replace('_', '-')}: {值};"
        self.setStyleSheet(样式字符串)

    def _按下效果(self):
        """按下时的动画效果"""
        self.setStyleSheet(self.styleSheet() + "opacity: 0.8;")

    def _释放效果(self):
        """释放时的动画效果"""
        self.setStyleSheet(self.styleSheet().replace("opacity: 0.8;", ""))

    def 设置加载状态(self, 加载中=True, 加载文字="加载中..."):
        """设置加载状态"""
        if 加载中:
            self.原始文字 = self.text()
            self.setText(加载文字)
            self.setEnabled(False)
        else:
            self.setText(getattr(self, '原始文字', self.text()))
            self.setEnabled(True)

    def 设置图标(self, 图标路径, 大小=16):
        """设置按钮图标"""
        self.setIcon(QIcon(图标路径))
        self.setIconSize(QSize(大小, 大小))


def 创建按钮(文字="", 图标=None, 样式="primary", 主题="light", 点击事件=None):
    """快速创建按钮"""
    样式映射 = {
        "primary": "primary_button",
        "secondary": "secondary_button",
        "outline": "outline_button"
    }

    按钮 = 高级按钮(文字, 图标, 样式映射.get(样式, "primary_button"), 主题)
    if 点击事件:
        按钮.clicked.connect(点击事件)

    return 按钮