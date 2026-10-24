# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_number_pad import _宿

from rich4.graphics import 图像_类
from rich4.item_paint import 物品绘图_类
from rich4.item_screen_types import 卡图等待_类, 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_物品放开只安排到下一帧且滑离取消(字体: 字体_类) -> None:
    屏, 调 = 物品屏幕_类(), []
    框 = _宿(字体, []).框
    屏._按住开始(框, "cards", (10, 10, 20, 20), lambda: 调.append(1), 1)
    框.指针x, 框.指针y, 框.按下 = 15, 15, True
    屏._释放按住(框, "cards")
    assert not 屏.api_有延迟()
    框.按下 = False
    屏._释放按住(框, "cards")
    assert 屏.api_有延迟() and not 调 and 屏._按住 is None
    屏.api_运行延迟()
    assert 调 == [1] and not 屏.api_有延迟()
    屏._按住开始(框, "cards", (10, 10, 20, 20), lambda: 调.append(2), 1)
    框.指针x = 20
    屏._释放按住(框, "cards")
    屏.api_运行延迟()
    assert 调 == [1]


def test_卡图到期延迟且新延迟留下一帧(字体: 字体_类) -> None:
    屏, 调 = 物品屏幕_类(), []
    框 = _宿(字体, []).框
    屏._弹图.append(卡图等待_类(1, 10, lambda: 调.append(1)))
    框.时钟 = 10
    屏.api_画卡图(框)
    assert not 屏.api_卡图中() and 屏.api_有延迟() and not 调

    def 追加() -> None:
        调.append(2)
        屏._延迟.append(lambda: 调.append(3))

    屏._延迟.append(追加)
    屏.api_运行延迟()
    assert 调 == [1, 2] and 屏.api_有延迟()
    屏.api_运行延迟()
    assert 调 == [1, 2, 3]


def test_物品按下暗边丢弃高位而内部沿原像素移动() -> None:
    图 = 图像_类(3, 3, [65535] * 9)
    物品绘图_类.api_下沉(图, (0, 0, 3, 3))
    assert 图.像素 == [15855, 15855, 15855, 15855, 65535, 65535, 15855, 65535, 65535]


def test_下车区域不会被随后道具循环覆盖且释放后才实际下车(字体: 字体_类) -> None:
    屏, 会, 关, 报 = 物品屏幕_类(), 会话样本(), [], []
    会._玩家().交通, 会._玩家().骰数 = 2, 3
    会._玩家().道具[:13] = [1] * 13
    框 = _宿(字体, []).框
    框.按下, 框.指针x, 框.指针y = True, 360, 260
    宿 = 物品宿主_类(lambda: 关.append(True), lambda ok, text: 报.append((ok, text)), 会.api_回答)
    屏.api_画库存(框, 会, False, 宿)
    next(b for b in 框.按钮 if b.编号 == 340).动作()
    assert 屏._按住.区域 == (340, 248, 418, 302) and 会._玩家().交通 == 2
    框.按下 = False
    屏.api_画库存(框, 会, False, 宿)
    assert 会._玩家().交通 == 2 and 屏.api_有延迟()
    屏.api_运行延迟()
    assert 会._玩家().交通 == 0 and 会._玩家().骰数 == 1 and 关 == [True]
    assert 报 == [(True, "目前無法下車")]


def test_被动卡先显示原卡图点击后拒绝且不消耗手牌(字体: 字体_类) -> None:
    屏, 会, 声, 报 = 物品屏幕_类(), 会话样本(), [], []
    屏.声音 = 声.append
    会._玩家().卡片[0] = 18
    框 = _宿(字体, []).框
    框.时钟, 框.指针x, 框.指针y, 框.按下 = 100, 30, 150, True
    宿 = 物品宿主_类(
        lambda: 报.append("close"), lambda ok, text: 报.append((ok, text)), 会.api_回答
    )
    屏.api_画库存(框, 会, True, 宿)
    next(b for b in 框.按钮 if b.编号 == 318).动作()
    框.按下 = False
    屏.api_画库存(框, 会, True, 宿)
    assert not 屏.api_卡图中() and 会._玩家().卡片[0] == 18 and not 报
    屏.api_运行延迟()
    assert 屏.api_卡图中() and not 报
    框.按钮.clear()
    屏.api_画卡图(框)
    next(b for b in 框.按钮 if b.编号 == 360).动作()
    assert not 屏.api_卡图中() and not 屏.api_有延迟() and 会._玩家().卡片[0] == 18
    assert 报 == [(False, "這張卡會在需要時自動使用")] and 声 == [1, 62, 3]
