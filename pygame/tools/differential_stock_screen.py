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
from rich4.cards import 卡片目标_类, 目标种类_类
from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.number_pad import 数字板_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.stock_screen import 股票动作_类, 股票屏幕_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 股票差分_类:
    """
    直接原股市报价/资讯/历史图表/股权饼图、买卖与卡目标组件差分。

    更新日志：
    2026.10.24 - 完整私有状态与数额回调，实际核心接线与窗口听感另验。
    """

    网格模式 = False

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        self.原文 = 原版文字_类(原版程序_类.api_读取(exe))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[tuple[int, int, int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append((0, n, 0)))
        self.屏 = 股票屏幕_类(self.原文)
        self.板 = 数字板_类()
        self.动 = 股票动作_类(
            lambda s, n: self._答(1, s, n),
            lambda s, n: self._答(2, s, n),
            lambda: self.调用.append((3, 0, 0)),
        )
        self.答成功 = True

    def _答(self, arg_种: int, arg_股: int, arg_数: int) -> bool:
        self.调用.append((arg_种, arg_股, arg_数))
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
        框, 宿, 屏, 板 = self.框, self.宿, self.屏, self.板
        old = self.世.api_导出() if op in ("D", "G", "K", "X", "B") else None
        if op == "N":
            图, 人, self.玩家 = map(int, 列)
            设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            for i, p in enumerate(设.玩家):
                p.角色 = (人 + i * 3) % 12
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", 图 * 2 + 1), 设)
            屏.api_重置()
            self.板 = 板 = 数字板_类()
            self.决 = 决策_类(决策种类_类.卡片目标, 0)
            框.按钮.clear()
            self.答成功 = True
        elif op == "T":
            d, m, y, days = map(int, 列)
            self.世.头.日期, self.世.新闻影响天数 = (d, m, y), days
        elif op == "S":
            sel, page, info = map(int, 列)
            屏.选中, 屏.页, 屏.资讯 = None if sel < 0 else sel, page, bool(info)
        elif op == "W":
            slot, bank = map(int, 列)
            self.世.玩家[slot].记录.银行 = bank
        elif op == "P":
            stock, current, previous, maximum, listed, halt = map(int, 列)
            q = self.世.股票[stock]
            q.浮点位[2], q.浮点位[1], q.标志10, q.标志4, q.停牌天数 = (
                current,
                previous,
                maximum,
                listed,
                halt,
            )
        elif op == "V":
            slot, stock, amount, cost = map(int, 列)
            h = self.世.玩家[slot].持仓[stock]
            h.数量, h.成本位 = amount, cost
        elif op == "H":
            stock, self.世.股史游标, count, bits, stride = map(int, 列)
            self.世.股史[stock] = [bits + stride * i if i < count else 0 for i in range(144)]
        elif op == "C":
            index, owner, kind, stock, funds, change, remaining, months = map(int, 列)
            c = self.世.公司[index]
            c.业主, c.类型, c.股票索引 = owner, kind, stock
            c.资金, c.资金变化, c.剩余股份, self.世.月数 = funds, change, remaining, months
        elif op == "A":
            base, mode = map(int, 列)
            self.决.选项 = [
                决策选项_类("", i, 对象=卡片目标_类(目标种类_类.股票, i)) for i in range(12)
            ]
            self.决.选项.append(决策选项_类("", -1))
            if mode:
                self.决.选项 += [
                    决策选项_类("", 0),
                    决策选项_类("", 0, 对象=卡片目标_类(目标种类_类.角色, 0)),
                    决策选项_类("", 0, 对象=卡片目标_类(目标种类_类.股票, 99)),
                ]
        elif op == "U":
            self.答成功 = bool(int(列[0]))
        elif op == "Z":
            板.api_缩放(int(列[0]))
        elif op in ("D", "G"):
            ticks, x, y, down, showpad, base, has = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = ticks, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            if op == "D":
                屏.api_绘制(宿, self.世, self.玩家, 板, self.动)
            else:
                屏.api_卡片目标(
                    宿,
                    self.世,
                    self.玩家,
                    self.决 if has else None,
                    base,
                    lambda n: self.调用.append((4, n, 0)),
                )
            if showpad and 板.api_活跃():
                框.按钮.clear()
                板.api_绘制(宿)
        elif op == "X":
            for b in 框.按钮:
                if b.编号 == int(列[0]) and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
        elif op == "K":
            板.api_键(宿, chr(int(列[0]) & 255))
        elif op == "B":
            屏.api_取消(宿, self.动.关)
        elif op == "R":
            屏.api_重置()
        elif op == "E":
            板.api_取消(宿)
        else:
            raise ValueError(op)
        if old is not None and old != self.世.api_导出():
            raise ValueError("股市界面改变世界DAT")
        数 = [-1, 屏.选中 if 屏.选中 is not None else -1, 屏.页, int(屏.资讯), 屏._弹止]
        数 += self._串(屏._弹文)
        数 += [int(板._活跃), int(板._拖), 板._x, 板._y, 板._比例, 板._上限]
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
        if 股票差分_类.网格模式:
            return 股票差分_类._网格命令()
        组 = []
        for 图 in range(8):
            for stock in range(12):
                ch, slot = stock, stock % 4
                current = (1.0, 14.99, 15.0, 149.9, 150.0, 9999.0)[stock % 6]
                previous = min(
                    9999.0,
                    max(
                        1.0,
                        current if stock % 3 == 0 else current * (0.89 if stock % 3 == 1 else 1.11),
                    ),
                )
                bits, prev = 股市_类._位(current), 股市_类._位(previous)
                count = (0, 1, 6, 24, 143, 144)[stock % 6]
                组 += [
                    f"N {图} {ch} {slot}",
                    "T 14 6 2000 0",
                    f"W {slot} 2147483647",
                    f"P {stock} {bits} {prev} 60000 {stock % 2} {stock % 5 == 4:d}",
                    f"H {stock} {stock * 13} {count} 1092616192 60000",
                    f"V {slot} {stock} {stock * 1000} {bits}",
                    f"S {stock} 0 0",
                    "D 0 140 20 1 0 210 0",
                    f"S {stock} 0 1",
                    "D 1 -1 -1 0 0 210 0",
                    "B",
                    f"S {stock} 1 0",
                    "D 2 40 20 1 0 210 0",
                    "B",
                    "D 3 -1 -1 0 0 210 0",
                ]
        for stock in range(12):
            组 += [
                f"N 0 {stock} 0",
                "T 14 6 2000 0",
                "A 210 1",
                "G 0 -1 -1 0 0 210 1",
                f"X {210 + stock}",
                "G 1 560 20 1 0 210 1",
                f"X {210 + stock}",
                "G 2 -1 -1 0 0 210 0",
                "G 3 -1 -1 0 0 210 1",
                "X 222",
                "G 4 -1 -1 0 0 210 1",
            ]
        for success in (0, 1):
            for current in (0.0, 9.0, 10.0, 11.0):
                for scale in (1, 2):
                    bits, prev = 股市_类._位(current), 股市_类._位(10.0)
                    组 += [
                        "N 0 2 0",
                        "T 14 6 2000 0",
                        f"U {success}",
                        f"Z {scale}",
                        "W 0 12345",
                        f"P 0 {bits} {prev} 1000 1 0",
                        "V 0 0 5000 1092616192",
                        "S 0 0 0",
                        "D 0 -1 -1 0 0 210 0",
                        "X 430",
                        "D 1499 -1 -1 0 1 210 0",
                        "K 77",
                        "K 13",
                        "D 1500 -1 -1 0 0 210 0",
                        "X 431",
                        "D 1501 -1 -1 0 1 210 0",
                        "K 77",
                        "K 13",
                        "D 3001 -1 -1 0 0 210 0",
                        "X 434",
                        "D 3002 -1 -1 0 0 210 0",
                        "X 60",
                        "D 3003 -1 -1 0 0 210 0",
                        "X 60",
                    ]
        for day, news in ((14, 0), (18, 0), (14, 1)):
            组 += ["N 0 0 0", f"T {day} 6 2000 {news}", "D 0 -1 -1 0 0 210 0", "X 60", "B"]
        return 组

    @staticmethod
    def _网格命令() -> list[str]:
        组 = []
        for 图 in range(8):
            for kind in range(14):
                组 += [
                    f"N {图} 9 3",
                    "T 14 6 2000 0",
                    "P 0 1092616192 1092616192 60000 1 0",
                    f"C 1 {kind % 5} {kind} 0 -123456 -12345 4321 {kind % 4}",
                    f"V 0 0 {kind * 1000} 1092616192",
                    "V 3 0 1 1092616192",
                    "H 0 143 144 1092616192 0",
                    "S 0 0 1",
                    "D 0 -1 -1 0 0 210 0",
                    "S 0 1 0",
                    "D 1 -1 -1 0 0 210 0",
                ]
        for cursor in (-1, 0, 1, 143, 144, 2147483647):
            for count in (0, 1, 6, 144):
                for stride in (0, 1, 60000):
                    组 += [
                        "N 0 2 0",
                        "T 14 6 2000 0",
                        f"H 0 {cursor} {count} 1092616192 {stride}",
                        "S 0 0 1",
                        "D 0 -1 -1 0 0 210 0",
                    ]
        for current in (0.0, 1.0, 14.999, 15.0, 149.999, 150.0, 9999.0):
            for previous in (1.0, 15.0, 150.0, 9999.0):
                bits, prev = 股市_类._位(current), 股市_类._位(previous)
                组 += [
                    "N 0 2 0",
                    "T 14 6 2000 0",
                    f"P 0 {bits} {prev} 0 0 0",
                    "S 0 0 0",
                    "D 0 -1 -1 0 0 210 0",
                    "S 0 0 1",
                    "D 1 -1 -1 0 0 210 0",
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
        工具 = 构 / "stock-screen-oracle"
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
                str(Path(__file__).with_name("stock_screen_oracle.cpp")),
                str(arg_源码 / "tools/screens/finance.cpp"),
                str(arg_源码 / "tools/screens/stocks.cpp"),
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
                "direct original StockMarket, explicit UI state and captured trade callbacks, "
                "real sprites, internal state and callbacks; "
                "not actual window/financial rule integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "grid" if cls.网格模式 else "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "stock_screen.py",
                    "stock_screen_draw.py",
                    "stock_info.py",
                    "number_pad.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/stock_screen.py").read_bytes()
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
                raise ValueError("参考股市界面故障：" + 错)
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
    参数.add_argument("--grid-only", action="store_true")
    选项 = 参数.parse_args()
    股票差分_类.网格模式 = 选项.grid_only
    股票差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
