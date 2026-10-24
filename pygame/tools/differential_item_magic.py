# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from array import array
from functools import lru_cache
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.flc import 动画_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.graphics import 图像_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.item_service_types import 施法电影_类, 魔法屏幕状态_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 魔法界面差分_类:
    """
    原魔法屋完整画布、真实电影/掩码和实际会话选择对照。

    更新日志：
    2026.10.24 - 人类输入、显式画廊电影与电脑表现区分记录，不虚称自然动画触发。
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
        movie = 动画_类(self.美术.api_解码("p", 20))
        while movie.api_下一帧():
            pass
        self.帧数, self.延迟 = movie.帧数, movie.间隔毫秒
        if not self.帧数 or movie.已解帧 != self.帧数 or len(self.美术.api_解码("p", 19)) < 307200:
            raise ValueError("真实电影/掩码预检不完整")

    def _通知(self, arg_好: bool, arg_文: str) -> None:
        self.调用.append([3, int(arg_好)])
        self.通知.append(arg_文)

    def _回答(self, arg_i: int) -> bool:
        ok = self.会.api_回答(arg_i) if self.真实 else False
        self.调用.append([2, arg_i, int(ok)])
        return ok

    @staticmethod
    @lru_cache(maxsize=256)
    def _散列(arg_数据: bytes) -> int:
        h = 14695981039346656037
        for b in arg_数据:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return h

    @classmethod
    def _串(cls, arg_文: str) -> list[int]:
        raw = arg_文.encode()
        return [len(raw), cls._散列(raw)]

    @staticmethod
    def _短字节(arg_数: list[int]) -> bytes:
        raw = array("H", arg_数)
        if byteorder != "little":
            raw.byteswap()
        return raw.tobytes()

    def _电影列(self, arg_电影: 施法电影_类 | None) -> list[int]:
        if arg_电影 is None:
            return [0]
        d, im = arg_电影.解码, arg_电影.图像
        return [
            1,
            d.宽,
            d.高,
            d.帧数,
            d.间隔毫秒,
            d.已解帧,
            d.游标,
            self._散列(bytes(d.像素索引)),
            self._散列(self._短字节(d.调色板)),
            im.宽,
            im.高,
            im.原点x,
            im.原点y,
            len(im.像素),
            self._散列(self._短字节(im.像素)),
            len(im.不透明),
            self._散列(im.不透明),
            int(arg_电影.已响),
        ]

    def _决策(self) -> 决策_类:
        if self.真实:
            if self.会.待决策 is None:
                raise ValueError("魔法决策已不存在")
            return self.会.待决策
        return self.夹具

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        self.通知.clear()
        框, 屏 = self.框, self.屏
        old = self.会.世界.api_导出() if op in ("D", "F") else None
        old_rng = self.会.随机.状态 if op in ("D", "F") else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色, p.控制 = (ch + 3 * i) % 12, 1
            self.会 = 游戏会话_类(世界_类.api_从地图(self.美术.api_解码("m", 2 * m + 1), opt), 1)
            屏.api_重置()
            框.按钮.clear()
            self.真实 = False
        elif op == "W":
            profile = int(列[0])
            w, base = self.会.世界, self.会._玩家()
            for i, p in enumerate(w.玩家):
                s = p.记录
                s.现金, s.银行, s.点券, s.性别 = 1000 + i * 100, 2000 + i * 100, 100 + i * 10, i % 2
                s.卡片, s.道具, p.状态.神明信息 = [0] * 15, [0] * 15, 1 if profile and i == 0 else 0
                s.交通 = i % 3 if profile else 0
                s.骰数 = 1 + (s.交通 & 3)
                s.x, s.y, s.节点, s.上次节点 = base.x, base.y, base.节点, base.上次节点
                if profile:
                    s.卡片[0], s.卡片[1], s.道具[0] = i + 1, 13, i + 1
            for i, land in enumerate(w.地产[1:], 1):
                land.经济.业主, land.经济.等级 = (1 + i % 4, i % 6) if profile else (0, 0)
                land.经济.连锁 = 0
            if profile:
                god = w.物件[0]
                god.附身玩家, god.节点, god.剩余天数 = 1, 0, 5
        elif op == "O":
            self.会._开魔法()
            if self.会.待决策 is None or self.会.待决策.种类 != 决策种类_类.魔法类别:
                raise ValueError("未到达真实魔法屋类别")
            self.真实 = True
        elif op == "B":
            group, effect, casting = map(int, 列)
            self.夹具 = 决策_类(
                决策种类_类.魔法效果,
                0,
                选项=[决策选项_类("", i) for i in range(12)] + [决策选项_类("", -1)],
            )
            self.真实 = False
            屏._魔法 = 魔法屏幕状态_类(活跃=True, 类别=group, 选中=effect, 施法时=casting)
        elif op == "T":
            group, effect = map(int, 列)
            屏.api_开始电脑施法(group, effect)
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
        elif op == "P":
            框.指针x, 框.指针y = map(int, 列)
        elif op == "K":
            i = 屏._魔法罩.index(int(列[0]))
            框.指针x, 框.指针y = i % 640, i // 640
        elif op in ("D", "F"):
            t, x, y, down = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            屏.截图名 = ""
            if op == "D":
                屏.api_画魔法(框, self.会, self._决策(), self.宿)
            else:
                屏.api_画电脑施法(框)
        elif op in ("X", "V"):
            id = int(列[0])
            if op == "V":
                id = 210 + next(i for i, o in enumerate(self._决策().选项) if o.值 == id)
            for b in 框.按钮:
                if b.编号 == id and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
            else:
                raise ValueError(f"预期魔法按钮不存在：{id}")
        else:
            raise ValueError(op)
        dat = self.会.世界.api_导出()
        if old is not None and (old != dat or old_rng != self.会.随机.状态):
            raise ValueError("魔法绘制改变World/RNG")
        d = self.会.待决策
        数 = [-1, int(self.会.阶段), self.会.随机.状态, int(d is not None)]
        if d is not None:
            数 += [int(d.种类), len(d.选项)]
            for o in d.选项:
                数 += [*self._串(o.标签), o.值]
        数.append(self.会.魔法类别)
        m = 屏._魔法
        数 += [int(m.活跃), m.打开, m.类别, m.选中, m.施法时, int(m.已安排), *self._电影列(m.电影)]
        数.append(int(屏._施法 is not None))
        if 屏._施法 is not None:
            c = 屏._施法
            数 += [c.类别, c.效果, c.开始, *self._电影列(c.电影)]
        数 += [len(屏._延迟), *self._串(屏._已说), int(屏.时钟 is not None)]
        if 屏.时钟 is not None:
            数.append(屏.时钟)
        数 += [*self._串(屏.截图名), len(屏._魔法罩), self._散列(屏._魔法罩), len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        数 += [len(self.通知)]
        for text in self.通知:
            数 += self._串(text)
        数 += [len(dat)]
        raw = self._短字节(框.画布.像素) if op in ("D", "F") else b""
        return " ".join(map(str, 数)), raw, dat

    def _命令(self) -> list[str]:
        组 = []
        for group in range(12):
            组 += [
                "N 0 0",
                "W 1",
                "O",
                "D 100 -1 -1 0",
                f"V {group}",
                "D 101 -1 -1 0",
                "V -1",
                "D 102 -1 -1 0",
            ]
        for profile in (0, 1):
            for m in range(8):
                组 += [f"N {m} {m}", f"W {profile}", "O", "D 100 68 366 1"]
        for group in range(12):
            for effect in range(12):
                组 += [
                    "N 0 0",
                    f"B {group} -1 0",
                    "D 100 -1 -1 0",
                    f"B {group} {effect} 0",
                    "D 101 320 384 1",
                    f"T {group} {effect}",
                    "F 1 -1 -1 0",
                    "F 1500 -1 -1 0",
                    "F 1501 -1 -1 0",
                ]
        for group, effect in ((0, 0), (3, 10), (11, 11)):
            组 += ["N 0 0", f"B {group} {effect} 2000", "D 2999 -1 -1 0"]
            for i in range(self.帧数):
                组 += [f"D {3000 + i * self.延迟} -1 -1 0"]
            end = 3000 + self.帧数 * self.延迟
            组 += [
                f"D {end - 1} -1 -1 0",
                f"D {end} -1 -1 0",
                f"D {end + 1} -1 -1 0",
                "U",
                f"T {group} {effect}",
                "F 1 -1 -1 0",
            ]
            for i in range(self.帧数):
                组 += [f"F {1501 + i * self.延迟} -1 -1 0"]
            组 += [f"F {1501 + self.帧数 * self.延迟} -1 -1 0"]
        for m in range(8):
            for effect in range(12):
                组 += [
                    f"N {m} {m}",
                    "W 1",
                    "O",
                    "D 100 -1 -1 0",
                    "V 3",
                    "D 101 -1 -1 0",
                    f"V {effect}",
                    "D 102 -1 -1 0",
                    f"V {effect}",
                    "D 10000 -1 -1 0",
                    f"V {effect}",
                ]
        for value in range(14):
            组 += ["N 0 0", "B 3 -1 0", "D 100 -1 -1 0", f"K {value}", "X 299", "D 101 -1 -1 0"]
        组 += [
            "N 0 0",
            "T 3 10",
            "F 0 -1 -1 0",
            "T 3 10",
            "F 1 -1 -1 0",
            "T -1 10",
            "T 3 12",
            "F 2 -1 -1 0",
            "X 1660",
            "B 3 10 0",
            "D 1 -1 -1 0",
            "P -1 -1",
            "X 299",
            "D 2 -1 -1 0",
            "C 0",
            "T 3 10",
            "F 9999 -1 -1 0",
            "C -1",
            "R",
        ]
        return 组

    @staticmethod
    def _预检命令() -> list[str]:
        return [
            "N 0 0",
            "W 1",
            "O",
            "D 100 -1 -1 0",
            "V 3",
            "D 101 -1 -1 0",
            "V 7",
            "D 102 -1 -1 0",
            "V 7",
            "D 10000 -1 -1 0",
            "V 7",
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
        工具 = 构 / "item-magic-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        头 = 构 / "item-magic-shim/SDL3/SDL_timer.h"
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
                str(Path(__file__).with_name("item_magic_oracle.cpp")),
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
                "direct original magic house and Panel20 FLC/mask, real assets, "
                "actual GameSession category/effect responses and explicit gallery movie states, "
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
                    "item_magic_screen.py",
                    "item_service_types.py",
                    "item_choice_screens.py",
                    "item_shop_screen.py",
                    "item_targets.py",
                    "item_paint.py",
                    "item_screen_types.py",
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
            commands = 自._命令()
            if arg_预检:
                commands = cls._预检命令()
            for i, 行 in enumerate(commands):
                报["last_command"], 报["last_index"] = 行, i
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "F") else b""
                if 行[:1] in ("D", "F") and len(cpp) != 614400:
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
                raise ValueError("参考魔法界面故障：" + 错)
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
    魔法界面差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.smoke
    )
