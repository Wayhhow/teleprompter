# -*- coding: utf-8 -*-
"""自动提词器 - 程序入口"""

import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from config import DARK_STYLE, MODEL_DIR
from ui.main_window import MainWindow


def check_dependencies():
    """检查必要的依赖是否已安装"""
    missing = []

    try:
        import PyQt5
    except ImportError:
        missing.append("PyQt5")

    try:
        import sherpa_onnx
    except ImportError:
        missing.append("sherpa-onnx")

    try:
        import sounddevice
    except ImportError:
        missing.append("sounddevice")

    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    if missing:
        return False, missing
    return True, []


def main():
    """程序入口"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用 Fusion 风格以更好地应用自定义样式

    # 应用深色主题
    app.setStyleSheet(DARK_STYLE)

    # 检查依赖
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        QMessageBox.critical(
            None,
            "依赖缺失",
            f"以下依赖未安装:\n\n" +
            "\n".join(f"  • {pkg}" for pkg in missing) +
            "\n\n请运行以下命令安装:\n"
            "pip install -r requirements.txt"
        )
        sys.exit(1)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 检查语音模型（仅在启动时提示，不阻塞）
    voice = window.voice
    is_valid, msg = voice.check_model()
    if not is_valid:
        # 不阻塞启动，仅在状态栏提示
        window.statusBar().showMessage(
            "提示: 语音识别模型未配置，语音跟读功能不可用。"
            "请将模型文件放入 models/ 目录。"
        )

    # 进入事件循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
