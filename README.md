# 自动提词器

一个支持自动播放和语音跟读的桌面提词器应用。

## 功能特性

- **稿件加载**：加载 TXT 文件，自动按句子分割
- **句子高亮**：当前朗读句子醒目高亮，上下文淡化显示
- **平滑滚动**：自动平滑滚动到当前句子，带缓动动画
- **自动播放**：按句子自动翻页，根据句子长度智能计算停留时间
- **速度调节**：0.5x ~ 5.0x 速度倍率，适应不同朗读节奏
- **字号调节**：16pt ~ 48pt 字号，满足近距离和远距离观看需求
- **语音跟读**：离线语音识别，自动匹配朗读进度并翻页
- **深色主题**：护眼深色界面，适合长时间使用
- **快捷键支持**：Space（播放/暂停）、←（上一句）、→（下一句）、Home（重置）

## 技术栈

- **GUI 框架**：PyQt5
- **语音识别**：sherpa-onnx（离线流式语音识别，支持中英文）
- **音频处理**：sounddevice、numpy

## 安装

### 环境要求

- Python 3.8 或更高版本
- Windows / macOS / Linux

### 步骤

1. 克隆仓库

```bash
git clone https://github.com/Wayhhow/teleprompter.git
cd teleprompter
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 下载语音模型（可选，仅使用语音功能需要）

```bash
# 下载 sherpa-onnx 中英双语模型
curl -L -o model.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2

# 解压
tar -xjf model.tar.bz2

# 移动模型文件到 models/ 目录
mv sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/*.onnx models/
mv sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/tokens.txt models/

# 清理
rm -rf model.tar.bz2 sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20
```

> 模型约 350MB，支持中文和英文的流式语音识别，完全离线运行。

## 使用

### 启动

```bash
python main.py
```

### 基本操作

1. **加载稿件**：点击「打开文件」或使用 `Ctrl+O`，选择 TXT 文件
2. **自动播放**：点击「播放」按钮或按 `Space` 键
3. **调节速度**：拖动速度滑块，从 0.5x 到 5.0x
4. **调节字号**：拖动字号滑块，从 16pt 到 48pt
5. **语音识别**：点击「开始语音识别」，开始朗读后会自动翻页
6. **手动控制**：使用「上一句」「下一句」「重置」按钮或快捷键

### 快捷键

| 快捷键 | 功能 |
| ------ | ---- |
| `Space` | 播放/暂停 |
| `←` | 上一句 |
| `→` | 下一句 |
| `Home` | 重置到第一句 |
| `Ctrl+O` | 打开文件 |
| `Ctrl+Q` | 退出程序 |

## 打包为可执行文件

使用 PyInstaller 将程序打包为独立的可执行文件，无需安装 Python：

```bash
build.bat
```

打包完成后，可执行文件位于 `dist/Teleprompter/Teleprompter.exe`。

> 注意：打包时需要将模型文件一起分发，或在目标机器上下载模型。

## 项目结构

```
teleprompter/
├── core/               # 核心逻辑
│   ├── auto_player.py  # 自动播放控制器
│   ├── text_parser.py  # 文本解析与句子分割
│   └── voice_tracker.py # 语音识别与文本匹配
├── ui/                 # 用户界面
│   ├── main_window.py   # 主窗口
│   ├── teleprompter_view.py  # 提词器显示视图
│   └── control_panel.py  # 控制面板
├── models/             # 语音模型目录
│   └── README.md       # 模型下载说明
├── main.py             # 程序入口
├── config.py           # 全局配置
├── requirements.txt    # Python 依赖
├── build.bat           # PyInstaller 构建脚本
└── Teleprompter.spec   # PyInstaller 配置
```

## 配置

所有可调参数位于 [config.py](config.py)，包括：

- 窗口大小、标题
- 字体配置（默认字号、最大/最小字号）
- 高亮颜色、淡化参数
- 自动播放参数（基础停留时间、速度范围）
- 语音识别参数（采样率、匹配阈值等）

## 许可证

MIT
