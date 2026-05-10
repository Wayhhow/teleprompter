# -*- coding: utf-8 -*-
"""全局配置常量"""

# ===== 界面配置 =====
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
WINDOW_TITLE = "自动提词器"

# 字体配置
DEFAULT_FONT_SIZE = 24  # 默认字号(pt)
MIN_FONT_SIZE = 16
MAX_FONT_SIZE = 48
FONT_FAMILY = "Microsoft YaHei"  # 微软雅黑

# ===== 提词器显示配置 =====
CONTEXT_SENTENCES = 3  # 前后各显示的上下文句子数
HIGHLIGHT_BG_COLOR = (255, 255, 100, 120)  # 当前句子高亮背景 (RGBA)
CONTEXT_FADE_STEP = 30  # 上下文每层淡化步进(alpha)
SCROLL_ANIMATION_DURATION = 800  # 滚动动画时长(ms)
SCROLL_POSITION_RATIO = 0.3  # 当前句子在视口中的位置比例

# ===== 自动播放配置 =====
BASE_STAY_MS = 3000  # 基础每句停留时间(ms)
MIN_SPEED = 0.5  # 最小速度倍率
MAX_SPEED = 5.0  # 最大速度倍率
SPEED_STEP = 0.1  # 速度调节步进
DEFAULT_SPEED = 1.0  # 默认速度倍率
CHAR_TIME_CN = 100  # 中文字符额外时间(ms)
CHAR_TIME_EN = 50  # 英文字符额外时间(ms)

# ===== 语音识别配置 =====
SAMPLE_RATE = 16000  # 音频采样率
BLOCK_SIZE = 8000  # 音频块大小
MATCH_THRESHOLD = 0.6  # 匹配阈值
SEARCH_FORWARD = 5  # 向前搜索句子数
MODEL_DIR = "models"  # 模型目录

# ===== 深色主题样式表 =====
DARK_STYLE = """
QMainWindow {
    background-color: #1e1e1e;
}
QTextEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: none;
    padding: 20px;
    selection-background-color: #264f78;
}
QPushButton {
    background-color: #3d3d3d;
    color: #ffffff;
    padding: 8px 16px;
    border-radius: 4px;
    border: 1px solid #555;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #4d4d4d;
    border: 1px solid #666;
}
QPushButton:pressed {
    background-color: #2d2d2d;
}
QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666;
    border: 1px solid #333;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #555;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #0078d4;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #1a8ae8;
}
QSlider::sub-page:horizontal {
    background: #0078d4;
    border-radius: 3px;
}
QLabel {
    color: #cccccc;
    font-size: 13px;
}
QGroupBox {
    color: #cccccc;
    border: 1px solid #444;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QMenuBar {
    background-color: #2d2d2d;
    color: #cccccc;
    border-bottom: 1px solid #444;
}
QMenuBar::item:selected {
    background-color: #3d3d3d;
}
QMenu {
    background-color: #2d2d2d;
    color: #cccccc;
    border: 1px solid #444;
}
QMenu::item:selected {
    background-color: #0078d4;
}
QStatusBar {
    background-color: #252525;
    color: #999;
}
QLineEdit {
    background-color: #3d3d3d;
    color: #e0e0e0;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
