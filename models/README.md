# 语音识别模型

本目录用于存放 sherpa-onnx 语音识别模型文件。

## 下载模型

请下载以下模型并解压到本目录：

**模型名称**: sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20

**下载地址**:
https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20.tar.bz2

## 目录结构

解压后，本目录应包含以下文件：

```
models/
├── tokens.txt
├── encoder-epoch-99-avg-1.onnx
├── decoder-epoch-99-avg-1.onnx
└── joiner-epoch-99-avg-1.onnx
```

## 说明

- 该模型支持中文和英文的流式语音识别
- 模型大小约 200MB
- 完全离线运行，无需联网
