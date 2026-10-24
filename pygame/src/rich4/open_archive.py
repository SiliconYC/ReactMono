# SPDX-License-Identifier: GPL-3.0-or-later
# 开放资源按JSON索引直接读取普通文件，绝不重建SPR/FLC/MKF中间包。
# ◑ 导入
import json
from functools import cache
from pathlib import Path

import pygame

from rich4.graphics import 图像_类
from rich4.open_image import 图片元数据_类, 开放图像_类
from rich4.terrain import 地面_类


# ◕ 功能
class 开放档案_类:
    """
    游戏自身资源目录的JSON索引、PNG图片/掩码、标准WAV与原数据字段。

    更新日志：
    2026.10.24 - 校验版本与目录边界；媒体只能走开放格式入口，不伪造原包数据。
    """

    def __init__(self, arg_根: Path, arg_库: str) -> None:
        self.根 = arg_根.resolve()
        manifest = self._清单(self.根)
        self.条目: list[str] = manifest["archives"][arg_库]
        self._元: dict[int, dict] = {}

    @staticmethod
    @cache
    def _清单(arg_根: Path) -> dict:
        data = json.loads((arg_根 / "manifest.json").read_text())
        if data["format"] != "reactmono-rich4-open-assets" or data["version"] != 1:
            raise ValueError("不支持的开放素材清单版本")
        return data

    def api_路径(self, arg_相对: str) -> Path:
        path = (self.根 / arg_相对).resolve()
        if not path.is_relative_to(self.根):
            raise ValueError("资源路径逃出游戏素材目录")
        return path

    def api_元数据(self, arg_条: int) -> dict:
        if not 0 <= arg_条 < len(self.条目):
            raise IndexError("开放资源条目越界")
        if arg_条 not in self._元:
            self._元[arg_条] = json.loads(self.api_路径(self.条目[arg_条]).read_text())
        return self._元[arg_条]

    def api_解码(self, arg_条: int, arg_上限: int = 256 * 1024 * 1024) -> bytes:
        data = self.api_元数据(arg_条)
        kind = data["kind"]
        if kind == "data":
            content = bytes(data["values"])
        elif kind == "wav":
            content = self.api_路径(data["file"]).read_bytes()
        elif kind == "mask":
            image = pygame.image.load(self.api_路径(data["file"]))
            if image.get_size() != (data["width"], data["height"]) or image.get_bitsize() != 8:
                raise ValueError("命中PNG掩码格式或尺寸不符")
            content = pygame.image.tobytes(image, "P")
        else:
            raise ValueError("PNG媒体须使用帧/动画/地形接口，不能重建原私有字节")
        if len(content) > arg_上限:
            raise ValueError("开放资源超过分配上限")
        return content

    def api_帧数(self, arg_条: int) -> int:
        data = self.api_元数据(arg_条)
        return len(data["frames"]) if data["kind"] in ("sprite", "picture", "animation") else 0

    def api_帧(self, arg_条: int, arg_帧: int) -> 图像_类:
        data = self.api_元数据(arg_条)
        if data["kind"] not in ("sprite", "picture", "animation"):
            raise ValueError("该资源不是PNG帧")
        if not 0 <= arg_帧 < len(data["frames"]):
            raise IndexError("PNG帧索引越界")
        item = data["frames"][arg_帧]
        return 开放图像_类.api_读取(
            self.api_路径(item["image"]), 图片元数据_类.api_从JSON(json.dumps(item))
        )

    def api_换色段(self, arg_条: int, arg_帧: int) -> tuple[tuple[int, int], ...]:
        data = self.api_元数据(arg_条)
        if data["kind"] != "sprite" or not data["indexed"]:
            return ()
        return tuple(tuple(v) for v in data["frames"][arg_帧]["team_color_ranges"])

    def api_地面(self, arg_条: int) -> 地面_类:
        data = self.api_元数据(arg_条)
        if data["kind"] != "ground":
            raise ValueError("该资源不是开放地形")
        image = pygame.image.load(self.api_路径(data["texture_indices_image"]))
        if image.get_bitsize() != 8 or image.get_size() != (32, data["tile_count"] * 32):
            raise ValueError("地形PNG索引图尺寸或格式不符")
        indices = data["tile_indices"]
        if len(indices) != data["width_tiles"] * data["height_tiles"] or any(
            not 0 <= i < data["tile_count"] for i in indices
        ):
            raise ValueError("开放地形瓦片索引越界或尺寸不符")
        return 地面_类(
            data["width_tiles"],
            data["height_tiles"],
            data["reserved"],
            tuple(data["palette_rgb555"]),
            list(indices),
            pygame.image.tobytes(image, "P"),
        )
