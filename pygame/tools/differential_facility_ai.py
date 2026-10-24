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

from rich4.ai_settings_screen import 托管动作_类, 托管屏幕_类
from rich4.artwork import 美术_类
from rich4.facility_picker import 设施选择_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类, 决策位置_类, 决策种类_类, 决策选项_类, 托管设置_类
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 设施托管差分_类:
    """
    原设施选择/托管设置，真实会话读取设置，完整画布/副本状态与回调对照。

    更新日志：
    2026.10.24 - 真实素材和字体；提交仅捕获，不伪称完整主应用接线。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[list[int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append([0, n]))
        self.动 = 托管动作_类(
            lambda i, e: self.调用.append([2, i, *self._设置(e)]), lambda: self.调用.append([3, 0])
        )

    @staticmethod
    def _设置(arg_设: 托管设置_类) -> list[int]:
        return [int(arg_设.自动), arg_设.卡片策略, arg_设.性格, arg_设.现金比例, arg_设.股票比例]

    @staticmethod
    def _串(arg_文: str) -> list[int]:
        data = arg_文.encode()
        h = 14695981039346656037
        for b in data:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(data), h]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        框, 宿 = self.框, self.宿
        readonly = op in ("F", "D", "X", "B", "E", "O")
        old = (self.会.世界.api_导出(), self.会.随机.状态) if readonly else None
        结果 = -1
        if op == "N":
            图, 人, mask = map(int, 列)
            设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            for i, p in enumerate(设.玩家):
                p.角色, p.控制 = (人 + i * 3) % 12, 1 if mask & (1 << i) else 2
            self.会 = 游戏会话_类(世界_类.api_从地图(self.美术.api_解码("m", 图 * 2 + 1), 设))
            self.选, self.AI = 设施选择_类(), 托管屏幕_类()
            self.决 = 决策_类(决策种类_类.购地, 0)
            框.按钮.clear()
        elif op == "Q":
            kind, valid, count, *options = map(int, 列)
            self.决 = 决策_类(决策种类_类(kind), 0, 提示=设施选择_类.提示 if valid else "other")
            self.决.选项 = [
                决策选项_类("", options[i * 2], 决策位置_类(0, 0) if options[i * 2 + 1] else None)
                for i in range(count)
            ]
            结果 = int(self.选.api_接管(self.决)) * 2 + int(self.选.api_可取消(self.决))
        elif op in ("F", "D"):
            t, x, y, down = map(int, 列[:4])
            key = 列[4]
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            if op == "F":
                self.选.api_绘制(宿, self.决, key, lambda n: self.调用.append([1, n]))
            else:
                self.AI.api_绘制(宿, self.会.世界, self.动)
        elif op == "O":
            结果 = int(self.AI.api_打开(self.会, int(列[0])))
        elif op == "V":
            slot, on, cards, pers, cash, stock = map(int, 列)
            self.AI._编辑[slot] = 托管设置_类(bool(on), cards, pers, cash, stock)
        elif op == "X":
            for b in 框.按钮:
                if b.编号 == int(列[0]) and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
        elif op == "B":
            self.选.api_取消(宿, self.决, lambda n: self.调用.append([1, n]))
        elif op == "E":
            self.AI.api_取消(宿, self.动)
        else:
            raise ValueError(op)
        if readonly and old != (self.会.世界.api_导出(), self.会.随机.状态):
            raise ValueError("界面编辑改变世界DAT或随机流")
        数 = [结果, self.会.随机.状态, int(self.会.阶段)] + self._串(self.选._键)
        数 += [self.选._选中 if self.选._选中 is not None else -1, self.AI._选中]
        for a in (self.AI._编辑, self.AI._原值):
            for e in a:
                数.append(int(e is not None))
                if e is not None:
                    数 += self._设置(e)
        数 += [len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        像 = b""
        if op in ("F", "D"):
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _命令() -> list[str]:
        组 = ["N 0 0 15"]
        for kind in range(21):
            for valid in (0, 1):
                for extra in ("0", "2 0 0 -1 0", "1 0 1", "1 5 0", "1 -2 0"):
                    组.append(f"Q {kind} {valid} {extra}")
        for kind in (7, 17):
            for mask in range(32):
                vals = [i for i in reversed(range(5)) if mask & (1 << i)] + (
                    [-1] if kind == 17 else []
                )
                组 += [
                    f"Q {kind} 1 {len(vals)} " + " ".join(f"{v} 0" for v in vals),
                    f"F 0 -1 -1 0 k{kind}-{mask}",
                ]
                for i, v in enumerate(vals):
                    if v < 0:
                        continue
                    组 += [
                        f"X {210 + i}",
                        f"F 1 100 300 1 k{kind}-{mask}",
                        f"X {210 + i}",
                        f"F 2 -1 -1 0 k{kind}-{mask}",
                    ]
                组 += ["X 207", "B", f"F 3 -1 -1 0 new{kind}-{mask}"]
        for 图 in range(8):
            for mask in (0, 1, 5, 10, 15):
                for current in (-1, 0, 2, 3, 4):
                    组 += [f"N {图} {图 % 12} {mask}", f"O {current}", "D 0 -1 -1 0 ai"]
                    if not mask:
                        组 += ["E"]
                        continue
                    for id in (
                        1600,
                        1602,
                        1602,
                        1610,
                        1611,
                        1612,
                        1613,
                        1614,
                        1620,
                        1621,
                        1623,
                        1624,
                    ):
                        组 += [f"X {id}", "D 1 -1 -1 0 ai"]
                    for x in (309, 310, 317, 318, 389, 390):
                        组 += [f"D 2 {x} 340 1 ai", f"D 3 {x} 375 1 ai"]
                    组 += ["D 4 490 180 1 ai", "X 1630", "D 5 490 260 1 ai", "X 1631", "E"]
        for cards in range(4):
            for ratio in (0, 1, 9, 10, 90, 99, 100, 255):
                组 += [
                    "N 0 11 15",
                    "O 2",
                    f"V 2 1 {cards} 255 {ratio} {ratio}",
                    "D 0 -1 -1 0 ai",
                    "X 1620",
                    "X 1624",
                    "D 1 -1 -1 0 ai",
                    "X 1630",
                ]
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
        工具 = 构 / "facility-ai-oracle"
        头 = 构 / "facility-ai-shim/SDL3/SDL_timer.h"
        头.parent.mkdir(parents=True, exist_ok=True)
        头.write_text(
            '#pragma once\n#include <cstdint>\nextern "C" std::uint64_t SDL_GetTicks();\n'
        )
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
                str(头.parents[1]),
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("facility_ai_oracle.cpp")),
                str(arg_源码 / "tools/screens/facility.cpp"),
                str(arg_源码 / "tools/screens/ai_settings.cpp"),
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
                "direct original facility Picker and AiSettingsScreen, "
                "real GameSession settings source, "
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
                    "facility_picker.py",
                    "ai_settings_screen.py",
                    "message_overlay.py",
                    "native_frame.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/facility_picker.py").read_bytes()
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
                raise ValueError("参考设施/托管故障：" + 错)
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
    设施托管差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
