# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from array import array
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.options_screen import 选项屏幕_类
from rich4.options_types import 选项动作_类, 选项状态_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.save_slot_screen import 存档槽_类, 存档槽屏幕_类
from rich4.screen_draw import 屏幕宿主_类


# ◕ 功能
class 选项存档差分_类:
    """
    原选项/存档槽，真实外部图片/歌曲原文、状态和回调的完整组件对照。

    更新日志：
    2026.10.24 - 槽位只是明确摘要夹具，不伪称真实存档/跨进程恢复。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        text = 原版文字_类(原版程序_类.api_读取(exe))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[list[int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append([0, n]))
        self.选项, self.存档 = 选项屏幕_类(text), 存档槽屏幕_类()
        self.数据 = [存档槽_类() for _ in range(6)]
        self.能力, self.曲 = 15, 0

    @staticmethod
    def _状态(arg_s: 选项状态_类) -> list[int]:
        return [arg_s.速度, int(arg_s.音乐), int(arg_s.音效), int(arg_s.动画)]

    def _动作(self) -> 选项动作_类:
        return 选项动作_类(
            lambda s: self.调用.append([1, *self._状态(s)]),
            lambda: self.调用.append([2, 0]),
            (lambda n: self.调用.append([3, n])) if self.能力 & 1 else None,
            self.曲,
            (lambda: self.调用.append([4, 0])) if self.能力 & 2 else None,
            (lambda: self.调用.append([5, 0])) if self.能力 & 4 else None,
            (lambda: self.调用.append([6, 0])) if self.能力 & 8 else None,
        )

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        框, 宿, 屏, 档 = self.框, self.宿, self.选项, self.存档
        if op == "O":
            speed, music, sound, animation, ingame, self.能力, self.曲 = map(int, 列)
            屏.api_打开(选项状态_类(speed, bool(music), bool(sound), bool(animation)), bool(ingame))
        elif op == "S":
            slot, valid, day, month, year, m, stage, count, *chars = map(int, 列)
            if len(chars) != count:
                raise ValueError("槽位人物数量不符")
            self.数据[slot] = 存档槽_类(bool(valid), (day, month, year), m, stage, chars)
        elif op == "L":
            档.api_打开(bool(int(列[0])), self.数据)
        elif op in ("D", "F"):
            t, x, y, down = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            if op == "D":
                屏.api_绘制(宿, self._动作())
            else:
                档.api_绘制(
                    宿, lambda n: self.调用.append([7, n]), lambda: self.调用.append([8, 0])
                )
        elif op == "X":
            for b in 框.按钮:
                if b.编号 == int(列[0]) and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
        else:
            raise ValueError(op)
        数 = [-1, *self._状态(屏._状态), int(屏._局内), 屏._确认, int(档._保存), 档._悬选]
        for s in 档._档:
            数 += [int(s.有效), *s.日期, s.地图, s.阶段, len(s.人物), *s.人物]
        数 += [len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        像 = b""
        if op in ("D", "F"):
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        for ingame in (0, 1):
            for speed in (0, 1, 2, 3, 4, 999):
                for flags in range(8):
                    caps = 15 if flags % 2 else 0
                    song = flags + 1
                    组 += [
                        f"O {speed} {flags & 1} {flags >> 1 & 1} "
                        f"{flags >> 2} {ingame} {caps} {song}",
                        "D 0 -1 -1 0",
                        "D 1 244 85 1",
                        "X 50",
                        "D 2 400 85 1",
                        "X 57",
                        "D 3 -1 -1 0",
                        "X 59",
                        "D 4 300 390 1",
                        "X 55",
                    ]
        for ingame in (0, 1):
            for caps in range(16):
                for id in (47, 48, 51, 52, 53, 54, 55, 56, 57, 61, 62, 63):
                    组 += [
                        f"O 1 0 0 0 {ingame} {caps} 0",
                        "D 0 175 400 1",
                        f"X {id}",
                        "D 1 270 250 1",
                        "X 58",
                        "D 2 -1 -1 0",
                    ]
        for song in range(10):
            for y in (200, 285, 299, 300, 389, 404, 500):
                组 += [f"O 1 1 1 1 0 15 {song}", f"D 0 200 {y} 1", "X 56", "D 1 -1 -1 0"]
        for mask in (0, 1, 21, 42, 63):
            for slot in range(6):
                valid = (mask >> slot) & 1
                组 += [
                    f"S {slot} {valid} {slot + 1} {slot + 1} {1998 + slot} "
                    f"{slot + 2} {slot % 3} 5 {slot} {slot + 1} 11 255 4"
                ]
            for saving in (0, 1):
                组.append(f"L {saving}")
                for x, y in (
                    (-1, -1),
                    (129, 25),
                    (130, 25),
                    (576, 455),
                    (577, 455),
                    (150, 58),
                    (150, 416),
                    (150, 417),
                ):
                    组.append(f"F 0 {x} {y} 0")
                for id in [520 + i for i in range(6)] + [530 + i for i in range(6)] + [429, 529]:
                    组 += ["F 1 150 200 1", f"X {id}", "F 2 -1 -1 0"]
        组 += ["S 0 1 255 255 65535 65535 65535 0", "L 0", "S 0 0 1 1 1998 0 0 0", "F 0 -1 -1 0"]
        return 组

    @classmethod
    def api_执行(
        cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_字体: Path, arg_报告: Path
    ) -> None:
        版 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        构 = arg_构建.resolve()
        工具 = 构 / "options-slots-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("options_slots_oracle.cpp")),
                str(arg_源码 / "tools/screens/menus.cpp"),
                str(arg_源码 / "tools/screens/draw.cpp"),
                str(构 / "librich4_core.a"),
                *链,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
        )
        自 = cls(arg_素材, arg_字体)
        进 = subprocess.Popen(
            [str(工具), str(arg_素材), str(arg_字体)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        报 = {
            "reference": 版,
            "status": "running",
            "commands": 0,
            "painted_frames": 0,
            "scope": (
                "direct original OptionsScreen and SaveLoadScreen, "
                "private state and captured settings/slot callbacks, "
                "real sprites, internal state and callbacks; "
                "not actual window/financial rule integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "options_screen.py",
                    "options_types.py",
                    "save_slot_screen.py",
                    "original_text.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/options_screen.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            for i, 行 in enumerate(cls._命令()):
                报["last_command"], 报["last_index"] = 行, i
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "F") else b""
                if 行[:1] in ("D", "F") and len(cpp) != 614400:
                    raise ValueError("C++画布输出截断")
                预, py = 自._操作(行, i)
                if 实 != 预:
                    报["failure_command"] = 行
                    报["cpp"] = 实
                    报["python"] = 预
                    raise ValueError(f"step={i} metadata differs")
                if cpp != py:
                    位 = next(j for j, (a, b) in enumerate(zip(cpp, py)) if a != b)
                    报["failure_command"] = 行
                    raise ValueError(f"step={i} pixel={位 // 2 % 640},{位 // 2 // 640}")
                摘.update(实.encode())
                摘.update(cpp)
                输.update((行 + "\n").encode())
                报["commands"] = i + 1
                报["painted_frames"] += int(bool(cpp))
            进.stdin.close()
            退 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退 or 错:
                raise ValueError("参考选项/存档故障：" + 错)
            报.update(
                status="passed",
                state_sha256=摘.hexdigest(),
                input_sha256=输.hexdigest(),
                compared_pixels=报["painted_frames"] * 307200,
            )
        except (ValueError, OSError, IndexError, AttributeError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            if 进.poll() is None:
                进.terminate()
                进.wait()
            自.字体.api_关闭()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(报))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    选项存档差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
