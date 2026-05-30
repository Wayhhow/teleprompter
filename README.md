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
- **窗口置顶**：提词器窗口始终保持在最前面
- **深色主题**：护眼深色界面，适合长时间使用
- **快捷键支持**：Space（播放/暂停）、←（上一句）、→（下一句）、Home（重置）

## 快速开始（下载即用）

### 方式一：下载免安装版（推荐普通用户）

无需安装 Python，下载解压即可使用。

1. 前往 [Releases](https://github.com/Wayhhow/teleprompter/releases) 页面
2. 下载最新版本的 `Teleprompter-Windows.zip`
3. 解压到任意文件夹
4. 双击 `Teleprompter.exe` 运行

> 如需语音跟读功能，首次使用前需下载语音模型（见下方「下载语音模型」）

### 方式二：从源码运行（推荐开发者）

需要安装 Python 3.8+。

```bash
# 1. 克隆仓库
git clone https://github.com/Wayhhow/teleprompter.git
cd teleprompter

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

---

## 下载语音模型（可选）

语音模型用于「语音跟读」功能，让提词器根据你的朗读自动翻页。

### Windows 用户

双击运行项目根目录下的 `download_model.bat`，自动下载并解压模型。

### macOS / Linux 用户

```bash
# 下载模型（约 350MB）
curl -L -o model.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2

# 解压
tar -xjf model.tar.bz2

# 移动模型文件到 models/ 目录
mv sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/*.onnx models/
mv sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/tokens.txt models/

# 清理
rm -rf model.tar.bz2 sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20
```

> 模型支持中文和英文的流式语音识别，完全离线运行，无需联网。

---

## 使用指南

### 界面说明

```
┌─────────────────────────────────────────┐
│  文件  播放  帮助          [提词器窗口]  │  ← 菜单栏
├─────────────────────────────────────────┤
│                                         │
│  欢迎使用自动提词器                      │
│  请点击「打开文件」加载 TXT 稿件         │  ← 提词器显示区
│  ...                                    │
│                                         │
├─────────────────────────────────────────┤
│ [打开文件] [上一句] [▶播放] [下一句] [⟲重置] [📌置顶] │  ← 控制按钮
│ 速度: [========●====] 1.5x              │  ← 速度滑块
│ 字号: [======●======] 24pt              │  ← 字号滑块
│ [🎤开始语音识别] ●未启动 识别: [______]  │  ← 语音控制区
└─────────────────────────────────────────┘
```

### 基本操作

| 步骤 | 操作 |
|------|------|
| 1 | 点击「打开文件」或按 `Ctrl+O`，选择你的 TXT 演讲稿 |
| 2 | 点击「播放」或按 `Space` 开始自动翻页 |
| 3 | 拖动「速度」滑块调节翻页速度（0.5x ~ 5.0x） |
| 4 | 拖动「字号」滑块调节字体大小（16pt ~ 48pt） |
| 5 | 点击「置顶」让窗口始终保持在最前面 |
| 6 | （可选）点击「开始语音识别」，朗读时自动翻页 |

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Space` | 播放/暂停 |
| `←` | 上一句 |
| `→` | 下一句 |
| `Home` | 重置到第一句 |
| `Ctrl+O` | 打开文件 |
| `Ctrl+Q` | 退出程序 |

### 稿件格式建议

提词器按以下符号分割句子，建议按自然断句编写稿件：

- 中文标点：`。` `！` `？`
- 英文标点：`.` `!` `?`
- 换行符：空行也会作为分隔

示例稿件格式：

```
大家好，欢迎来到今天的演讲。

今天我想和大家分享的主题是关于人工智能的发展与未来。

首先，让我们回顾一下人工智能的发展历程。
```

---

## 自行打包为可执行文件

如果你想自己打包 exe（例如修改源码后）：

```bash
# Windows
build.bat

# 打包完成后
# 可执行文件位于 dist/Teleprompter/Teleprompter.exe
# 需要将 dist/Teleprompter/ 整个文件夹分发给用户
```

> 打包前请确保已下载语音模型到 `models/` 目录，否则打包后的程序无法使用语音功能。

---

## 项目结构

```
teleprompter/
├── core/                    # 核心逻辑
│   ├── auto_player.py       # 自动播放控制器
│   ├── text_parser.py       # 文本解析与句子分割
│   └── voice_tracker.py     # 语音识别与文本匹配
├── ui/                      # 用户界面
│   ├── main_window.py       # 主窗口
│   ├── teleprompter_view.py # 提词器显示视图
│   └── control_panel.py     # 控制面板
├── models/                  # 语音模型目录
│   └── README.md            # 模型下载说明
├── main.py                  # 程序入口
├── config.py                # 全局配置
├── requirements.txt         # Python 依赖
├── build.bat                # PyInstaller 构建脚本
├── Teleprompter.spec        # PyInstaller 配置
└── test_speech.txt          # 示例测试稿件
```

---

## 配置

所有可调参数位于 [config.py](config.py)，包括：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `WINDOW_WIDTH` / `WINDOW_HEIGHT` | 窗口大小 | 1000x700 |
| `DEFAULT_FONT_SIZE` | 默认字号 | 24pt |
| `BASE_STAY_MS` | 每句基础停留时间 | 3000ms |
| `MATCH_THRESHOLD` | 语音匹配阈值 | 0.4 |
| `MATCH_DEBOUNCE_MS` | 匹配防抖时间 | 1200ms |
| `HIGHLIGHT_BG_COLOR` | 高亮背景色 | 黄色半透明 |

---

## 常见问题

**Q: 语音跟读功能无法使用？**
> 请检查 `models/` 目录下是否有 4 个模型文件（`tokens.txt`、`encoder-epoch-99-avg-1.onnx`、`decoder-epoch-99-avg-1.onnx`、`joiner-epoch-99-avg-1.onnx`）。如果没有，请运行 `download_model.bat` 或手动下载。

**Q: 程序启动后界面显示异常？**
> 确保已安装所有依赖：`pip install -r requirements.txt`。PyQt5 需要正确的显示驱动支持。

**Q: 如何准备自己的演讲稿？**
> 用任意文本编辑器编写，保存为 `.txt` 格式。按自然句子断句（使用 `。` `！` `？` 或 `.` `!` `?` 结尾），程序会自动分割。

---

## 技术栈

- **GUI 框架**：PyQt5
- **语音识别**：sherpa-onnx（离线流式语音识别，支持中英文）
- **音频处理**：sounddevice、numpy

## 许可证

MIT
