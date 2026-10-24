# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_number_pad import _宿

from rich4.board_models import 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.cards import 卡片用法_类, 卡片目标_类, 目标种类_类
from rich4.game_types import 决策_类, 决策位置_类, 决策种类_类, 决策选项_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.item_targets import 地图目标绘制_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_重叠目标命中按当前手指最近中心而非注册顺序(字体: 字体_类) -> None:
    框, 选 = _宿(字体, []).框, []
    相机 = 相机_类((16, 16))
    决 = 决策_类(
        决策种类_类.行动目标,
        0,
        选项=[
            决策选项_类("甲", 1, 决策位置_类(16, 16)),
            决策选项_类("乙", 2, 决策位置_类(48, 16)),
            决策选项_类("取消", 0),
        ],
    )
    名 = 地图目标绘制_类.api_绘制(框, 决, 相机, 0, 选.append, 1, 0)
    assert 名 == "target-tool-1-selected" and len(框.按钮) == 2
    框.指针x, 框.指针y = 棋盘投影_类.api_投影((48, 16), 相机)
    框.按钮[0].动作()
    assert 选 == [1]


def test_遥控骰原面按钮回答真实决策并启动相应步数(字体: 字体_类) -> None:
    屏, 会 = 物品屏幕_类(), 会话样本()
    会._玩家().道具[7] = 1
    assert 会.api_用道具(8)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    屏.api_画遥控骰(框, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 213).动作()
    assert 会.骰面 == [4] and 会.剩余步 == 4 and 会._玩家().道具[7] == 0


def test_抢夺先选中再确认才经真实会话转移卡片(字体: 字体_类) -> None:
    屏, 会 = 物品屏幕_类(), 会话样本()
    会._玩家().卡片[0] = 13
    会.世界.玩家[1].记录.卡片[0] = 4
    assert 会.api_用卡(卡片用法_类(13, 卡片目标_类(目标种类_类.角色, 1)))
    决 = 会.待决策
    index = next(i for i, o in enumerate(决.选项) if o.值 == (int(目标种类_类.卡片) << 16) | 4)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    屏.api_画抢夺(框, 会, 决, 宿)
    next(b for b in 框.按钮 if b.编号 == 210 + index).动作()
    assert 屏._抢夺选择 == index and 会.世界.玩家[1].记录.卡片[0] == 4
    框.按钮.clear()
    屏.api_画抢夺(框, 会, 决, 宿)
    next(b for b in 框.按钮 if b.编号 == 210 + index).动作()
    assert 屏._抢夺选择 is None and 4 in 会._玩家().卡片
    assert 4 not in 会.世界.玩家[1].记录.卡片 and 13 not in 会._玩家().卡片
