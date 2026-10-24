# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿

from rich4.native_ui import 字体_类
from rich4.new_game_screen import 新局屏幕_类


# ◕ 功能
def test_重新打开保留设置但清人选忙碌下拉和私有补位随机流() -> None:
    屏 = 新局屏幕_类()
    屏._值 = [0, 3, 2, 5, 0, 0]
    屏._人选 = [10, 3]
    屏._填充, 屏._离开, 屏._下拉 = True, True, 2
    屏.api_打开(1, 7, 1)
    assert 屏.api_地图() == 3 and 屏.api_阶段() == 1 and not 屏.api_忙()
    assert 屏.api_人选() == () and 屏._下拉 == -1 and 屏._值 == [0, 3, 2, 5, 0, 0]
    屏._人选 = [10]
    屏._补一人()
    assert 屏.api_人选() == (10, 0)


def test_满员不消费补位随机且选择保留人类数交通和资金租期() -> None:
    屏 = 新局屏幕_类()
    屏.api_打开(1, 2, 1)
    屏._值, 屏._人选, 屏._人类数 = [0, 3, 2, 5, 0, 0], [10, 3], 1
    词, 位 = 屏._随机._词.copy(), 屏._随机._位
    屏._补一人()
    assert 屏._随机._词 == 词 and 屏._随机._位 == 位
    选 = 屏._选择()
    assert (选.阶段, 选.地图, 选.资金, 选.租期) == (1, 2, 50000, 5)
    assert [(p.角色, p.控制, p.交通) for p in 选.玩家] == [(10, 1, 2), (3, 2, 2)]


def test_取消先关下拉忙碌时不退出闲置才退出但都请求取消声(字体: 字体_类) -> None:
    屏, 声, 关 = 新局屏幕_类(), [], []
    宿 = _宿(字体, 声)
    屏._下拉 = 1
    屏.api_取消(宿, lambda: 关.append(True))
    屏._填充 = True
    屏.api_取消(宿, lambda: 关.append(True))
    assert not 关 and 声 == [4, 4] and 屏._下拉 == -1
    屏._填充 = False
    屏.api_取消(宿, lambda: 关.append(True))
    assert 关 == [True] and 声 == [4, 4, 4]
