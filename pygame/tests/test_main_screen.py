# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from pathlib import Path

from test_game import 会话样本

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.main_screen import 主屏幕_类
from rich4.main_text import 主屏字样_类, 主屏绘字_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_开发预设按原atoi和unsigned处理并保留默认() -> None:
    屏 = 主屏幕_类("view=2,tab=3,calendar=1,map=1,ignored=4")
    assert (屏.视图, 屏.日历, 屏.全图, 屏.页签) == (2, 1, True, [3] * 9)
    assert 主屏幕_类("view=-1").视图 == 0
    assert 主屏幕_类("view=nonsense").视图 == 0
    assert 主屏幕_类("view=٤").视图 == 0
    assert 主屏幕_类("view=\u00a02").视图 == 0
    assert 主屏幕_类().视图 == 1


def test_显示覆盖为零仍遮挡真实GO且显示槽位按原上界夹紧() -> None:
    会, 屏 = 会话样本(), 主屏幕_类()
    assert 屏.api_显示人类回合(会)
    屏.api_显示玩家(0)
    assert not 屏.api_显示人类回合(会)
    屏.api_显示玩家(999)
    assert 屏.api_显示槽位(会.世界) == len(会.世界.玩家) - 1
    屏.api_显示玩家(None)
    assert 屏.api_显示人类回合(会)


def test_GO轻点待释放才掷而拖拽取消轻点并夹紧原边界() -> None:
    屏, 调用 = 主屏幕_类(), []
    屏._拖拽, 屏._按点 = (5, 7), (10, 10)
    屏._待掷 = lambda: 调用.append(1)
    屏.api_指针移动(13, 13, True)
    屏.api_指针释放(13, 13, False)
    assert 调用 == [1] and 屏._待掷 is None
    屏._拖拽, 屏._按点 = (5, 7), (10, 10)
    屏._待掷 = lambda: 调用.append(2)
    屏.api_指针移动(2000, -100, True)
    assert (屏.GOx, 屏.GOy) == (568, 0)
    屏.api_指针释放(2000, -100, False)
    assert 调用 == [1]


def test_小地图拖拽坐标与右键恢复跟随() -> None:
    屏 = 主屏幕_类()
    屏._小图拖拽 = True
    屏.api_指针移动(640, 480, True)
    assert 屏.api_相机中心((100, 100)) == (2084, 2084)
    屏.api_指针释放(500, 300, True)
    assert 屏.api_相机中心((100, 100)) == (100, 100)
    屏.api_切视图()
    屏.api_切视图()
    assert 屏.视图 == 0


def test_主屏墨框对齐使用实际单色字形与原间距(字体: 字体_类) -> None:
    框 = 画框_类(图像_类(120, 100, [0] * 12000), 美术_类(Path("unused")), 字体, [])
    for 对齐 in range(4):
        主屏绘字_类.api_文字(框, "AB", 50, 50, 对齐, 主屏字样_类(18, 32767, 1))
    assert any(框.画布.像素)


def test_主屏布局的描框与色章转发不额外绑定屏幕实例() -> None:
    屏, 图 = 主屏幕_类(), 图像_类(4, 4, [0] * 16)
    屏._框线(图, (0, 0, 2, 2), 7, (0, 0, 4, 4))
    屏._色章(图, 图像_类(1, 1, [1]), 3, 3, 9, (0, 0, 4, 4))
    assert 图.像素 == [7, 7, 0, 0, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9]
