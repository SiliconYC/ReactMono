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
from rich4.game_types import 游戏事件_类, 游戏事件种类_类
from rich4.graphics import 图像_类
from rich4.item_screen_types import 卡图等待_类, 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 物品库存差分_类:
    """
    原库存/卡图画布与真实GameSession动作的测试宿主。

    更新日志：
    2026.10.24 - 对照完整DAT、会话阶段/随机/决策及UI私有状态，不冒充正式应用。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        self.屏 = 物品屏幕_类()
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[list[int]] = []
        self.通知: list[str] = []
        self.屏.声音 = lambda n: self.调用.append([0, n])
        self.屏.语音 = lambda n, q: self.调用.append([1, n, int(q)])
        self.宿 = 物品宿主_类(lambda: self.调用.append([2]), self._通知, self._回答)
        self._图摘: dict[int, list[int]] = {}

    def _通知(self, arg_好: bool, arg_文: str) -> None:
        self.调用.append([3, int(arg_好)])
        self.通知.append(arg_文)

    def _回答(self, arg_i: int) -> bool:
        ok = self.会.api_回答(arg_i)
        self.调用.append([4, arg_i, int(ok)])
        return ok

    @staticmethod
    def _散列(arg_数: bytes) -> int:
        h = 14695981039346656037
        for b in arg_数:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return h

    @classmethod
    def _串(cls, arg_文: str) -> list[int]:
        raw = arg_文.encode()
        return [len(raw), cls._散列(raw)]

    @staticmethod
    def _字节(arg_图: 图像_类) -> bytes:
        raw = array("H", arg_图.像素)
        if byteorder != "little":
            raw.byteswap()
        return raw.tobytes()

    def _图片(self, arg_图: 图像_类) -> list[int]:
        key = id(arg_图)
        if key not in self._图摘:
            self._图摘[key] = [
                arg_图.宽,
                arg_图.高,
                arg_图.原点x,
                arg_图.原点y,
                len(arg_图.像素),
                self._散列(self._字节(arg_图)),
            ]
        return self._图摘[key]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        self.通知.clear()
        框, 屏 = self.框, self.屏
        old = self.会.世界.api_导出() if op in ("D", "P") else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色, p.控制 = (ch + 3 * i) % 12, 1
            self.会 = 游戏会话_类(世界_类.api_从地图(self.美术.api_解码("m", 2 * m + 1), opt), 1)
            屏.api_重置()
            框.按钮.clear()
        elif op == "W":
            profile, vehicle = map(int, 列)
            p = self.会._玩家()
            p.卡片, p.道具, p.交通, p.骰数 = [0] * 15, [0] * 15, vehicle, 1 + (vehicle & 3)
            if profile:
                p.卡片 = [1 + j + (15 if profile == 2 else 0) for j in range(15)]
                p.道具[:13] = [1 + j % 9 for j in range(13)]
            if profile == 3:
                p.卡片 = [0, 1, 14, 14, 18, 30, 31, 0, 20, 2, 255, 15, 0, 9, 8]
        elif op == "H":
            slot, flags = map(int, 列)
            self.会.世界.玩家[slot].记录.控制标志 = flags
        elif op == "O":
            slot, card = map(int, 列)
            屏.api_观察(游戏事件_类(游戏事件种类_类(0), slot, 卡片=card), self.会.世界)
        elif op == "G":
            card, callback = map(int, 列)
            屏._弹图.append(
                卡图等待_类(card, 0, (lambda: self.调用.append([5])) if callback else None)
            )
        elif op == "C":
            t = int(列[0])
            屏.时钟 = t if t >= 0 else None
        elif op == "U":
            屏.api_运行延迟()
        elif op == "R":
            屏.api_重置()
            框.按钮.clear()
        elif op in ("D", "P"):
            values = list(map(int, 列))
            cards = bool(values.pop(0)) if op == "D" else False
            t, x, y, down = values
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            屏.截图名 = ""
            if op == "D":
                屏.api_画库存(框, self.会, cards, self.宿)
            else:
                屏.api_画卡图(框)
        elif op == "X":
            id = int(列[0])
            for b in 框.按钮:
                if b.编号 == id and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
            else:
                raise ValueError(f"预期物品按钮不存在：{id}")
        else:
            raise ValueError(op)
        dat = self.会.世界.api_导出()
        if old is not None and old != dat:
            raise ValueError("绘制改变World DAT")
        d = self.会.待决策
        数 = [-1, int(self.会.阶段), self.会.随机.状态, int(d is not None)]
        if d is not None:
            数 += [int(d.种类), d.玩家, d.地产, d.金额, *self._串(d.提示), len(d.选项)]
            for o in d.选项:
                数 += [*self._串(o.标签), o.值, int(o.位置 is not None)]
                if o.位置 is not None:
                    数 += [o.位置.x, o.位置.y]
                数 += [int(o.对象 is not None)]
                if o.对象 is not None:
                    数 += [int(o.对象.种类), o.对象.数值]
            数 += [d.金额上限, d.不活跃玩家, int(d.被抢玩家 is not None)]
            if d.被抢玩家 is not None:
                数.append(d.被抢玩家)
        数 += [len(屏._弹图)]
        for q in 屏._弹图:
            数 += [q.卡片, q.截止, int(q.之后 is not None)]
        数 += [len(屏._延迟), int(屏._按住 is not None)]
        if 屏._按住:
            q = 屏._按住
            数 += [*self._串(q.所有者), *q.区域, int(q.动作 is not None), q.物品]
        数 += [屏._上卡, 屏._上道具, *self._串(屏._已说), int(屏.时钟 is not None)]
        if 屏.时钟 is not None:
            数.append(屏.时钟)
        数 += [*self._串(屏.截图名), len(屏._说明表)]
        for (card, id), text in sorted(屏._说明表.items()):
            数 += [int(card), id, *self._串(text)]
        数 += [len(屏._卡图表)]
        for id, image in sorted(屏._卡图表.items()):
            数 += [id, *self._图片(image)]
        数 += [len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += [len(c), *c]
        数 += [len(self.通知)]
        for text in self.通知:
            数 += self._串(text)
        数 += [len(dat)]
        return " ".join(map(str, 数)), self._字节(框.画布) if op in ("D", "P") else b"", dat

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        for m in range(8):
            for profile in range(4):
                for vehicle in range(4):
                    组 += [
                        f"N {m} {m + profile}",
                        f"W {profile} {vehicle}",
                        "D 1 100 -1 -1 0",
                        "D 0 101 -1 -1 0",
                    ]
        for card in range(1, 31):
            tile = (card - 1) % 15
            x, y = 30 + 80 * (tile % 5), 150 + 56 * (tile // 5)
            组 += [
                f"N {card % 8} {card % 12}",
                f"W {1 if card <= 15 else 2} 0",
                f"D 1 1 {x} {y} 1",
                f"X {300 + card}",
                f"D 1 2 {x} {y} 1",
                f"D 1 3 {x} {y} 0",
                "U",
                "P 4 -1 -1 0",
            ]
            组 += ["X 360"] if card % 2 == 0 else ["P 1503 -1 -1 0", "P 1504 -1 -1 0", "U"]
        for tool in range(1, 14):
            for vehicle in (0, 1, 2):
                tile = tool - 1
                x, y = 30 + 80 * (tile % 5), 150 + 56 * (tile // 5)
                组 += [
                    f"N {tool % 8} {tool % 12}",
                    f"W 1 {vehicle}",
                    f"D 0 10 {x} {y} 1",
                    f"X {300 + tool}",
                    f"D 0 11 {x} {y} 1",
                    f"D 0 12 {x} {y} 0",
                    "U",
                ]
        for card in range(1, 31):
            组 += ["N 0 0", f"G {card} 1", "P 10 -1 -1 0", "P 1509 -1 -1 0", "P 1510 -1 -1 0", "U"]
        for vehicle in (1, 2):
            for profile in (0, 1):
                组 += [
                    "N 0 0",
                    f"W {profile} {vehicle}",
                    "D 0 10 360 260 1",
                    "X 340",
                    "D 0 11 360 260 1",
                    "D 0 12 360 260 0",
                    "U",
                ]
        for flags in (0, 1, 2, 5):
            组 += ["N 0 0", f"H 0 {flags}"]
            for card in range(32):
                组 += [f"O 0 {card}"]
            组 += ["O 99 1", "R"]
        组 += [
            "N 0 0",
            "W 1 1",
            "D 1 10 30 150 1",
            "X 301",
            "D 1 11 30 150 1",
            "D 1 12 500 150 0",
            "U",
            "D 1 13 30 150 1",
            "X 301",
            "D 0 14 30 150 0",
            "U",
            "C 0",
            "G 1 1",
            "P 9999 -1 -1 0",
            "C 1499",
            "P 9999 -1 -1 0",
            "C 1500",
            "P 9999 -1 -1 0",
            "U",
            "C -1",
            "R",
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
        工具 = 构 / "item-inventory-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        头 = 构 / "item-inventory-shim/SDL3/SDL_timer.h"
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
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("item_inventory_oracle.cpp")),
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
                "direct original inventory/card popups, real maps and assets, "
                "actual GameSession item actions, phase/RNG/pending decision "
                "and complete World DAT, "
                "real sprites, internal state and callbacks; "
                "not actual window or full Application integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "item_screens.py",
                    "item_shop_screen.py",
                    "item_service_types.py",
                    "item_choice_screens.py",
                    "item_targets.py",
                    "item_paint.py",
                    "item_screen_types.py",
                    "native_frame.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/item_screens.py").read_bytes()
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
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "P") else b""
                if 行[:1] in ("D", "P") and len(cpp) != 614400:
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
                raise ValueError("参考物品界面故障：" + 错)
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
    选项 = 参数.parse_args()
    物品库存差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
