# -*- coding: utf-8 -*-
"""语音识别与文本匹配模块 - 使用 sherpa-onnx 实现离线流式中英双语识别"""

import os
import sys
import threading
import time
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from config import (
    SAMPLE_RATE, BLOCK_SIZE, MATCH_THRESHOLD, SEARCH_RANGE, MODEL_DIR,
    MATCH_DEBOUNCE_MS, MATCH_MIN_TEXT_LENGTH
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

        # 模型路径 - 支持打包后的路径
        self._model_dir = self._get_model_dir()

        # 实时匹配防抖
        self._last_match_time = 0  # 上次匹配时间戳
        
        # 智能匹配状态
        self._confirmed_index = -1  # 已确认读到的句子索引
        self._skip_detection_count = 0  # 连续检测到跳过的计数
        self._last_recognized_text = ""  # 上次识别的文本

    def _get_model_dir(self) -> str:
        """获取模型目录路径，支持源码运行和打包后的程序"""
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包环境：模型在 _internal/models 目录
            model_path = Path(sys.executable).parent / "_internal" / "models"
            if model_path.exists():
                return str(model_path)
        # 源码运行，使用配置中的路径
        return MODEL_DIR

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
        self._confirmed_index = -1  # 重置已确认索引
        self._skip_detection_count = 0
        self._accumulated_text = ""
        self._last_result = ""
        self._last_recognized_text = ""

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
        self._last_match_time = 0
        self._confirmed_index = -1
        self._skip_detection_count = 0
        self._last_recognized_text = ""

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
        self._last_recognized_text = ""
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

            # 智能匹配：主要向下滚动，智能回翻
            self._try_match_intelligent(result)

        if is_endpoint:
            if result:
                # 一句话完成，更新累积文本
                self._accumulated_text += result
                self.recognizedTextUpdated.emit(self._accumulated_text)

            # 重置流以准备下一句
            self._recognizer.reset(self._stream)
            self._last_result = ""

    def _try_match_intelligent(self, recognized_text: str):
        """
        智能匹配逻辑：
        1. 主要向下滚动：优先匹配当前句之后的句子
        2. 智能回翻：只有确定跳过了句子才往回翻
        3. 预测下一句：根据当前句推断下一句内容
        """
        if not recognized_text or not self._sentences:
            return

        recognized = recognized_text.strip()
        if len(recognized) < MATCH_MIN_TEXT_LENGTH:
            return

        # 防抖检查
        current_time = time.time() * 1000
        if current_time - self._last_match_time < MATCH_DEBOUNCE_MS:
            return

        # 搜索范围：当前句及后面3句（优先向下）
        # 如果检测可能跳过了，也搜索前面2句
        search_start = max(0, self._current_index - 2)  # 向前2句（用于回翻）
        search_end = min(len(self._sentences), self._current_index + 4)  # 向后3句

        best_match = self._current_index
        best_score = 0.0
        current_score = 0.0

        # 计算所有候选句的相似度
        scores = {}
        for i in range(search_start, search_end):
            sentence_text = self._sentences[i][2]
            score = calculate_similarity(recognized, sentence_text)
            scores[i] = score
            if i == self._current_index:
                current_score = score
            if score > best_score:
                best_score = score
                best_match = i

        # 决策逻辑
        if best_score < MATCH_THRESHOLD:
            # 相似度太低，不跳转
            return

        if best_match == self._current_index:
            # 匹配到当前句，确认已读
            self._confirmed_index = self._current_index
            self._skip_detection_count = 0
            return

        # 匹配到其他句子
        if best_match > self._current_index:
            # 向下匹配（正常流程）
            # 检查是否是下一句或跳过了几句
            skip_count = best_match - self._current_index
            
            if skip_count == 1:
                # 匹配到下一句，正常向下滚动
                self._current_index = best_match
                self._confirmed_index = best_match
                self._last_match_time = current_time
                self.sentenceMatched.emit(best_match)
            elif skip_count <= 3:
                # 可能跳过了1-3句，需要确认
                # 要求跳过的句子相似度明显低于当前匹配
                skipped_similar = all(
                    scores.get(i, 0) < best_score - 0.2 
                    for i in range(self._current_index + 1, best_match)
                )
                if skipped_similar:
                    self._current_index = best_match
                    self._confirmed_index = best_match
                    self._last_match_time = current_time
                    self.sentenceMatched.emit(best_match)
        else:
            # 向上匹配（往回翻）
            # 只有确定读错了才回翻
            # 条件：当前句及后面几句的相似度都很低，且前面某句相似度很高
            forward_scores = [
                scores.get(i, 0) 
                for i in range(self._current_index, min(self._current_index + 3, len(self._sentences)))
            ]
            
            # 如果后面几句的相似度都很低（< 0.3），且前面某句相似度高，则回翻
            if all(s < 0.3 for s in forward_scores) and best_score > 0.5:
                self._current_index = best_match
                self._confirmed_index = best_match
                self._last_match_time = current_time
                self.sentenceMatched.emit(best_match)
