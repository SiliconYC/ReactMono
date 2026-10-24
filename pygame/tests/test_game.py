# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import pytest
from test_services import 服务样本

from rich4.cards import 卡片用法_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策种类_类, 托管设置_类, 游戏阶段_类
from rich4.save import 存档_类
from rich4.world import 世界_类


# ◕ 功能
def 会话样本() -> 游戏会话_类:
    世 = 服务样本()
    for 人 in 世.玩家:
        人.记录.x, 人.记录.y, 人.记录.节点, 人.记录.上次节点 = 32, 32, 1, 4
        人.记录.控制标志 = 1
        人.记录.卡片[:] = [0] * 15
        人.记录.道具[:] = [0] * 15
    for 特 in 世.特殊角色:
        特.不活跃状态 = 1
    世.有初始随机状态 = False
    return 游戏会话_类(世, 1)


def test_公开会话持有独立世界且骰子350毫秒前不能推进() -> None:
    会 = 会话样本()
    assert 会.阶段 == 游戏阶段_类.人类待命 and 会.api_可保存()
    assert 会.api_掷骰()
    assert 会.阶段 == 游戏阶段_类.掷骰 and not 会.api_可保存()
    会.api_步进(349)
    assert 会.阶段 == 游戏阶段_类.掷骰 and 会.阶段毫秒 == 349
    会.api_步进(1)
    assert 会.阶段 == 游戏阶段_类.移动 and 会.动画.已过毫秒 == 0
    assert not 会.api_掷骰()


def test_真实行走后交给下一人类回合而非重置游戏() -> None:
    会 = 会话样本()
    assert 会.api_掷骰()
    for _ in range(20):
        会.api_步进(160)
        if 会.阶段 == 游戏阶段_类.人类待命:
            break
    assert 会.阶段 == 游戏阶段_类.人类待命 and 会.世界.头.当前玩家 == 1
    assert 会.世界.玩家[0].记录.节点 != 1


def test_遥控骰实际启程且不消耗普通骰随机() -> None:
    会 = 会话样本()
    会._玩家().道具[7] = 1
    assert 会.api_用道具(8, 3)
    assert 会.阶段 == 游戏阶段_类.掷骰 and 会.骰面 == [3] and 会.剩余步 == 3
    assert 会.随机.状态 == 1 and 会._玩家().道具[7] == 0


def test_公开银行存提拒绝非法额且提款回到菜单() -> None:
    会 = 会话样本()
    会._开银行(False)
    现, 银 = 会._玩家().现金, 会._玩家().银行
    assert 会.待决策.种类 == 决策种类_类.银行
    assert not 会.api_回答(0, 0)
    assert 会.api_回答(0, 1000)
    assert (会._玩家().现金, 会._玩家().银行) == (现 - 1000, 银 + 1000)
    提 = next(i for i, 项 in enumerate(会.待决策.选项) if 项.值 == 2)
    assert 会.api_回答(提, 1000)
    assert 会.待决策.种类 == 决策种类_类.银行
    assert (会._玩家().现金, 会._玩家().银行) == (现, 银)


def test_公开购买彩票确实扣钱记票而非伪造成功() -> None:
    会 = 会话样本()
    会._开彩票()
    原 = 会._玩家().现金
    assert 会.api_回答(0)
    assert 会.世界.彩票[0] == 1 and 会._玩家().现金 == 原 - 1000


def test_路过银行离开后真实遭遇一次并减少附身炸弹计时() -> None:
    会 = 会话样本()
    会._状态().附身炸弹 = 19
    炸 = 会.世界.物件[18]
    炸.种类, 炸.节点, 炸.附身玩家, 炸.剩余天数 = 18, 1, 1, 4
    会.世界.节点[2].标志, 会.下节点, 会.剩余步 = 14, 2, 2
    会._置阶段(游戏阶段_类.移动)
    会._完成一步()
    assert 会.银行后遭遇 and 会.待决策.种类 == 决策种类_类.银行
    离 = next(i for i, 项 in enumerate(会.待决策.选项) if 项.值 == 0)
    assert 会.api_回答(离)
    assert 炸.剩余天数 == 3 and 会.阶段 == 游戏阶段_类.移动
    assert 会.剩余步 == 1 and not 会.银行后遭遇


def test_骰数受交通低位限制且非待命不改() -> None:
    会 = 会话样本()
    assert not 会.api_设骰数(2)
    会._玩家().交通 = 130
    assert 会.api_设骰数(3) and 会._玩家().骰数 == 3
    assert not 会.api_设骰数(4)
    会.api_掷骰()
    assert not 会.api_设骰数(1)


def test_非法行动实际拒绝且非待命不能使用卡道具市场() -> None:
    会 = 会话样本()
    assert not 会.api_用卡(卡片用法_类(1))
    assert not 会.api_用道具(1)
    会.api_掷骰()
    assert not 会.api_用卡(卡片用法_类(1)) and not 会.api_下车()
    assert not 会.api_买股票(0, 1) and not 会.api_开交易()


def test_存档只允许结算状态并保持原DAT不声称保存随机或阶段() -> None:
    会 = 会话样本()
    档 = 会.api_导出存档()
    assert 档.api_导出() == 会.世界.api_导出()
    另 = 游戏会话_类(世界_类.api_从存档(存档_类.api_解码(档.api_导出())), 123)
    assert 另.世界.api_导出() == 会.世界.api_导出() and 另.随机.状态 == 123
    会.api_掷骰()
    with pytest.raises(RuntimeError, match="settled"):
        会.api_导出存档()


def test_托管中途延后且配置边界拒绝() -> None:
    会 = 会话样本()
    assert not 会.api_设置托管(1, 托管设置_类(True, 4))
    会.api_掷骰()
    设 = 托管设置_类(True, 2, 1, 65, 40)
    assert 会.api_设置托管(1, 设)
    assert 会.世界.玩家[1].记录.控制标志 == 1 and 会.api_托管设置(1) == 设


def test_原生时钟零毫秒不跨未完成动画且相机校验() -> None:
    会 = 会话样本()
    会.api_设相机(7)
    assert 会.世界.相机旋转 == 7
    with pytest.raises(ValueError):
        会.api_设相机(8)
    会.api_掷骰()
    会.api_步进(0)
    assert 会.阶段毫秒 == 0 and 会.阶段 == 游戏阶段_类.掷骰
