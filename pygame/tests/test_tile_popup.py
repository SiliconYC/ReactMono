# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from copy import deepcopy

from test_message_overlay import _框
from test_services import 服务样本

from rich4.board_models import 相机_类
from rich4.native_ui import 字体_类
from rich4.tile_popup import 地图弹框_类, 地图提示_类


# ◕ 功能
def test_同街收费与连锁数量沿用核心且空地直接展示存储租金() -> None:
    w = 服务样本()
    w.头.物价 = 3
    w.地产.append(deepcopy(w.地产[1]))
    a, b = w.地产[1:3]
    a.经济.业主 = b.经济.业主 = 1
    a.经济.等级 = b.经济.等级 = 1
    a.经济.街道名 = b.经济.街道名 = b"same"
    a.经济.各级租金 = (7, 11, 0, 0, 0, 0)
    b.经济.各级租金 = (8, 13, 0, 0, 0, 0)
    assert 地图提示_类.api_文字(w, 2001)[-1] == (54, "$72")
    a.经济.连锁 = b.经济.连锁 = 1
    assert 地图提示_类.api_文字(w, 2001)[-1] == (54, "$6,000×2")
    a.经济.业主 = 0
    assert 地图提示_类.api_文字(w, 2001)[-1] == (54, "$11")


def test_拾取角色优先建筑且消失角色不进入原包围盒() -> None:
    w = 服务样本()
    for p in w.玩家:
        p.记录.x = 0
    p = w.玩家[0]
    p.记录.x, p.记录.y, p.记录.控制标志 = 96, 96, 1
    w.地产[1].x, w.地产[1].y = 96, 96
    c = 相机_类((96, 96))
    assert 地图提示_类.api_拾取(w, c, 220, 250) == 0x8001
    p.状态.消失天数 = 1
    assert 地图提示_类.api_拾取(w, c, 220, 250) == 2001
    assert 地图提示_类.api_拾取(w, c, 440, 250) == 0


def test_弹框指针使用图片原点锚定而非Frame图片左上位置(字体: 字体_类) -> None:
    w, f = 服务样本(), _框(字体)
    w.节点[1].名字 = b"road"
    地图提示_类.api_绘制(f, w, 地图弹框_类(10, 20, 1))
    assert f.画布.像素[17 * 640 + 8] == 100
    assert f.画布.像素[16 * 640 + 8] == 9
