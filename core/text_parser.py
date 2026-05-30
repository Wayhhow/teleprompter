# -*- coding: utf-8 -*-
"""文本解析与句子分割模块"""

import re
import os


def read_text_file(file_path: str) -> str:
    """
    读取TXT文件，自动检测编码（UTF-8 / GBK）。

    Args:
        file_path: 文件路径

    Returns:
        文件文本内容

    Raises:
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 无法解码文件
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 优先尝试 UTF-8
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        pass

    # 回退到 GBK
    try:
        with open(file_path, "r", encoding="gbk") as f:
            return f.read()
    except UnicodeDecodeError:
        pass

    # 最后尝试 GB18030（GBK 的超集）
    with open(file_path, "r", encoding="gb18030") as f:
        return f.read()


def split_sentences(text: str) -> list:
    """
    按中英文标点和换行符分割文本为句子列表。

    支持的句子分隔符：
    - 中文：。！？
    - 英文：. ! ?
    - 换行符：\\n

    注意：音标部分（/.../）内的点号不会被当作句号。

    Args:
        text: 原始文本

    Returns:
        句子列表，每个元素为 (start_pos, end_pos, sentence_text) 元组
    """
    if not text or not text.strip():
        return []

    # 第一步：将所有音标（/.../）整体替换为不含任何标点的占位符
    # 这样分句时音标不会被截断
    phonetic_map = []  # [(placeholder, original), ...]

    def _save_phonetic(match):
        idx = len(phonetic_map)
        # 使用纯字母占位符，不含任何标点
        placeholder = f'PHONMARK{idx}X'
        phonetic_map.append((placeholder, match.group()))
        return placeholder

    protected_text = re.sub(r'/[^/]+/', _save_phonetic, text)

    # 第二步：在保护后的文本上进行正常分句
    pattern = r'[^。！？.!?\n]+[。！？.!?\n]?'
    sentences = []

    for match in re.finditer(pattern, protected_text):
        sentence = match.group().strip()
        if not sentence:
            continue

        # 第三步：恢复音标占位符
        for placeholder, original in phonetic_map:
            sentence = sentence.replace(placeholder, original)

        if sentence:
            sentences.append((match.start(), match.end(), sentence))

    return sentences


def calculate_sentence_interval(sentence_text: str, base_ms: int = 3000) -> int:
    """
    根据句子长度动态计算停留时间。

    中文字符每个额外增加 CHAR_TIME_CN 毫秒，
    英文字符每个额外增加 CHAR_TIME_EN 毫秒。

    Args:
        sentence_text: 句子文本
        base_ms: 基础停留时间（毫秒）

    Returns:
        建议停留时间（毫秒）
    """
    from config import CHAR_TIME_CN, CHAR_TIME_EN

    extra = 0
    for c in sentence_text:
        if '\u4e00' <= c <= '\u9fff':
            extra += CHAR_TIME_CN
        elif c.isalpha():
            extra += CHAR_TIME_EN

    return base_ms + extra


def normalize_text_for_matching(text: str) -> str:
    """
    标准化文本用于匹配比较。
    去除标点、空白，转小写。

    Args:
        text: 原始文本

    Returns:
        标准化后的文本
    """
    # 移除所有标点和空白
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
    return text.lower()


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两段文本的相似度（0.0 ~ 1.0）。
    针对实时语音识别优化：支持部分匹配（text1 是 text2 的子串或前缀）。

    Args:
        text1: 文本1（通常为识别文本，可能是不完整的）
        text2: 文本2（通常为完整的稿子句子）

    Returns:
        相似度分数
    """
    t1 = normalize_text_for_matching(text1)
    t2 = normalize_text_for_matching(text2)

    if not t1 or not t2:
        return 0.0

    len1, len2 = len(t1), len(t2)

    # 策略1：如果识别文本是句子文本的子串，给予高相似度
    if t1 in t2:
        # 子串匹配：根据覆盖比例打分
        return 0.6 + 0.4 * (len1 / len2)

    # 策略2：计算最长公共子串长度
    max_common_len = 0
    for i in range(len1):
        for j in range(i + 1, len1 + 1):
            substr = t1[i:j]
            if substr in t2:
                max_common_len = max(max_common_len, len(substr))

    if max_common_len > 0:
        # 基于最长公共子串的相似度
        return 0.3 + 0.5 * (max_common_len / len1)

    # 策略3：字符重叠率（兜底）
    set1 = set(t1)
    set2 = set(t2)
    common = set1 & set2

    if not common:
        return 0.0

    common_count = sum(min(t1.count(c), t2.count(c)) for c in common)
    return common_count / max(len1, len2) * 0.3  # 降低权重
