# -*- coding: utf-8 -*-
"""提词器显示视图 - 滚动 + 高亮"""

from PyQt5.QtWidgets import QTextEdit, QApplication
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal
from PyQt5.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont,
    QWheelEvent, QTextFormat, QTextOption
)

from config import (
    DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE, FONT_FAMILY,
    CONTEXT_SENTENCES, HIGHLIGHT_BG_COLOR, CONTEXT_FADE_STEP,
    SCROLL_ANIMATION_DURATION, SCROLL_POSITION_RATIO
)


class TeleprompterView(QTextEdit):
    """提词器文本显示视图，支持句子高亮和平滑滚动"""

    # 信号：用户手动滚动时发出
    manualScrollRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 基本设置
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)

        # 字体设置
        self._font_size = DEFAULT_FONT_SIZE
        self._update_font()

        # 句子数据
        self._sentences = []  # [(start, end, text), ...]
        self._current_index = -1

        # 高亮更新节流
        self._highlight_pending = False
        self._highlight_timer = QTimer(self)
        self._highlight_timer.setSingleShot(True)
        self._highlight_timer.setInterval(50)  # 50ms 节流
        self._highlight_timer.timeout.connect(self._do_update_highlight)

        # 滚动动画
        self._scroll_animation = None

        # 欢迎文本
        self._show_welcome()

    def _update_font(self):
        """更新字体设置"""
        font = QFont(FONT_FAMILY, self._font_size)
        self.setFont(font)

    def _show_welcome(self):
        """显示欢迎文本"""
        self.setPlainText(
            "欢迎使用自动提词器\n\n"
            "请点击「打开文件」加载 TXT 稿件\n"
            "或使用菜单 文件 → 打开\n\n"
            "功能说明：\n"
            "• 自动播放：按句自动翻页，可调节速度\n"
            "• 语音跟读：实时语音识别，自动匹配翻页\n"
            "• 字号调节：拖动滑块调整字体大小\n"
            "• 手动控制：上一句/下一句/重置"
        )

    def load_text(self, text: str, sentences: list):
        """
        加载文本并显示。

        Args:
            text: 原始文本
            sentences: 句子列表 [(start, end, text), ...]
        """
        self._sentences = sentences
        self._current_index = 0
        self.setPlainText(text)
        self._update_highlight()

    def set_current_index(self, index: int, animated: bool = True):
        """
        设置当前高亮句子索引。

        Args:
            index: 句子索引
            animated: 是否使用动画滚动
        """
        if not self._sentences or index < 0 or index >= len(self._sentences):
            return

        self._current_index = index
        self._request_highlight_update()

        # 滚动到当前句子
        if animated:
            self._smooth_scroll_to_sentence(index)
        else:
            self._instant_scroll_to_sentence(index)

    def get_current_index(self) -> int:
        """获取当前句子索引"""
        return self._current_index

    def get_sentence_count(self) -> int:
        """获取句子总数"""
        return len(self._sentences)

    def set_font_size(self, size: int):
        """
        设置字体大小。

        Args:
            size: 字号（pt）
        """
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
        if size != self._font_size:
            self._font_size = size
            self._update_font()
            self._request_highlight_update()

    def get_font_size(self) -> int:
        """获取当前字号"""
        return self._font_size

    def _request_highlight_update(self):
        """请求高亮更新（带节流）"""
        if not self._highlight_pending:
            self._highlight_pending = True
            self._highlight_timer.start()

    def _do_update_highlight(self):
        """执行高亮更新"""
        self._highlight_pending = False
        if not self._sentences or self._current_index < 0:
            return
        self._update_highlight()

    def _update_highlight(self):
        """更新当前句子高亮和上下文淡化效果"""
        if not self._sentences or self._current_index < 0:
            return

        selections = []
        doc = self.document()

        # 遍历所有句子，设置高亮/淡化
        for i, (start, end, text) in enumerate(self._sentences):
            cursor = QTextCursor(doc)
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)

            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor

            if i == self._current_index:
                # 当前句子：醒目高亮
                fmt = QTextCharFormat()
                fmt.setBackground(QColor(*HIGHLIGHT_BG_COLOR))
                fmt.setFontWeight(QFont.Bold)
                fmt.setFontPointSize(self._font_size + 2)
                fmt.setForeground(QColor(255, 255, 255))
                selection.format = fmt
            else:
                # 上下文句子：根据距离淡化
                distance = abs(i - self._current_index)
                if distance <= CONTEXT_SENTENCES:
                    alpha = max(60, 220 - distance * CONTEXT_FADE_STEP)
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor(200, 200, 200, alpha))
                    fmt.setFontPointSize(self._font_size)
                    selection.format = fmt
                else:
                    # 远处句子：重度淡化
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor(100, 100, 100, 40))
                    fmt.setFontPointSize(self._font_size)
                    selection.format = fmt

            selections.append(selection)

        self.setExtraSelections(selections)

    def _smooth_scroll_to_sentence(self, index: int):
        """平滑滚动到指定句子"""
        if index < 0 or index >= len(self._sentences):
            return

        start_pos = self._sentences[index][0]

        # 创建临时光标计算目标位置
        cursor = QTextCursor(self.document())
        cursor.setPosition(start_pos)
        self.setTextCursor(cursor)

        # 计算目标滚动值
        cursor_rect = self.cursorRect(cursor)
        viewport_height = self.viewport().height()
        target_scroll = (
            self.verticalScrollBar().value()
            + cursor_rect.top()
            - int(viewport_height * SCROLL_POSITION_RATIO)
        )

        # 限制范围
        bar = self.verticalScrollBar()
        target_scroll = max(bar.minimum(), min(target_scroll, bar.maximum()))

        # 停止之前的动画
        if self._scroll_animation and self._scroll_animation.state() == QPropertyAnimation.Running:
            self._scroll_animation.stop()

        # 创建新动画
        self._scroll_animation = QPropertyAnimation(bar, b"value")
        self._scroll_animation.setDuration(SCROLL_ANIMATION_DURATION)
        self._scroll_animation.setStartValue(bar.value())
        self._scroll_animation.setEndValue(target_scroll)
        self._scroll_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._scroll_animation.start()

    def _instant_scroll_to_sentence(self, index: int):
        """立即滚动到指定句子（无动画）"""
        if index < 0 or index >= len(self._sentences):
            return

        start_pos = self._sentences[index][0]
        cursor = QTextCursor(self.document())
        cursor.setPosition(start_pos)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def wheelEvent(self, event: QWheelEvent):
        """重写滚轮事件，支持平滑滚动"""
        # 使用 Qt 内置的平滑滚动
        # 对于手动滚动，发出信号通知外部
        super().wheelEvent(event)

        # 计算滚动后的句子位置（简单估算）
        if self._sentences:
            bar = self.verticalScrollBar()
            viewport_height = self.viewport().height()
            # 获取视口中间位置对应的文本位置
            center_pos = bar.value() + viewport_height // 2
            cursor = self.cursorForPosition(QPoint(self.viewport().width() // 2, viewport_height // 2))
            pos = cursor.position()

            # 找到最近的句子
            for i, (start, end, text) in enumerate(self._sentences):
                if start <= pos <= end:
                    if i != self._current_index:
                        self._current_index = i
                        self._request_highlight_update()
                    break

    def resizeEvent(self, event):
        """窗口大小改变时重新高亮"""
        super().resizeEvent(event)
        if self._sentences and self._current_index >= 0:
            self._request_highlight_update()
