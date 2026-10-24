# SPDX-License-Identifier: GPL-3.0-or-later
# 合成纹理只验证取样缓存；实际八图另作C++完整像素差分。
# ◑ 导入
from pathlib import Path

import pytest
from test_board_renderer import 构造资源

from rich4.board_models import 相机_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.graphics import 图像_类
from rich4.ground_samples import 地面取样_类


# ◕ 功能
@pytest.mark.parametrize("arg_旋转", range(8))
@pytest.mark.parametrize("arg_掩码", (0, 1, 2), ids=("none", "clear", "mixed"))
def test_非均匀纹理跨地图边界与原扫描全像素掩码一致(
    tmp_path: Path,
    arg_旋转: int,
    arg_掩码: int,
) -> None:
    构造资源(tmp_path)
    原 = 棋盘绘制_类(tmp_path, 0)
    地 = 原.地面
    地.宽瓦片, 地.高瓦片 = 20, 20
    地.索引 = [(i * 7 + i // 20) % 2 for i in range(400)]
    地.纹理 = bytes((i * 37 + i // 32) % 256 for i in range(2048))
    地.调色板 = tuple((i * 511) & 65535 for i in range(256))
    快 = 地面取样_类(地)
    for 中心 in ((0, 0), (320, 288), (608, 608), (-32, 672)):
        相机 = 相机_类(中心, arg_旋转, (3, 5, 93, 77))
        mask = (b"", bytes(7680), bytes([2, 0]) * 3840)[arg_掩码]
        a = 图像_类(96, 80, [0x7777] * 7680, 不透明=mask)
        b = 图像_类(96, 80, a.像素.copy(), 不透明=a.不透明)
        统计 = 原._绘地面原始(a, 相机)
        数 = 快.api_绘制(b, 相机)
        assert 统计.道路 == 0 and 数 == 统计.地面
        assert (a.像素, a.不透明) == (b.像素, b.不透明)


def test_错位中心与坏画布拒绝且保留目标() -> None:
    from test_terrain import 合成地面

    from rich4.terrain import 地面_类

    快 = 地面取样_类(地面_类.api_解码(合成地面()))
    图 = 图像_类(32, 32, [0x7777] * 1024)
    with pytest.raises(ValueError):
        快.api_绘制(图, 相机_类((1, 0), 0, (0, 0, 32, 32)))
    assert 图.像素 == [0x7777] * 1024
    图.像素.pop()
    with pytest.raises(ValueError):
        快.api_绘制(图, 相机_类((0, 0), 0, (0, 0, 32, 32)))
