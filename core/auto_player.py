# -*- coding: utf-8 -*-
"""自动播放控制器 - 按句定时推进"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from config import BASE_STAY_MS, DEFAULT_SPEED
from core.text_parser import calculate_sentence_interval


class AutoPlayer(QObject):
    """自动播放控制器，使用 QTimer 按句定时推进"""

    # 信号：切换到新句子
    sentenceChanged = pyqtSignal(int)  # 新句子索引
    # 信号：播放结束（到达最后一句话）
    playbackFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._sentences = []       # 句子列表
        self._current_index = 0    # 当前句子索引
        self._speed = DEFAULT_SPEED  # 速度倍率
        self._is_running = False   # 是否正在播放

        # 定时器
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._advance_to_next)

    def load_sentences(self, sentences: list):
        """
        加载句子列表。

        Args:
            sentences: [(start, end, text), ...]
        """
        self._sentences = sentences
        self._current_index = 0
        self.stop()

    def start(self):
        """开始自动播放"""
        if not self._sentences:
            return
        self._is_running = True
        self._schedule_next()

    def pause(self):
        """暂停播放"""
        self._is_running = False
        self._timer.stop()

    def resume(self):
        """恢复播放"""
        if not self._sentences:
            return
        self._is_running = True
        self._schedule_next()

    def stop(self):
        """停止播放"""
        self._is_running = False
        self._timer.stop()

    def reset(self):
        """重置到第一句"""
        self._current_index = 0
        self._timer.stop()
        self._is_running = False

    def set_current_index(self, index: int):
        """
        设置当前句子索引（外部跳转时调用）。

        Args:
            index: 句子索引
        """
        if 0 <= index < len(self._sentences):
            self._current_index = index
            # 如果正在播放，重新调度
            if self._is_running:
                self._timer.stop()
                self._schedule_next()

    def get_current_index(self) -> int:
        """获取当前句子索引"""
        return self._current_index

    def set_speed(self, multiplier: float):
        """
        设置速度倍率。

        Args:
            multiplier: 速度倍率（0.5 ~ 5.0）
        """
        self._speed = multiplier
        # 如果正在播放，重新调度以应用新速度
        if self._is_running and self._timer.isActive():
            self._timer.stop()
            self._schedule_next()

    def is_running(self) -> bool:
        """是否正在播放"""
        return self._is_running

    def _schedule_next(self):
        """调度下一次句子切换"""
        if not self._sentences or self._current_index >= len(self._sentences):
            self._is_running = False
            self.playbackFinished.emit()
            return

        # 根据当前句子长度和速度计算停留时间
        sentence_text = self._sentences[self._current_index][2]
        interval = calculate_sentence_interval(sentence_text, BASE_STAY_MS)
        interval = max(200, int(interval / self._speed))  # 应用速度倍率，最小200ms

        self._timer.start(interval)

    def _advance_to_next(self):
        """推进到下一句"""
        if self._current_index < len(self._sentences) - 1:
            self._current_index += 1
            self.sentenceChanged.emit(self._current_index)
            self._schedule_next()
        else:
            # 到达最后一句话
            self._is_running = False
            self.playbackFinished.emit()
