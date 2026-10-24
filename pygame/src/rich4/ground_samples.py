# SPDX-License-Identifier: GPL-3.0-or-later
# 原board_renderer.cpp地面投影/terrain.cpp取样的缓存；不近似投影或生成替代素材。
# ◑ 导入
from array import array
from collections import OrderedDict
from dataclasses import dataclass

from rich4.board_models import 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.graphics import 图像_类
from rich4.projection_tables import 投影表_类
from rich4.terrain import 地形_类, 地面_类


# ◕ 功能
@dataclass
class 地形取样图_类:
    """
    每像素的相对瓦片号/原纹理坐标及覆盖位，不含任何地图颜色或商业图像。

    更新日志：
    2026.10.24 - 用32位标准数组存地址；第0瓦片始终为原调色板零索引背景。
    """

    地址: array
    覆盖: bytes
    瓦片: list[tuple[int, int]]


class 地面取样_类:
    """
    对齐瓦片中心后几何与地图位置无关，缓存原扫描产生的精确取样地址。

    更新日志：
    2026.10.24 - 两个位面经原扫描器求出10位纹理地址；GND只读色表在内存中展开。
    """

    def __init__(self, arg_地面: 地面_类) -> None:
        self.地面 = arg_地面
        self._颜色 = [arg_地面.调色板[i] for i in arg_地面.纹理] + [arg_地面.调色板[0]] * 1024
        self._空纹理 = len(arg_地面.纹理)
        self._缓存: OrderedDict[
            tuple[int, int, tuple[int, int, int, int], int], 地形取样图_类
        ] = OrderedDict()

    @staticmethod
    def _建立(
        arg_宽: int,
        arg_高: int,
        arg_相机: 相机_类,
        arg_框: tuple[int, int, int, int],
    ) -> 地形取样图_类:
        count = arg_宽 * arg_高
        high = 图像_类(arg_宽, arg_高, [-1] * count, 不透明=bytes(count))
        low = 图像_类(arg_宽, arg_高, [0] * count)
        upper = bytes(i >> 8 for i in range(1024))
        lower, identity = bytes(i & 255 for i in range(1024)), tuple(range(256))
        tiles: list[tuple[int, int]] = []
        mid = 棋盘投影_类.api_屏幕中心(arg_相机)
        for x, y in 投影表_类.地面次序[arg_相机.旋转]:
            if y == -128:
                break
            tiles.append((x, y))
            points = [
                棋盘投影_类.api_格点(a, b, arg_相机)
                for a, b in ((x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1))
            ]
            corners = [
                (
                    ((p[1] + mid[1] + 32768) & 65535) - 32768,
                    ((p[0] + mid[0] + 32768) & 65535) - 32768,
                )
                for p in points
            ]
            # 暂存的是地址位而非RGB555；两个8位纹理位面保留全部1024种原取样坐标。
            palette = tuple((len(tiles) << 10) | (i << 8) for i in range(256))
            地形_类.api_绘瓦片(high, upper, palette, corners, arg_框)
            地形_类.api_绘瓦片(low, lower, identity, corners, arg_框)
        addresses = array("I", (max(0, a | b) for a, b in zip(high.像素, low.像素)))
        return 地形取样图_类(addresses, high.不透明, tiles)

    def api_绘制(self, arg_目标: 图像_类, arg_相机: 相机_类) -> int:
        棋盘投影_类.api_验证相机(arg_相机)
        w, h = arg_目标.宽, arg_目标.高
        if (
            not 0 < w <= 8192
            or not 0 < h <= 8192
            or w * h > 32 * 1024 * 1024
            or len(arg_目标.像素) != w * h
            or arg_目标.不透明 and len(arg_目标.不透明) != w * h
            or any(n & 31 for n in arg_相机.中心)
        ):
            raise ValueError("取样缓存需要有效画布与对齐32格的相机中心")
        left, top, right, bottom = arg_相机.视口
        right, bottom = min(right, w), min(bottom, h)
        if left >= right or top >= bottom:
            return 0
        key = w, h, arg_相机.视口, arg_相机.旋转
        if key not in self._缓存:
            self._缓存[key] = self._建立(w, h, arg_相机, (left, top, right, bottom))
            while len(self._缓存) > 4:
                self._缓存.popitem(last=False)
        self._缓存.move_to_end(key)
        pattern, g = self._缓存[key], self.地面
        tile_x, tile_y = arg_相机.中心[0] // 32, arg_相机.中心[1] // 32
        bases = [self._空纹理]
        for dx, dy in pattern.瓦片:
            x, y = tile_x + dx, tile_y + dy
            bases.append(
                g.索引[y * g.宽瓦片 + x] * 1024
                if 0 <= x < g.宽瓦片 and 0 <= y < g.高瓦片
                else self._空纹理
            )
        colors = self._颜色
        old_mask = arg_目标.不透明
        clear_mask = bool(old_mask) and old_mask.count(0) == len(old_mask)
        mask = bytearray(old_mask) if not clear_mask else bytearray()
        for y in range(top, bottom):
            start, end = y * w + left, y * w + right
            arg_目标.像素[start:end] = [
                colors[bases[p >> 10] + (p & 1023)] for p in pattern.地址[start:end]
            ]
            if mask:
                mask[start:end] = bytes(
                    1 if covered else old
                    for covered, old in zip(pattern.覆盖[start:end], mask[start:end])
                )
        arg_目标.不透明 = pattern.覆盖 if clear_mask else bytes(mask)
        return len(pattern.瓦片)
