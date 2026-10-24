# SPDX-License-Identifier: GPL-3.0-or-later
# 只读审计源素材与本地开放资源；公开报告仅保存数量/哈希和失败位置。
# ◑ 导入
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.flc import 动画_类
from rich4.graphics import 图像_类
from rich4.midi_player import MIDI播放器_类
from rich4.open_archive import 开放档案_类
from rich4.terrain import 地面_类


# ◕ 功能
class 开放资源审计_类:
    """
    全条目/全图帧/透明原点/换色位置/地形/WAV/MIDI与磁盘内容审计。

    更新日志：
    2026.10.24 - 不把导入时自检替代独立读回；不上传商业内容或原程序。
    """

    @staticmethod
    def api_执行(arg_来源: Path, arg_开放: Path, arg_报告: Path) -> None:
        source = 美术_类(arg_来源)
        manifest = json.loads((arg_开放 / "manifest.json").read_text())
        stats: Counter[str] = Counter()
        trace = hashlib.sha256()
        report = {
            "status": "running",
            "scope": "Python original codecs versus fresh open-format file reads; "
            "no new C++ full-frame/OS/manual claim",
            "statistics": {},
            "manifest_sha256": hashlib.sha256(
                (arg_开放 / "manifest.json").read_bytes()
            ).hexdigest(),
        }
        try:
            for key in 美术_类.文件名:
                original = source.api_包(key)
                opened = 开放档案_类(arg_开放, key)
                if len(original.条目) != len(opened.条目):
                    raise ValueError("档案条目数不同")
                for entry in range(len(original.条目)):
                    report["last_entry"] = [key, entry]
                    data = original.api_解码(entry)
                    metadata = opened.api_元数据(entry)
                    if hashlib.sha256(data).hexdigest() != metadata["source_sha256"]:
                        raise ValueError("源条目哈希不同")
                    kind = metadata["kind"]
                    if kind == "sprite":
                        count = int.from_bytes(data[4:8], "little")
                        if count != opened.api_帧数(entry):
                            raise ValueError("精灵帧数不同")
                        offset = int.from_bytes(data[8:12], "little") + (
                            512 if metadata["indexed"] else 0
                        )
                        for frame in range(count):
                            expected, actual = (
                                图像_类.api_解码(data, frame),
                                opened.api_帧(entry, frame),
                            )
                            if expected != actual:
                                raise ValueError(f"精灵PNG不同：{frame}")
                            size = struct.unpack_from("<I", data, 20 + frame * 12)[0]
                            actual_team = [
                                i
                                for start, end in opened.api_换色段(entry, frame)
                                for i in range(start, end)
                            ]
                            expected_team = (
                                [i for i, v in enumerate(data[offset : offset + size]) if v == 255]
                                if metadata["indexed"]
                                else []
                            )
                            if actual_team != expected_team:
                                raise ValueError("玩家换色索引255不同")
                            offset += size
                            trace.update(actual.api_RGBA())
                            stats["sprite_frames"] += 1
                    elif kind == "animation":
                        movie = 动画_类(data)
                        if (
                            movie.帧数 != opened.api_帧数(entry)
                            or movie.间隔毫秒 != metadata["interval_ms"]
                        ):
                            raise ValueError("动画帧数或间隔不同")
                        frame = 0
                        while movie.api_下一帧():
                            actual = opened.api_帧(entry, frame)
                            if movie.api_图像() != actual:
                                raise ValueError(f"动画PNG不同：{frame}")
                            trace.update(actual.api_RGBA())
                            stats["animation_frames"] += 1
                            frame += 1
                    elif kind == "picture":
                        actual = opened.api_帧(entry, 0)
                        pixels = list(struct.unpack(f"<{len(data) // 2}H", data))
                        if actual.像素 != pixels or actual.不透明 or actual.原点x or actual.原点y:
                            raise ValueError("原图PNG像素或元数据不同")
                        trace.update(actual.api_RGBA())
                        stats["pictures"] += 1
                    elif kind == "ground":
                        if 地面_类.api_解码(data) != opened.api_地面(entry):
                            raise ValueError("地形JSON/PNG不同")
                        stats["grounds"] += 1
                    else:
                        if data != opened.api_解码(entry):
                            raise ValueError("WAV/命中掩码/JSON数据字节不同")
                        trace.update(data)
                        stats[kind + "_entries"] += 1
                    stats["entries"] += 1
                print(f"[信息] 已审计{key}，累计{stats['entries']}条目。", flush=True)
            files = {p.name.lower(): p for p in arg_来源.iterdir() if p.is_file()}
            for name in set(MIDI播放器_类.歌单 + MIDI播放器_类.上下文文件[1:]):
                if files[name].read_bytes() != (arg_开放 / "music" / name).read_bytes():
                    raise ValueError("MIDI文件不同：" + name)
                stats["midi_files"] += 1
            root = arg_开放.resolve()
            for name, info in manifest["files"].items():
                path = (root / name).resolve()
                if not path.is_relative_to(root):
                    raise ValueError("清单文件越出资源目录")
                payload = path.read_bytes()
                if (
                    len(payload) != info["bytes"]
                    or hashlib.sha256(payload).hexdigest() != info["sha256"]
                ):
                    raise ValueError("磁盘文件哈希不同：" + name)
                stats["verified_files"] += 1
                stats["asset_bytes"] += len(payload)
            illegal = [
                str(p.relative_to(root))
                for p in root.rglob("*")
                if p.is_file() and p.suffix.lower() in (".mkf", ".flc", ".spr", ".smp", ".exe")
            ]
            if illegal:
                raise ValueError("开放目录残留私有媒体或原程序：" + repr(illegal))
            report.update(status="passed", content_sha256=trace.hexdigest())
        except (ValueError, OSError, IndexError, KeyError) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            report["statistics"] = dict(stats)
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report, ensure_ascii=False))


# ◍ 运行
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    开放资源审计_类.api_执行(args.source, args.assets, args.report)
