# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_services import 服务样本

from rich4.native_ui import 字体_类
from rich4.player_info_screen import 玩家查询_类
from rich4.world_map import 设施_类


# ◕ 功能
class 查询原文夹具_类:
    """
    不含商业公司名称的查询夹具，原文字形另做真实素材差分。

    更新日志：
    2026.10.24 - 仅为公开股票名称读取接口提供明确值。
    """

    def api_股票(self, arg_索引: int) -> str:
        return f"公司{arg_索引}"


def test_打开查询重置页签分类滚动且房屋数量依原统计建筑地块数() -> None:
    世, 屏 = 服务样本(), 玩家查询_类(查询原文夹具_类())
    for d in 世.地产[1:]:
        d.经济.业主, d.经济.连锁, d.经济.等级 = 1, 0, 5
    屏._页, 屏._分类, 屏._滚动 = 2, 4, 10
    屏.api_打开(0)
    assert (屏._人, 屏._页, 屏._分类, 屏._滚动) == (0, 0, 0, 0)
    assert 屏._统计(世)[2] == len(世.地产) - 1


def test_地产分类按原区分连锁住宅房屋与设施且价格没有改用财富估值() -> None:
    世, 屏 = 服务样本(), 玩家查询_类(查询原文夹具_类())
    屏.api_打开(0)
    世.头.物价 = 2
    for d in 世.地产[1:]:
        d.经济.业主 = 0
    d = 世.地产[1]
    d.经济.业主, d.经济.连锁, d.经济.等级 = 1, 1, 5
    d.地价, d.每级造价 = 100, 20
    世.设施.append(设施_类(编号=1, 业主=1))
    屏._分类 = 4
    rows = 屏._地产行(世)
    assert len(rows) == 1 and rows[0].价格 == 400 and rows[0].开发 == "連鎖店"
    屏._分类 = 3
    assert 屏._地产行(世) == []
    屏._分类 = 2
    assert len(屏._地产行(世)) == 1


def test_滚动等于行数时保留空页而超过才回起点(字体: 字体_类) -> None:
    from test_number_pad import _宿

    世, 屏 = 服务样本(), 玩家查询_类(查询原文夹具_类())
    世.地产[1].经济.业主 = 1
    count = len(屏._地产行(世))
    assert count > 0
    屏._滚动 = count
    屏._画地产(_宿(字体, []), 世)
    assert 屏._滚动 == count
    屏._滚动 += 1
    屏._画地产(_宿(字体, []), 世)
    assert 屏._滚动 == 0
