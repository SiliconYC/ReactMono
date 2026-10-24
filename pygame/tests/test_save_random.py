# SPDX-License-Identifier: GPL-3.0-or-later
# 原Application::load使用uint32流提取；不是Python整词数字/UTF-8协议。
# ◑ 导入
from pathlib import Path

import pytest

from rich4.save_random import 随机旁车_类


# ◕ 功能
@pytest.mark.parametrize(
    "arg_数据,arg_种子",
    (
        (b"RICH4-RNG-1 0", 0),
        (b"RICH4-RNG-1 1", 1),
        (b"RICH4-RNG-1 4294967295", 0xFFFFFFFF),
        (b"RICH4-RNG-1 4294967296", 123),
        (b"RICH4-RNG-1 -1", 0xFFFFFFFF),
        (b"RICH4-RNG-1 -2", 0xFFFFFFFE),
        (b"RICH4-RNG-1 -4294967295", 1),
        (b"RICH4-RNG-1 -4294967296", 123),
        (b"RICH4-RNG-1 +17", 17),
        (b"RICH4-RNG-1 1junk", 1),
        (b"RICH4-RNG-1 0x10", 0),
        (b"RICH4-RNG-1 +bad", 123),
        (b"RICH4-RNG-1 --1", 123),
        (b"RICH4-RNG-1 18446744073709551615", 123),
        (b"RICH4-RNG-1 12\xff", 12),
        (b"RICH4-RNG-1 \xff", 123),
        (b"RICH4-RNG-1 \0", 123),
        (b"RICH4-RNG-1 17 42", 17),
        (b" \t\v\r\nRICH4-RNG-1\f 23\n", 23),
        (b"RICH4-RNG-1", 123),
        (b"RICH4-RNG-2 17", 123),
        (b"", 123),
        (b"\xff", 123),
        (b"RICH4-RNG-1 " + b"0" * 5000 + b"17", 17),
    ),
    ids=[str(i) for i in range(24)],
)
def test_原uint32流提取与拒绝边界(arg_数据: bytes, arg_种子: int) -> None:
    assert 随机旁车_类.api_解码(arg_数据, 123) == arg_种子


def test_缺失或不可读旁车不阻止有效DAT读取(tmp_path: Path) -> None:
    assert 随机旁车_类.api_读取(tmp_path / "missing", 999) == 999
    assert 随机旁车_类.api_读取(tmp_path, 999) == 999
    path = tmp_path / "valid.rng"
    path.write_bytes(b"RICH4-RNG-1 14\xff")
    assert 随机旁车_类.api_读取(path, 999) == 14
