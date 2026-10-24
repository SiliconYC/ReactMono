# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿

from rich4.endgame_screen import 结局屏幕_类
from rich4.endgame_types import 结局动作_类, 过关资料_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_倒数等语音后才开始且确认与真实影片完成分开即时模式不播放(字体: 字体_类) -> None:
    s, sounds, calls = 结局屏幕_类(), [], []
    h = _宿(字体, sounds)
    a = 结局动作_类(lambda: calls.append("agree"), lambda ok: calls.append(ok))
    s.api_再玩()
    h.框.时钟 = 100
    s.api_绘制(h, True, a)
    assert not s._已开始 and s.api_退出按钮() == 1100
    h.框.时钟 = 1000
    s.api_绘制(h, False, a)
    assert s._倒数毫秒 == 0
    h.框.按钮[0].动作()
    assert calls == ["agree"] and s.api_退出按钮() == -1
    s.api_绘制(h, True, a)
    assert s.api_活跃()
    h.即时 = True
    s.api_绘制(h, False, a)
    assert not s.api_活跃() and calls == ["agree", True] and sounds == []


def test_过关私有线性随机独立且面板先落地才给未清地图入口() -> None:
    s = 结局屏幕_类()
    s.api_过关(过关资料_类(已清=5, 种子=1))
    assert s.api_退出按钮() == -1
    s._已开始 = True
    for _ in range(24):
        s._过关步()
    assert s._面板y == 360 and s.api_退出按钮() == 1102
    assert s._随机状态 == 48271 and s._跑y == 48271 % 360 + 100
    s._已选, s._选余步 = 1, 10
    for _ in range(9):
        s._过关步()
    assert not s._离开
    s._过关步()
    assert s._离开 and s.api_退出按钮() == -1
    s.api_关闭()
    assert s._随机状态 == 48271 and s._面板y == -80
