# SPDX-License-Identifier: GPL-3.0-or-later
# PNG保存可见颜色；JSON另记RGB555高位、原点和掩码存在性，避免丢失原绘制语义。
# ◑ 导入
import json
from dataclasses import dataclass
from pathlib import Path

import pygame

from rich4.graphics import 图像_类


# ◕ 功能
@dataclass(frozen=True)
class 图片元数据_类:
    """
    PNG无法表达的原点/无掩码与RGB555保留位，使用公开JSON整数与区间。

    更新日志：
    2026.10.24 - 高位段采用左闭右开像素索引，PNG本身仍是普通RGBA图片。
    """

    width: int
    height: int
    origin_x: int
    origin_y: int
    has_mask: bool
    high_bit_ranges: tuple[tuple[int, int], ...]

    @classmethod
    def api_从JSON(cls, arg_JSON: str) -> "图片元数据_类":
        data = json.loads(arg_JSON)
        return cls(
            data["width"],
            data["height"],
            data["origin_x"],
            data["origin_y"],
            data["has_mask"],
            tuple(tuple(v) for v in data["high_bit_ranges"]),
        )


class 开放图像_类:
    """
    普通RGBA PNG与独立JSON元数据之间的无损原RGB555转换。

    更新日志：
    2026.10.24 - 全65536原像素、透明像素底色和无掩码黑色均须可恢复。
    """

    _红蓝 = bytes(min(range(32), key=lambda n: abs(n * 255 // 31 - v)) for v in range(256))
    _绿 = bytes(min(range(32), key=lambda n: abs(n * 510 // 63 - v)) for v in range(256))

    @staticmethod
    def api_区间(arg_位置: list[int]) -> tuple[tuple[int, int], ...]:
        ranges: list[tuple[int, int]] = []
        for index in arg_位置:
            if ranges and ranges[-1][1] == index:
                ranges[-1] = ranges[-1][0], index + 1
            else:
                ranges.append((index, index + 1))
        return tuple(ranges)

    @classmethod
    def api_保存(cls, arg_图: 图像_类, arg_路径: Path) -> 图片元数据_类:
        metadata = 图片元数据_类(
            arg_图.宽,
            arg_图.高,
            arg_图.原点x,
            arg_图.原点y,
            bool(arg_图.不透明),
            cls.api_区间([i for i, v in enumerate(arg_图.像素) if v & 0x8000]),
        )
        if arg_图.宽 and arg_图.高:
            arg_路径.parent.mkdir(parents=True, exist_ok=True)
            image = pygame.image.frombytes(arg_图.api_RGBA(), (arg_图.宽, arg_图.高), "RGBA")
            pygame.image.save(image, arg_路径)
        return metadata

    @classmethod
    def api_读取(cls, arg_路径: Path, arg_描述: 图片元数据_类) -> 图像_类:
        m = arg_描述
        if not m.width or not m.height:
            return 图像_类(m.width, m.height, [], m.origin_x, m.origin_y)
        image = pygame.image.load(arg_路径)
        if image.get_size() != (m.width, m.height):
            raise ValueError("PNG尺寸与元数据不符：" + str(arg_路径))
        rgba = pygame.image.tobytes(image, "RGBA")
        r, g, b = (
            rgba[0::4].translate(cls._红蓝),
            rgba[1::4].translate(cls._绿),
            rgba[2::4].translate(cls._红蓝),
        )
        pixels = [
            (red << 10) | (green << 5) | blue for red, green, blue in zip(r, g, b, strict=True)
        ]
        last = 0
        for start, end in m.high_bit_ranges:
            if not last <= start < end <= len(pixels):
                raise ValueError("PNG保留高位区间越界或相互重叠")
            for i in range(start, end):
                pixels[i] |= 0x8000
            last = end
        mask = bytes(v != 0 for v in rgba[3::4]) if m.has_mask else b""
        return 图像_类(m.width, m.height, pixels, m.origin_x, m.origin_y, mask)
