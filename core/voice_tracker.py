# -*- coding: utf-8 -*-
"""语音识别与文本匹配模块 - 使用 sherpa-onnx 实现离线流式中英双语识别"""

import os
import sys
import json
import threading
import queue
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from config import (
    SAMPLE_RATE, BLOCK_SIZE, MATCH_THRESHOLD, SEARCH_FORWARD, MODEL_DIR
)
from core.text_parser import calculate_similarity


class VoiceTracker(QObject):
    """语音识别与文本匹配控制器"""

    # 信号：识别到新句子，需要跳转
    sentenceMatched = pyqtSignal(int)  # 匹配到的句子索引
    # 信号：识别文本更新（用于显示）
    recognizedTextUpdated = pyqtSignal(str)  # 当前识别的文本
    # 信号：错误信息
    errorOccurred = pyqtSignal(str)  # 错误信息

    def __init__(self, parent=None):
        super().__init__(parent)

        self._recognizer = None
        self._stream = None
        self._is_running = False
        self._audio_thread = None
        self._stop_event = threading.Event()

        # 句子数据
        self._sentences = []
        self._current_index = 0

        # 识别结果累积
        self._accumulated_text = ""  # 端点检测后的累积文本
        self._last_result = ""

        # 音频数据队列
        self._audio_queue = queue.Queue()

        # 模型路径
        self._model_dir = MODEL_DIR

    def set_model_dir(self, model_dir: str):
        """设置模型目录"""
        self._model_dir = model_dir

    def check_model(self) -> tuple:
        """
        检查模型文件是否存在。

        Returns:
            (is_valid, message) 元组
        """
        model_path = Path(self._model_dir)
        if not model_path.exists():
            return False, (
                f"模型目录不存在: {self._model_dir}\n\n"
                "请下载 sherpa-onnx-streaming-zipformer-bilingual-zh-en 模型，\n"
                "解压后将文件放入 models/ 目录。\n\n"
                "下载地址:\n"
                "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2"
            )

        required_files = ["tokens.txt", "encoder-epoch-99-avg-1.onnx",
                          "decoder-epoch-99-avg-1.onnx", "joiner-epoch-99-avg-1.onnx"]
        for f in required_files:
            if not (model_path / f).exists():
                return False, f"模型文件缺失: {model_path / f}\n请确保模型文件完整。"

        return True, "模型文件完整"

    def initialize(self) -> bool:
        """
        初始化语音识别器。

        Returns:
            是否初始化成功
        """
        try:
            import sherpa_onnx
        except ImportError:
            self.errorOccurred.emit(
                "sherpa-onnx 未安装！\n"
                "请运行: pip install sherpa-onnx"
            )
            return False

        # 检查模型
        is_valid, msg = self.check_model()
        if not is_valid:
            self.errorOccurred.emit(msg)
            return False

        try:
            model_path = Path(self._model_dir)
            self._recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
                tokens=str(model_path / "tokens.txt"),
                encoder=str(model_path / "encoder-epoch-99-avg-1.onnx"),
                decoder=str(model_path / "decoder-epoch-99-avg-1.onnx"),
                joiner=str(model_path / "joiner-epoch-99-avg-1.onnx"),
                num_threads=4,
                sample_rate=16000,
                feature_dim=80,
                enable_endpoint_detection=True,
                rule1_min_trailing_silence=2.4,
                rule2_min_trailing_silence=1.2,
                rule3_min_utterance_length=300,
                decoding_method="greedy_search",
                provider="cpu",
            )
            self._stream = self._recognizer.create_stream()
            return True
        except Exception as e:
            self.errorOccurred.emit(f"语音识别器初始化失败: {str(e)}")
            return False

    def load_sentences(self, sentences: list, current_index: int = 0):
        """
        加载句子列表用于匹配。

        Args:
            sentences: [(start, end, text), ...]
            current_index: 当前句子索引
        """
        self._sentences = sentences
        self._current_index = current_index
        self._accumulated_text = ""
        self._last_result = ""

    def set_current_index(self, index: int):
        """设置当前句子索引"""
        self._current_index = index

    def start(self):
        """开始语音识别"""
        if self._recognizer is None:
            if not self.initialize():
                return

        if self._is_running:
            return

        self._is_running = True
        self._stop_event.clear()
        self._accumulated_text = ""
        self._last_result = ""

        # 重置流
        if self._stream:
            self._recognizer.reset(self._stream)
        else:
            self._stream = self._recognizer.create_stream()

        # 启动音频采集线程
        self._audio_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self._audio_thread.start()

    def stop(self):
        """停止语音识别"""
        self._is_running = False
        self._stop_event.set()

        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=2.0)

        self._accumulated_text = ""
        self._last_result = ""
        self.recognizedTextUpdated.emit("")

    def is_running(self) -> bool:
        """是否正在识别"""
        return self._is_running

    def _audio_capture_loop(self):
        """音频采集循环（在独立线程中运行）"""
        try:
            import sounddevice as sd
        except ImportError:
            self.errorOccurred.emit(
                "sounddevice 未安装！\n"
                "请运行: pip install sounddevice"
            )
            return

        try:
            # 使用 48kHz 采样率，sherpa-onnx 内部会自动重采样到 16kHz
            sample_rate = 48000
            samples_per_read = int(0.1 * sample_rate)  # 100ms

            with sd.InputStream(channels=1, dtype="float32", samplerate=sample_rate) as stream:
                while not self._stop_event.is_set():
                    try:
                        samples, _ = stream.read(samples_per_read)
                        samples = samples.reshape(-1)

                        if not self._stop_event.is_set():
                            self._process_audio(samples, sample_rate)
                    except Exception as e:
                        if not self._stop_event.is_set():
                            self.errorOccurred.emit(f"音频采集错误: {str(e)}")
                        break
        except Exception as e:
            if not self._stop_event.is_set():
                self.errorOccurred.emit(f"无法打开麦克风: {str(e)}\n请确保麦克风设备可用。")

    def _process_audio(self, samples, sample_rate: int):
        """处理音频数据（在音频线程中调用）"""
        if not self._stream or not self._recognizer:
            return

        # 送入识别器
        self._stream.accept_waveform(sample_rate, samples.tolist())

        while self._recognizer.is_ready(self._stream):
            self._recognizer.decode_stream(self._stream)

        # 获取识别结果
        result = self._recognizer.get_result(self._stream)

        # 检查端点（一句话说完）
        is_endpoint = self._recognizer.is_endpoint(self._stream)

        if result and result != self._last_result:
            self._last_result = result
            # 发送实时识别文本到 UI
            self.recognizedTextUpdated.emit(result)

        if is_endpoint:
            if result:
                # 一句话完成，进行文本匹配
                self._on_sentence_end(result)
                self._accumulated_text += result
                self.recognizedTextUpdated.emit(self._accumulated_text)

            # 重置流以准备下一句
            self._recognizer.reset(self._stream)
            self._last_result = ""

    def _on_sentence_end(self, recognized_text: str):
        """一句话识别完成，进行文本匹配"""
        if not recognized_text or not self._sentences:
            return

        recognized = recognized_text.strip()
        if not recognized:
            return

        # 搜索范围：当前句到当前句+SEARCH_FORWARD
        best_match = self._current_index
        best_score = 0.0

        search_end = min(self._current_index + SEARCH_FORWARD + 1, len(self._sentences))

        for i in range(self._current_index, search_end):
            sentence_text = self._sentences[i][2]
            score = calculate_similarity(recognized, sentence_text)
            if score > best_score:
                best_score = score
                best_match = i

        # 相似度超过阈值且不是当前句子才跳转
        if best_score >= MATCH_THRESHOLD and best_match > self._current_index:
            self._current_index = best_match
            self.sentenceMatched.emit(best_match)
