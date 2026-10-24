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
from rich4.main_menu import 主菜单_类, 主菜单动作_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.new_game_screen import 新局屏幕_类
from rich4.new_game_types import 新局选择_类
from rich4.screen_draw import 屏幕宿主_类


# ◕ 功能
class 菜单新局差分_类:
    """
    原菜单/新局完整画布、时钟、私有MT与真实NewGameChoice逐操作比较。

    更新日志：
    2026.10.24 - 不将即时回放的首个可用补位冒充正式MT补位。
    """

    生命周期 = False
    骑帧: list[int] = []

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[list[int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append([0, n]))
        self.菜单, self.新局 = 主菜单_类(), 新局屏幕_类()
        type(self).骑帧 = [self.美术.api_帧数("j", i) for i in range(9, 45)]
        for i, n in enumerate(type(self).骑帧, 9):
            if n < 1:
                raise ValueError("骑乘条目没有帧")
            for f in range(n):
                self.美术.api_帧("j", i, f)

    def _菜单动作(self, arg_可读: bool) -> 主菜单动作_类:
        return 主菜单动作_类(
            lambda: self.调用.append([1, 1]),
            lambda: self.调用.append([1, 2]),
            lambda: self.调用.append([1, 3]),
            lambda: self.调用.append([1, 5]),
            lambda: self.调用.append([1, 4]),
            arg_可读,
        )

    @staticmethod
    def _选择(arg_选: 新局选择_类) -> list[int]:
        nums = [2, arg_选.阶段, arg_选.地图, arg_选.资金, arg_选.租期, len(arg_选.玩家)]
        for p in arg_选.玩家:
            nums += [p.角色, p.控制, p.交通, p.起点]
        return nums

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        框, 宿, 菜, 屏 = self.框, self.宿, self.菜单, self.新局
        if op == "O":
            a, b, c = map(int, 列)
            屏.api_打开(a, b, c)
        elif op == "R":
            self.菜单 = 菜 = 主菜单_类()
        elif op == "V":
            屏._值 = list(map(int, 列))
        elif op == "G":
            屏._补一人()
        elif op == "Q":
            self.调用.append(self._选择(屏._选择()))
        elif op in ("D", "M"):
            t, x, y, down, flag = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            if op == "M":
                菜.api_绘制(宿, self._菜单动作(bool(flag)))
            else:
                宿.即时 = bool(flag)
                屏.api_绘制(
                    宿, lambda c: self.调用.append(self._选择(c)), lambda: self.调用.append([3, 0])
                )
        elif op == "X":
            for b in 框.按钮:
                if b.编号 == int(列[0]) and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
        elif op == "B":
            屏.api_取消(宿, lambda: self.调用.append([3, 0]))
        else:
            raise ValueError(op)
        数 = [
            -1,
            菜._悬选,
            屏._阶段,
            屏._地图,
            *屏._值,
            len(屏._人选),
            *屏._人选,
            屏._人类数,
            屏._下拉,
            屏._悬选,
            int(屏._填充),
            int(屏._离开),
            屏._填时,
            屏._离时,
            屏._背景键,
            屏._背景.宽,
            屏._背景.高,
        ]
        r = 屏._随机
        mt = r._词[r._位 :] + r._词[: r._位]
        数 += [len(mt), *mt, len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        像 = b""
        if op in ("D", "M"):
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _命令() -> list[str]:
        if 菜单新局差分_类.生命周期:
            return 菜单新局差分_类._生命周期命令()
        组 = []
        for enabled in (0, 1):
            for id, x, y in (
                (1, 190, 380),
                (2, 328, 380),
                (3, 468, 378),
                (5, 328, 450),
                (4, 62, 380),
            ):
                组 += [
                    "R",
                    f"M 0 {x} {y} 0 {enabled}",
                    f"M 1 {x} {y} 1 {enabled}",
                    f"X {id}",
                    f"M 2 -1 -1 0 {enabled}",
                ]
        for 图 in range(8):
            for traffic in range(3):
                for players in (2, 3, 4):
                    seed = (1, 5489, 4294967295)[traffic]
                    char = (图 * 3 + traffic + players) % 12
                    组 += [
                        f"O {图 // 4} {图 % 4} {seed}",
                        f"V {players - 2} 1 {traffic} 0 0 0",
                        "D 0 -1 -1 0 0",
                        f"X {10 + char}",
                        "D 1 -1 -1 0 0",
                        "X 40",
                    ]
                    for t in (1100, 1101, 2200, 2201, 3300, 3301, 4400, 4401):
                        组.append(f"D {t} -1 -1 0 0")
                    组 += ["D 4500 -1 -1 0 0", "X 49", "D 4501 -1 -1 0 0", "Q"]
        for row in range(6):
            for item in range(3 if row in (0, 2) else 6):
                组 += [
                    "O 0 0 123456789",
                    "D 0 8 15 0 0",
                    "X 10",
                    "D 1 88 20 0 0",
                    "X 11",
                    "D 2 160 20 0 0",
                    "X 12",
                    "D 3 232 20 0 0",
                    "X 13",
                    "D 4 -1 -1 0 0",
                    f"X {43 + row}",
                    "D 5 580 300 1 0",
                    f"X {130 + item}",
                    "D 6 -1 -1 0 0",
                    "B",
                    "D 7 -1 -1 0 0",
                    "X 40",
                    "D 1107 -1 -1 0 0",
                    "Q",
                ]
        for instant in (0, 1):
            组 += [
                "O 1 3 0",
                "V 2 0 2 5 0 0",
                f"D 0 -1 -1 0 {instant}",
                "X 19",
                f"D 1 -1 -1 0 {instant}",
                "X 18",
                f"D 2 -1 -1 0 {instant}",
                "X 40",
                "B",
                "Q",
            ]
        组 += ["O 0 0 1", "V 0 1 0 0 0 0", "G", "G", "G", "Q", "D 0 -1 -1 0 0", "X 43", "B", "B"]
        return 组

    @staticmethod
    def _生命周期命令() -> list[str]:
        组 = []
        for character in range(12):
            for traffic in range(3):
                图 = (character + traffic) % 8
                组 += [
                    f"O {图 // 4} {图 % 4} {character * 117 + traffic}",
                    f"V 0 1 {traffic} 0 0 0",
                    "D 0 -1 -1 0 0",
                    f"X {10 + character}",
                ]
                for f in range(菜单新局差分_类.骑帧[character * 3 + traffic]):
                    组.append(f"D {100 * f} -1 -1 0 0")
                # 重新打开后独立测试1100补位与每个50毫秒退场阶段，避免时间倒流。
                组 += [
                    f"O {图 // 4} {图 % 4} {character * 117 + traffic}",
                    f"V 0 1 {traffic} 0 0 0",
                    "D 0 -1 -1 0 0",
                    f"X {10 + character}",
                    "D 0 -1 -1 0 0",
                    "X 40",
                    "D 1099 -1 -1 0 0",
                    "D 1100 -1 -1 0 0",
                ]
                for step in range(1, 16):
                    组.append(f"D {1100 + 50 * step} -1 -1 0 0")
                组 += ["Q", "B"]
        for players in (2, 3, 4):
            组 += ["O 0 0 1", f"V {players - 2} 1 0 0 0 0", "D 0 -1 -1 0 0", "X 10"]
            for i in range(1, players):
                组 += ["D 0 -1 -1 0 0", f"X {10 + i}"]
            组 += [
                "D 0 -1 -1 0 0",
                "X 40",
                "D 1099 -1 -1 0 0",
                "D 1100 -1 -1 0 0",
                "D 1150 -1 -1 0 0",
                "X 49",
                "D 1850 -1 -1 0 0",
                "Q",
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
        工具 = 构 / "main-setup-oracle"
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
                str(Path(__file__).with_name("main_setup_oracle.cpp")),
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
                "direct original MainMenu and NewGameSetup, "
                "full private MT state and real choices, "
                "real sprites, internal state and callbacks; "
                "not actual window/financial rule integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "lifecycle" if cls.生命周期 else "base",
            "preflight_rider_entries": 36,
            "preflight_rider_frames": sum(cls.骑帧),
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "main_menu.py",
                    "new_game_screen.py",
                    "new_game_types.py",
                    "menu_random.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/new_game_screen.py").read_bytes()
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
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "M") else b""
                if 行[:1] in ("D", "M") and len(cpp) != 614400:
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
                raise ValueError("参考主菜单/新局故障：" + 错)
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
    参数.add_argument("--lifecycle-only", action="store_true")
    选项 = 参数.parse_args()
    菜单新局差分_类.生命周期 = 选项.lifecycle_only
    菜单新局差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
