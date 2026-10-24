# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_item_shop import 商店台词夹具_类
from test_number_pad import _宿

from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_医院NPC先感谢再延迟真实释放与扣点且语音按顺序排队(字体: 字体_类) -> None:
    屏, 会, 配 = 物品屏幕_类(商店台词夹具_类()), 会话样本(), []
    屏.语音 = lambda n, q: 配.append((n, q))
    会.世界.节点[2].标志 = 5
    会._玩家().点券 = 300
    会._收容(4, 3, True)
    会._探望收容(True)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    框.时钟 = 100
    屏.api_画救援(框, 会, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    框.按钮.clear()
    框.时钟 = 101
    屏.api_画救援(框, 会, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 290).动作()
    assert 会.世界.医院名单[4] == 1 and 会._玩家().点券 == 300
    assert 配 == [(127, False), (128, False), (129, True), (124, True), (130, True)]
    for t in (102, 2601, 2602, 2603):
        框.按钮.clear()
        框.时钟 = t
        屏.api_画救援(框, 会, 会.待决策, 宿)
    assert len(屏._延迟) == 1 and 会.世界.医院名单[4] == 1
    屏.api_运行延迟()
    assert 会.世界.医院名单[4] == 0 and 会.世界.玩家[0].记录.点券 == 0
    assert 会.世界.特殊角色[0].不活跃状态 == 0


def test_玩家保释二十九点拒绝三十点确认后实际释放(字体: 字体_类) -> None:
    屏, 会, 声 = 物品屏幕_类(商店台词夹具_类()), 会话样本(), []
    屏.声音 = 声.append
    会._玩家().点券 = 29
    会.世界.监狱名单[1], 会.世界.玩家[1].状态.监狱天数 = 1, 3
    会._探望收容(False)
    框 = _宿(字体, []).框
    宿 = 物品宿主_类(lambda: None, lambda ok, text: None, 会.api_回答)
    框.时钟 = 100
    屏.api_画救援(框, 会, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    框.按钮.clear()
    框.时钟 = 101
    屏.api_画救援(框, 会, 会.待决策, 宿)
    assert 屏._救援.选中 == -1 and 屏._救援.不足止 == 2101 and 声 == [3]
    assert 会._玩家().点券 == 29 and 会.世界.监狱名单[1] == 1
    会._玩家().点券 = 30
    框.按钮.clear()
    屏.api_画救援(框, 会, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 210).动作()
    框.按钮.clear()
    屏.api_画救援(框, 会, 会.待决策, 宿)
    next(b for b in 框.按钮 if b.编号 == 290).动作()
    assert 会.世界.玩家[0].记录.点券 == 0 and 会.世界.监狱名单[1] == 0
    assert 会.世界.玩家[1].状态.监狱天数 == 128
