# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import random
import shlex
import subprocess
import tempfile
from array import array
from collections import Counter
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.world import 世界_类


# ◕ 功能
class 画框差分_类:
    """
    直接固定Frame/draw.cpp，对照整幅640×480画布和实际按钮/回调/声音元数据。

    更新日志：
    2026.10.24 - 真实外部精灵、透明/裁切、八种对齐与节庆图，无正式运行后端。
    """

    @staticmethod
    def _命令(arg_美术: 美术_类) -> list[str]:
        生, 组 = random.Random(2026102403), []
        文 = ["", "大富翁4", "Aa jgy", "第一行\n\n第三行\n", "🀄"]
        原 = [s.encode().hex() or "-" for s in 文]

        def 加(arg_文: str) -> None:
            操作, _, 余 = arg_文.partition(" ")
            组.append(f"{操作} {生.randrange(65536)} {余}")

        for flags in range(8):
            for align in range(8):
                for text in 原:
                    加(
                        f"T {生.randrange(-20, 640)} {生.randrange(-20, 480)} {align} "
                        f"{生.choice([12, 16, 20, 28])} 15790320 1052688 {flags} {text}"
                    )
        for _ in range(50):
            x, y = 生.randrange(-20, 640), 生.randrange(-20, 480)
            加(
                f"{生.choice(['B', 'D'])} {x} {y} {x + 生.randrange(-5, 160)} "
                f"{y + 生.randrange(-5, 80)} {生.randrange(2)} {生.choice(原)}"
            )
            加(
                f"{生.choice(['F', 'Z'])} {x} {y} {生.choice([0, 20, 100])} "
                f"{生.choice([12, 16, 20, 28])} {生.randrange(65536)} 0 0 {生.choice(原)}"
            )
        for _ in range(140):
            x, y = 生.randrange(-20, 640), 生.randrange(-20, 480)
            加(
                f"{生.choice(['X', 'Y', 'V', 'Q'])} {x} {y} {x + 生.randrange(-5, 180)} "
                f"{y + 生.randrange(-5, 100)} {生.choice([-100, -32, -16, 0, 32, 32767])}"
            )
        帧 = []
        for 库, 条 in [("p", 2), ("p", 3), ("p", 65), ("p", 73), ("p", 79), ("p", 100)]:
            数 = arg_美术.api_帧数(库, 条)
            帧.extend((库, 条, i) for i in (0, 数 - 1) if 数)
        for _ in range(100):
            库, 条, i = 生.choice(帧)
            图 = arg_美术.api_帧(库, 条, i)
            x, y = 生.randrange(-20, 640), 生.randrange(-20, 480)
            加(
                f"{生.choice(['A', 'L', 'U', 'O'])} {库} {条} {i} {x} {y} "
                f"{生.choice([1, 2, 3])} {-2} {1} {图.宽 - 1} {图.高 + 2}"
            )
        for effect in (-1, 0, 1, 3, 9):
            for enabled in (0, 1):
                加(f"H {effect} {enabled}")
        for 地图 in range(8):
            for 年, 月, 日 in (
                (1998, 1, 1),
                (1998, 2, 1),
                (1998, 12, 25),
                (2026, 10, 5),
                (2026, 99, 1),
            ):
                加(f"E {年} {月} {日} {地图 % 4} {地图 // 4}")
        for v in (-9223372036854775808, -1000, -1, 0, 1, 999, 1000, 9223372036854775807):
            加(f"M {v}")
        for y in (-30, 196, 450):
            for 文 in 原:
                加(f"P {y} {文}")
        return 组

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_报告: Path,
        arg_暗化网格: bool = False,
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
        工具 = arg_构建.resolve() / "native-frame-oracle"
        ft = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("native_frame_oracle.cpp")),
                str(arg_源码 / "tools/screens/draw.cpp"),
                str(arg_构建 / "librich4_core.a"),
                *ft,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
        )
        美术, 字, 绘 = 美术_类(arg_素材), 字体_类(arg_字体), 屏幕绘图_类()
        世界 = 世界_类.api_从地图(美术.api_解码("m", 1))
        if arg_暗化网格:
            组 = [f"X 0 0 0 640 480 {v}" for v in (*range(-32, 1), -100, 1, 32)]
            组 += [
                f"X 32768 {x} {y} {r} {b} -16"
                for x, y, r, b in ((-20, -20, 20, 20), (20, 10, 10, 5), (600, 470, 660, 490))
            ]
        else:
            组 = cls._命令(美术)
        报 = {
            "reference": 版,
            "generator_seed": 2026102403,
            "darken_grid": arg_暗化网格,
            "status": "running",
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "freetype_library": 字.库路径,
            "python_source_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in ("native_frame.py", "screen_draw.py")
            },
            "scope": (
                "direct fixed Frame/draw.cpp; full canvas and button/callback data; "
                "no GUI gameplay acceptance"
            ),
        }
        摘, 计 = hashlib.sha256(), Counter()
        try:
            with tempfile.TemporaryDirectory(prefix="rich4-frame-pixels-") as 临:
                根 = Path(临)
                结果 = subprocess.run(
                    [str(工具), str(arg_素材), str(arg_字体), str(根)],
                    input="\n".join(组) + "\n",
                    text=True,
                    capture_output=True,
                    check=True,
                )
                行表 = 结果.stdout.splitlines()
                if len(行表) != len(组):
                    raise ValueError("原画框输出数量不同")
                for i, (命令, 实) in enumerate(zip(组, 行表)):
                    op, seed, *列 = 命令.split()
                    seed = int(seed)
                    图 = 图像_类(
                        640, 480, [(j * 1103515245 + seed) & 65535 for j in range(640 * 480)]
                    )
                    框 = 画框_类(图, 美术, 字, [])
                    动作, 声音, 量 = [], [], -1
                    货币 = "-"
                    if op in "BD":
                        x, y, r, b, en = map(int, 列[:-1])
                        文 = bytes.fromhex(列[-1]) if 列[-1] != "-" else b""
                        if op == "B":
                            框.api_按钮(71, (x, y, r, b), 文, lambda: 动作.append(71), bool(en))
                        else:
                            框.api_对话框((x, y, r, b), 文)
                    elif op in "TFZ":
                        x, y, align, size, fg, bg, flags = map(int, 列[:-1])
                        文 = bytes.fromhex(列[-1]) if 列[-1] != "-" else b""
                        if op == "T":
                            式 = 屏幕字样_类(size, fg, bg, flags)
                            绘.api_文字(框, 文, x, y, align, 式)
                            量 = 绘.api_测量(框, 文, 式)
                        elif op == "F":
                            框.api_文字(文, x, y, size, fg, align)
                        else:
                            框.api_居中(文, x, y, size, fg)
                    elif op in "XYVQ":
                        x, y, r, b, lev = map(int, 列)
                        if op == "X":
                            绘.api_暗化(图, (x, y, r, b), lev)
                        elif op == "Y":
                            绘.api_灰阶(图, (x, y, r, b))
                        elif op == "V":
                            绘.api_按下斜面(图, (x, y, r, b))
                        else:
                            绘.api_边框(图, (x, y, r, b), lev)
                    elif op in "ALUO":
                        库 = 列[0]
                        条, 帧, x, y, 倍, 左, 顶, r, b = map(int, 列[1:])
                        if op == "A":
                            框.api_资源图(库, 条, 帧, x, y)
                        elif op == "L":
                            绘.api_局部(图, 美术.api_帧(库, 条, 帧), (左, 顶, r, b), x, y)
                        elif op == "U":
                            框.api_图片(绘.api_缩放(框, 库, 条, 帧, 倍), x, y)
                        else:
                            绘.api_背景(框, 库, 条, 帧)
                    elif op == "H":
                        效, 启用 = map(int, 列)
                        绘.api_命中(
                            屏幕宿主_类(框, 声音.append),
                            75,
                            (3, 4, 50, 60),
                            效,
                            lambda: 动作.append(75),
                            bool(启用),
                        )
                        框.按钮[0].动作()
                    elif op == "E":
                        年, 月, 日, 地图, 阶段 = map(int, 列)
                        世界.头.日期, 世界.头.地图, 世界.头.阶段 = (日, 月, 年), 地图, 阶段
                        节 = 绘.api_节日(框, 世界)
                        量 = int(节 is not None)
                        if 节:
                            框.api_图片(节, 20, 30)
                    elif op == "P":
                        y = int(列[0])
                        文 = bytes.fromhex(列[1]).decode() if 列[1] != "-" else ""
                        绘.api_弹框(屏幕宿主_类(框), 文, y)
                    elif op == "M":
                        货币 = 绘.api_货币(int(列[0]))
                    else:
                        raise ValueError(op)
                    数 = [量, len(框.按钮)]
                    for 按钮 in 框.按钮:
                        数 += [按钮.编号, *按钮.区域, int(按钮.启用), int(按钮.点击声音)]
                    数 += [len(动作), *动作, len(声音), *声音]
                    预 = " ".join(map(str, 数)) + " " + 货币
                    if 预 != 实:
                        raise ValueError(f"元数据不同 step={i} {命令} cpp={实} py={预}")
                    像 = array("H", 图.像素)
                    if byteorder != "little":
                        像.byteswap()
                    像素 = 像.tobytes()
                    cpp = (根 / f"{i}.555").read_bytes()
                    if cpp != 像素:
                        位 = next(j for j, (a, b) in enumerate(zip(cpp, 像素)) if a != b)
                        raise ValueError(
                            f"画布不同 step={i} {命令} pixel={位 // 2 % 640},{位 // 2 // 640}"
                        )
                    (根 / f"{i}.555").unlink()
                    摘.update(像素)
                    摘.update(预.encode())
                    计[op] += 1
            报.update(
                status="passed",
                commands=len(组),
                operations=dict(计),
                complete_canvas_pixels=len(组) * 640 * 480,
                state_sha256=摘.hexdigest(),
            )
        except (ValueError, subprocess.CalledProcessError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            字.api_关闭()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": 报["status"], "commands": len(组), "operations": dict(计)}))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    参数.add_argument("--darken-grid", action="store_true")
    选项 = 参数.parse_args()
    画框差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.darken_grid
    )
