"""
卡片组件 - 现代化的卡片容器
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class 卡片(QFrame):
    """现代化卡片组件"""

    def __init__(self, 标题=None, 样式="card", 主题="light"):
        super().__init__()

        from ..样式.主题 import 获取样式
        样式规则 = 获取样式(样式, 主题)

        # 应用样式
        self.应用样式(样式规则)

        # 设置布局
        self.布局 = QVBoxLayout(self)
        self.布局.setContentsMargins(20, 20, 20, 20)
        self.布局.setSpacing(12)

        # 添加标题
        if 标题:
            self.标题标签 = QLabel(标题)
            self.标题标签.setStyleSheet("font-size: 18px; font-weight: bold;")
            self.布局.addWidget(self.标题标签)

    def 应用样式(self, 样式规则):
        """应用样式到卡片"""
        样式字符串 = ""
        for 键, 值 in 样式规则.items():
            if 键 == "阴影":
                # 阴影效果需要特殊处理
                continue
            样式字符串 += f"{键.replace('_', '-')}: {值};"

        self.setStyleSheet(样式字符串)

        # 应用阴影效果
        if "阴影" in 样式规则:
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            from PySide6.QtGui import QColor

            阴影 = QGraphicsDropShadowEffect()
            阴影.setBlurRadius(15)
            阴影.setXOffset(0)
            阴影.setYOffset(4)
            阴影.setColor(QColor(0, 0, 0, 30))
            self.setGraphicsEffect(阴影)

    def 添加控件(self, 控件):
        """添加控件到卡片"""
        self.布局.addWidget(控件)

    def 添加间距(self, 大小=10):
        """添加间距"""
        self.布局.addSpacing(大小)

    def 添加弹性空间(self):
        """添加弹性空间"""
        self.布局.addStretch()


def 创建卡片(标题=None, 主题="light"):
    """快速创建卡片"""
    return 卡片(标题, "card", 主题)