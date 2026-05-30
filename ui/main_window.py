# -*- coding: utf-8 -*-
"""主窗口 - 组装所有组件"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFileDialog,
    QMessageBox, QAction, QStatusBar, QLabel
)
from PyQt5.QtCore import Qt

from config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, DARK_STYLE
from ui.teleprompter_view import TeleprompterView
from ui.control_panel import ControlPanel
from core.text_parser import read_text_file, split_sentences
from core.auto_player import AutoPlayer
from core.voice_tracker import VoiceTracker


class MainWindow(QMainWindow):
    """提词器主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_file = ""
        self._text = ""
        self._sentences = []

        self._setup_ui()
        self._setup_menu()
        self._setup_connections()
        self._setup_statusbar()

    def _setup_ui(self):
        """构建UI布局"""
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 提词器视图
        self.view = TeleprompterView()
        layout.addWidget(self.view, stretch=1)

        # 控制面板
        self.control = ControlPanel()
        layout.addWidget(self.control)

        # 自动播放器
        self.player = AutoPlayer(self)

        # 语音跟踪器
        self.voice = VoiceTracker(self)

    def _setup_menu(self):
        """构建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        open_action = QAction("打开文件", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 播放菜单
        play_menu = menubar.addMenu("播放")

        play_action = QAction("播放/暂停", self)
        play_action.setShortcut("Space")
        play_action.triggered.connect(self._toggle_play)
        play_menu.addAction(play_action)

        prev_action = QAction("上一句", self)
        prev_action.setShortcut("Left")
        prev_action.triggered.connect(self._prev_sentence)
        play_menu.addAction(prev_action)

        next_action = QAction("下一句", self)
        next_action.setShortcut("Right")
        next_action.triggered.connect(self._next_sentence)
        play_menu.addAction(next_action)

        reset_action = QAction("重置", self)
        reset_action.setShortcut("Home")
        reset_action.triggered.connect(self._reset)
        play_menu.addAction(reset_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_connections(self):
        """连接信号与槽"""
        # 控制面板信号
        self.control.openFileRequested.connect(self._open_file)
        self.control.playToggled.connect(self._on_play_toggled)
        self.control.prevSentenceRequested.connect(self._prev_sentence)
        self.control.nextSentenceRequested.connect(self._next_sentence)
        self.control.resetRequested.connect(self._reset)
        self.control.speedChanged.connect(self.player.set_speed)
        self.control.fontSizeChanged.connect(self.view.set_font_size)
        self.control.voiceToggled.connect(self._on_voice_toggled)
        self.control.alwaysOnTopToggled.connect(self._on_always_on_top_toggled)

        # 自动播放器信号
        self.player.sentenceChanged.connect(self._on_player_sentence_changed)
        self.player.playbackFinished.connect(self._on_playback_finished)

        # 语音跟踪器信号
        self.voice.sentenceMatched.connect(self._on_voice_sentence_matched)
        self.voice.recognizedTextUpdated.connect(self.control.update_recognized_text)
        self.voice.errorOccurred.connect(self._on_voice_error)

    def _setup_statusbar(self):
        """构建状态栏"""
        self.statusBar().showMessage("就绪")

    def _open_file(self):
        """打开文件对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开稿件",
            "",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                self._load_file(file_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")

    def _load_file(self, file_path: str):
        """加载文件"""
        text = read_text_file(file_path)
        sentences = split_sentences(text)

        if not sentences:
            QMessageBox.warning(self, "警告", "文件内容为空或无法分割为句子。")
            return

        self._current_file = file_path
        self._text = text
        self._sentences = sentences

        # 更新视图
        self.view.load_text(text, sentences)

        # 更新自动播放器
        self.player.load_sentences(sentences)

        # 更新语音跟踪器
        self.voice.load_sentences(sentences, current_index=0)

        # 停止当前播放
        self.player.stop()
        self.control.set_playing(False)

        # 停止语音识别
        if self.voice.is_running():
            self.voice.stop()
            self.control.set_voice_active(False)

        # 更新状态栏
        self.statusBar().showMessage(
            f"已加载: {file_path} | 共 {len(sentences)} 句"
        )

    def _toggle_play(self):
        """切换播放/暂停"""
        if not self._sentences:
            QMessageBox.information(self, "提示", "请先打开一个稿件文件。")
            return

        if self.player.is_running():
            self.player.pause()
            self.control.set_playing(False)
        else:
            self.player.start()
            self.control.set_playing(True)

    def _on_play_toggled(self, is_playing: bool):
        """播放状态切换回调"""
        if not self._sentences:
            QMessageBox.information(self, "提示", "请先打开一个稿件文件。")
            self.control.set_playing(False)
            return

        if is_playing:
            self.player.start()
            self.statusBar().showMessage("自动播放中...")
        else:
            self.player.pause()
            self.statusBar().showMessage("已暂停")

    def _prev_sentence(self):
        """上一句"""
        if not self._sentences:
            return
        current = self.view.get_current_index()
        if current > 0:
            new_index = current - 1
            self.view.set_current_index(new_index)
            self.player.set_current_index(new_index)
            self.voice.set_current_index(new_index)
            self._update_status_sentence(new_index)

    def _next_sentence(self):
        """下一句"""
        if not self._sentences:
            return
        current = self.view.get_current_index()
        if current < len(self._sentences) - 1:
            new_index = current + 1
            self.view.set_current_index(new_index)
            self.player.set_current_index(new_index)
            self.voice.set_current_index(new_index)
            self._update_status_sentence(new_index)

    def _reset(self):
        """重置到第一句"""
        if not self._sentences:
            return
        self.player.reset()
        self.view.set_current_index(0, animated=False)
        self.voice.set_current_index(0)
        self.control.set_playing(False)
        self._update_status_sentence(0)
        self.statusBar().showMessage("已重置")

    def _on_player_sentence_changed(self, index: int):
        """自动播放器切换句子回调"""
        self.view.set_current_index(index)
        self.voice.set_current_index(index)
        self._update_status_sentence(index)

    def _on_playback_finished(self):
        """播放结束回调"""
        self.control.set_playing(False)
        self.statusBar().showMessage("播放结束")

    def _on_voice_toggled(self, is_active: bool):
        """语音识别开关回调"""
        if is_active:
            if not self._sentences:
                QMessageBox.information(self, "提示", "请先打开一个稿件文件。")
                self.control.set_voice_active(False)
                return

            # 初始化语音识别器
            self.voice.set_current_index(self.view.get_current_index())
            self.voice.start()
            self.statusBar().showMessage("语音识别已启动，请开始朗读...")
        else:
            self.voice.stop()
            self.statusBar().showMessage("语音识别已停止")

    def _on_voice_sentence_matched(self, index: int):
        """语音匹配到句子回调"""
        self.view.set_current_index(index)
        self.player.set_current_index(index)
        self._update_status_sentence(index)
        self.statusBar().showMessage(f"语音匹配: 第 {index + 1}/{len(self._sentences)} 句")

    def _on_voice_error(self, error_msg: str):
        """语音识别错误回调"""
        QMessageBox.critical(self, "语音识别错误", error_msg)
        self.control.set_voice_active(False)

    def _on_always_on_top_toggled(self, is_on: bool):
        """窗口置顶切换回调"""
        if is_on:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.statusBar().showMessage("窗口已置顶")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.statusBar().showMessage("已取消置顶")
        # 重新显示窗口（修改窗口标志后需要）
        self.show()

    def _update_status_sentence(self, index: int):
        """更新状态栏句子信息"""
        if self._sentences and 0 <= index < len(self._sentences):
            sentence_text = self._sentences[index][2]
            # 截断过长的句子
            display_text = sentence_text[:30] + "..." if len(sentence_text) > 30 else sentence_text
            self.statusBar().showMessage(
                f"第 {index + 1}/{len(self._sentences)} 句 | {display_text}"
            )

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于自动提词器",
            "<h3>自动提词器 v1.0</h3>"
            "<p>一个支持自动播放和语音跟读的桌面提词器。</p>"
            "<p><b>功能特性：</b></p>"
            "<ul>"
            "<li>加载 TXT 稿件，按句高亮显示</li>"
            "<li>可调节速度的自动播放模式</li>"
            "<li>离线语音识别，自动匹配朗读位置</li>"
            "<li>支持中英文混合朗读</li>"
            "<li>可调节字体大小</li>"
            "</ul>"
            "<p>技术栈：Python + PyQt5 + sherpa-onnx</p>"
        )

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止语音识别
        if self.voice.is_running():
            self.voice.stop()
        # 停止自动播放
        self.player.stop()
        event.accept()
