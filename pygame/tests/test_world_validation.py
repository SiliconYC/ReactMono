# ◑ 导入
from copy import deepcopy

import pytest
from test_world import 合成地图

from rich4.world import 世界_类
from rich4.world_validation import 世界验证_类


# ◕ 功能
def test_合法新局验证不修改世界() -> None:
    世界 = 世界_类.api_从地图(合成地图())
    原字节 = 世界.api_导出()
    世界验证_类.api_验证(世界)
    assert 世界.api_导出() == 原字节


def test_事件堆重复与链接越界被拒绝() -> None:
    世界 = 世界_类.api_从地图(合成地图())
    副 = deepcopy(世界)
    副.新闻牌堆[0] = 副.新闻牌堆[1]
    with pytest.raises(ValueError, match="news_deck"):
        世界验证_类.api_验证(副)
    世界.节点[1].邻居[0] = 65535
    with pytest.raises(ValueError, match="neighbors"):
        世界验证_类.api_验证(世界)


def test_只在活跃物件或角色上验证位置方向() -> None:
    世界 = 世界_类.api_从地图(合成地图())
    世界.特殊角色[0].方向 = 250
    世界.物件[0].种类 = 0
    世界.玩家[0].记录.交通 = 0xF2
    世界.玩家[0].状态.医院天数 = 0x80
    世界验证_类.api_验证(世界)
    世界.节点[1].标志 |= 0x10000
    with pytest.raises(ValueError, match="objects"):
        世界验证_类.api_验证(世界)


def test_拒绝NaN及无效出售项目而不吞掉未知空项字段() -> None:
    世界 = 世界_类.api_从地图(合成地图())
    世界.出售表[0][0].项目 = 65535
    世界验证_类.api_验证(世界)
    世界.出售表[0][0].种类 = 4
    with pytest.raises(ValueError, match="offers"):
        世界验证_类.api_验证(世界)
    世界.出售表[0][0].种类 = 0
    世界.股票[0].浮点位[0] = 0x7FC01234
    with pytest.raises(ValueError, match="float_bits"):
        世界验证_类.api_验证(世界)


def test_Python列表不能突破原固定数组维度() -> None:
    世界 = 世界_类.api_从地图(合成地图())
    世界.物件.clear()
    with pytest.raises(ValueError, match="objects"):
        世界验证_类.api_验证(世界)
