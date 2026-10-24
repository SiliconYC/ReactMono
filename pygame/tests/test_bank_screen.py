# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from collections.abc import Callable

from test_number_pad import _宿

from rich4.bank_screen import 银行屏幕_类
from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.native_ui import 字体_类
from rich4.number_pad import 数字板_类
from rich4.original_text import 台词_类
from rich4.screen_draw import 屏幕宿主_类


# ◕ 功能
class 银行原文夹具_类:
    """
    无商业台词的明确语音编号夹具，不代替真实美术/原文差分。

    更新日志：
    2026.10.24 - 仅用于银行动作的顺序和可重入测试。
    """

    def api_配音(self, arg_声音: int, arg_变体: int = 0) -> 台词_类:
        return 台词_类(arg_声音, f"测试{arg_声音}/{arg_变体}")


def _答(arg_结果: list[tuple[int, int]], arg_成功: bool = True) -> Callable[[int, int], bool]:
    def 答(arg_值: int, arg_数: int) -> bool:
        arg_结果.append((arg_值, arg_数))
        return arg_成功

    return 答


def test_ATM离开依原转柜台或回答离开且取消声不重复(字体: 字体_类) -> None:
    声, 结果 = [], []
    宿 = _宿(字体, 声)
    银行 = 银行屏幕_类(银行原文夹具_类())
    决策 = 决策_类(决策种类_类.银行, 0, 选项=[决策选项_类("贷款", 3)])
    银行.api_取消(宿, 决策, _答(结果))
    assert 银行.api_柜台() and 结果 == [] and 声 == [4]
    assert 银行._行 == ["测试75/0", "测试76/0"]
    银行.api_取消(宿, 决策, _答(结果))
    assert 结果 == [(0, 0)] and 声 == [4, 4]


def test_贷款完成保留两条台词而取消清面板(字体: 字体_类) -> None:
    银行, 板, 结果 = 银行屏幕_类(银行原文夹具_类()), 数字板_类(), []
    宿 = _宿(字体, [])
    银行._借贷(宿, 板, _答(结果), 500, 100)
    assert 板.api_上限() == 400 and 银行._侧栏
    板.api_键(宿, "m")
    板.api_键(宿, "\r")
    assert 结果 == [(3, 400)] and 银行._行 == ["测试79/0", "测试80/0"]
    银行._借贷(宿, 板, _答(结果), 500, 100)
    板.api_取消(宿)
    assert not 银行._行 and not 银行._侧栏


def test_还贷不足只重试一次且回调失败不伪装成功(字体: 字体_类) -> None:
    银行, 板, 结果 = 银行屏幕_类(银行原文夹具_类()), 数字板_类(), []
    宿 = _宿(字体, [])
    银行._还贷(宿, 板, _答(结果), 100, 30)
    板.api_键(宿, "m")
    板.api_键(宿, "\r")
    assert 板.api_活跃() and 银行._行 == ["测试83/0"] and not 结果
    for c in "20\r":
        板.api_键(宿, c)
    assert 结果 == [(4, 20)] and 银行._行 == ["测试84/0"]
    银行._还贷(宿, 板, _答(结果, False), 100, 30)
    for c in "20\r":
        板.api_键(宿, c)
    assert 银行._行 == ["测试82/0"]


def test_董事融资成功顺序先真实融资再离开而还款不足不提交(字体: 字体_类) -> None:
    银行, 板, 结果 = 银行屏幕_类(银行原文夹具_类()), 数字板_类(), []
    宿: 屏幕宿主_类 = _宿(字体, [])
    银行._阶段 = 2
    银行._融资(宿, 板, _答(结果), 300, 100)
    板.api_键(宿, "m")
    板.api_键(宿, "\r")
    assert 结果 == [(5, 200), (0, 0)] and 银行.api_柜台()
    银行._还融资(宿, 板, _答(结果), 100, 30)
    板.api_键(宿, "m")
    板.api_键(宿, "\r")
    assert 结果 == [(5, 200), (0, 0)] and 银行._行 == ["测试90/0"]


def test_ATM拒绝交易时保留输入并给错误声且再次确认只提交一次(字体: 字体_类) -> None:
    from test_world import 合成地图

    from rich4.world import 世界_类

    世, 银行, 结果, 声 = 世界_类.api_从地图(合成地图()), 银行屏幕_类(银行原文夹具_类()), [], []
    世.玩家[0].记录.银行 = 123
    宿 = _宿(字体, 声)
    决策 = 决策_类(决策种类_类.银行, 0, 选项=[决策选项_类("提款", 2)])
    银行._ATM键(宿, 16, 世, 决策, _答(结果, False))
    银行._ATM键(宿, 17, 世, 决策, _答(结果, False))
    assert 结果 == [(2, 123)] and 声 == [3] and 银行.api_ATM数字() == "123"
    银行._ATM键(宿, 17, 世, 决策, _答(结果))
    assert 结果 == [(2, 123), (2, 123), (0, 0)] and 银行.api_ATM数字() == "0"
    assert 世.玩家[0].记录.银行 == 123


def test_银行所有权依原仅检查节点对应公司业主且统计包含其它所有槽() -> None:
    from test_world import 合成地图

    from rich4.world import 世界_类

    世 = 世界_类.api_从地图(合成地图())
    世.玩家[0].记录.节点 = 1
    世.节点[1].类型索引 = 6001
    世.公司[1].业主 = 1
    assert 银行屏幕_类._拥有(世, 0)
    世.公司[1].业主 = 2
    assert not 银行屏幕_类._拥有(世, 0)
    for p in 世.玩家[1:]:
        p.记录.银行, p.记录.控制标志 = 2147483647, 0
    assert 银行屏幕_类._别人存款(世, 0) == 2147483647
