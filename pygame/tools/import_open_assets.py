# SPDX-License-Identifier: GPL-3.0-or-later
# 一次性离线转换；商业媒体只写调用方本地、Git忽略的资源目录。
# ◑ 导入
import argparse
import hashlib
import json
import shutil
import struct
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import pygame
from import_open_text import 开放文字导入_类

from rich4.artwork import 美术_类
from rich4.flc import 动画_类
from rich4.graphics import 图像_类
from rich4.midi_player import MIDI播放器_类
from rich4.open_image import 开放图像_类
from rich4.terrain import 地面_类


# ◕ 功能
class 开放资源导入_类:
    """
    七包逐项转换为普通PNG/WAV/JSON，保留完整动画帧与换色位置。

    更新日志：
    2026.10.24 - 每张PNG读回比较完整原图；原目录只读，未转换完整前不发布manifest。
    """

    def __init__(self, arg_输入: Path, arg_输出: Path) -> None:
        self.输入, self.输出 = arg_输入.resolve(), arg_输出.resolve()
        if self.输出 == self.输入 or self.输入 in self.输出.parents:
            raise ValueError("转换不能写入正版来源目录")
        self.输出.mkdir(parents=True, exist_ok=True)
        self.美术 = 美术_类(self.输入)
        self.统计: Counter[str] = Counter()
        self.文件: dict[str, dict] = {}

    def _JSON(self, arg_相对: Path, arg_内容: dict) -> str:
        path = self.输出 / arg_相对
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(arg_内容, ensure_ascii=False, separators=(",", ":")) + "\n")
        self._记录(path)
        return arg_相对.as_posix()

    def _记录(self, arg_路径: Path) -> None:
        data = arg_路径.read_bytes()
        self.文件[arg_路径.relative_to(self.输出).as_posix()] = {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    def _图(self, arg_图: 图像_类, arg_相对: Path) -> dict:
        path = self.输出 / arg_相对
        info = 开放图像_类.api_保存(arg_图, path)
        if 开放图像_类.api_读取(path, info) != arg_图:
            raise ValueError("PNG完整原图往返不同：" + str(arg_相对))
        if arg_图.宽 and arg_图.高:
            self._记录(path)
        self.统计["verified_png_frames"] += 1
        return {"image": arg_相对.as_posix(), **asdict(info)}

    def _精灵(self, arg_数据: bytes, arg_库: str, arg_条: int) -> dict:
        signature, count, offset = struct.unpack_from("<4sII", arg_数据)
        indexed = signature == b"SPR\0"
        pixel_offset = offset + (512 if indexed else 0)
        frames = []
        for i in range(count):
            image = 图像_类.api_解码(arg_数据, i)
            item = self._图(image, Path("images") / arg_库 / str(arg_条) / f"{i}.png")
            size = struct.unpack_from("<I", arg_数据, 20 + i * 12)[0]
            indices = arg_数据[pixel_offset : pixel_offset + size] if indexed else b""
            item["team_color_ranges"] = 开放图像_类.api_区间(
                [j for j, v in enumerate(indices) if v == 255]
            )
            pixel_offset += size
            frames.append(item)
        return {"kind": "sprite", "indexed": indexed, "frames": frames}

    def _动画(self, arg_数据: bytes, arg_库: str, arg_条: int) -> dict:
        movie = 动画_类(arg_数据)
        frames = []
        while movie.api_下一帧():
            frames.append(
                self._图(
                    movie.api_图像(), Path("images") / arg_库 / str(arg_条) / f"{len(frames)}.png"
                )
            )
        if len(frames) != movie.帧数:
            raise ValueError("原动画帧数不足")
        return {
            "kind": "animation",
            "width": movie.宽,
            "height": movie.高,
            "interval_ms": movie.间隔毫秒,
            "frames": frames,
        }

    def _地面(self, arg_数据: bytes, arg_条: int) -> dict:
        ground = 地面_类.api_解码(arg_数据)
        size = (32, 32 * ground.api_瓦片数())
        image = pygame.image.frombytes(ground.纹理, size, "P")
        palette = 图像_类(256, 1, list(ground.调色板)).api_RGBA()
        image.set_palette([tuple(palette[i : i + 3]) for i in range(0, 1024, 4)])
        relative = Path("terrain") / f"{arg_条}.png"
        path = self.输出 / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(image, path)
        if pygame.image.tobytes(pygame.image.load(path), "P") != ground.纹理:
            raise ValueError("地形纹理PNG索引不同")
        self._记录(path)
        return {
            "kind": "ground",
            "width_tiles": ground.宽瓦片,
            "height_tiles": ground.高瓦片,
            "reserved": ground.保留,
            "palette_rgb555": ground.调色板,
            "tile_indices": ground.索引,
            "texture_indices_image": relative.as_posix(),
            "tile_count": ground.api_瓦片数(),
        }

    def _条目(self, arg_库: str, arg_条: int, arg_数据: bytes) -> dict:
        if arg_数据[:4] in (b"SPR\0", b"SMP\0"):
            return self._精灵(arg_数据, arg_库, arg_条)
        if len(arg_数据) >= 128 and arg_数据[4:6] == b"\x12\xaf":
            return self._动画(arg_数据, arg_库, arg_条)
        if arg_数据[:4] == b"GND\0":
            return self._地面(arg_数据, arg_条)
        if arg_数据[:4] == b"RIFF" and arg_数据[8:12] == b"WAVE":
            relative = Path("audio") / arg_库 / f"{arg_条}.wav"
            path = self.输出 / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(arg_数据)
            self._记录(path)
            return {"kind": "wav", "file": relative.as_posix()}
        dimensions = {80000: (200, 200), 194776: (388, 251), 84480: (165, 256), 614400: (640, 480)}
        if arg_库 in ("d", "p", "j") and len(arg_数据) in dimensions:
            width, height = dimensions[len(arg_数据)]
            image = 图像_类(width, height, list(struct.unpack(f"<{width * height}H", arg_数据)))
            return {
                "kind": "picture",
                "frames": [self._图(image, Path("images") / arg_库 / str(arg_条) / "0.png")],
            }
        masks = {("p", 8): (72, 67), ("p", 19): (640, 480), ("p", 81): (640, 480)}
        if (arg_库, arg_条) in masks:
            size = masks[arg_库, arg_条]
            if len(arg_数据) != size[0] * size[1]:
                raise ValueError("原命中掩码尺寸不符")
            relative = Path("masks") / f"{arg_库}-{arg_条}.png"
            path = self.输出 / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            image = pygame.image.frombytes(arg_数据, size, "P")
            image.set_palette([(i, i, i) for i in range(256)])
            pygame.image.save(image, path)
            if pygame.image.tobytes(pygame.image.load(path), "P") != arg_数据:
                raise ValueError("命中掩码PNG数值不同")
            self._记录(path)
            return {
                "kind": "mask",
                "file": relative.as_posix(),
                "width": size[0],
                "height": size[1],
            }
        return {"kind": "data", "encoding": "uint8", "values": list(arg_数据)}

    def api_转换(self, arg_字体: Path, arg_音库: Path) -> None:
        archives = {}
        for key in 美术_类.文件名:
            archive = self.美术.api_包(key)
            entries = []
            for i in range(len(archive.条目)):
                data = archive.api_解码(i)
                item = self._条目(key, i, data)
                item["source_sha256"] = hashlib.sha256(data).hexdigest()
                entries.append(self._JSON(Path("entries") / key / f"{i}.json", item))
                self.统计[item["kind"]] += 1
                if i % 64 == 0:
                    total = len(archive.条目)
                    verified = self.统计["verified_png_frames"]
                    print(
                        f"[信息] 转换{key}:{i}/{total}，已验证{verified}图。",
                        flush=True,
                    )
            archives[key] = entries
        files = {p.name.lower(): p for p in self.输入.iterdir() if p.is_file()}
        for name in sorted(set(MIDI播放器_类.歌单 + MIDI播放器_类.上下文文件[1:])):
            target = self.输出 / "music" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(files[name], target)
            self._记录(target)
        for source, name in ((arg_字体, "fonts/ui.ttc"), (arg_音库, "music/gm.dls")):
            target = self.输出 / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            self._记录(target)
        manifest = {
            "format": "reactmono-rich4-open-assets",
            "version": 1,
            "archives": archives,
            "statistics": dict(self.统计),
            "files": self.文件,
        }
        manifest["text"] = self._JSON(
            Path("text/original.json"), 开放文字导入_类.api_导出(self.输入)
        )
        self._JSON(Path("manifest.json"), manifest)
        print("[完成] 开放资源已转换并逐图验证：" + json.dumps(dict(self.统计), ensure_ascii=False))


# ◍ 运行
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="一次性转换正版游戏素材，产物禁止上传GitHub。")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("pygame/assets"))
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--soundbank", type=Path, required=True)
    args = parser.parse_args()
    开放资源导入_类(args.source, args.output).api_转换(args.font, args.soundbank)
