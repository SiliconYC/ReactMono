# SPDX-License-Identifier: GPL-3.0-or-later
# 本文件仅创建无商业内容的格式样本；正式渲染器始终读取调用方的真实资源。
# ◑ 导入
import struct
from pathlib import Path

import pytest
from test_terrain import 合成地面
from test_world import 合成地图

from rich4.board_models import 业主外观_类, 地产外观_类, 场景_类, 玩家精灵_类, 相机_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.graphics import 图像_类


# ◕ 功能
def 样本包(arg_条目: list[bytes]) -> bytes:
    包 = bytearray(4)
    偏移 = []
    for 项 in arg_条目:
        偏移.append(len(包))
        包.extend(struct.pack("<4I", len(项), len(项), 0, 0) + 项)
    struct.pack_into("<I", 包, 0, len(包))
    return bytes(包) + struct.pack(f"<{len(偏移)}I", *偏移)


def 样本精灵(arg_色: int, arg_帧数: int = 8, arg_像素: bytes = b"\x01" * 4) -> bytes:
    调色 = [0] * 256
    调色[1], 调色[2], 调色[255] = arg_色, 0x4321, 0x001F
    return (
        b"SPR\0"
        + struct.pack("<II", arg_帧数, 12 + arg_帧数 * 12)
        + struct.pack("<hhhhI", 2, 2, 0, 0, 4) * arg_帧数
        + struct.pack("<256H", *调色)
        + arg_像素 * arg_帧数
    )


def 构造资源(arg_目录: Path) -> None:
    地图 = [b""] * 40
    地图[0], 地图[1] = 合成地面(), 合成地图()
    地图[25] = 样本精灵(0x7FFF, 12)
    地图[26] = 样本精灵(0x7FFF, 4)
    地图[39] = 样本精灵(0x1234, 8, bytes([255, 1, 0, 2]))
    数据 = [b""] * 339
    数据[128], 数据[338] = 样本精灵(0x7C00), 样本精灵(0x03E0)
    (arg_目录 / "mAp.MkF").write_bytes(样本包(地图))
    (arg_目录 / "dAtA.mKf").write_bytes(样本包(数据))


def test_地图编号先拒绝并按大小写无关读取节点(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        棋盘绘制_类(tmp_path / "missing", 8)
    构造资源(tmp_path)
    绘制 = 棋盘绘制_类(tmp_path, 0)
    assert 绘制.api_地图编号() == 0 and 绘制.api_节点数() == 4
    assert 绘制.api_节点位置(0) is 绘制.api_节点位置(65535) is None
    assert 绘制.api_节点位置(1) == (32, 32)


def test_活动人物在同锚点后画而外部栏不被覆盖(tmp_path: Path) -> None:
    构造资源(tmp_path)
    绘制 = 棋盘绘制_类(tmp_path, 0)
    相机 = 相机_类((-4096, -4096))
    场景 = 场景_类(
        玩家=[
            玩家精灵_类(位置=相机.中心, 角色=0, 活跃=True),
            玩家精灵_类(位置=相机.中心, 角色=10, 槽位=1),
        ]
    )
    图 = 图像_类(640, 480, [0x2222] * (640 * 480))
    统计 = 绘制.api_绘制(图, 场景, 相机)
    assert 统计.精灵 == 2 and 统计.地面 > 100 and 统计.道路 == 0
    assert 图.像素[260 * 640 + 220] == 0x7C00
    assert 图.像素[0] == 图.像素[-1] == 0x2222


def test_不在画面的业主颜色优先仅改SPR槽255且缓存互不污染(tmp_path: Path) -> None:
    构造资源(tmp_path)
    绘制 = 棋盘绘制_类(tmp_path, 0)
    场景 = 场景_类(地产=[地产外观_类(1, 2, 1)], 业主=[业主外观_类(), 业主外观_类(0x7C1F, 10)])
    for 色 in [0x7C1F, 0x03E0, 0x7C1F]:
        场景.业主[1].颜色 = 色
        图 = 图像_类(640, 480, [0] * (640 * 480))
        绘制.api_绘制(图, 场景, 相机_类())
        assert 图.像素[260 * 640 + 220] == 色
        assert 图.像素[260 * 640 + 221] == 0x1234
        assert 图.像素[261 * 640 + 221] == 0x4321


def test_临时地产着色只按掩码或运算而不产生假建筑(tmp_path: Path) -> None:
    构造资源(tmp_path)
    绘制 = 棋盘绘制_类(tmp_path, 0)
    原 = 图像_类(640, 480, [0x1234] * (640 * 480))
    绘制.api_绘制(原, 场景_类(), 相机_类())
    for 临时, 色 in [(0x50, 0x7C00), (0x31, 0x003F)]:
        图 = 图像_类(640, 480, [0x1234] * (640 * 480))
        绘制.api_绘制(图, 场景_类(地产=[地产外观_类(1, 0, 0, 0, 临时)]), 相机_类())
        差 = [(a, b) for a, b in zip(原.像素, 图.像素) if a != b]
        assert len(差) == 4 and all(b == a | 色 for a, b in 差)
