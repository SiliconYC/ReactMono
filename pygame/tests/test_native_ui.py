# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入


from rich4.graphics import 图像_类
from rich4.native_ui import 原生界面_类, 字体_类


# ◕ 功能
def test_原UTF8解析保留过长编码与坏续字节的原消费边界() -> None:
    assert 原生界面_类.api_码点(b"\xc0\x80\xffA\x80") == [0, 63, 65, 63]
    assert 原生界面_类.api_码点("大富翁4") == [22823, 23500, 32705, 52]


def test_坏Big5前导与尾字节整体替换而非遗留ASCII尾字节() -> None:
    assert 原生界面_类.api_繁中(b"A\x81Bz") == "A?z"
    assert 原生界面_类.api_繁中(b"\x81") == "?"
    assert 原生界面_类.api_繁中(b"A\0B") == "A\0B"


def test_CP950不接受Python额外纳入的Big5日文区域() -> None:
    assert 原生界面_类.api_繁中(b"A\xc6\xa1z") == "A?z"
    assert 原生界面_类.api_繁中(b"\xc7\xfc") == "?"


def test_填充和边框保持原半开矩形与裁切() -> None:
    画 = 图像_类(4, 4, [0] * 16)
    原生界面_类.api_填充(画, (-1, -1, 2, 2), 5)
    原生界面_类.api_边框(画, (1, 1, 4, 4), 9)
    assert 画.像素 == [5, 5, 0, 0, 5, 9, 9, 9, 0, 9, 0, 9, 0, 9, 9, 9]
    assert 原生界面_类.api_包含((1, 1, 4, 4), 3, 3)
    assert not 原生界面_类.api_包含((1, 1, 4, 4), 4, 3)


def test_原单色字体阈值56保持灰度字形尺寸和前进量(字体: 字体_类) -> None:
    灰 = 字体._字形(ord("A"), 16, False)
    单 = 字体._字形(ord("A"), 16, True)
    assert 灰.宽 > 0 and 灰.高 > 0 and 灰.前进 > 0 and max(灰.遮罩) >= 56
    assert (灰.宽, 灰.高, 灰.左, 灰.顶, 灰.前进) == (单.宽, 单.高, 单.左, 单.顶, 单.前进)
    assert 单.遮罩 == bytes(255 if v >= 56 else 0 for v in 灰.遮罩)


def test_字体裁切与完整画布相同区域像素完全相同(字体: 字体_类) -> None:
    大, 小 = 图像_类(80, 80, [0x4210] * 6400), 图像_类(20, 20, [0x4210] * 400)
    字体.api_绘制(大, "Ag", 0, 0, 16, 0x7FFF)
    字体.api_绘制(小, "Ag", -3, -2, 16, 0x7FFF)
    assert any(值 != 0x4210 for 值 in 大.像素)
    assert 小.像素 == [大.像素[y * 80 + x] for y in range(2, 22) for x in range(3, 23)]


def test_原自动换行等价于相同位置显式换行(字体: 字体_类) -> None:
    a, b = 图像_类(60, 60, [0] * 3600), 图像_类(60, 60, [0] * 3600)
    字体.api_绘制(a, "AA", 0, 0, 16, 0x7FFF, 字体.api_测量("A", 16))
    字体.api_绘制(b, "A\nA", 0, 0, 16, 0x7FFF)
    assert a.像素 == b.像素


def test_单色黑字保留真实墨迹且不修改目标透明遮罩(字体: 字体_类) -> None:
    遮罩 = bytes(i % 2 for i in range(800))
    图 = 图像_类(40, 20, [32767] * 800, 不透明=遮罩)
    字体.api_绘制(图, "A", 0, 0, 16, 0, 0, True)
    assert 0 in 图.像素 and set(图.像素) <= {0, 32767}
    assert 图.不透明 == 遮罩


def test_单色裁切只覆盖墨迹并清除前景的RGB555最高位(字体: 字体_类) -> None:
    图 = 图像_类(8, 8, [0x8000] * 64)
    字体.api_绘制(图, "Ag", -3, -3, 16, 65535, 0, True)
    assert 32767 in 图.像素 and 0x8000 in 图.像素
    assert set(图.像素) == {32767, 0x8000}
