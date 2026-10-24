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
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类, 决策位置_类, 决策种类_类, 决策选项_类, 游戏阶段_类
from rich4.graphics import 图像_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 救援界面差分_类:
    """
    原保释界面/完整物品分发和真实收容、探望、回应对照。

    更新日志：
    2026.10.24 - 访客不在收容名单，站位使用原出口；路由夹具不冒充规则触发。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        self.屏 = 物品屏幕_类(原版文字_类(原版程序_类.api_读取(exe)))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[list[int]] = []
        self.通知: list[str] = []
        self.屏.声音 = lambda n: self.调用.append([0, n])
        self.屏.语音 = lambda n, q: self.调用.append([1, n, int(q)])
        self.宿 = 物品宿主_类(lambda: self.调用.append([4]), self._通知, self._回答)

    def _通知(self, arg_好: bool, arg_文: str) -> None:
        self.调用.append([3, int(arg_好)])
        self.通知.append(arg_文)

    def _回答(self, arg_i: int) -> bool:
        ok = self.会.api_回答(arg_i) if self.真实 else False
        self.调用.append([2, arg_i, int(ok)])
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
        self.通知.clear()
        框, 屏 = self.框, self.屏
        result, old = -1, self.会.世界.api_导出() if op == "D" else None
        old_rng = self.会.随机.状态 if op == "D" else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色, p.控制 = (ch + 3 * i) % 12, 1
            self.会 = 游戏会话_类(世界_类.api_从地图(self.美术.api_解码("m", 2 * m + 1), opt), 1)
            屏.api_重置()
            框.按钮.clear()
            self.医院, self.真实 = False, True
        elif op == "W":
            hospital, points, mask, visitor = map(int, 列)
            if mask & (1 << visitor):
                raise ValueError("访客自己在收容夹具中")
            self.医院 = bool(hospital)
            w = self.会.世界
            w.头.当前玩家 = visitor
            p = self.会._玩家()
            p.点券 = points
            node = next(n for n in w.节点[1:] if n.标志 & 255 == (5 if hospital else 4))
            w.节点[p.节点].标志 &= ~(0x100 << visitor)
            p.节点, p.上次节点, p.x, p.y = node.编号, 0, node.x & 65535, node.y & 65535
            node.标志 |= 0x100 << visitor
            for i in range(8):
                if mask & (1 << i):
                    self.会._收容(i, 3, self.医院)
        elif op == "O":
            self.会._探望收容(self.医院)
            if self.会.待决策 is not None and self.会.待决策.种类 != 决策种类_类.救援:
                raise ValueError("实际救援决策类型不符")
            self.真实 = True
        elif op == "B":
            kind, shape = map(int, 列)
            d = 决策_类(决策种类_类(kind), self.会.世界.头.当前玩家)
            if d.种类 == 决策种类_类.商店:
                d.选项 = [决策选项_类("", v) for v in (101, 201, 0)]
            elif d.种类 == 决策种类_类.魔法类别:
                d.选项 = [决策选项_类("", v) for v in (0, 3, 6, 9, 11)]
            elif d.种类 == 决策种类_类.魔法效果:
                d.选项 = [决策选项_类("", v) for v in (*range(12), -1)]
            elif d.种类 == 决策种类_类.救援:
                d.提示 = "探望住院角色"
                d.选项 = [决策选项_类("", v) for v in (*range(8), -1)]
            elif d.种类 == 决策种类_类.行动目标:
                if shape in (1, 3):
                    d.选项 = [决策选项_类("", v) for v in (1, 2, 3, 4, 5, 6, 0)]
                    if shape == 3:
                        d.选项[0].位置 = 决策位置_类(1, 2)
                elif shape == 2:
                    d.被抢玩家 = 0
                    d.选项 = [决策选项_类("", (4 << 16) | 1), 决策选项_类("", -1)]
                    self.会.世界.玩家[0].记录.卡片[0] = 1
            elif d.种类 == 决策种类_类.卡片目标:
                d.提示 = {1: "請選擇嫁禍對象...", 2: "使用嫁祸卡？", 3: "是否嫁禍給某人？"}.get(
                    shape, "other"
                )
                d.选项 = [决策选项_类("", 1)]
                if shape == 1:
                    d.选项.append(决策选项_类("", 2))
                d.选项.append(决策选项_类("", -1))
            self.会.待决策, self.会.阶段, self.真实 = d, 游戏阶段_类.等待决策, False
        elif op == "Z":
            屏._店.活跃, 屏._店.模式 = True, 1
            屏._魔法.活跃, 屏._魔法.类别, 屏._魔法.选中 = True, 7, -1
            屏._救援.活跃, 屏._救援.选中 = True, -1
            屏._已说, 屏._抢夺选择 = "seed", 0
        elif op == "C":
            t = int(列[0])
            屏.时钟 = t if t >= 0 else None
        elif op == "U":
            屏.api_运行延迟()
        elif op == "R":
            屏.api_重置()
            框.按钮.clear()
        elif op == "E":
            屏.api_结束访问()
            框.按钮.clear()
        elif op == "D":
            t, x, y, down, dispatch = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            屏.截图名 = ""
            if self.会.待决策 is None:
                raise ValueError("绘制时没有待决策")
            if dispatch:
                result = int(屏.api_画决策(框, self.会, self.宿))
            else:
                屏.api_画救援(框, self.会, self.会.待决策, self.宿)
        elif op in ("X", "V"):
            id = int(列[0])
            if op == "V":
                id = 210 + next(i for i, o in enumerate(self.会.待决策.选项) if o.值 == id)
            for b in 框.按钮:
                if b.编号 == id and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
            else:
                raise ValueError(f"预期救援按钮不存在：{id}")
        else:
            raise ValueError(op)
        dat = self.会.世界.api_导出()
        if old is not None and (old != dat or old_rng != self.会.随机.状态):
            raise ValueError("物品分发绘制改变World/RNG")
        d = self.会.待决策
        数 = [result, int(self.会.阶段), self.会.随机.状态, int(d is not None)]
        if d is not None:
            数 += [int(d.种类), len(d.选项)]
            for o in d.选项:
                数 += [*self._串(o.标签), o.值]
        数.append(int(self.会.救援医院))
        r, m = 屏._救援, 屏._魔法
        数 += [
            int(r.活跃),
            r.选中,
            r.不足止,
            r.打开,
            r.感谢,
            r.感谢止,
            int(r.感谢已安排),
            int(屏._店.活跃),
            屏._店.模式,
            int(m.活跃),
            m.类别,
            m.选中,
            m.施法时,
            int(m.已安排),
            int(m.电影 is not None),
            int(屏._施法 is not None),
            len(屏._延迟),
            len(屏._弹图),
            int(屏._抢夺选择 is not None),
        ]
        if 屏._抢夺选择 is not None:
            数.append(屏._抢夺选择)
        数 += [*self._串(屏._已说), int(屏.时钟 is not None)]
        if 屏.时钟 is not None:
            数.append(屏.时钟)
        数 += [*self._串(屏.截图名), len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        数 += [len(self.通知)]
        for text in self.通知:
            数 += self._串(text)
        数 += [len(dat)]
        raw = array("H", 框.画布.像素) if op == "D" else array("H")
        if byteorder != "little":
            raw.byteswap()
        return " ".join(map(str, 数)), raw.tobytes(), dat

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        for ch in range(12):
            for hospital in (0, 1):
                for slot in range(8):
                    visitor = int(slot == 0)
                    组 += [
                        f"N {ch % 8} {ch}",
                        f"W {hospital} 300 {1 << slot} {visitor}",
                        "O",
                        "D 100 -1 -1 0 1",
                        f"V {slot}",
                        "D 101 320 240 1 1",
                        "X 291",
                        "D 102 -1 -1 0 1",
                        f"V {slot}",
                        "D 103 -1 -1 0 1",
                        "X 290",
                    ]
                    if slot >= 4:
                        组 += [
                            "D 104 -1 -1 0 1",
                            "D 2603 -1 -1 0 1",
                            "D 2604 -1 -1 0 1",
                            "D 2605 -1 -1 0 1",
                            "U",
                        ]
        for hospital in (0, 1):
            for slot in (1, 4):
                for points in (0, 29, 30, 299, 300, 65535):
                    组 += [
                        "N 0 0",
                        f"W {hospital} {points} {1 << slot} 0",
                        "O",
                        "D 1 -1 -1 0 0",
                        f"V {slot}",
                        "D 2 -1 -1 0 0",
                    ]
                    if points < (30 if slot < 4 else 300):
                        组 += ["D 2001 -1 -1 0 0", "D 2002 -1 -1 0 0"]
                    else:
                        组 += [f"V {slot}"]
                        if slot >= 4:
                            组 += ["D 3 -1 -1 0 0", f"V {slot}"]
        for m in range(8):
            for hospital in (0, 1):
                组 += [
                    f"N {m} {m}",
                    f"W {hospital} 300 254 0",
                    "O",
                    "D 100 -1 -1 0 1",
                    "V -1",
                    f"N {m} {m}",
                    f"W {hospital} 300 0 0",
                    "O",
                ]
        for kind in range(21):
            for shape in range(4):
                组 += ["N 0 0", f"B {kind} {shape}", "Z", "D 100 320 240 1 1", "E"]
        组 += [
            "N 0 0",
            "W 1 300 16 0",
            "O",
            "C 0",
            "D 9999 -1 -1 0 1",
            "V 4",
            "D 9999 -1 -1 0 1",
            "V 4",
            "D 9999 -1 -1 0 1",
            "C 2500",
            "D 9999 -1 -1 0 1",
            "U",
            "C -1",
            "R",
        ]
        return 组

    @staticmethod
    def _预检命令() -> list[str]:
        return [
            "N 0 0",
            "W 1 300 16 0",
            "O",
            "D 100 -1 -1 0 1",
            "V 4",
            "D 101 -1 -1 0 1",
            "X 290",
            "D 102 -1 -1 0 1",
            "D 2601 -1 -1 0 1",
            "D 2602 -1 -1 0 1",
            "D 2603 -1 -1 0 1",
            "U",
        ]

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_报告: Path,
        arg_预检: bool = False,
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
        工具 = 构 / "item-rescue-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        头 = 构 / "item-rescue-shim/SDL3/SDL_timer.h"
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
                str(arg_源码 / "src"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("item_rescue_oracle.cpp")),
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
                "direct original hospital/prison rescue and full items dispatcher, real assets, "
                "actual confinement/visit/respond paths and explicit dispatcher display fixtures, "
                "phase/RNG/decision "
                "and complete World DAT, "
                "real sprites, internal state and callbacks; "
                "not actual window or full Application integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "smoke" if arg_预检 else "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "item_screens.py",
                    "item_rescue_screen.py",
                    "item_dispatch.py",
                    "item_magic_screen.py",
                    "item_service_types.py",
                    "item_choice_screens.py",
                    "item_shop_screen.py",
                    "item_targets.py",
                    "item_paint.py",
                    "item_screen_types.py",
                    "message_overlay.py",
                    "original_text.py",
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
            if arg_预检:
                commands = cls._预检命令()
            for i, 行 in enumerate(commands):
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
                raise ValueError("参考救援界面故障：" + 错)
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
    参数.add_argument("--smoke", action="store_true")
    选项 = 参数.parse_args()
    救援界面差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.smoke
    )
