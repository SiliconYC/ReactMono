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
from rich4.game_types import 决策种类_类
from rich4.graphics import 图像_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_screens import 物品屏幕_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 商店界面差分_类:
    """
    原商店画布、真实访问/回应、点券/收入/货架与完整DAT对照。

    更新日志：
    2026.10.24 - 私有访问入口只用于测试，后续选择走真实公开GameSession.respond。
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
        ok = self.会.api_回答(arg_i)
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
        elif op == "W":
            points, profile, cards, tools, amount, owner = map(int, 列)
            w, p = self.会.世界, self.会._玩家()
            p.点券, p.卡片, p.道具 = points, [0] * 15, [0] * 15
            if profile:
                p.卡片 = [1 + j + (15 if profile == 2 else 0) for j in range(15)]
                p.道具[:13] = [9 if profile == 2 else 1 + j % 3 for j in range(13)]
            if profile == 3:
                p.卡片 = [1, 0, 14, 14, 18, 0, 30, 0, 20, 2, 0, 15, 0, 9, 8]
            w.卡供应[:] = [amount if cards == -1 or cards == j + 1 else 0 for j in range(30)]
            w.道具供应[:] = [amount if tools == -1 or tools == j + 1 else 0 for j in range(8)]
            for c in w.公司:
                c.业主 = owner
        elif op == "O":
            node = next(n for n in self.会.世界.节点 if n.标志 & 255 == 15)
            self.会._开商店(node.类型索引)
            if self.会.待决策 is None or self.会.待决策.种类 != 决策种类_类.商店:
                raise ValueError("未到达实际商店决策")
        elif op == "S":
            result = int(屏.api_商店显示选项(int(列[0])))
        elif op == "C":
            t = int(列[0])
            屏.时钟 = t if t >= 0 else None
        elif op == "U":
            屏.api_运行延迟()
        elif op == "R":
            屏.api_重置()
            框.按钮.clear()
        elif op == "F":
            屏.api_结束访问()
            框.按钮.clear()
        elif op == "D":
            t, x, y, down = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            屏.截图名 = ""
            if self.会.待决策 is None or self.会.待决策.种类 != 决策种类_类.商店:
                raise ValueError("绘制时没有实际商店决策")
            屏.api_画商店(框, self.会, self.会.待决策, self.宿)
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
                raise ValueError(f"预期商店按钮不存在：{id}")
        else:
            raise ValueError(op)
        dat = self.会.世界.api_导出()
        if old is not None and (old != dat or old_rng != self.会.随机.状态):
            raise ValueError("商店绘制改变World/RNG")
        d, core = self.会.待决策, self.会.商店
        数 = [result, int(self.会.阶段), self.会.随机.状态, int(d is not None)]
        if d is not None:
            数 += [int(d.种类), len(d.选项)]
            for o in d.选项:
                数 += [*self._串(o.标签), o.值]
        数.append(int(core is not None))
        if core is not None:
            数 += [
                len(core.卡片),
                *core.卡片,
                len(core.道具),
                *core.道具,
                core.收入,
                core.赠卡,
                core.赠道具,
                int(core.已关闭),
            ]
        数.append(self.会.商店地产)
        s = 屏._店
        数 += [
            int(s.活跃),
            s.模式,
            len(s.卡片),
            *s.卡片,
            len(s.道具),
            *s.道具,
            len(s.卡已买),
            *map(int, s.卡已买),
            len(s.道具已买),
            *map(int, s.道具已买),
            s.打开,
            s.气泡止,
            *self._串(s.气泡),
            int(s.离开中),
            s.离开时,
            s.选择类,
            s.选择行,
            s.选择值,
            int(屏.api_商店待选() is not None),
        ]
        if 屏.api_商店待选() is not None:
            数.append(屏.api_商店待选())
        数 += [len(屏._延迟), *self._串(屏._已说), int(屏.时钟 is not None)]
        if 屏.时钟 is not None:
            数.append(屏.时钟)
        数 += [*self._串(屏.截图名), len(屏._说明表)]
        for (card, id), text in sorted(屏._说明表.items()):
            数 += [int(card), id, *self._串(text)]
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
        raw = array("H", 框.画布.像素) if op == "D" else array("H")
        if byteorder != "little":
            raw.byteswap()
        return " ".join(map(str, 数)), raw.tobytes(), dat

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        # 各原地图真实商店代码、重复货架/动画/店员声音与离开入公司账。
        for m in range(8):
            组 += [f"N {m} {m}", "W 1000 0 1 1 3 0", "O"]
            for t in (
                0,
                49,
                50,
                99,
                100,
                149,
                150,
                199,
                200,
                299,
                300,
                399,
                400,
                999,
                1000,
                1999,
                2000,
                3699,
                3700,
            ):
                组 += [f"D {t} 550 40 1"]
            组 += [
                "V 101",
                "D 3800 50 90 1",
                "V 101",
                "D 3801 50 90 0",
                "X 280",
                "D 3802 550 40 1",
                "V 201",
                "D 3803 50 90 1",
                "V 201",
                "D 3804 -1 -1 0",
                "V 401",
                "D 3805 250 330 1",
                "V 401",
                "D 3806 -1 -1 0",
                "X 280",
                "D 3807 -1 -1 0",
                "V 301",
                "D 3808 250 330 1",
                "V 301",
                "D 3809 -1 -1 0",
                "V 0",
                "D 3810 -1 -1 0",
                "D 5309 -1 -1 0",
                "D 5310 -1 -1 0",
                "D 5311 -1 -1 0",
                "U",
            ]
        # 全部卡片与八可购道具；高编号道具通过真实出售流程覆盖。
        for item in range(1, 31):
            组 += [
                f"N {item % 8} {item % 12}",
                f"W 65535 0 {item} 0 3 0",
                "O",
                "D 100 -1 -1 0",
                f"V {100 + item}",
                "D 150 -1 -1 0",
                f"V {100 + item}",
                "D 200 -1 -1 0",
                "V 0",
                "D 201 -1 -1 0",
                "V 0",
            ]
        for item in range(1, 9):
            组 += [
                f"N {item % 8} {item}",
                f"W 65535 0 0 {item} 3 0",
                "O",
                "D 100 -1 -1 0",
                "X 280",
                "D 101 -1 -1 0",
                f"V {200 + item}",
                "D 102 -1 -1 0",
                f"V {200 + item}",
                "D 103 -1 -1 0",
            ]
        for profile in (1, 2):
            for item in range(1, 14):
                组 += [
                    "N 0 0",
                    f"W 0 {profile} 0 0 0 0",
                    "O",
                    "D 100 -1 -1 0",
                    "S 401",
                    "D 101 -1 -1 0",
                    f"V {400 + item}",
                    "D 102 250 330 1",
                    f"V {400 + item}",
                    "D 103 -1 -1 0",
                ]
        # 不足、满栏、货架切换/取消帮助、重放归零与主动清访问。
        for points in (0, 14, 15, 65535):
            for profile in (0, 1, 2, 3):
                组 += [
                    "N 0 0",
                    f"W {points} {profile} 1 1 3 0",
                    "O",
                    "D 100 -1 -1 0",
                    "V 101",
                    "D 101 -1 -1 0",
                    "X 280",
                    "D 102 -1 -1 0",
                    "V 201",
                    "D 103 -1 -1 0",
                    "X 281",
                    "D 104 -1 -1 0",
                    "F",
                    "D 105 -1 -1 0",
                ]
        组 += [
            "N 0 0",
            "W 1000 0 -1 -1 3 0",
            "O",
            "C 0",
            "D 9999 -1 -1 0",
            "C 50",
            "D 9999 -1 -1 0",
            "C 2000",
            "D 9999 -1 -1 0",
            "C -1",
            "R",
        ]
        return 组

    @staticmethod
    def _分支() -> list[str]:
        组 = []
        for owner in range(5):
            for profile in range(4):
                for points in (0, 65535):
                    组 += [
                        f"N {(owner + profile) % 8} {profile * 3}",
                        f"W {points} {profile} -1 -1 3 {owner}",
                        "O",
                        "D 100 -1 -1 0",
                        "X 280",
                        "D 101 -1 -1 0",
                        "V 201",
                        "D 102 -1 -1 0",
                    ]
                    组 += ["V 201"] if points and profile != 2 else ["X 281"]
                    组 += [
                        "D 103 -1 -1 0",
                        "X 280",
                        "D 104 -1 -1 0",
                        "V 0",
                        "D 105 -1 -1 0",
                        "D 1604 -1 -1 0",
                        "D 1605 -1 -1 0",
                        "U",
                    ]
        组 += [
            "N 0 0",
            "W 65535 0 1 1 3 0",
            "O",
            "D 100 -1 -1 0",
            "V 101",
            "D 101 -1 -1 0",
            "X 282",
            "D 102 -1 -1 0",
            "D 99 -1 -1 0",
            "D 0 -1 -1 0",
            "R",
            "D 18446744073709551605 -1 -1 0",
            "D 18446744073709551615 -1 -1 0",
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
        arg_预检: bool = False,
        arg_分支: bool = False,
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
        工具 = 构 / "item-shop-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        头 = 构 / "item-shop-shim/SDL3/SDL_timer.h"
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
                str(Path(__file__).with_name("item_shop_oracle.cpp")),
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
                "direct original point shop, real map shop entry and assets, "
                "actual GameSession shop entry/respond, full shop state and phase/RNG/decision "
                "and complete World DAT, "
                "real sprites, internal state and callbacks; "
                "not actual window or full Application integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "branches" if arg_分支 else "smoke" if arg_预检 else "base",
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
            if arg_分支:
                commands = cls._分支()
            if arg_预检:
                commands = commands[: commands.index("U") + 1]
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
                raise ValueError("参考商店界面故障：" + 错)
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
    参数.add_argument("--branches", action="store_true")
    选项 = 参数.parse_args()
    商店界面差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.smoke, 选项.branches
    )
