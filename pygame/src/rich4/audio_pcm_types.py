# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp::Impl::Clip/Queued及native_audio.hpp::Statistics。
# ◑ 导入
from array import array
from dataclasses import dataclass

from rich4.audio_types import 循环通道_类


# ◕ 功能
@dataclass
class PCM片段_类:
    """
    不移动的已解码F32样本引用及独立播放游标。

    更新日志：
    2026.10.24 - 样本只读共享；语音和三个循环通道保持原字段。
    """

    样本: array
    位置: int = 0
    语音: bool = False
    循环: bool = False
    通道: 循环通道_类 = 循环通道_类.转盘


@dataclass
class PCM统计_类:
    """
    原Statistics全部字段；设备与宿主另填实际耗时，不伪造无欠载成绩。

    更新日志：
    2026.10.24 - 混音核只更新可由采样/片段直接得到的计数。
    """

    渲染帧: int = 0
    非零采样: int = 0
    效果启动: int = 0
    语音启动: int = 0
    片段完成: int = 0
    音乐帧: int = 0
    超时次数: int = 0
    饥饿毫秒: int = 0
    削波采样: int = 0
    限幅采样: int = 0
    峰值: float = 0.0
    最长更新间隔: int = 0
    最长渲染微秒: int = 0
