# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿
from test_world import 合成地图

from rich4.auction_room_screen import 拍卖室_类
from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.native_ui import 字体_类
from rich4.world import 世界_类


# ◕ 功能
def test_出价等待原五帧后才回答也可二次点击提前结束(字体: 字体_类) -> None:
    房, 世, 答, 声 = 拍卖室_类(), 世界_类.api_从地图(合成地图()), [], []
    决 = 决策_类(决策种类_类.拍卖, 0, 地产=2001, 金额=1000, 选项=[决策选项_类("加价", 1)])
    宿 = _宿(字体, 声)
    宿.框.时钟 = 100
    房.api_绘制(宿, 世, 决, 答.append)
    next(b for b in 宿.框.按钮 if b.编号 == 210).动作()
    assert 房._出价 is not None and not 答 and 声 == [1, 29]
    宿.框.时钟 = 200
    宿.框.按钮.clear()
    房.api_绘制(宿, 世, 决, 答.append)
    assert next(b for b in 宿.框.按钮 if b.编号 == 210).区域 == (0, 0, 640, 480)
    宿.框.时钟 = 1199
    宿.框.按钮.clear()
    房.api_绘制(宿, 世, 决, 答.append)
    assert not 答
    宿.框.时钟 = 1200
    宿.框.按钮.clear()
    房.api_绘制(宿, 世, 决, 答.append)
    assert 答 == [0] and 房._出价 is None and not 宿.框.按钮


def test_成交零时钟依原无符号差立即退休而重置同时清两种演出(字体: 字体_类) -> None:
    房, 世, 声 = 拍卖室_类(), 世界_类.api_从地图(合成地图()), []
    房.api_成交(0, 1000, 2001)
    assert 房.api_成交中()
    房.api_画成交(_宿(字体, 声), 世)
    assert not 房.api_成交中() and not 声
    房.api_成交(0, 1000, 2001)
    房.api_重置()
    assert not 房.api_成交中() and 房._出价 is None
