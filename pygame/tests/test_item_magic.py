# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_item_shop import 商店台词夹具_类
from test_number_pad import _宿

from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_电脑施法无效参数不覆盖原演出而重置会清除() -> None:
    屏 = 物品屏幕_类()
    屏.api_开始电脑施法(3, 10)
    原 = 屏._施法
    屏.api_开始电脑施法(-1, 10)
    屏.api_开始电脑施法(3, 12)
    assert 屏.api_电脑施法中() and 屏._施法 is 原
    屏.api_重置()
    assert not 屏.api_电脑施法中()


def test_人类施法哨兵按参考保留直到点击跳过(字体: 字体_类) -> None:
    屏, 会, 答, 声, 配 = 物品屏幕_类(商店台词夹具_类()), 会话样本(), [], [], []
    屏.声音 = 声.append
    屏.语音 = lambda n, q: 配.append((n, q))
    决 = 决策_类(决策种类_类.魔法效果, 0, 选项=[决策选项_类("", i) for i in range(12)])
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, lambda i: 答.append(i) or True)
    屏._魔法.类别 = 3
    屏._魔法.活跃 = True
    框.时钟 = 100
    屏.api_画魔法(框, 会, 决, 宿)
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    assert 屏._魔法.选中 == 0 and not 答
    框.按钮.clear()
    屏.api_画魔法(框, 会, 决, 宿)
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    assert 屏._魔法.施法时 == 1 and not 答
    框.按钮.clear()
    框.时钟 = 20000
    屏.api_画魔法(框, 会, 决, 宿)
    assert 屏._魔法.施法时 == 1 and 屏.截图名 == "magic-casting" and not 答
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    assert 答 == [0] and 声 == [39] and not 屏._魔法.活跃
    assert 配 == [(49, False), (40, True), (41, False)]
