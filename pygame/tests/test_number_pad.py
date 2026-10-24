# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_message_overlay import 消息素材夹具_类

from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.number_pad import 数字板_类
from rich4.screen_draw import 屏幕宿主_类


# ◕ 功能
def _宿(arg_字体: 字体_类, arg_声音: list[int]) -> 屏幕宿主_类:
    return 屏幕宿主_类(
        画框_类(图像_类(640, 480, [9] * 307200), 消息素材夹具_类(), arg_字体, []), arg_声音.append
    )


def test_数字键稳定编号与只接收ASCII且不超过九位输入(字体: 字体_类) -> None:
    pad, 声 = 数字板_类(), []
    宿 = _宿(字体, 声)
    pad.api_打开(2147483647, lambda n: None)
    for c in "1234567890１":
        pad.api_键(宿, c)
    assert pad.api_数字() == "123456789" and pad.api_值() == 123456789
    assert 声 == [7] * 10
    assert [pad.api_数字号(i) for i in range(10)] == [
        905,
        913,
        914,
        915,
        910,
        911,
        912,
        907,
        908,
        909,
    ]


def test_MAX可显示十位上限而中点量尺依原取十七分之三十三(字体: 字体_类) -> None:
    pad, 声 = 数字板_类(), []
    宿 = _宿(字体, 声)
    pad.api_打开(2147483647, lambda n: None)
    pad.api_键(宿, "m")
    assert pad.api_值() == 2147483647 and pad.api_数字() == "2147483647"
    pad.api_键(宿, "h")
    assert pad.api_值() == 2147483647 * 17 // 33 and 声 == [7, 9]
    pad.api_键(宿, "c")
    pad.api_键(宿, "\b")
    assert pad.api_数字() == "0"


def test_输入钳制上限且确认回调先取出允许重入开启下一块数字板(字体: 字体_类) -> None:
    pad, 声, 结果 = 数字板_类(), [], []
    宿 = _宿(字体, 声)

    def 完成(arg_数: int) -> None:
        结果.append(arg_数)
        pad.api_打开(50, 结果.append)

    pad.api_打开(42, 完成)
    for c in "999":
        pad.api_键(宿, c)
    assert pad.api_值() == 42
    pad.api_键(宿, "\r")
    assert 结果 == [42] and pad.api_活跃() and pad.api_上限() == 50
    pad.api_取消(宿)
    assert 结果 == [42, 0] and not pad.api_活跃() and 声[-1] == 4
    pad.api_取消(宿)
    assert 结果 == [42, 0]


def test_缩放仅影响原几何打开时定位且下一键建议不发出假输入() -> None:
    pad = 数字板_类()
    pad.api_缩放(99)
    pad.api_打开(-5, lambda n: None)
    assert pad.api_比例() == 2 and pad.api_提示顶() == 2 and (pad._x, pad._y) == (192, 92)
    assert pad.api_上限() == 0 and pad.api_下一键(99) == 903
    pad.api_打开(1000, lambda n: None)
    assert pad.api_下一键(123) == 913 and pad.api_数字() == "0"
    pad.api_关闭()
    assert not pad.api_活跃()
