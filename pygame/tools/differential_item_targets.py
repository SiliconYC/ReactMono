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
from rich4.board_models import 相机_类
from rich4.cards import 卡片用法_类, 卡片目标_类, 目标种类_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类, 决策位置_类, 决策种类_类, 决策选项_类
from rich4.graphics import 图像_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.services import 服务_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 物品目标差分_类:
    """
    原目标/遥控骰/抢夺/嫁祸图形、显式夹具与真实核心选择的对照。

    更新日志：
    2026.10.24 - 原触摸目标、同距次序、重放时钟与实际DAT独立观察。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        self.屏 = 物品屏幕_类()
        self.相机 = 相机_类((16, 16))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[list[int]] = []
        self.屏.声音 = lambda n: self.调用.append([0, n])
        self.宿 = 物品宿主_类(
            lambda: self.调用.append([3]),
            lambda ok, text: self.调用.append([4, int(ok)]),
            self._回答,
        )

    def _回答(self, arg_i: int) -> bool:
        ok = self.会.api_回答(arg_i) if self.真实 else False
        self.调用.append([1, arg_i, int(ok)])
        return ok

    @staticmethod
    def _串(arg_文: str) -> list[int]:
        raw, h = arg_文.encode(), 14695981039346656037
        for b in raw:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(raw), h]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        框, 屏 = self.框, self.屏
        old = self.会.世界.api_导出() if op == "D" else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色, p.控制 = (ch + 3 * i) % 12, 1
            self.会 = 游戏会话_类(世界_类.api_从地图(self.美术.api_解码("m", 2 * m + 1), opt), 1)
            屏.api_重置()
            框.按钮.clear()
            self.真实 = False
        elif op == "W":
            profile = int(列[0])
            p = self.会.世界.玩家[1].记录
            p.卡片, p.道具 = [0] * 15, [0] * 15
            if profile:
                p.卡片 = [1 + j + (15 if profile == 2 else 0) for j in range(15)]
                p.道具[:13] = [1 + j % 9 for j in range(13)]
            if profile == 3:
                p.卡片 = [0, 1, 14, 14, 18, 30, 0, 0, 20, 2, 0, 15, 0, 9, 8]
        elif op == "M":
            x, y, r = map(int, 列)
            self.相机 = 相机_类((x, y), r)
        elif op == "B":
            kind, n, cancel = map(int, 列)
            self.决 = 决策_类(决策种类_类.行动目标, 0)
            self.真实 = False
            if kind == 0:
                self.决.选项 = [决策选项_类("", i) for i in range(1, 7)]
                if cancel:
                    self.决.选项.append(决策选项_类("", 0))
            elif kind == 1:
                self.决.被抢玩家 = 1
                if n:
                    p = self.会.世界.玩家[1].记录
                    self.决.选项 = [
                        决策选项_类("", (int(目标种类_类.卡片) << 16) | i)
                        for i in range(1, 31)
                        if i in p.卡片
                    ]
                    self.决.选项 += [
                        决策选项_类("", (int(目标种类_类.道具) << 16) | i)
                        for i in range(1, 14)
                        if p.道具[i - 1]
                    ]
                if cancel:
                    self.决.选项.append(决策选项_类("", -1))
            elif kind == 2:
                self.决.种类 = 决策种类_类.卡片目标
                self.决.选项 = [决策选项_类("", i) for i in range(min(n, 4))]
                if cancel:
                    self.决.选项.append(决策选项_类("", -1))
            elif kind == 3:
                屏._上道具 = n
                self.决.提示 = (
                    服务_类.卡名[cancel - 1]
                    if 1 <= cancel <= 30
                    else "目的"
                    if cancel == 31
                    else ""
                )
                offsets = [
                    (-480, 0),
                    (-448, 0),
                    (-400, 0),
                    (-64, 0),
                    (-32, 0),
                    (-16, 0),
                    (0, 0),
                    (1, 0),
                    (16, 0),
                    (32, 0),
                    (64, 0),
                    (400, 0),
                    (448, 0),
                    (480, 0),
                    (0, -400),
                    (0, 400),
                    (320, 320),
                    (-320, -320),
                ]
                cx, cy = self.相机.中心
                self.决.选项 = [
                    决策选项_类("", i, 决策位置_类(cx + x, cy + y))
                    for i, (x, y) in enumerate(offsets)
                ]
                self.决.选项.append(决策选项_类("", -1))
            else:
                raise ValueError(kind)
        elif op == "A":
            kind = int(列[0])
            p = self.会._玩家()
            p.卡片, p.道具 = [0] * 15, [0] * 15
            if kind == 0:
                p.道具[7] = 1
                ok = self.会.api_用道具(8)
            else:
                victim = self.会.世界.玩家[1].记录
                victim.x, victim.y, victim.节点, victim.上次节点 = p.x, p.y, p.节点, p.上次节点
                p.卡片[0] = 13
                ok = self.会.api_用卡(卡片用法_类(13, 卡片目标_类(目标种类_类.角色, 1)))
            if not ok or self.会.待决策 is None:
                raise ValueError("未到达真实物品决策")
            self.决, self.真实 = self.会.待决策, True
        elif op == "C":
            t = int(列[0])
            屏.时钟 = t if t >= 0 else None
        elif op == "R":
            屏.api_重置()
            框.按钮.clear()
        elif op == "V":
            框.指针x, 框.指针y = map(int, 列)
        elif op == "D":
            kind, t, x, y, down, selected = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            屏.截图名 = ""
            if kind == 0:
                屏.api_画遥控骰(框, self.决, self.宿)
            elif kind == 1:
                屏.api_画抢夺(框, self.会, self.决, self.宿)
            elif kind == 2:
                屏.api_画嫁祸(框, self.会, self.决, self.宿)
            else:
                屏.api_画地图目标(
                    框,
                    self.决,
                    self.相机,
                    selected if selected >= 0 else None,
                    lambda i: self.调用.append([2, i]),
                )
        elif op == "X":
            id = int(列[0])
            for b in 框.按钮:
                if b.编号 == id and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
            else:
                raise ValueError(f"预期目标按钮不存在：{id}")
        else:
            raise ValueError(op)
        dat = self.会.世界.api_导出()
        if old is not None and old != dat:
            raise ValueError("绘制改变World DAT")
        d = self.会.待决策
        数 = [-1, int(self.会.阶段), self.会.随机.状态, int(d is not None)]
        if d is not None:
            数 += [int(d.种类), len(d.选项)]
        数 += [int(屏._抢夺选择 is not None)]
        if 屏._抢夺选择 is not None:
            数.append(屏._抢夺选择)
        数 += [屏._上道具, int(屏.时钟 is not None)]
        if 屏.时钟 is not None:
            数.append(屏.时钟)
        数 += [*self._串(屏.截图名), len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        数 += [len(dat)]
        raw = array("H", 框.画布.像素) if op == "D" else array("H")
        if byteorder != "little":
            raw.byteswap()
        return " ".join(map(str, 数)), raw.tobytes(), dat

    @staticmethod
    def _命令() -> list[str]:
        组 = ["N 0 0"]
        for rotation in range(8):
            组 += [f"M 1001 2003 {rotation}"]
            for card, tool in (
                [(0, t) for t in range(14)] + [(c, 0) for c in range(1, 31)] + [(31, 11)]
            ):
                组 += [f"B 3 {tool} {card}"]
                for selected in (-1, 0, 6, 7, 99):
                    组 += [f"D 3 {rotation * 199} 220 260 0 {selected}", "V 221 260", "X 5006"]
        for card in range(1, 31):
            组 += ["M 16 16 0", f"B 3 0 {card}"]
            for tick in range(15):
                组.append(f"D 3 {tick * 100} -1 -1 0 6")
        for ch in range(12):
            for count in range(5):
                for cancel in (0, 1):
                    组 += [
                        f"N {ch % 8} {ch}",
                        f"B 2 {count} {cancel}",
                        "D 2 1 220 320 1 -1",
                        "D 2 2 120 330 1 -1",
                    ]
        for cancel in (0, 1):
            组 += ["N 0 0", f"B 0 0 {cancel}"]
            for face in range(6):
                组 += [f"D 0 1 {110 + 40 * face} 320 1 -1", f"X {210 + face}"]
        for profile in range(4):
            组 += ["N 0 3", f"W {profile}", "B 1 1 1", "D 1 1 30 90 1 -1"]
            if profile:
                组 += [
                    "X 210",
                    "D 1 2 30 90 0 -1",
                    "X 210",
                    "D 1 3 -1 -1 0 -1",
                    "X 210",
                    "R",
                    "B 1 0 0",
                    "D 1 4 -1 -1 0 -1",
                ]
        for m in range(8):
            for face in range(7):
                组 += [f"N {m} {m}", "A 0", f"D 0 10 {110 + 40 * face} 320 1 -1", f"X {210 + face}"]
            for profile in (1, 2, 3):
                组 += [
                    f"N {m} {m}",
                    f"W {profile}",
                    "A 1",
                    "D 1 10 30 90 1 -1",
                    "X 210",
                    "D 1 11 30 90 0 -1",
                    "X 210",
                ]
        组 += [
            "N 0 0",
            "M 16 16 0",
            "B 3 11 31",
            "C 0",
            "D 3 9999 220 260 0 6",
            "C 639",
            "D 3 9999 -1 -1 0 6",
            "C 640",
            "D 3 9999 -1 -1 0 6",
            "C -1",
        ]
        return 组

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_报告: Path,
        arg_核心: bool = False,
        arg_重置边界: bool = False,
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
        工具 = 构 / "item-targets-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        头 = 构 / "item-targets-shim/SDL3/SDL_timer.h"
        头.parent.mkdir(parents=True, exist_ok=True)
        头.write_text(
            '#pragma once\n#include <cstdint>\nextern "C" std::uint64_t SDL_GetTicks();\n'
        )
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(头.parents[1]),
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("item_targets_oracle.cpp")),
                str(arg_源码 / "tools/screens/messages.cpp"),
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
                "direct original target/dice/steal/frame-up screens, real maps and assets, "
                "explicit display fixtures and actual GameSession dice/steal choices, phase/RNG "
                "and complete World DAT, "
                "real sprites, internal state and callbacks; "
                "not actual window or full Application integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "reset-edge" if arg_重置边界 else "core-only" if arg_核心 else "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "item_screens.py",
                    "item_choice_screens.py",
                    "item_targets.py",
                    "item_paint.py",
                    "item_screen_types.py",
                    "message_overlay.py",
                    "native_frame.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/item_screens.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            commands = cls._命令()
            if arg_核心:
                commands = commands[commands.index("A 0") - 1 :]
            if arg_重置边界:
                commands = [
                    "N 0 0",
                    "W 1",
                    "B 1 1 1",
                    "D 1 1 30 90 0 -1",
                    "X 210",
                    "R",
                    "B 1 0 1",
                    "D 1 2 -1 -1 0 -1",
                ]
            for i, 行 in enumerate(commands):
                报["last_command"], 报["last_index"] = 行, i
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    error = 进.stderr.read().decode()
                    try:
                        自._操作(行, i)
                    except (ValueError, IndexError, AttributeError) as py_error:
                        报["python_exception"] = type(py_error).__name__ + ": " + str(py_error)
                    raise ValueError("C++提前结束：" + error)
                cpp = 进.stdout.read(614400) if 行[:1] == "D" else b""
                if 行[:1] == "D" and len(cpp) != 614400:
                    raise ValueError("C++画布输出截断")
                大小 = int(实.split()[-1])
                cpp_dat = 进.stdout.read(大小)
                if len(cpp_dat) != 大小:
                    raise ValueError("C++世界输出截断")
                预, py, py_dat = 自._操作(行, i)
                if 实 != 预:
                    报["failure_command"] = 行
                    报["cpp"] = 实
                    报["python"] = 预
                    raise ValueError(f"step={i} metadata differs")
                if cpp != py:
                    位 = next(j for j, (a, b) in enumerate(zip(cpp, py)) if a != b)
                    报["failure_command"] = 行
                    raise ValueError(f"step={i} pixel={位 // 2 % 640},{位 // 2 // 640}")
                if cpp_dat != py_dat:
                    位 = next((j for j, (a, b) in enumerate(zip(cpp_dat, py_dat)) if a != b), -1)
                    raise ValueError(f"step={i} World DAT differs at {位}")
                摘.update(cpp_dat)
                摘.update(实.encode())
                摘.update(cpp)
                输.update((行 + "\n").encode())
                报["commands"] = i + 1
                报["painted_frames"] += int(bool(cpp))
            进.stdin.close()
            退 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退 or 错:
                raise ValueError("参考目标界面故障：" + 错)
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
    参数.add_argument("--core-only", action="store_true")
    参数.add_argument("--reset-edge", action="store_true")
    选项 = 参数.parse_args()
    物品目标差分_类.api_执行(
        选项.source,
        选项.build,
        选项.assets,
        选项.font,
        选项.report,
        选项.core_only,
        选项.reset_edge,
    )
