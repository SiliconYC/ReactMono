# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_number_pad import _宿

from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_ui import 字体_类
from rich4.original_text import 台词_类
from rich4.services import 服务_类


# ◕ 功能
class 商店台词夹具_类:
    """
    仅流程单测的语音索引文字，真实素材另作直接CPP画布对照。

    更新日志：
    2026.10.24 - 不把占位文字用于正式游戏或图形验收。
    """

    def api_配音(self, arg_号: int) -> 台词_类:
        return 台词_类(arg_号, f"voice{arg_号}")


def test_商店重放显示选项只切合法货架且未选中为空() -> None:
    屏 = 物品屏幕_类()
    assert 屏.api_商店待选() is None
    assert 屏.api_商店显示选项(201) and not 屏.api_商店显示选项(413)
    assert 屏.api_商店显示选项(301) and not 屏.api_商店显示选项(300)


def test_商店两次点击才扣真实点券并保留重复货架行(字体: 字体_类) -> None:
    屏, 会 = 物品屏幕_类(商店台词夹具_类()), 会话样本()
    会._玩家().点券 = 1000
    会.世界.卡供应[:] = [3] + [0] * 29
    会.世界.道具供应[:] = [0] * 8
    会._开商店(6001)
    框 = _宿(字体, []).框
    框.时钟 = 100
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    屏.api_画商店(框, 会, 会.待决策, 宿)
    assert 屏._店.卡片 == [1, 1, 1]
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    assert 屏.api_商店待选() == 101 and 会._玩家().点券 == 1000
    assert not any(会._玩家().卡片)
    框.按钮.clear()
    屏.api_画商店(框, 会, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    assert 会._玩家().点券 == 1000 - 服务_类.卡价[0] and 会._玩家().卡片[0] == 1
    assert 屏._店.卡已买 == [True, False, False] and 会.世界.卡供应[0] == 2


def test_商店告别只排一次下一帧真实离开(字体: 字体_类) -> None:
    屏, 会 = 物品屏幕_类(商店台词夹具_类()), 会话样本()
    会._开商店(6001)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    框.时钟 = 100
    屏.api_画商店(框, 会, 会.待决策, 宿)
    leave = next(i for i, o in enumerate(会.待决策.选项) if o.值 == 0)
    next(b for b in 框.按钮 if b.编号 == 210 + leave).动作()
    for t in (200, 1699, 1700, 1701):
        框.按钮.clear()
        框.时钟 = t
        屏.api_画商店(框, 会, 会.待决策, 宿)
    assert len(屏._延迟) == 1 and 会.商店 is not None
    屏.api_运行延迟()
    assert 会.商店 is None and not 屏.api_有延迟()


def test_参考出售气泡按全部数量报价但默认回答只卖一件(字体: 字体_类) -> None:
    屏, 会 = 物品屏幕_类(商店台词夹具_类()), 会话样本()
    会._玩家().点券, 会._玩家().道具[0] = 0, 3
    会.世界.卡供应[:] = [0] * 30
    会.世界.道具供应[:] = [0] * 8
    会._开商店(6001)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    屏.api_画商店(框, 会, 会.待决策, 宿)
    屏.api_商店显示选项(401)
    框.按钮.clear()
    屏.api_画商店(框, 会, 会.待决策, 宿)
    index = next(i for i, o in enumerate(会.待决策.选项) if o.值 == 401)
    next(b for b in 框.按钮 if b.编号 == 210 + index).动作()
    assert f"可得{服务_类.道具价[0] * 3 * 9 // 10}點" in 屏._店.气泡
    assert 会._玩家().道具[0] == 3 and 会._玩家().点券 == 0
    框.按钮.clear()
    屏.api_画商店(框, 会, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 210 + index).动作()
    assert 会._玩家().道具[0] == 2 and 会._玩家().点券 == 服务_类.道具价[0] * 9 // 10
