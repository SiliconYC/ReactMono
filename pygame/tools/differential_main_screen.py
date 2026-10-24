# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from array import array
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.flc import 动画_类
from rich4.game import 游戏会话_类
from rich4.graphics import 图像_类
from rich4.main_screen import 主屏幕_类
from rich4.main_screen_types import 主屏动作_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.save import 存档_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 主屏差分_类:
    """
    固定原生MainScreen整画布/内部值/按钮/真实回调对照；菜单回调仅记录宿主请求。

    更新日志：
    2026.10.24 - 公共核心操作与真实输入时间线，无运行时C++后端或规则结果注入。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.美术, self.字 = 美术_类(arg_素材), 字体_类(arg_字体)
        self.框 = 画框_类(图像_类(640, 480, [0] * 307200), self.美术, self.字, [])
        self.调用: list[int] = []
        self.声音: list[int] = []
        self.旋转 = 0
        self.覆盖: dict[str, set[int | str]] = {
            n: set()
            for n in (
                "maps",
                "views",
                "tabs",
                "calendars",
                "characters",
                "traffic",
                "dice_counts",
                "dice_rotations",
                "dice_stages",
                "recorded_action_ids",
            )
        }
        self.动作 = 主屏动作_类(
            *[self._请求(n) for n in (81, 76, 82, 72, 71, 75, 78, 77, 80, 79)],
            self._转,
            self._掷,
            self._骰数,
            self.声音.append,
        )

    def _请求(self, arg_号: int) -> Callable[[], None]:
        def 请求() -> None:
            self.调用.append(arg_号)

        return 请求

    def _事件(self) -> None:
        for 事件 in self.会.api_取事件():
            self.屏.api_事件(事件, self.会, self.美术)

    def _转(self, arg_步: int) -> None:
        self.旋转 = (self.旋转 + arg_步) & 7
        self.会.api_设相机(self.旋转)
        self.调用.append(1000 + arg_步)

    def _掷(self) -> None:
        self.调用.extend((100, int(self.会.api_掷骰())))
        self._事件()

    def _骰数(self, arg_数: int) -> None:
        self.调用.extend((101, arg_数, int(self.会.api_设骰数(arg_数))))

    @staticmethod
    def _命令() -> list[str]:
        组, 序 = [], 0
        for 预设 in ("view=٤", "view=\u00a02", "view=-1", "tab=+3suffix,calendar=1"):
            组.append(f"n 0 1 10 0 2026 10 5 {预设}")
        for 图 in range(10):
            for view in range(3):
                for tab in range(4):
                    for cal in range(2):
                        序 += 1
                        月 = (1, 4, 7, 10)[序 % 4]
                        组.append(
                            f"n {图} {序} {序 % 12} {序 % 3} 2026 {月} 5 "
                            f"view={view},tab={tab},calendar={cal}"
                        )
                        组.append(f"a {序 % 2} {(序 // 2) % 2}")
                        if tab == 0:
                            组 += [f"s {序 % 4}", "s -1"]
        for 图 in range(8):
            组 += [f"n {图} 1 10 0 1998 1 1 map=1", "p 10 10"]
        for traffic in (0, 1, 2):
            for ch in range(12):
                组 += [
                    f"n {ch % 8} 1 {ch} {traffic} 2026 10 5 -",
                    "a 1 1",
                    "g 180 120",
                    "g 210 150",
                    "g 251 186",
                    "g 252 187",
                    "p 620 110",
                    "p 620 180",
                    "p 620 250",
                    "p 620 30",
                    "p 550 400",
                    "m 600 460 1",
                    "u 500 300 1",
                    "p 450 290",
                    "p 480 290",
                    "v",
                    "p 450 300",
                    "p 480 300",
                    "v",
                    "p 182 122",
                    "m 500 400 1",
                    "u 500 400 0",
                ]
                if traffic in (1, 2):
                    组 += ["p 510 440"]
                组 += ["p 500 400", "m 503 403 1", "u 503 403 0", "c 350", "d 0 -1 -1 0"]
                for dt in (79, 1, 80, 160, 200, 300, 400, 500, 500, 1000, 1000):
                    组 += [f"d {dt} -1 -1 0", "c 350"]
        return 组

    @staticmethod
    def _旋转命令(arg_美术: 美术_类) -> list[str]:
        组 = []
        for 交通 in range(3):
            总帧 = 动画_类(arg_美术.api_解码("p", 4 + 交通)).帧数
            for 转 in range(8):
                角色, 跳 = (交通 * 8 + 转) % 12, 转 % 2
                投帧 = arg_美术.api_帧数("d", 0x80 + 角色 * 21 + 交通 * 3 + 2) // 8
                投时 = 0 if 跳 else 投帧 * 80
                组 += [f"n {转} 1 {角色} {交通} 2026 10 5 -", f"h {跳}"]
                组 += ["p 450 290"] * 转
                组 += ["p 210 150", "c 350", "d 0 -1 -1 0"]
                if 投时:
                    组 += [f"d {投时 - 1} -1 -1 0", "d 1 -1 -1 0"]
                组 += ["d 28 -1 -1 0"] * 总帧
                组 += ["d 499 -1 -1 0", "c 350", "d 1 -1 -1 0", "c 350", "d 28 -1 -1 0"]
        return 组

    def _操作(self, arg_命令: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = (t.decode() for t in arg_命令.encode().split())
        self.调用.clear()
        self.声音.clear()
        结果 = -1
        if op == "n":
            图, 种, 角色, 交通, 年, 月, 日 = map(int, 列[:-1])
            if 图 >= 8:
                名 = "save0.dat" if 图 == 8 else "save1.dat"
                路 = next(p for p in self.美术.目录.iterdir() if p.name.lower() == 名)
                世 = 世界_类.api_从存档(存档_类.api_解码(路.read_bytes()))
            else:
                设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种, 日期=(日, 月, 年))
                设.玩家[0].角色, 设.玩家[0].交通 = 角色, 交通
                世 = 世界_类.api_从地图(self.美术.api_解码("m", 图 * 2 + 1), 设)
            self.会, self.屏 = 游戏会话_类(世, 种), 主屏幕_类("" if 列[-1] == "-" else 列[-1])
            self.旋转, self.框.指针x, self.框.指针y, self.框.按下, self.框.时钟 = (
                0,
                -1,
                -1,
                False,
                0,
            )
            self._事件()
        elif op == "d":
            dt, x, y, down = map(int, 列)
            self.框.时钟 += dt
            self.框.指针x, self.框.指针y, self.框.按下 = x, y, bool(down)
            self.屏.api_递进(dt)
        elif op == "p":
            x, y = map(int, 列)
            self.框.指针x, self.框.指针y, self.框.按下 = x, y, True
            for 按钮 in self.框.按钮:
                if 按钮.启用 and self.框.api_指针内(按钮.区域):
                    动作 = 按钮.动作
                    self.调用.append(按钮.编号)
                    self.框.按钮.clear()
                    动作()
                    break
        elif op in ("m", "u"):
            x, y, down = map(int, 列)
            self.框.指针x, self.框.指针y, self.框.按下 = x, y, bool(down) if op == "m" else False
            if op == "m":
                self.屏.api_指针移动(x, y, bool(down))
            else:
                self.屏.api_指针释放(x, y, bool(down))
        elif op == "s":
            self.屏.api_显示玩家(int(列[0]) if int(列[0]) >= 0 else None)
        elif op == "v":
            self.屏.api_切视图()
        elif op == "h":
            self.屏.api_跳过投掷(bool(int(列[0])))
        elif op == "g":
            结果 = self.屏._GO命中值(self.框, *map(int, 列))
        elif op == "r":
            结果 = int(self.会.api_掷骰())
            self._事件()
        elif op == "c":
            结果 = int(not self.屏.api_骰子忙())
            if 结果:
                self.会.api_步进(int(列[0]))
                self._事件()
        elif op == "a":
            self.动作.可保存, self.动作.可载入 = map(lambda v: bool(int(v)), 列)
        else:
            raise ValueError(op)
        self.框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
        self.框.按钮.clear()
        self.屏.api_绘制(self.框, self.会, self.旋转, self.动作)
        屏 = self.屏
        世 = self.会.世界
        记 = 世.玩家[屏.api_显示槽位(世)].记录
        for 名, 值 in (
            ("maps", 世.头.阶段 * 4 + 世.头.地图),
            ("views", 屏.视图),
            ("tabs", 屏.页签[屏.api_显示槽位(世)] % 4),
            ("calendars", 屏.日历),
            ("characters", 记.角色),
            ("traffic", 记.交通 & 3),
        ):
            self.覆盖[名].add(值)
        self.覆盖["recorded_action_ids"].update(n for n in self.调用 if 71 <= n <= 102)
        if 屏._骰活跃:
            self.覆盖["dice_counts"].add(len(屏._骰面))
            self.覆盖["dice_rotations"].add(self.旋转)
            时 = 屏._骰毫秒
            self.覆盖["dice_stages"].add(
                "pose"
                if 时 < 屏._投掷毫秒
                else "flc"
                if 时 < 屏._投掷毫秒 + 屏._骰帧数 * 28
                else "faces"
            )
        数 = [
            结果,
            int(self.会.阶段),
            self.会.世界.头.当前玩家,
            self.旋转,
            self.框.时钟,
            int(屏.api_骰子忙()),
            int(屏.api_显示人类回合(self.会)),
            屏.api_显示槽位(self.会.世界),
            屏.视图,
            屏.日历,
            *屏.页签,
            屏._悬停,
            屏.GOx,
            屏.GOy,
            int(屏._拖拽 is not None),
        ]
        if 屏._拖拽 is not None:
            数.extend(屏._拖拽)
        数 += [
            -1 if 屏._显示玩家 is None else 屏._显示玩家,
            int(屏._待掷 is not None),
            *屏._按点,
            int(屏._自由中心 is not None),
        ]
        if 屏._自由中心 is not None:
            数.extend(屏._自由中心)
        数 += [
            int(屏._小图拖拽),
            int(屏.全图),
            屏._小图顶,
            len(屏._GO掩码),
            len(屏._骰面),
            *屏._骰面,
            屏._骰向,
            int(屏._骰活跃),
            int(屏._骰已响),
            int(屏._跳过姿态),
            屏._骰毫秒,
            屏._骰帧数,
            屏._投掷槽,
            屏._投掷帧数,
            屏._投掷毫秒,
            len(屏._骰动画),
        ]
        for n, frames in sorted(屏._骰动画.items()):
            数.extend((n, len(frames)))
        数.extend(-1 if (pose := 屏.api_投掷帧(i)) is None else pose for i in range(4))
        数.append(len(self.框.按钮))
        for b in self.框.按钮:
            数.extend((b.编号, *b.区域, int(b.启用), int(b.点击声音)))
        数 += [len(self.调用), *self.调用, len(self.声音), *self.声音]
        像 = array("H", self.框.画布.像素)
        if byteorder != "little":
            像.byteswap()
        return " ".join(map(str, 数)), 像.tobytes()

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_报告: Path,
        arg_旋转专项: bool = False,
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
        工具 = arg_构建.resolve() / (
            "main-screen-oracle-rotations" if arg_旋转专项 else "main-screen-oracle"
        )
        ft = shlex.split(
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
                str(Path(__file__).with_name("main_screen_oracle.cpp")),
                str(arg_源码 / "tools/screens/main_screen.cpp"),
                str(arg_源码 / "tools/screens/draw.cpp"),
                str(arg_构建 / "librich4_core.a"),
                *ft,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
        )
        自 = cls(arg_素材, arg_字体)
        组 = cls._旋转命令(自.美术) if arg_旋转专项 else cls._命令()
        报 = {
            "reference": 版,
            "scope": (
                "direct fixed MainScreen canvas/state/input callbacks; "
                "not full app/menu/audio acceptance"
            ),
            "status": "running",
            "planned_commands": len(组),
            "compared_commands": 0,
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "freetype_library": 自.字.库路径,
            "rotation_only": arg_旋转专项,
            "input_sha256": hashlib.sha256(("\n".join(组) + "\n").encode()).hexdigest(),
            "python_source_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in (
                    "main_screen.py",
                    "main_panels.py",
                    "main_text.py",
                    "main_screen_types.py",
                )
            },
        }
        摘, 计 = hashlib.sha256(), Counter()
        进 = subprocess.Popen(
            [str(工具), str(arg_素材), str(arg_字体)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            for i, 命令 in enumerate(组):
                进.stdin.write((命令 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                cpp = 进.stdout.read(614400)
                预, 像 = 自._操作(命令, i)
                if 实 != 预:
                    raise ValueError(f"step={i} cmd={命令} metadata cpp={实} py={预}")
                if cpp != 像:
                    位 = next(j for j, (a, b) in enumerate(zip(cpp, 像)) if a != b)
                    raise ValueError(f"step={i} cmd={命令} pixel={位 // 2 % 640},{位 // 2 // 640}")
                摘.update(cpp)
                摘.update(实.encode())
                计[命令[0]] += 1
                报["compared_commands"] = i + 1
                if i % 100 == 0:
                    arg_报告.parent.mkdir(parents=True, exist_ok=True)
                    arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
            进.stdin.close()
            if 进.wait() != 0:
                raise ValueError(进.stderr.read().decode())
            报.update(
                status="passed",
                operations=dict(计),
                complete_canvas_pixels=len(组) * 307200,
                state_sha256=摘.hexdigest(),
                coverage={n: sorted(v) for n, v in 自.覆盖.items()},
            )
        except (ValueError, OSError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            if 进.poll() is None:
                进.terminate()
                进.wait()
            自.字.api_关闭()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": 报["status"], "commands": len(组), "operations": dict(计)}))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    参数.add_argument("--rotation-only", action="store_true")
    选项 = 参数.parse_args()
    主屏差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.rotation_only
    )
