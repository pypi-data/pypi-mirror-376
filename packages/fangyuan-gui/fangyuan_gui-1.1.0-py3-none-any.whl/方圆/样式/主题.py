"""
主题样式 - 提供现代化的UI主题和样式预设
"""

# 现代化主题配色
主题配色 = {
    "light": {
        "primary": "#007AFF",
        "secondary": "#5856D6",
        "success": "#34C759",
        "warning": "#FF9500",
        "danger": "#FF3B30",
        "background": "#F2F2F7",
        "card": "#FFFFFF",
        "text": "#000000",
        "text_secondary": "#8E8E93",
        "border": "#C6C6C8"
    },
    "dark": {
        "primary": "#0A84FF",
        "secondary": "#5E5CE6",
        "success": "#30D158",
        "warning": "#FF9F0A",
        "danger": "#FF453A",
        "background": "#000000",
        "card": "#1C1C1E",
        "text": "#FFFFFF",
        "text_secondary": "#8E8E93",
        "border": "#38383A"
    },
    "material": {
        "primary": "#6200EE",
        "secondary": "#03DAC6",
        "success": "#018786",
        "warning": "#FFC107",
        "danger": "#B00020",
        "background": "#FAFAFA",
        "card": "#FFFFFF",
        "text": "#212121",
        "text_secondary": "#757575",
        "border": "#E0E0E0"
    }
}

# 预设样式
预设样式 = {
    # 按钮样式
    "primary_button": {
        "背景颜色": "{primary}",
        "文字颜色": "white",
        "圆角": "8px",
        "内边距": "10px 20px",
        "字体粗细": "bold",
        "边框": "none",
        "最小宽度": "80px"
    },
    "secondary_button": {
        "背景颜色": "{secondary}",
        "文字颜色": "white",
        "圆角": "8px",
        "内边距": "10px 20px",
        "边框": "none"
    },
    "outline_button": {
        "背景颜色": "transparent",
        "文字颜色": "{primary}",
        "圆角": "8px",
        "内边距": "8px 18px",
        "边框": "2px solid {primary}"
    },

    # 输入框样式
    "modern_input": {
        "背景颜色": "white",
        "文字颜色": "#333",
        "圆角": "8px",
        "内边距": "12px",
        "边框": "1px solid {border}",
        "字体大小": "14px"
    },

    # 卡片样式
    "card": {
        "背景颜色": "{card}",
        "圆角": "12px",
        "内边距": "20px",
        "边框": "none",
        "阴影": "0 4px 12px rgba(0,0,0,0.1)"
    },

    # 标签样式
    "title": {
        "字体大小": "24px",
        "字体粗细": "bold",
        "文字颜色": "{text}",
        "外边距": "0 0 16px 0"
    },
    "subtitle": {
        "字体大小": "18px",
        "字体粗细": "600",
        "文字颜色": "{text_secondary}",
        "外边距": "0 0 12px 0"
    }
}


def 获取主题(主题名称="light"):
    """获取指定主题的配色"""
    return 主题配色.get(主题名称, 主题配色["light"])


def 获取样式(样式名称, 主题名称="light"):
    """获取带有主题颜色的样式"""
    主题 = 获取主题(主题名称)
    样式 = 预设样式.get(样式名称, {}).copy()

    # 替换颜色变量
    for 键, 值 in 样式.items():
        if isinstance(值, str) and 值.startswith("{") and 值.endswith("}"):
            颜色键 = 值[1:-1]
            样式[键] = 主题.get(颜色键, 值)

    return 样式


def 应用主题(窗口, 主题名称="light"):
    """应用完整主题到窗口"""
    主题 = 获取主题(主题名称)

    样式表 = f"""
        QMainWindow {{
            background-color: {主题['background']};
            font-family: "微软雅黑", "PingFang SC", "Hiragino Sans GB";
            font-size: 14px;
        }}
        QWidget {{
            color: {主题['text']};
        }}
        QPushButton {{
            background-color: {主题['primary']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {主题['primary']}DD;
        }}
        QPushButton:pressed {{
            background-color: {主题['primary']}AA;
        }}
        QLineEdit, QTextEdit {{
            background-color: white;
            border: 1px solid {主题['border']};
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
        }}
        QListWidget {{
            background-color: white;
            border: 1px solid {主题['border']};
            border-radius: 8px;
            padding: 8px;
        }}
        QListWidget::item {{
            padding: 10px;
            border-bottom: 1px solid {主题['border']};
        }}
        QListWidget::item:selected {{
            background-color: {主题['primary']}20;
        }}
    """

    窗口.setStyleSheet(样式表)
    return 主题