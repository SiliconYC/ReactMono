# ◑ 导入
import struct

import pytest

from rich4.assets import 解压器_类, 资源包_类


# ◕ 功能
def test_读取真实索引布局而非传统首部偏移表() -> None:
    数据 = struct.pack("<I4I", 23, 3, 3, 0, 0) + b"abc" + struct.pack("<I", 4)
    包 = 资源包_类(数据)
    assert 包.api_解码(0) == b"abc"
    with pytest.raises(IndexError):
        包.api_解码(-1)
    with pytest.raises(ValueError, match="上限"):
        包.api_解码(0, 2)


@pytest.mark.parametrize("arg_数据", [b"", struct.pack("<I", 3), struct.pack("<II", 4, 0)])
def test_拒绝损坏索引(arg_数据: bytes) -> None:
    with pytest.raises(ValueError):
        资源包_类(arg_数据)


def test_压缩流截断不能补零() -> None:
    with pytest.raises(ValueError, match="截断"):
        解压器_类.api_解压(b"", 1)


def test_已知自适应树首符号() -> None:
    # 321 个等频叶的初始树；字面量 0 的根路径 LSB-first 为 101111110。
    assert 解压器_类.api_解压(bytes([0xFD, 0]), 1) == b"\x00"
