# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_number_pad import _宿

from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_正式分发只把原七选项形状识别为遥控骰并运行真实规则(字体: 字体_类) -> None:
    屏, 会 = 物品屏幕_类(), 会话样本()
    会._玩家().道具[7] = 1
    assert 会.api_用道具(8)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    assert 屏.api_画决策(框, 会, 宿) and 屏.截图名 == "remote-dice"
    next(b for b in 框.按钮 if b.编号 == 213).动作()
    assert 会.骰面 == [4] and 会._玩家().道具[7] == 0


def test_不支持决策清访问但按原不清抢夺选择(字体: 字体_类) -> None:
    屏, 会 = 物品屏幕_类(), 会话样本()
    屏._店.活跃 = 屏._魔法.活跃 = 屏._救援.活跃 = True
    屏._已说, 屏._抢夺选择 = "old", 0
    会.待决策 = 决策_类(决策种类_类.购地, 0)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    assert not 屏.api_画决策(框, 会, 宿)
    assert not 屏._店.活跃 and not 屏._魔法.活跃 and not 屏._救援.活跃 and not 屏._已说
    assert 屏._抢夺选择 == 0
    会.待决策 = 决策_类(
        决策种类_类.行动目标, 0, 选项=[决策选项_类("", i) for i in (1, 2, 3, 4, 5, 9, 0)]
    )
    assert not 屏.api_画决策(框, 会, 宿) and 屏._抢夺选择 is None
