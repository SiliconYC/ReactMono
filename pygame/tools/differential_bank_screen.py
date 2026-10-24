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
from rich4.bank_screen import 银行屏幕_类
from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.number_pad import 数字板_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.primary_stock_screen import 一级股票屏幕_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 银行差分_类:
    """
    真实原金融组件，完整画布、台词/时钟/按钮与数额回调对照。

    更新日志：
    2026.10.24 - 回调仅观察成功/拒绝序列，不伪称真实核心或窗口验收。
    """

    分支模式 = False
    传输冒烟 = False

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        self.原文 = 原版文字_类(原版程序_类.api_读取(exe))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[tuple[int, int]] = []
        self.宿 = 屏幕宿主_类(
            self.框, lambda n: self.调用.append((0, n)), 语音=lambda n: self.调用.append((1, n))
        )
        self.屏 = 银行屏幕_类(self.原文)
        self.板 = 数字板_类()
        self.认购 = 一级股票屏幕_类(self.原文)
        self.答成功 = True

    def _答(self, arg_值: int, arg_数: int) -> bool:
        self.调用.append((2 + arg_值, arg_数))
        return self.答成功

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
        结果, extra = -1, []
        框, 宿, 屏, 板 = self.框, self.宿, self.屏, self.板
        old = self.世.api_导出() if op in ("D", "G", "K", "X", "B", "P") else None
        if op == "N":
            图, 人, 槽 = map(int, 列)
            设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            for i, p in enumerate(设.玩家):
                p.角色 = (人 + i * 3) % 12
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", 图 * 2 + 1), 设)
            屏.api_重置()
            self.板 = 板 = 数字板_类()
            self.决 = 决策_类(决策种类_类.银行, 槽)
            框.按钮.clear()
            self.答成功 = True
        elif op == "O":
            mask = int(列[0])
            self.决.选项 = [决策选项_类("", i) for i in range(7) if mask & (1 << i)]
        elif op == "W":
            slot, cash, bank, loan, special, days, due = map(int, 列)
            p = self.世.玩家[slot]
            p.记录.现金, p.记录.银行, p.记录.贷款, p.记录.特殊融资 = cash, bank, loan, special
            p.状态.银行禁贷天数, p.状态.贷款到期 = days, due & 0xFFFFFFFF
        elif op == "M":
            self.世.玩家[self.决.玩家].记录.节点 = 0
            for i, n in enumerate(self.世.节点):
                code = n.类型索引
                if 6000 < code < 8000 and code - 6000 < len(self.世.公司):
                    self.世.玩家[self.决.玩家].记录.节点 = i
                    self.世.公司[code - 6000].业主 = self.决.玩家 + 1 if int(列[0]) else 0
                    break
        elif op == "Z":
            self.世.公司[0].股票索引 = int(列[0])
        elif op == "T":
            self.世.头.日期 = tuple(map(int, 列))
        elif op == "S":
            板.api_缩放(int(列[0]))
        elif op == "U":
            self.答成功 = bool(int(列[0]))
        elif op in ("D", "G"):
            ticks, x, y, down, instant, showpad = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下, 宿.即时 = ticks, x, y, bool(down), bool(instant)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            if op == "D":
                屏.api_绘制(宿, self.世, self.决, 板, self._答)
            else:
                self.认购.api_绘制(宿, self.世, self.决, 板, self._答)
            if showpad and 板.api_活跃():
                框.按钮.clear()
                板.api_绘制(宿)
        elif op == "J":
            self.决.地产, self.决.金额, self.决.金额上限 = map(int, 列)
        elif op == "K":
            板.api_键(宿, chr(int(列[0]) & 255))
        elif op == "X":
            for b in 框.按钮:
                if b.编号 == int(列[0]) and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
        elif op == "B":
            屏.api_取消(宿, self.决, self._答)
        elif op == "P":
            板.api_取消(宿)
        elif op == "R":
            屏.api_重置()
        elif op == "C":
            板.api_关闭()
        elif op == "I":
            结果 = 屏.api_ATM数字号(int(列[0]))
        elif op == "L":
            v, variant = map(int, 列)
            extra = self._串(self.原文.api_配音(v, variant).文字)
        else:
            raise ValueError(op)
        if old is not None and old != self.世.api_导出():
            raise ValueError("金融界面改变世界DAT")
        数 = extra + [结果, 屏._阶段, int(屏._开始), int(屏._拖), int(屏._侧栏), 屏._模式]
        数 += self._串(屏._ATM文) + [len(屏._行)]
        for line in 屏._行:
            数 += self._串(line)
        数 += [屏._行起, 屏._侧起, 屏._弹止] + self._串(屏._弹文)
        数 += [
            屏._说号,
            屏._已声号,
            屏._声行,
            int(板._活跃),
            int(板._拖),
            板._x,
            板._y,
            板._比例,
            板._上限,
        ]
        数 += self._串(板._文) + [int(板._完成 is not None), len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for call in self.调用:
            数 += list(call)
        像 = b""
        if op in ("D", "G"):
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _命令() -> list[str]:
        if 银行差分_类.传输冒烟:
            return [
                "N 0 0 0",
                "O 127",
                "W 0 100 200 30 0 1 0",
                "M 1",
                "D 0 -1 -1 0 0 0",
                "B",
                "D 2000 -1 -1 0 0 0",
                "X 941",
                "D 2050 -1 -1 0 0 1",
                "K 77",
                "K 13",
                "D 5000 -1 -1 0 0 0",
                "X 943",
                "D 6000 -1 -1 0 0 0",
                "X 945",
                "D 6001 -1 -1 0 0 0",
                "C",
                "J 1 20 100",
                "G 6002 -1 -1 0 0 1",
                "P",
            ]
        if 银行差分_类.分支模式:
            return 银行差分_类._分支命令()
        组 = ["N 0 0 0"] + [f"L {i} 0" for i in range(75, 92)] + ["L 89 1"]
        组 += [f"I {i}" for i in range(-2, 13)]
        for 图 in range(8):
            for 人 in range(12):
                槽 = 人 % 4
                for scale in (1, 2):
                    组 += [
                        f"N {图} {人} {槽}",
                        "O 127",
                        f"S {scale}",
                        f"W {槽} 123456 789012 20000 10000 {人 * 13} 132382977",
                        "M 1",
                        "D 0 -1 -1 0 0 0",
                        "D 1499 120 280 1 0 0",
                        "D 1500 -1 -1 0 0 0",
                        "X 936",
                        "D 1501 -1 -1 0 0 0",
                        "X 937",
                        "D 1600 -1 -1 0 0 0",
                        "D 3600 -1 -1 0 0 0",
                        "D 5600 -1 -1 0 0 0",
                        "X 941",
                        "D 5650 -1 -1 0 0 1",
                        "D 5800 -1 -1 0 0 1",
                        "K 77",
                        "K 13",
                        "D 5900 -1 -1 0 0 0",
                        "D 7900 -1 -1 0 0 0",
                        "D 9900 -1 -1 0 0 0",
                        "X 943",
                        "D 10000 40 320 0 0 0",
                        "X 944",
                        "D 10001 -1 -1 0 0 1",
                        "K 77",
                        "K 13",
                        "D 10002 -1 -1 0 0 0",
                        "X 943",
                        "D 10003 40 380 1 0 0",
                        "X 945",
                        "D 10004 -1 -1 0 0 1",
                        "K 77",
                        "K 13",
                        "D 10005 -1 -1 0 0 0",
                        "B",
                    ]
        # 独立拒绝/不足/取消分支，不把回调成功夹具当成真实交易结算。
        for accepted in (0, 1):
            for maximum in (-1, 0, 1, 999999999, 2147483647):
                组 += [
                    "N 0 0 0",
                    "O 127",
                    f"W 0 {maximum} {maximum} 100000 0 0 0",
                    f"U {accepted}",
                    "D 0 -1 -1 0 0 0",
                ]
                for id in range(920, 938):
                    组 += ["D 0 120 285 1 0 0", f"X {id}"]
                组 += [
                    "B",
                    "D 2000 -1 -1 0 0 0",
                    "X 942",
                    "K 77",
                    "K 13",
                    "D 2100 -1 -1 0 0 1",
                    "K 49",
                    "K 13",
                    "D 6001 -1 -1 0 0 0",
                ]
        for scale in (1, 2):
            组 += ["N 1 9 2", f"S {scale}", "O 1", "D 0 -1 -1 0 0 0", "X 922", "B"]
            for x in (-1, 117, 118, 123, 124, 319, 322, 999):
                组 += [
                    "R",
                    "O 127",
                    "D 0 -1 -1 0 0 0",
                    "X 923",
                    f"D 0 {x} 220 1 0 0",
                    "D 0 -1 -1 0 0 0",
                ]
            组 += [
                "R",
                "D 0 -1 -1 0 0 0",
                "X 938",
                "D 1 -1 -1 0 0 1",
                "P",
                "D 2 -1 -1 0 0 0",
                "X 938",
                "K 77",
                "K 13",
                "D 3 -1 -1 0 0 0",
            ]
            for land in (0, 1, 65535):
                for maximum in (-1, 0, 1, 2147483647):
                    组 += ["C", f"J {land} -20 {maximum}", "G 0 -1 -1 0 0 1", "K 77", "K 13"]
        return 组

    @staticmethod
    def _分支命令() -> list[str]:
        组 = []
        for scale in (1, 2):
            for mode in (0, 1):
                for maximum in (0, 42, 2147483647):
                    for id in range(920, 939):
                        组 += [
                            "N 0 2 0",
                            "O 127",
                            f"S {scale}",
                            f"W 0 {maximum} {maximum} 100 0 0 0",
                            "D 0 -1 -1 0 0 0",
                        ]
                        if mode:
                            组 += ["X 921", "D 1 -1 -1 0 0 0"]
                        组 += ["X 936", "D 2 120 285 1 0 0", f"X {id}", "D 3 -1 -1 0 0 1"]
        for accepted in (0, 1):
            for retry in (0, 20, 40):
                组 += [
                    "N 0 0 0",
                    "O 127",
                    "W 0 10 20 100 0 0 0",
                    f"U {accepted}",
                    "D 0 -1 -1 0 0 0",
                    "B",
                    "D 100 -1 -1 0 0 0",
                    "X 942",
                    "D 101 -1 -1 0 0 1",
                    "K 77",
                    "K 13",
                    "D 5000 -1 -1 0 0 1",
                ]
                组 += [f"K {ord(c)}" for c in str(retry)]
                组 += ["K 13", "D 5001 -1 -1 0 0 0", "D 9001 -1 -1 0 0 0"]
            for special in (0, 1, 1000000, 2147483647):
                for action in (944, 945, 946):
                    组 += [
                        "N 0 8 0",
                        "O 127",
                        "M 1",
                        f"U {accepted}",
                        f"W 0 10 20 0 {special} 0 0",
                        "W 1 0 100 0 0 0 0",
                        "W 2 0 0 0 0 0 0",
                        "W 3 0 0 0 0 0 0",
                        "D 0 -1 -1 0 0 0",
                        "B",
                        "D 1 -1 -1 0 0 0",
                        "X 943",
                        "D 2 -1 -1 0 0 0",
                        f"X {action}",
                        "D 3 -1 -1 0 0 1",
                        "K 77",
                        "K 13",
                        "D 4 -1 -1 0 0 0",
                        "B",
                        "D 5000 -1 -1 0 0 0",
                    ]
        for days in (0, 1, 127, 128, 255):
            组 += [
                "N 0 5 0",
                "O 127",
                f"W 0 300 400 100 0 {days} 0",
                "S 2",
                "M 0",
                "D 0 -1 -1 0 1 0",
                "B",
                "D 100 -1 -1 0 1 0",
                "X 941",
                "T 31 2 2000",
                "D 101 -1 -1 0 1 1",
                "P",
                "D 6000 -1 -1 0 1 0",
            ]
        for mask in (0, 1, 2, 4, 8, 16, 32, 64):
            组 += ["N 0 0 0", f"O {mask}", "D 0 -1 -1 0 0 0", "B", "D 1 -1 -1 0 0 0", "B"]
        for 图 in range(8):
            for stock in range(13):
                组 += [f"N {图} 1 0", f"Z {stock}", "J 0 15 100", "G 0 -1 -1 0 0 1", "P"]
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
        工具 = 构 / "bank-screen-oracle"
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
                str(Path(__file__).with_name("bank_screen_oracle.cpp")),
                str(arg_源码 / "tools/screens/finance.cpp"),
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
                "direct original BankScreen and primary-stock, explicit callback inputs, "
                "real sprites, internal state and callbacks; "
                "not actual window/financial rule integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "transport-smoke" if cls.传输冒烟 else "branches" if cls.分支模式 else "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "bank_screen.py",
                    "primary_stock_screen.py",
                    "number_pad.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/bank_screen.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            for i, 行 in enumerate(cls._命令()):
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "G") else b""
                if 行[:1] in ("D", "G") and len(cpp) != 614400:
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
                raise ValueError("参考银行界面故障：" + 错)
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
    参数.add_argument("--branches-only", action="store_true")
    参数.add_argument("--transport-smoke", action="store_true")
    选项 = 参数.parse_args()
    银行差分_类.分支模式 = 选项.branches_only
    银行差分_类.传输冒烟 = 选项.transport_smoke
    银行差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
