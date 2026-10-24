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
from rich4.number_pad import 数字板_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.stocks import 股市_类
from rich4.trading import 交易_类, 挂单_类
from rich4.trading_board_screen import 交易公告栏_类
from rich4.trading_screen_types import 交易动作_类, 交易视图_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 交易屏幕差分_类:
    """
    直接原TradingBoard/NumberPad、真实交易回调及完整World DAT差分。

    更新日志：
    2026.10.24 - 显式显示夹具和失败回调独立标识，不冒充自然对局或正式应用。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        self.屏 = 交易公告栏_类(原版文字_类(原版程序_类.api_读取(exe)))
        self.板 = 数字板_类()
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[list[int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append([0, n]))
        self.动作 = 交易动作_类(self._挂牌, self._撤件, self._购买, lambda: self.调用.append([4]))

    def _挂牌(self, arg_单: 挂单_类) -> bool:
        ok = (
            bool(self.模式[0])
            if self.模式[0] >= 0
            else 交易_类.api_挂牌(self.世, self.人, arg_单).已应用
        )
        self.调用.append([1, arg_单.种类, arg_单.项目, arg_单.价格, arg_单.数量, int(ok)])
        return ok

    def _撤件(self, arg_i: int) -> bool:
        ok = bool(self.模式[1]) if self.模式[1] >= 0 else 交易_类.api_取消(self.世, self.人, arg_i)
        self.调用.append([2, arg_i, int(ok)])
        return ok

    def _购买(self, arg_s: int, arg_i: int) -> bool:
        ok = (
            bool(self.模式[2])
            if self.模式[2] >= 0
            else 交易_类.api_购买(self.世, self.人, arg_s, arg_i).已应用
        )
        self.调用.append([3, arg_s, arg_i, int(ok)])
        return ok

    @staticmethod
    def _串(arg_文: str) -> list[int]:
        data, h = arg_文.encode(), 14695981039346656037
        for b in data:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(data), h]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        框, 屏, 板 = self.框, self.屏, self.板
        result, old = -1, self.世.api_导出() if op == "D" else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色 = (ch + 3 * i) % 12
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", m * 2 + 1), opt)
            屏.api_重置()
            板.api_关闭()
            框.按钮.clear()
            self.人, self.模式 = 0, [-1] * 3
        elif op == "W":
            variant, owner = map(int, 列)
            self.世.头.物价 = 1 + variant % 5
            for s, p in enumerate(self.世.玩家):
                p.记录.现金, p.记录.银行, p.记录.控制标志 = (0 if variant == 9 else 1000000, 0, 1)
                for j in range(12):
                    p.持仓[j].数量 = (j + 3) * (s + 1)
                    self.世.股票[j].浮点位[2] = 股市_类._位(10.25 + j * 1.5)
                p.记录.道具[:13] = [1 + j % 3 for j in range(13)]
                p.记录.卡片 = [1 + j + variant % 2 * 15 for j in range(15)]
            for j, land in enumerate(self.世.地产[1:], 1):
                land.经济.业主 = owner or 1 + j % 4
                land.经济.等级, land.经济.连锁 = (j + variant) % 6, int(j % 7 == 0)
                land.到期日 = 0 if j % 3 else 0x07C70C1F
            for j, land in enumerate(self.世.设施[1:], 1):
                land.业主, land.等级 = owner or 1 + j % 4, (j + variant) % 6
                land.到期日 = 0 if j % 2 else 0x07C80102
        elif op == "Z":
            s = int(列[0])
            p = self.世.玩家[s]
            for h in p.持仓:
                h.数量 = 0
            p.记录.道具, p.记录.卡片 = [0] * 15, [0] * 15
            for land in self.世.地产:
                if land.经济.业主 == s + 1:
                    land.经济.业主 = 0
            for land in self.世.设施:
                if land.业主 == s + 1:
                    land.业主 = 0
        elif op == "A":
            self.人 = int(列[0])
        elif op == "E":
            self.模式 = list(map(int, 列))
        elif op == "O":
            s, kind, item, price, quantity = map(int, 列)
            result = int(交易_类.api_挂牌(self.世, s, 挂单_类(kind, item, price, quantity)).已应用)
            if not result:
                raise ValueError("真实挂牌夹具未成功")
        elif op == "B":
            s, i = map(int, 列)
            result = int(交易_类.api_取消(self.世, s, i))
        elif op == "V":
            v, 屏._货类, 屏._分类, 屏._滚动 = map(int, 列)
            屏._视图 = 交易视图_类(v)
            板.api_关闭()
        elif op == "D":
            t, x, y, down, overlay = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            屏.api_绘制(self.宿, self.世, self.人, 板, self.动作)
            if overlay:
                板.api_绘制(self.宿)
        elif op in ("X", "I"):
            id = int(列[0])
            if op == "I":
                kind, item = map(int, 列)
                items = 交易_类.api_可售项目(self.世, self.人)
                id = 460 + next(
                    i for i, it in enumerate(items) if (it.种类, it.编号) == (kind, item)
                )
            for b in 框.按钮:
                if b.编号 == id and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
            else:
                raise ValueError(f"预期按钮不存在：{id}")
        elif op == "K":
            板.api_键(self.宿, chr(int(列[0])))
        elif op == "C":
            屏.api_取消(self.宿, self.动作)
        elif op == "R":
            屏.api_重置()
            板.api_关闭()
            框.按钮.clear()
        else:
            raise ValueError(op)
        dat = self.世.api_导出()
        if old is not None and old != dat:
            raise ValueError("绘制改变世界DAT")
        数 = [result, 屏._视图, 屏._货类, 屏._分类, 屏._滚动, int(屏._详情 is not None)]
        if 屏._详情 is not None:
            q = 屏._详情
            数 += [q.卖家, q.索引, q.出售项.种类, q.出售项.项目, q.出售项.价格, q.出售项.数量]
        数 += self._串(屏._提示) + self._串(屏._通知) + [屏._通知止, 屏._现在, 屏._建议]
        数 += [int(板._活跃), int(板._拖), 板._x, 板._y, 板._比例, 板._上限, 板.api_值()]
        数 += self._串(板._文) + [int(板._完成 is not None), len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        数 += [len(dat)]
        像 = b""
        if op == "D":
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像, dat

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        # 实际菜单→数量→价格→真实挂牌→撤件→购买；四种货类分别独立。
        for m in range(8):
            for category in range(4):
                组 += [
                    f"N {m} {m}",
                    "W 0 1",
                    "D 100 -1 -1 0 1",
                    "X 480",
                    "D 101 480 130 1 1",
                    f"X {484 + category}",
                    "D 102 160 112 0 1",
                ]
                # 挑选列表的首项编号由真实库存顺序决定，不假设第八图有普通地产。
                # 全部含12股票；首地产紧随其后，首道具/卡另用独立选择命令生成。
                if category > 1:
                    组 += ["C", "D 103 -1 -1 0 1"]
                    continue
                组 += [f"X {460 + (0 if category == 0 else 12)}", "D 104 -1 -1 0 1"]
                if category == 0:
                    组 += ["K 50", "K 13", "D 105 -1 -1 0 1"]
                组 += [
                    "K 49",
                    "K 13",
                    "D 106 -1 -1 0 1",
                    "X 600",
                    "D 107 250 350 1 1",
                    "X 456",
                    "D 108 -1 -1 0 1",
                ]
                组 += [
                    "O 1 3 1 1 1",
                    "D 109 -1 -1 0 1",
                    "X 600",
                    "D 110 -1 -1 0 1",
                    "X 456",
                    "D 111 -1 -1 0 1",
                    "C",
                ]
        # 每张图的所有地产类别、分页/等于/超过总数以及股票、道具和两组30卡名。
        for m in range(8):
            for variant in (0, 1):
                组 += [f"N {m} {m + variant}", f"W {variant} 1"]
                for tab in range(5):
                    组 += [
                        f"V 3 1 {tab} 0",
                        "D 200 114 113 1 1",
                        "X 496",
                        "D 201 520 115 1 1",
                        "X 495",
                        "D 202 520 80 1 1",
                        f"V 3 1 {tab} 9999",
                        "D 203 -1 -1 0 1",
                    ]
                for v, cat in ((2, 0), (4, 2), (4, 3)):
                    组 += [f"V {v} {cat} 0 0", "D 204 170 210 1 1"]
        # 全部人物/槽/性别图标、七件满栏及报价详情各类型。
        for ch in range(12):
            for actor in range(4):
                组 += [f"N 0 {ch}", "W 1 0", f"A {actor}"]
                for i in range(7):
                    组.append(f"O {actor} 1 {i} {i + 1} 1")
                组 += [
                    "D 300 470 80 1 1",
                    "X 480",
                    "D 1799 -1 -1 0 1",
                    "D 1800 -1 -1 0 1",
                    "X 600",
                    "D 1801 240 330 1 1",
                    "X 457",
                    "D 1802 -1 -1 0 1",
                ]
        for kind, item in ((1, 0), (2, 2001), (2, 4001), (3, 13), (4, 30)):
            for actor in (0, 1):
                组 += [
                    "N 0 10",
                    "W 1 1",
                    f"A {actor}",
                    f"O 0 {kind} {item} 1 1",
                    "D 400 110 120 1 1",
                    "X 600",
                    "D 401 240 350 1 1",
                    "X 456",
                    "D 402 -1 -1 0 1",
                ]
        # 真规则拒买（现金0）、失效快照、空库存分类、回调拒绝和取消通知。
        for kind in range(4):
            组 += [
                "N 0 0",
                "Z 0",
                "D 500 -1 -1 0 1",
                "X 480",
                "D 501 -1 -1 0 1",
                f"X {484 + kind}",
                "D 502 -1 -1 0 1",
            ]
        组 += [
            "N 0 0",
            "W 9 0",
            "A 1",
            "O 0 3 1 100 1",
            "D 600 -1 -1 0 1",
            "X 600",
            "D 601 -1 -1 0 1",
            "X 456",
            "D 2100 -1 -1 0 1",
            "D 2101 -1 -1 0 1",
            "B 0 0",
            "D 2102 -1 -1 0 1",
            "C",
            "C",
            "R",
        ]
        return 组

    @staticmethod
    def _扩展() -> list[str]:
        组 = []
        for actor in range(4):
            for kind, ids in ((3, range(1, 14)), (4, range(1, 31))):
                for item in ids:
                    variant, category = int(kind == 4 and item > 15), 2 if kind == 3 else 3
                    组 += [
                        f"N {(actor + item) % 8} {item % 12}",
                        f"W {variant} {actor + 1}",
                        f"A {actor}",
                        f"V 4 {category} 0 0",
                        "D 10 160 210 1 1",
                        f"I {kind} {item}",
                        "D 11 -1 -1 0 1",
                        "K 49",
                        "K 13",
                        "D 12 -1 -1 0 1",
                        "X 600",
                        "D 13 -1 -1 0 1",
                        "X 456",
                        "D 14 -1 -1 0 1",
                    ]
        组 += [
            "N 0 0",
            "W 0 1",
            "V 4 2 0 0",
            "D 20 -1 -1 0 1",
            "I 3 1",
            "D 21 -1 -1 0 1",
            "E 0 -1 -1",
            "K 49",
            "K 13",
            "D 22 -1 -1 0 1",
            "D 1520 -1 -1 0 1",
            "D 1521 -1 -1 0 1",
            "C",
            "V 2 0 0 0",
            "D 2000 -1 -1 0 1",
            "I 1 0",
            "D 2001 -1 -1 0 1",
            "K 13",
            "D 2002 -1 -1 0 1",
            "C",
            "V 4 2 0 0",
            "D 2010 -1 -1 0 1",
            "I 3 1",
            "D 2011 -1 -1 0 1",
            "K 13",
            "D 2012 -1 -1 0 1",
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
        arg_扩展: bool = False,
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
        工具 = 构 / "trading-board-oracle"
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
                str(Path(__file__).with_name("trading_board_oracle.cpp")),
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
                "direct original TradingBoard and NumberPad, real maps and assets, "
                "actual trading post/cancel/buy callbacks, complete World DAT and "
                "real sprites, internal state and callbacks; "
                "not actual window or full Application integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "all-inventory-actions" if arg_扩展 else "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "trading_board_screen.py",
                    "trading_screen_text.py",
                    "trading_screen_types.py",
                    "trading.py",
                    "number_pad.py",
                    "original_text.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/trading_board_screen.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            for i, 行 in enumerate(cls._扩展() if arg_扩展 else cls._命令()):
                报["last_command"], 报["last_index"] = 行, i
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
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
                raise ValueError("参考交易界面故障：" + 错)
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
    参数.add_argument("--expanded", action="store_true")
    选项 = 参数.parse_args()
    交易屏幕差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.expanded
    )
