# -*- coding: utf-8 -*-
"""控制面板 - 播放控制、速度、字号、语音识别控制"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QFileDialog, QLineEdit, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal

from config import (
    DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE,
    MIN_SPEED, MAX_SPEED, SPEED_STEP, DEFAULT_SPEED
)


class ControlPanel(QWidget):
    """提词器控制面板"""

    # 信号定义
    openFileRequested = pyqtSignal()       # 请求打开文件
    playToggled = pyqtSignal(bool)         # 播放/暂停切换 (True=播放)
    prevSentenceRequested = pyqtSignal()   # 上一句
    nextSentenceRequested = pyqtSignal()   # 下一句
    resetRequested = pyqtSignal()          # 重置
    speedChanged = pyqtSignal(float)       # 速度改变
    fontSizeChanged = pyqtSignal(int)      # 字号改变
    voiceToggled = pyqtSignal(bool)        # 语音识别开关 (True=开始)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self._is_voice_active = False
        self._setup_ui()

    def _setup_ui(self):
        """构建控制面板UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        # ===== 第一行：文件操作 + 播放控制 =====
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.btn_open = QPushButton("📂 打开文件")
        self.btn_open.clicked.connect(self.openFileRequested.emit)
        row1.addWidget(self.btn_open)

        # 分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setStyleSheet("color: #555;")
        row1.addWidget(separator1)

        self.btn_prev = QPushButton("◀ 上一句")
        self.btn_prev.clicked.connect(self.prevSentenceRequested.emit)
        row1.addWidget(self.btn_prev)

        self.btn_play = QPushButton("▶ 播放")
        self.btn_play.clicked.connect(self._toggle_play)
        row1.addWidget(self.btn_play)

        self.btn_next = QPushButton("下一句 ▶")
        self.btn_next.clicked.connect(self.nextSentenceRequested.emit)
        row1.addWidget(self.btn_next)

        self.btn_reset = QPushButton("⟲ 重置")
        self.btn_reset.clicked.connect(self.resetRequested.emit)
        row1.addWidget(self.btn_reset)

        row1.addStretch()
        layout.addLayout(row1)

        # ===== 第二行：速度控制 =====
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        speed_label = QLabel("速度:")
        speed_label.setFixedWidth(40)
        row2.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(int(MIN_SPEED * 10))
        self.speed_slider.setMaximum(int(MAX_SPEED * 10))
        self.speed_slider.setValue(int(DEFAULT_SPEED * 10))
        self.speed_slider.setSingleStep(int(SPEED_STEP * 10))
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        row2.addWidget(self.speed_slider)

        self.speed_value_label = QLabel(f"{DEFAULT_SPEED:.1f}x")
        self.speed_value_label.setFixedWidth(40)
        self.speed_value_label.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.speed_value_label)

        layout.addLayout(row2)

        # ===== 第三行：字号控制 =====
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        font_label = QLabel("字号:")
        font_label.setFixedWidth(40)
        row3.addWidget(font_label)

        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setMinimum(MIN_FONT_SIZE)
        self.font_slider.setMaximum(MAX_FONT_SIZE)
        self.font_slider.setValue(DEFAULT_FONT_SIZE)
        self.font_slider.setSingleStep(1)
        self.font_slider.setTickPosition(QSlider.TicksBelow)
        self.font_slider.setTickInterval(4)
        self.font_slider.valueChanged.connect(self._on_font_changed)
        row3.addWidget(self.font_slider)

        self.font_value_label = QLabel(f"{DEFAULT_FONT_SIZE}pt")
        self.font_value_label.setFixedWidth(45)
        self.font_value_label.setAlignment(Qt.AlignCenter)
        row3.addWidget(self.font_value_label)

        layout.addLayout(row3)

        # ===== 第四行：语音识别控制 =====
        row4 = QHBoxLayout()
        row4.setSpacing(8)

        self.btn_voice = QPushButton("🎤 开始语音识别")
        self.btn_voice.clicked.connect(self._toggle_voice)
        row4.addWidget(self.btn_voice)

        # 状态指示灯
        self.voice_status_label = QLabel("● 未启动")
        self.voice_status_label.setStyleSheet("color: #888; font-weight: bold;")
        row4.addWidget(self.voice_status_label)

        # 识别文本显示
        recog_label = QLabel("识别:")
        recog_label.setFixedWidth(35)
        row4.addWidget(recog_label)

        self.recog_text = QLineEdit()
        self.recog_text.setReadOnly(True)
        self.recog_text.setPlaceholderText("等待语音输入...")
        row4.addWidget(self.recog_text)

        layout.addLayout(row4)

    def _toggle_play(self):
        """切换播放/暂停状态"""
        self._is_playing = not self._is_playing
        if self._is_playing:
            self.btn_play.setText("⏸ 暂停")
        else:
            self.btn_play.setText("▶ 播放")
        self.playToggled.emit(self._is_playing)

    def _toggle_voice(self):
        """切换语音识别状态"""
        self._is_voice_active = not self._is_voice_active
        if self._is_voice_active:
            self.btn_voice.setText("🎤 停止语音识别")
            self.voice_status_label.setText("● 正在识别")
            self.voice_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.recog_text.setPlaceholderText("正在聆听...")
        else:
            self.btn_voice.setText("🎤 开始语音识别")
            self.voice_status_label.setText("● 未启动")
            self.voice_status_label.setStyleSheet("color: #888; font-weight: bold;")
            self.recog_text.setPlaceholderText("等待语音输入...")
            self.recog_text.clear()
        self.voiceToggled.emit(self._is_voice_active)

    def _on_speed_changed(self, value: int):
        """速度滑块变化"""
        multiplier = value / 10.0
        self.speed_value_label.setText(f"{multiplier:.1f}x")
        self.speedChanged.emit(multiplier)

    def _on_font_changed(self, value: int):
        """字号滑块变化"""
        self.font_value_label.setText(f"{value}pt")
        self.fontSizeChanged.emit(value)

    def update_recognized_text(self, text: str):
        """更新识别文本显示"""
        self.recog_text.setText(text)

    def set_playing(self, is_playing: bool):
        """外部设置播放状态"""
        self._is_playing = is_playing
        if is_playing:
            self.btn_play.setText("⏸ 暂停")
        else:
            self.btn_play.setText("▶ 播放")

    def set_voice_active(self, is_active: bool):
        """外部设置语音识别状态"""
        self._is_voice_active = is_active
        if is_active:
            self.btn_voice.setText("🎤 停止语音识别")
            self.voice_status_label.setText("● 正在识别")
            self.voice_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.recog_text.setPlaceholderText("正在聆听...")
        else:
            self.btn_voice.setText("🎤 开始语音识别")
            self.voice_status_label.setText("● 未启动")
            self.voice_status_label.setStyleSheet("color: #888; font-weight: bold;")
            self.recog_text.setPlaceholderText("等待语音输入...")
            self.recog_text.clear()

    def get_speed(self) -> float:
        """获取当前速度倍率"""
        return self.speed_slider.value() / 10.0
