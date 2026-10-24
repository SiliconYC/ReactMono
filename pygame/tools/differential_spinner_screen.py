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
from rich4.game_types import 决策_类, 决策种类_类, 效果_类, 效果种类_类, 转盘状态_类
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.spinner_screen import 转盘声音_类, 转盘屏幕_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 转盘画面差分_类:
    """
    固定原Spinners，真实外部美术/字体/原文，完整画布及私有随机时序对照。

    更新日志：
    2026.10.24 - 显式已结算效果与交互状态夹具，音频只观察请求，不称为实际听感。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.美术, self.字体 = 美术_类(arg_素材), 字体_类(arg_字体)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        self.原文 = 原版文字_类(原版程序_类.api_读取(exe))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用 = []

    @staticmethod
    def _状态(arg_s: 转盘状态_类) -> list[int]:
        s = arg_s
        return [s.类型, *s.数位, s.阶段, s.游标, s.主体, s.种子, s.结果]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        结果 = -1
        if op in ("F", "D"):
            self.框.画布 = 图像_类(
                640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)]
            )
        if op == "N":
            图, 人 = map(int, 列)
            设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            设.玩家[0].角色 = 人
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", 图 * 2 + 1), 设)
            self.框.按钮.clear()
            self.屏 = 转盘屏幕_类(
                转盘声音_类(
                    lambda n: self.调用.append((0, n)),
                    lambda n: self.调用.append((1, n)),
                    lambda: self.调用.append((2, 0)),
                ),
                self.原文,
            )
        elif op in ("E", "D"):
            k, has, t, d0, d1, d2, d3, phase, cursor, subject, seed, result = map(int, 列)
            s = 转盘状态_类(t, [d0, d1, d2, d3], phase, cursor, subject, seed, result)
            if op == "E":
                self.屏.api_入队(效果_类(效果种类_类(k), 转盘=s if has else None))
            else:
                self.框.按钮.clear()
                self.屏.api_绘决策(
                    self.框,
                    self.世,
                    决策_类(决策种类_类(k), 0, 转盘=s),
                    901,
                    lambda: self.调用.append((3, 901)),
                )
        elif op == "F":
            self.框.按钮.clear()
            self.屏.api_绘效果(self.框, self.世, int(列[0]), 901)
        elif op == "Z":
            self.屏.api_收帧()
        elif op == "S":
            self.屏.api_跳过(bool(int(列[0])))
        elif op == "C":
            self.屏.api_清空()
        elif op == "X":
            for b in self.框.按钮:
                if b.编号 == int(列[0]):
                    动作 = b.动作
                    self.框.按钮.clear()
                    动作()
                    break
        elif op == "V":
            k, has, d = map(int, 列)
            s = 转盘状态_类() if has else None
            结果 = int(
                self.屏.api_处理决策(决策_类(决策种类_类(k), 0, 转盘=s))
                if d
                else self.屏.api_处理效果(效果_类(效果种类_类(k), 转盘=s))
            )
        else:
            raise ValueError(op)
        屏 = self.屏
        数 = [结果, int(屏._跳过), 屏._待循环, 屏._正在循环, 屏._决策阶段, len(屏._队列)]
        for e in 屏._队列:
            数 += [int(e.种类), int(e.转盘 is not None)]
            if e.转盘 is not None:
                数 += self._状态(e.转盘)
        数.append(int(屏._当前 is not None))
        if (p := 屏._当前) is not None:
            数 += [
                int(p.效果.种类),
                *self._状态(p.效果.转盘),
                *self._状态(p.状态),
                p.已过,
                p.帧数,
                p.轮状态,
                p.周期,
                p.计数,
                p.上次,
                p.随机.状态,
                int(p.跳过),
                int(p.机器 is not None),
            ]
            if (m := p.机器) is not None:
                数 += [*m.数字, m.省位, m.阶段, m.帧数, m.减速周期, m.减速累计, m.上次减速位]
        数.append(len(self.框.按钮))
        for b in self.框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数.append(len(self.调用))
        for k, n in self.调用:
            数 += [k, n]
        像 = b""
        if op in ("F", "D"):
            raw = array("H", self.框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _静态命令() -> list[str]:
        组 = ["N 0 0"]
        for 决, 数 in ((0, 33), (1, 21)):
            for k in range(数):
                for has in (0, 1):
                    组.append(f"V {k} {has} {决}")
        for 图 in range(8):
            组.append(f"N {图} {图 % 12}")
            for t in (1, 2, 5, 6):
                for phase in range(11):
                    digits = [(phase * 3 + j * 7) % 20 for j in range(4)]
                    组 += [f"D 19 1 {t} " + " ".join(map(str, digits)) + f" {phase} 0 0 1 0", "Z"]
            for t in (0, 1, 2, 3, 255):
                for cursor in range(12):
                    subject = (cursor % 6) - 1
                    组 += [f"D 9 1 {t} 0 0 0 0 1 {cursor} {subject} 1 0", "Z"]
            组 += ["X 901", "C", "Z"]
        return 组

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_报告: Path,
        arg_仅静态: bool = False,
        arg_生命周期: bool = False,
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
        头 = 构 / "spinner-shim/SDL3/SDL_timer.h"
        头.parent.mkdir(parents=True, exist_ok=True)
        头.write_text(
            '#pragma once\n#include <cstdint>\nextern "C" std::uint64_t SDL_GetTicks();\n'
        )
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        工具 = 构 / "spinner-screen-oracle"
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
                str(Path(__file__).with_name("spinner_screen_oracle.cpp")),
                str(arg_源码 / "tools/screens/spinners.cpp"),
                str(arg_源码 / "tools/screens/messages.cpp"),
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
            "static_only": arg_仅静态,
            "lifecycle_only": arg_生命周期,
            "scope": (
                "direct original Spinners, external assets/font/text, "
                "explicit decisions and effect DTOs, full private replay state; "
                "not natural triggers, main-game handoff or audible playback"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/spinner_screen.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()

        def 操作(arg_行: str) -> None:
            进.stdin.write((arg_行 + "\n").encode())
            进.stdin.flush()
            实 = 进.stdout.readline().decode().strip()
            if not 实:
                raise ValueError("C++提前结束：" + 进.stderr.read().decode())
            cpp = 进.stdout.read(614400) if arg_行[:1] in ("D", "F") else b""
            原 = 自.世.api_导出() if hasattr(自, "世") else None
            预, py = 自._操作(arg_行, 报["commands"])
            if arg_行[:1] != "N" and 原 != 自.世.api_导出():
                raise ValueError("转盘表现修改了世界")
            if 实 != 预:
                Path(".research-cache/spinner-private-failure.json").write_text(
                    json.dumps({"cpp": 实, "python": 预})
                )
                报["failure_command"] = arg_行
                raise ValueError(f"step={报['commands']} metadata differs")
            if cpp != py:
                位 = next(i for i, (a, b) in enumerate(zip(cpp, py)) if a != b)
                报["failure_command"] = arg_行
                raise ValueError(f"step={报['commands']} pixel={位 // 2 % 640},{位 // 2 // 640}")
            摘.update(实.encode())
            摘.update(cpp)
            输.update((arg_行 + "\n").encode())
            报["commands"] += 1
            报["painted_frames"] += int(bool(cpp))
            if 报["commands"] % 100 == 0:
                arg_报告.parent.mkdir(parents=True, exist_ok=True)
                arg_报告.write_text(json.dumps(报, indent=2) + "\n")

        try:
            for 行 in [] if arg_生命周期 else cls._静态命令():
                操作(行)
            if not arg_仅静态 and not arg_生命周期:
                for n, (k, t, phase) in enumerate(
                    [(12, t, 1) for t in (1, 2, 5, 6)]
                    + [(13, t, p) for t in range(4) for p in (1, 2)]
                ):
                    操作(f"N {n % 8} {n % 12}")
                    操作(f"E {k} 1 {t} 0 0 0 0 {phase} {n % 12} {n % 4} {n * 12345 + 1} 0")
                    for j in range(2048):
                        if not 自.屏.api_活跃():
                            break
                        操作(f"F {(0, 29, 1, 30, 60, 100, 9999)[j % 7]}")
                        p = 自.屏._当前
                        if p and p.轮状态 == 5 and p.效果.转盘.阶段 == 2 and j % 2:
                            操作("X 901")
                        操作("Z")
                    else:
                        raise ValueError("转盘重放未结束")
                    操作("C")
                    操作("Z")
            if arg_生命周期:
                for 行 in (
                    "N 0 0",
                    "S 1",
                    "E 13 1 0 0 0 0 0 1 0 1 1 0",
                    "F 100",
                    "Z",
                    "S 0",
                    "E 13 1 0 0 0 0 0 2 0 1 1 0",
                    "E 12 1 1 0 0 0 0 1 0 0 7 0",
                    "F 100",
                    "Z",
                    "S 1",
                    "E 13 1 0 0 0 0 0 1 0 1 1 0",
                    "C",
                    "Z",
                    "S 0",
                    "D 19 1 1 0 0 0 0 1 0 0 1 0",
                    "Z",
                    "C",
                    "D 19 1 1 0 0 0 0 2 0 0 1 0",
                    "X 901",
                    "Z",
                    "C",
                    "Z",
                    "E 13 1 0 0 0 0 0 2 0 1 1 0",
                    "E 12 1 1 0 0 0 0 1 0 0 7 0",
                ):
                    操作(行)
                for _ in range(1024):
                    if not 自.屏.api_活跃():
                        break
                    操作("F 100")
                    if any(b.编号 == 901 for b in 自.框.按钮):
                        操作("X 901")
                    操作("Z")
                else:
                    raise ValueError("连续队列未结束")
            进.stdin.close()
            退 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退 or 错:
                raise ValueError("参考转盘故障：" + 错)
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
    参数.add_argument("--static-only", action="store_true")
    参数.add_argument("--lifecycle-only", action="store_true")
    选项 = 参数.parse_args()
    转盘画面差分_类.api_执行(
        选项.source,
        选项.build,
        选项.assets,
        选项.font,
        选项.report,
        选项.static_only,
        选项.lifecycle_only,
    )
