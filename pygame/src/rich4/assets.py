# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/assets.cpp；格式/自适应树来自 Iru Cai 的 mytbk/rich4 (2018)。
# ◑ 导入
import struct
from dataclasses import dataclass
from pathlib import Path


# ◕ 功能
@dataclass(frozen=True)
class 资源项_类:
    """
    MKF 文件内的原始元数据，不改写成主机指针。

    更新日志：
    2026.10.23 - 对应 EntryInfo。
    """

    偏移: int
    解码长度: int
    存储长度: int
    图形偏移: int
    图形长度: int


class 位流_类:
    """
    Rich4 压缩流按低位优先消费，窥视不能改变游标。

    更新日志：
    2026.10.23 - 对应 BitReader。
    """

    def __init__(self, arg_数据: bytes) -> None:
        self.数据 = arg_数据
        self.位置 = 0

    def api_读取(self, arg_位数: int) -> int:
        if self.位置 + arg_位数 > len(self.数据) * 8:
            raise ValueError("压缩位流截断")
        值 = 0
        for 序号 in range(arg_位数):
            值 |= ((self.数据[self.位置 // 8] >> (self.位置 % 8)) & 1) << 序号
            self.位置 += 1
        return 值

    def api_窥视(self, arg_位数: int) -> int:
        原位置 = self.位置
        值 = self.api_读取(arg_位数)
        self.位置 = 原位置
        return 值


class 自适应树_类:
    """
    保留相同频率节点的稳定顺序，避免跨语言解码在重标度后漂移。

    更新日志：
    2026.10.23 - 对应 AdaptiveTree，321 叶、641 节点。
    """

    def __init__(self) -> None:
        self.频率 = [0] * 642
        self.子节点 = [0] * 641
        self.父节点 = [0] * 962
        for 符号 in range(321):
            self.频率[符号] = 1
            self.子节点[符号] = 符号 + 641
            self.父节点[符号 + 641] = 符号
        for 节点 in range(321, 641):
            子 = 2 * (节点 - 321)
            self.子节点[节点] = 子
            self.频率[节点] = self.频率[子] + self.频率[子 + 1]
            self.父节点[子] = self.父节点[子 + 1] = 节点
        self.父节点[640] = 0
        self.频率[641] = 65535

    def _设置父节点(self, arg_首子: int, arg_父: int) -> None:
        self.父节点[arg_首子] = arg_父
        if arg_首子 < 641:
            self.父节点[arg_首子 + 1] = arg_父

    def _递增(self, arg_符号: int) -> None:
        节点 = self.父节点[641 + arg_符号]
        while True:
            self.频率[节点] += 1
            新频率 = self.频率[节点]
            if 新频率 > self.频率[节点 + 1]:
                目标 = 节点 + 1
                while self.频率[目标 + 1] == 新频率 - 1:
                    目标 += 1
                self.频率[节点], self.频率[目标] = self.频率[目标], self.频率[节点]
                self.子节点[节点], self.子节点[目标] = self.子节点[目标], self.子节点[节点]
                self._设置父节点(self.子节点[节点], 节点)
                self._设置父节点(self.子节点[目标], 目标)
                节点 = 目标
            节点 = self.父节点[节点]
            if 节点 == 0:
                break

    def api_解码(self, arg_位流: 位流_类) -> int:
        节点 = 640
        while self.子节点[节点] < 641:
            节点 = self.子节点[节点] + arg_位流.api_读取(1)
        符号 = self.子节点[节点] - 641
        if self.频率[640] == 0x8000:
            for 项 in range(321):
                if self.频率[self.父节点[641 + 项]] & 1:
                    self._递增(项)
            for 项 in range(641):
                self.频率[项] >>= 1
        self._递增(符号)
        return 符号


class 解压器_类:
    """
    自适应 Huffman 与重叠回引用；输出受声明长度与分配上限双重约束。

    更新日志：
    2026.10.23 - 对应 decompress。
    """

    前缀位数 = (8, 5, 6, 4, 7, 5, 6, 3, 7, 5, 6, 4, 7, 4, 5, 3)
    距离前缀 = (
        0x3F,
        0x0B,
        0x17,
        0x03,
        0x2F,
        0x0A,
        0x16,
        0x00,
        0x2E,
        0x09,
        0x15,
        0x02,
        0x2D,
        0x01,
        0x08,
        0x00,
        0x3E,
        0x07,
        0x14,
        0x03,
        0x2C,
        0x06,
        0x13,
        0x00,
        0x2B,
        0x05,
        0x12,
        0x02,
        0x2A,
        0x01,
        0x04,
        0x00,
        0x3D,
        0x0B,
        0x11,
        0x03,
        0x29,
        0x0A,
        0x10,
        0x00,
        0x28,
        0x09,
        0x0F,
        0x02,
        0x27,
        0x01,
        0x08,
        0x00,
        0x3C,
        0x07,
        0x0E,
        0x03,
        0x26,
        0x06,
        0x0D,
        0x00,
        0x25,
        0x05,
        0x0C,
        0x02,
        0x24,
        0x01,
        0x04,
        0x00,
        0x3B,
        0x0B,
        0x17,
        0x03,
        0x23,
        0x0A,
        0x16,
        0x00,
        0x22,
        0x09,
        0x15,
        0x02,
        0x21,
        0x01,
        0x08,
        0x00,
        0x3A,
        0x07,
        0x14,
        0x03,
        0x20,
        0x06,
        0x13,
        0x00,
        0x1F,
        0x05,
        0x12,
        0x02,
        0x1E,
        0x01,
        0x04,
        0x00,
        0x39,
        0x0B,
        0x11,
        0x03,
        0x1D,
        0x0A,
        0x10,
        0x00,
        0x1C,
        0x09,
        0x0F,
        0x02,
        0x1B,
        0x01,
        0x08,
        0x00,
        0x38,
        0x07,
        0x0E,
        0x03,
        0x1A,
        0x06,
        0x0D,
        0x00,
        0x19,
        0x05,
        0x0C,
        0x02,
        0x18,
        0x01,
        0x04,
        0x00,
        0x37,
        0x0B,
        0x17,
        0x03,
        0x2F,
        0x0A,
        0x16,
        0x00,
        0x2E,
        0x09,
        0x15,
        0x02,
        0x2D,
        0x01,
        0x08,
        0x00,
        0x36,
        0x07,
        0x14,
        0x03,
        0x2C,
        0x06,
        0x13,
        0x00,
        0x2B,
        0x05,
        0x12,
        0x02,
        0x2A,
        0x01,
        0x04,
        0x00,
        0x35,
        0x0B,
        0x11,
        0x03,
        0x29,
        0x0A,
        0x10,
        0x00,
        0x28,
        0x09,
        0x0F,
        0x02,
        0x27,
        0x01,
        0x08,
        0x00,
        0x34,
        0x07,
        0x0E,
        0x03,
        0x26,
        0x06,
        0x0D,
        0x00,
        0x25,
        0x05,
        0x0C,
        0x02,
        0x24,
        0x01,
        0x04,
        0x00,
        0x33,
        0x0B,
        0x17,
        0x03,
        0x23,
        0x0A,
        0x16,
        0x00,
        0x22,
        0x09,
        0x15,
        0x02,
        0x21,
        0x01,
        0x08,
        0x00,
        0x32,
        0x07,
        0x14,
        0x03,
        0x20,
        0x06,
        0x13,
        0x00,
        0x1F,
        0x05,
        0x12,
        0x02,
        0x1E,
        0x01,
        0x04,
        0x00,
        0x31,
        0x0B,
        0x11,
        0x03,
        0x1D,
        0x0A,
        0x10,
        0x00,
        0x1C,
        0x09,
        0x0F,
        0x02,
        0x1B,
        0x01,
        0x08,
        0x00,
        0x30,
        0x07,
        0x0E,
        0x03,
        0x1A,
        0x06,
        0x0D,
        0x00,
        0x19,
        0x05,
        0x0C,
        0x02,
        0x18,
        0x01,
        0x04,
        0x00,
    )

    @classmethod
    def api_解压(
        cls,
        arg_源: bytes,
        arg_长度: int,
        arg_上限: int = 256 * 1024 * 1024,
    ) -> bytes:
        if not 0 <= arg_长度 <= arg_上限:
            raise ValueError("解码长度超过分配上限")
        输出 = bytearray()
        位流 = 位流_类(arg_源)
        树 = 自适应树_类()
        while len(输出) < arg_长度:
            符号 = 树.api_解码(位流)
            if 符号 < 256:
                输出.append(符号)
                continue
            前缀 = 位流.api_窥视(8)
            位流.api_读取(cls.前缀位数[前缀 & 15])
            距离码 = (cls.距离前缀[前缀] << 6) | 位流.api_读取(6)
            if 距离码 == 0xFFF:
                raise ValueError("压缩资源提前终止")
            距离 = 距离码 + 1
            if 距离 > len(输出):
                raise ValueError("回引用位于解码起点之前")
            for _ in range(min(符号 - 0xFD, arg_长度 - len(输出))):
                输出.append(输出[-距离])
        return bytes(输出)


class 资源包_类:
    """
    只读 MKF；索引位于文件尾，由首个 DWORD 定位。

    更新日志：
    2026.10.23 - 对应 Archive，所有偏移先校验再访问。
    """

    def __init__(self, arg_源: bytes | Path) -> None:
        self.数据 = arg_源.read_bytes() if isinstance(arg_源, Path) else arg_源
        self.api_检查范围(0, 4, len(self.数据))
        索引 = struct.unpack_from("<I", self.数据)[0]
        if 索引 < 4 or 索引 > len(self.数据) or (len(self.数据) - 索引) % 4:
            raise ValueError("无效 MKF 索引表")
        self.条目: list[资源项_类] = []
        for 位置 in range(索引, len(self.数据), 4):
            偏移 = struct.unpack_from("<I", self.数据, 位置)[0]
            if 偏移 < 4:
                raise ValueError("资源与文件头重叠")
            self.api_检查范围(偏移, 16, 索引)
            项 = 资源项_类(偏移, *struct.unpack_from("<4I", self.数据, 偏移))
            self.api_检查范围(偏移 + 16, 项.存储长度, 索引)
            if 项.图形长度:
                self.api_检查范围(项.图形偏移, 项.图形长度, 项.解码长度)
            self.条目.append(项)

    @staticmethod
    def api_检查范围(
        arg_偏移: int,
        arg_长度: int,
        arg_总长: int,
    ) -> None:
        if arg_偏移 < 0 or arg_长度 < 0 or arg_偏移 + arg_长度 > arg_总长:
            raise ValueError("资源截断或偏移越界")

    def api_解码(self, arg_索引: int, arg_上限: int = 256 * 1024 * 1024) -> bytes:
        if not 0 <= arg_索引 < len(self.条目):
            raise IndexError("MKF 条目越界")
        项 = self.条目[arg_索引]
        if 项.解码长度 > arg_上限:
            raise ValueError("解码长度超过分配上限")
        数据 = self.数据[项.偏移 + 16 : 项.偏移 + 16 + 项.存储长度]
        if 项.解码长度 == 项.存储长度:
            return 数据
        return 解压器_类.api_解压(数据, 项.解码长度, arg_上限)
