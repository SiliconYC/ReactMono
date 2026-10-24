# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from array import array
from collections.abc import Iterable
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.flc import 动画_类
from rich4.game_types import 效果_类, 效果种类_类, 月报_类, 股利行_类
from rich4.graphics import 图像_类
from rich4.monthly_screen import 月报声音_类, 月报屏幕_类
from rich4.monthly_types import 月片_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 月报画面差分_类:
    """
    原MonthlyScreens真实画布及完整私有状态，对照明确的月结数据夹具。

    更新日志：
    2026.10.24 - 预检全部26关联FLC，电影缓冲/调色板及每绘制帧都对照；不代替自然触发。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.美术, self.字体 = 美术_类(arg_素材), 字体_类(arg_字体)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        self.原文 = 原版文字_类(原版程序_类.api_读取(exe))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用 = []
        self._图缓存 = {}
        self._解缓存 = {}
        self.资源 = []
        for 库, 条 in [("p", 16), ("p", 17)] + [("d", i) for i in range(416, 440)]:
            b = self.美术.api_解码(库, 条)
            d = 动画_类(b)
            while d.api_下一帧():
                pass
            if d.已解帧 != d.帧数:
                raise ValueError("关联月报影片不完整")
            self.资源.append(
                {
                    "archive": 库,
                    "entry": 条,
                    "frames": d.帧数,
                    "decoded_sha256": hashlib.sha256(b).hexdigest(),
                }
            )

    @staticmethod
    def _摘要(arg_列: Iterable[int]) -> int:
        h = 1469598103934665603
        for v in arg_列:
            h = ((h ^ v) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return h

    @staticmethod
    def _字(arg_文: str) -> str:
        return arg_文.encode().hex() or "-"

    @staticmethod
    def _数据(arg_f: 月报_类) -> list[int]:
        f = arg_f
        数 = [f.活跃, *f.人物, len(f.股利)]
        for r in f.股利:
            数 += [r.股票, r.盈余, *r.派发]
        数 += [
            *f.票,
            f.奖池,
            f.号码,
            f.赢家,
            *f.现金,
            *f.存款,
            *f.利息,
            *f.余额,
            *f.总资产,
            f.贷款,
            *f.倒霉天,
            *f.收入,
            *f.支出,
            f.冠军,
            f.悲情,
        ]
        return 数

    @staticmethod
    def _夹具(arg_ch: int, arg_mask: int, arg_v: int) -> 月报_类:
        ch, mask, v = arg_ch, arg_mask, arg_v
        f = 月报_类(活跃=mask, 人物=[(ch + i * 3) % 12 for i in range(4)])
        slots = [i for i in range(4) if mask & (1 << i)]
        f.贷款 = 1 << slots[0]
        for i in range(4):
            f.现金[i] = 52000 + 9000 * i
            f.存款[i] = 10000 + 15000 * i
            f.利息[i] = f.存款[i] // 10
            f.余额[i] = f.存款[i] + f.利息[i]
            f.总资产[i] = f.现金[i] + f.余额[i] + 40000
            f.收入[i] = 0xFFFFFFFF if i == 3 else 800 + 31 * i
            f.支出[i] = 0x80000000 if i == 2 else 1500 * i
            f.倒霉天[i] = i * 3
        for i in slots:
            if f.贷款 & (1 << i):
                f.利息[i], f.余额[i] = 0, f.存款[i]
        for i in range(12):
            money = 12000 - 2500 * i
            half = abs(money) // 2 * (-1 if money < 0 else 1)
            quarter = abs(money) // 4 * (-1 if money < 0 else 1)
            f.股利.append(股利行_类(i, money, [half, quarter, 0, quarter]))
        for n in range(0, 36, 3):
            f.票[n] = slots[(n // 3) % len(slots)] + 1
        f.奖池, f.号码 = 27000, (29 if v % 2 else 7)
        f.赢家 = f.票[f.号码 - 1] - 1 if f.票[f.号码 - 1] else -1
        f.冠军 = slots[-1]
        f.悲情 = slots[0] if v % 3 == 0 else -1 if v % 3 == 1 else f.冠军
        return f

    def _影片(self, arg_片: 月片_类, arg_位: str) -> list[int]:
        m = arg_片
        数 = [int(m.解码 is not None)]
        if (d := m.解码) is not None:
            key = (d, d.已解帧, d.游标)
            if self._解缓存.get(arg_位, ())[0:1] != (key,):
                self._解缓存[arg_位] = (key, self._摘要(d.像素索引), self._摘要(d.调色板))
            _, a, b = self._解缓存[arg_位]
            数 += [d.宽, d.高, d.帧数, d.间隔毫秒, d.已解帧, d.游标, a, b]
        g = m.静帧
        缓 = self._图缓存.get(arg_位)
        if 缓 is None or 缓[0] is not g:
            缓 = (g, self._摘要(g.像素), self._摘要(g.不透明))
            self._图缓存[arg_位] = 缓
        数 += [
            g.宽,
            g.高,
            g.原点x,
            g.原点y,
            缓[1],
            缓[2],
            m.x,
            m.y,
            m.次数,
            m.已过,
            int(m.运行),
            int(m.叠加),
        ]
        return 数

    def _语音(self, arg_声: int) -> int:
        self.调用.append((1, arg_声))
        return 2000 + arg_声 * 37 % 1700

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        结果 = -1
        if op == "N":
            图 = int(列[0])
            self.世 = 世界_类.api_从地图(
                self.美术.api_解码("m", 图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            )
            self.框.按钮.clear()
            self.屏 = 月报屏幕_类(
                月报声音_类(lambda n: self.调用.append((0, n)), self._语音), self.原文
            )
        elif op == "E":
            k, has, ch, mask, v = map(int, 列)
            self.屏.api_入队(效果_类(效果种类_类(k), 月报=self._夹具(ch, mask, v) if has else None))
        elif op == "F":
            self.框.画布 = 图像_类(
                640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)]
            )
            self.框.按钮.clear()
            原 = self.世.api_导出()
            self.屏.api_绘制(self.框, self.世, int(列[0]))
            if 原 != self.世.api_导出():
                raise ValueError("月报表现修改了世界")
        elif op == "X":
            for b in self.框.按钮:
                if b.编号 == int(列[0]):
                    动作 = b.动作
                    self.框.按钮.clear()
                    动作()
                    break
        elif op == "S":
            self.屏.api_跳过(bool(int(列[0])))
        elif op == "C":
            self.屏.api_清空()
        elif op == "V":
            k, has = map(int, 列)
            结果 = int(self.屏.api_处理(效果_类(效果种类_类(k), 月报=月报_类() if has else None)))
        else:
            raise ValueError(op)
        屏 = self.屏
        数 = [结果, int(屏._跳过), self._字(屏.api_画面名()), len(屏._队列)]
        for e in 屏._队列:
            数 += [int(e.种类), *self._数据(e.月报)]
        数.append(int(屏._当前 is not None))
        if (p := 屏._当前) is not None:
            数 += [
                int(p.效果.种类),
                *self._数据(p.效果.月报),
                *self._数据(p.数据),
                p.状态,
                p.计数,
                p.节拍,
                p.已过,
                int(p.点过),
                int(p.略等待),
                int(p.画过),
            ]
            b = p.泡
            数 += [b.条帧, b.x, b.y, b.dx, b.dy, self._字(b.文字), b.剩余毫秒, int(b.显示)]
            数 += self._影片(p.片, "main") + self._影片(p.次片, "second")
            数 += [
                p.布局,
                p.女士,
                p.聚光,
                p.隐藏,
                p.奖,
                int(p.卡片),
                int(p.列队),
                int(p.欢颜),
                int(p.排过),
                int(p.球),
                int(p.绿),
                int(p.名牌),
                p.眼,
                p.嘴,
                p.左,
                p.眨眼,
                p.眨步,
                p.嘴时,
                p.种子,
                int(p.关闭),
            ]
        数.append(len(self.框.按钮))
        for b in self.框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数.append(len(self.调用))
        for k, n in self.调用:
            数 += [k, n]
        像 = b""
        if op == "F":
            raw = array("H", self.框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_报告: Path,
        arg_上限: int = 0,
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
        工具 = 构 / "monthly-screen-oracle"
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
                str(Path(__file__).with_name("monthly_screen_oracle.cpp")),
                str(arg_源码 / "tools/screens/monthly.cpp"),
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
            "episodes": [],
            "scope": (
                "direct original MonthlyScreens, explicit figures; real assets/fonts/PE, "
                "full private state and movie buffer fingerprints; "
                "not natural events, audible playback or full app"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "movies_preflight": 自.资源,
            "python_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [
                    *Path(__file__).parents[1].joinpath("src/rich4").glob("monthly_*.py"),
                    Path(__file__).parents[1].joinpath("src/rich4/screen_draw.py"),
                ]
            },
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()

        def 保存() -> None:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, indent=2) + "\n")

        def 操作(arg_行: str) -> None:
            进.stdin.write((arg_行 + "\n").encode())
            进.stdin.flush()
            实 = 进.stdout.readline().decode().strip()
            if not 实:
                raise ValueError("C++提前结束：" + 进.stderr.read().decode())
            cpp = 进.stdout.read(614400) if arg_行[:1] == "F" else b""
            预, py = 自._操作(arg_行, 报["commands"])
            if 实 != 预:
                Path(".research-cache/monthly-private-failure.json").write_text(
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
                保存()

        try:
            操作("N 0")
            for k in range(33):
                for has in (0, 1):
                    操作(f"V {k} {has}")
            组 = [
                (0, 14, 0, 15, 0, False),
                (1, 15, 0, 15, 0, False),
                (7, 15, 0, 10, 1, False),
                (0, 16, 0, 15, 0, False),
            ]
            组 += [(ch % 8, 16, ch, 15, 0, False) for ch in range(1, 12)]
            组 += [
                (1, 16, 3, 3, 1, False),
                (2, 16, 7, 7, 2, False),
                (3, 16, 5, 10, 0, True),
                (4, 15, 9, 7, 0, True),
            ]
            if arg_上限:
                组 = 组[:arg_上限]
            for 图, k, ch, mask, v, tap in 组:
                起 = 报["painted_frames"]
                操作(f"N {图}")
                操作(f"E {k} 1 {ch} {mask} {v}")
                操作("F 0")
                for n in range(5000):
                    if not 自.屏.api_活跃():
                        break
                    p = 自.屏._当前
                    if tap and n % 3 == 1:
                        操作("X 911")
                    dt = 1000 if k == 14 else 50 if k == 15 else 20 if p and p.片.运行 else 100
                    操作(f"F {dt}")
                else:
                    raise ValueError("月结屏幕未自然结束")
                报["episodes"].append(
                    {
                        "map": 图,
                        "kind": k,
                        "character_base": ch,
                        "active": mask,
                        "variant": v,
                        "tap": tap,
                        "painted_frames": 报["painted_frames"] - 起,
                    }
                )
                保存()
            进.stdin.close()
            退 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退 or 错:
                raise ValueError("参考月报故障：" + 错)
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
            保存()
        print(
            json.dumps(
                {
                    "status": 报["status"],
                    "commands": 报["commands"],
                    "frames": 报["painted_frames"],
                    "episodes": len(报["episodes"]),
                }
            )
        )


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    参数.add_argument("--limit", type=int, default=0)
    选项 = 参数.parse_args()
    月报画面差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.limit
    )
