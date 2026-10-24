# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import struct

import pytest

from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
def _程序(arg_内容: bytes) -> bytes:
    头 = bytearray(512)
    头[:2] = b"MZ"
    struct.pack_into("<I", 头, 60, 128)
    头[128:132] = b"PE\0\0"
    struct.pack_into("<HH", 头, 132, 0x14C, 1)
    struct.pack_into("<H", 头, 148, 224)
    struct.pack_into("<H", 头, 152, 0x10B)
    struct.pack_into("<I", 头, 180, 0x400000)
    # 实际Rich4的VirtualSize为零，定位必须依据有文件内容的RawSize。
    struct.pack_into("<8sIIII", 头, 376, b"DGROUP", 0, 0x1000, len(arg_内容), 512)
    return bytes(头) + arg_内容


def test_PE零虚拟尺寸仍按原始区定位并读取指针和空槽() -> None:
    程序 = 原版程序_类(_程序(struct.pack("<II", 0x401008, 0) + b"#0001ABC\0"))
    assert 程序.api_指针表(0x401000, 2) == (0x401008, 0)
    assert 程序.api_原串(0x401008) == b"#0001ABC"
    assert 程序.api_定位(0x401000, 8) == 512


def test_PE无效签名截断原始区和未映射指针拒绝而不执行() -> None:
    for 数据 in (b"MZ", b"not an exe", _程序(b"AB\0")[:-1]):
        with pytest.raises(ValueError):
            原版程序_类(数据)
    程序 = 原版程序_类(_程序(b"AB\0"))
    for 地址, 长 in ((0x400FFF, 1), (0x401002, 2), (0, 0), (0x401000, -1)):
        with pytest.raises(ValueError):
            程序.api_定位(地址, 长)


def test_原始字符串必须在所属原始区结束之前遇到NUL() -> None:
    with pytest.raises(ValueError, match="NUL"):
        原版程序_类(_程序(b"ABC")).api_原串(0x401000)


def test_语音索引保留编号零及相同重复文本并规范化标点() -> None:
    数据 = b"#0000A\xa1\xe3B\xa1\x4f\0#0000A\xa1\xe3B\xa1\x4f\0#0002C\0"
    文 = 原版文字_类(原版程序_类(_程序(数据)))
    assert 文.api_配音(0).声音 == 0
    assert 文.api_配音(0).文字 == "A～B．"
    assert 文.api_配音(2).文字 == "C"
    with pytest.raises(KeyError):
        文.api_配音(1)


def test_仅两条指定卡台词删除无Unicode映射的商业自造字() -> None:
    数据 = b"#0752A\x9d\xddB\0#0753A\x9d\xddB\0#0754A\x9d\xddB\0"
    文 = 原版文字_类(原版程序_类(_程序(数据)))
    assert 文.api_配音(752).文字 == "AB"
    assert 文.api_配音(753).文字 == "AB"
    assert 文.api_配音(754).文字 == "A?B"


def test_相同语音编号对应不同文本必须拒绝() -> None:
    with pytest.raises(ValueError, match="重复"):
        原版文字_类(原版程序_类(_程序(b"#0002A\0#0002B\0")))


def test_重定位区偶然出现的数字前缀不参与商业文字索引() -> None:
    数据 = bytearray(_程序(b"#0002A\0"))
    struct.pack_into("<H", 数据, 134, 2)
    struct.pack_into("<8sIIII", 数据, 416, b".reloc", 0, 0x2000, 8, len(数据))
    数据 += b"#0002BB\0"
    文 = 原版文字_类(原版程序_类(bytes(数据)))
    assert 文.api_配音(2).文字 == "A"


def test_银行89的参考界面变体显式选择而不覆盖原文() -> None:
    原 = "#0089ABCD要\nW".encode("cp950") + b"\0"
    文 = 原版文字_类(原版程序_类(_程序(原)))
    assert 文.api_配音(89).文字 == "ABCD要\nW"
    assert 文.api_配音(89, 1).文字 == "ABCD預備\nW"
    with pytest.raises(ValueError):
        文.api_配音(89, 2)


def test_角色台词表越界不环绕且空指针不变成假台词() -> None:
    偏 = 0x48084A - 0x401000
    数据 = bytearray(偏 + 324 * 4)
    数据[:8] = b"#1050AB\0"
    struct.pack_into("<I", 数据, 偏, 0x401000)
    文 = 原版文字_类(原版程序_类(_程序(bytes(数据))))
    assert 文.api_台词("event", 0, 0).文字 == "AB"
    assert 文.api_台词("event", 0, 1) is None
    with pytest.raises(IndexError):
        文.api_台词("event", 12, 0)
    with pytest.raises(IndexError):
        文.api_台词("tool", 0, 26)
    with pytest.raises(KeyError):
        文.api_台词("unknown", 0, 0)


def test_外部股票标签费名与新闻标题只读索引保留原文() -> None:
    数据 = bytearray(0x90000)

    def 写(arg_地址: int, arg_数据: bytes) -> None:
        偏 = arg_地址 - 0x401000
        数据[偏 : 偏 + len(arg_数据)] = arg_数据

    写(0x46677D, b"STOCK\0")
    写(0x47517C, struct.pack("<4I", 0x401010, 0x401020, 0x401030, 0x401040))
    写(0x475ED8, struct.pack("<6I", *(0x401050 + i * 8 for i in range(6))))
    for i in range(4):
        写(0x401010 + i * 16, f"F{i}\0".encode())
    for i in range(6):
        写(0x401050 + i * 8, f"N{i}\0".encode())
    文 = 原版文字_类(原版程序_类(_程序(bytes(数据))))
    assert 文.api_股票(0) == "STOCK"
    assert [文.api_费名(i) for i in range(4)] == ["F0", "F1", "F2", "F3"]
    assert [文.api_新闻标题(i) for i in range(6)] == ["N0", "N1", "N2", "N3", "N4", "N5"]
    assert 文.api_原文(0x401010) == "F0"
    for 操作, 值 in ((文.api_股票, -1), (文.api_股票, 96), (文.api_费名, 4), (文.api_新闻标题, 6)):
        with pytest.raises(IndexError):
            操作(值)
