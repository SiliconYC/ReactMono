# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from pathlib import Path

import pytest

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
def test_画框图片原点抵消与原Frame一致且掩码仍有效(字体: 字体_类) -> None:
    画 = 图像_类(5, 4, [9] * 20)
    框 = 画框_类(画, 美术_类(Path("unused")), 字体, [])
    框.api_图片(图像_类(2, 1, [0, 12], 3, -2, b"\0\1"), 1, 2)
    assert 画.像素[10:15] == [9, 9, 12, 9, 9]
    assert (框.指针x, 框.指针y, 框.按下, 框.时钟) == (-1, -1, False, 0)


def test_按钮共用原列表并保留禁用声音和回调(字体: 字体_类) -> None:
    按钮, 动作 = [], []
    框 = 画框_类(图像_类(100, 40, [0] * 4000), 美术_类(Path("unused")), 字体, 按钮)
    框.api_按钮(71, (0, 0, 60, 30), "保存", lambda: 动作.append(71), False)
    assert 框.按钮 is 按钮
    assert len(按钮) == 1 and 按钮[0].编号 == 71 and not 按钮[0].启用
    assert 按钮[0].点击声音
    按钮[0].动作()
    assert 动作 == [71]
    assert any(框.画布.像素)


def test_宿主命中先播指定声音再执行动作且关闭通用点击音(字体: 字体_类) -> None:
    框 = 画框_类(图像_类(1, 1, [0]), 美术_类(Path("unused")), 字体, [])
    记录 = []
    宿 = 屏幕宿主_类(框, lambda n: 记录.append(n))
    屏幕绘图_类.api_命中(宿, 5, (0, 0, 4, 4), 3, lambda: 记录.append(99))
    assert not 框.按钮[0].点击声音
    框.按钮[0].动作()
    assert 记录 == [3, 99]


def test_按下斜面使用倒序复制并只暗化顶和左() -> None:
    画 = 图像_类(3, 3, [32767] * 9)
    画.像素[0] = 0
    屏幕绘图_类.api_按下斜面(画, (0, 0, 3, 3))
    assert 画.像素 == [0, 15855, 15855, 15855, 0, 32767, 15855, 32767, 32767]


def test_局部图像复制按源局部框裁切而非整个精灵(字体: 字体_类) -> None:
    画 = 图像_类(4, 2, [9] * 8)
    图 = 图像_类(3, 2, [1, 2, 3, 4, 5, 6], -7, 8)
    屏幕绘图_类.api_局部(画, 图, (1, 0, 3, 2), 0, 0)
    assert 画.像素 == [2, 3, 9, 9, 5, 6, 9, 9]


@pytest.mark.parametrize("对齐", range(8))
def test_八种文字对齐均绘制实际字体且空行保留高度(字体: 字体_类, 对齐: int) -> None:
    框 = 画框_类(图像_类(120, 100, [1234] * 12000), 美术_类(Path("unused")), 字体, [])
    屏幕绘图_类.api_文字(框, "AB\n\nC", 60, 50, 对齐, 屏幕字样_类())
    assert any(v != 1234 for v in 框.画布.像素)
    assert 屏幕绘图_类.api_测量(框, "AB\n\nC", 屏幕字样_类()) > 1
