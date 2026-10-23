# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import struct
from pathlib import Path

from rich4.artwork import 美术_类


# ◕ 功能
def test_图帧计数只解析元数据不要求支持像素布局(tmp_path: Path) -> None:
    库 = 美术_类(tmp_path)
    库.数据["p", 0] = struct.pack("<4sIIhhhhI", b"SMP\0", 1, 24, 2, 2, 0, 0, 0)
    assert 库.api_帧数("p", 0) == 1
    库.数据["p", 1] = b"not-sprite"
    assert 库.api_帧数("p", 1) == 0


def test_原图按15位读取截断忽略尾字节并补黑(tmp_path: Path) -> None:
    库 = 美术_类(tmp_path)
    库.数据["p", 92] = bytes([255, 255, 0, 128, 7])
    assert 库.api_原图("p", 92, 2, 2).像素 == [32767, 0, 0, 0]
