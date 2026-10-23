# SPDX-License-Identifier: GPL-3.0-or-later
# 边界依据固定 C++ tests/numeric_tests.cpp；不依赖主机 long double。
# ◑ 导入
import pytest

from rich4.numeric import 扩展数_类


# ◕ 功能
def test_保留超过binary64的有效位但在x87精度舍入() -> None:
    一 = 扩展数_类.api_从值(1)
    大 = 扩展数_类.api_从值(2**53)
    assert ((大 + 一) - 大).api_整数() == 1
    assert (大 + 一).api_双精度() == 2**53
    assert (大 + 扩展数_类.api_从值(3)).api_双精度() == 2**53 + 4
    巨 = 扩展数_类.api_从值(2**64)
    assert ((巨 + 一) - 巨).api_整数() == 0
    assert ((巨 + 扩展数_类.api_从值(3)) - 巨).api_整数() == 4


def test_落盘中点上下和偶数规则() -> None:
    一 = 扩展数_类.api_从值(1)
    半 = 一 + 扩展数_类.api_从值(2**-24)
    末位 = 扩展数_类.api_从值(2**-63)
    assert (半 + 末位).api_单精度位() == 0x3F800001
    assert (半 - 末位).api_单精度位() == 0x3F800000
    双半 = 一 + 扩展数_类.api_从值(2**-53)
    assert (双半 + 末位).api_双精度位() == 0x3FF0000000000001


def test_截断溢出零与除法() -> None:
    assert (-扩展数_类.api_从值(100.9)).api_整数() == -100
    assert 扩展数_类.api_从值(2147483648).api_整数() == -2147483648
    assert 扩展数_类.api_从值(-2147483648).api_整数() == -2147483648
    assert 扩展数_类.api_从值(1e-300).api_整数() == 0
    assert (扩展数_类.api_从值(1) / 扩展数_类.api_从值(3)).api_单精度位() == 0x3EAAAAAB
    with pytest.raises(ValueError, match="除零"):
        扩展数_类.api_从值(1) / 扩展数_类.api_从值(0)
    with pytest.raises(ValueError):
        扩展数_类.api_从值(float("nan"))
    with pytest.raises(ValueError):
        扩展数_类.api_从值(1e-300).api_单精度()


def test_区分非有限输入与正常浮点落盘范围错误() -> None:
    from rich4.numeric import 数值范围错误_类

    with pytest.raises(数值范围错误_类):
        扩展数_类.api_从值(1e-300).api_单精度()
