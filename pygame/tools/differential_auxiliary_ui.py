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
from rich4.board_models import 相机_类
from rich4.graphics import 图像_类
from rich4.help_screen import 帮助屏幕_类
from rich4.help_topics import 帮助目录_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.tile_popup import 地图弹框_类, 地图提示_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 辅助屏幕差分_类:
    """
    固定原帮助与地图提示直接组件、真实外部资源和完整世界只读对照。

    更新日志：
    2026.10.24 - 显式属性/人物/物件展示夹具，不冒充自然事件或桌面操作。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        self.屏 = 帮助屏幕_类()
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[int] = []
        self.宿 = 屏幕宿主_类(self.框, self.调用.append)

    @staticmethod
    def _串(arg_文: str) -> list[int]:
        raw, h = arg_文.encode(), 14695981039346656037
        for b in raw:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(raw), h]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        f, s = self.框, self.屏
        result, lines = -1, []
        old = self.世.api_导出() if op not in ("N", "V") else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色, p.控制 = (ch + 3 * i) % 12, 1
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", m * 2 + 1), opt)
            self.屏 = s = 帮助屏幕_类()
            f.按钮.clear()
        elif op == "V":
            seed = int(列[0])
            w = self.世
            w.头.物价 = 1 + seed % 5
            for i, d in enumerate(w.地产[1:], 1):
                d.经济.业主, d.经济.连锁, d.经济.等级 = (
                    (i + seed) % 6,
                    int((i + seed) % 3 == 0),
                    (i + seed) % 6,
                )
            for i, d in enumerate(w.设施[1:], 1):
                d.业主, d.类型, d.等级 = (i + seed) % 6, (i + seed) % 6, (i + seed) % 6
            for i, d in enumerate(w.公司[1:], 1):
                d.业主, d.剩余股份 = (i + seed) % 6, seed * 127 + i
            n = w.节点[1 + seed % (len(w.节点) - 1)]
            for i, p in enumerate(w.玩家):
                p.记录.x, p.记录.y = (n.x + 8 * i) & 65535, (n.y + 4 * i) & 65535
                p.记录.控制标志, p.状态.消失天数 = int(i != 3), int(i == 2)
            for i, a in enumerate(w.特殊角色[:4]):
                a.x, a.y, a.节点, a.不活跃状态 = (
                    (n.x + 6 * i) & 65535,
                    (n.y + 3 * i) & 65535,
                    n.编号,
                    int(i == 2),
                )
            for i, o in enumerate(w.物件):
                o.种类, o.节点, o.附身玩家 = (
                    1 + (i + seed) % 20,
                    1 + (i + seed) % (len(w.节点) - 1) if i % 5 else 0,
                    int(i % 7 == 0),
                )
        elif op == "O":
            s.api_打开(*map(int, 列))
        elif op == "A":
            s._选择(self.美术, *map(int, 列))
        elif op == "J":
            s._滚动(int(列[0]))
        elif op == "C":
            s.api_关闭()
        elif op == "E":
            s.api_取消(self.宿)
        elif op == "P":
            cx, cy, rot, x, y = map(int, 列)
            result = 地图提示_类.api_拾取(self.世, 相机_类((cx, cy), rot), x, y)
        elif op == "L":
            lines = 地图提示_类.api_文字(self.世, int(列[0]) & 65535)
        elif op in ("D", "T"):
            f.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            f.按钮.clear()
            if op == "D":
                t, x, y, down = map(int, 列)
                f.时钟, f.指针x, f.指针y, f.按下 = t, x, y, bool(down)
                s.api_绘制(self.宿)
            else:
                code, x, y = map(int, 列)
                lines = 地图提示_类.api_文字(self.世, code & 65535)
                地图提示_类.api_绘制(f, self.世, 地图弹框_类(x, y, code & 65535))
        elif op == "X":
            id = int(列[0])
            for b in f.按钮:
                if b.编号 == id and b.启用:
                    action = b.动作
                    f.按钮.clear()
                    action()
                    break
            else:
                raise ValueError(f"预期帮助按钮不存在：{id}")
        else:
            raise ValueError(op)
        dat = self.世.api_导出()
        if old is not None and old != dat:
            raise ValueError("辅助界面改变World DAT")
        out = [result, len(lines)]
        for dy, text in lines:
            out += [dy, *self._串(text)]
        out += [int(s._开), s._x, s._y, s._类别, s._话题, *s._首行, s._页, s._已载, len(s._页表)]
        for page in s._页表:
            out.append(len(page))
            for text in page:
                out += self._串(text)
        out.append(len(f.按钮))
        for b in f.按钮:
            out += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        out += [len(self.调用), *self.调用, len(dat)]
        raw = array("H", f.画布.像素) if op in ("D", "T") else array("H")
        if byteorder != "little":
            raw.byteswap()
        return " ".join(map(str, out)), raw.tobytes(), dat

    def _命令(self) -> list[str]:
        groups = []
        for m in range(8):
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            w = 世界_类.api_从地图(self.美术.api_解码("m", m * 2 + 1), opt)
            groups += [f"N {m} {m}"]
            for seed in range(6):
                groups += [f"V {seed}"]
                for start, count in (
                    (0, len(w.节点)),
                    (2000, len(w.地产)),
                    (4000, len(w.设施)),
                    (6000, len(w.公司)),
                    (8000, len(w.景物)),
                ):
                    for i in range(1, count):
                        groups += [f"L {start + i}"]
                    for code in (
                        start,
                        start + 1,
                        start + 2,
                        start + count - 1,
                        start + count,
                        start + 1999,
                    ):
                        for x, y in ((30, 60), (430, 60), (30, 460), (430, 460)):
                            groups += [f"T {code} {x} {y}"]
                for mask in (1, 2, 4, 8, 16, 32, 64, 128, 255):
                    groups += [f"T {32768 | mask} 220 240"]
                for i in range(47):
                    groups += [f"T {32768 | (i << 8)} 220 240"]
            for n in (w.节点[1], w.节点[len(w.节点) // 2]):
                for rot in range(8):
                    for x in range(-1, 461, 44):
                        for y in range(39, 501, 44):
                            groups += [f"P {n.x} {n.y} {rot} {x} {y}"]
        groups += ["N 0 0", "O 20 60", "D 0 -1 -1 0"]
        for cat, (_, topics, _) in enumerate(帮助目录_类.分类):
            groups += [f"X {1120 + cat}", "D 1 -1 -1 0"]
            for topic in range(len(topics)):
                check = 帮助屏幕_类()
                check._选择(self.美术, cat, topic)
                groups += [f"A {cat} {topic}", "D 2 -1 -1 0", "D 3 192 106 1", "D 4 365 112 1"]
                if len(check._页表) > 1:
                    for _ in range(len(check._页表)):
                        groups += ["X 1144", "D 20 -1 -1 0"]
                    groups += ["X 1143", "D 21 343 108 1", "X 1142", "D 22 365 108 1"]
            groups += [
                "J 1",
                "D 5 -1 -1 0",
                "J 1",
                "D 6 -1 -1 0",
                "J 1",
                "D 7 -1 -1 0",
                "J -1",
                "D 8 -1 -1 0",
            ]
        groups += [
            "O -1 -1",
            "D 9 -1 -1 0",
            "X 1122",
            "D 10 -1 -1 0",
            "X 1141",
            "D 11 -1 -1 0",
            "X 1130",
            "D 12 -1 -1 0",
            "X 1145",
            "D 13 -1 -1 0",
            "X 1146",
            "D 14 -1 -1 0",
            "E",
            "O 20 60",
            "D 15 -1 -1 0",
            "C",
        ]
        return groups

    @staticmethod
    def _预检命令() -> list[str]:
        return [
            "N 0 0",
            "V 1",
            "T 2001 220 240",
            "T 4001 430 460",
            "P 512 512 0 220 250",
            "O -1 -1",
            "D 0 -1 -1 0",
            "X 1126",
            "D 1 -1 -1 0",
            "X 1141",
            "D 2 -1 -1 0",
            "X 1132",
            "D 3 -1 -1 0",
            "E",
        ]

    @staticmethod
    def api_资源预检(arg_素材: Path, arg_报告: Path) -> None:
        art, entries = 美术_类(arg_素材), []
        for c, (_, topics, start) in enumerate(帮助目录_类.分类):
            for t in range(len(topics)):
                raw = art.api_解码("h", start + t)
                if not raw:
                    raise ValueError("空帮助条目")
                s = 帮助屏幕_类()
                s._选择(art, c, t)
                if not any(s._页表):
                    raise ValueError("帮助话题未载入正文")
                entries.append(
                    {
                        "entry": start + t,
                        "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "pages": list(map(len, s._页表)),
                    }
                )
        report = {
            "reference": "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557",
            "status": "passed",
            "scope": "read-only external help text presence/pagination preflight; no text emitted",
            "topics": len(entries),
            "pages": sum(len(e["pages"]) for e in entries),
            "lines": sum(sum(e["pages"]) for e in entries),
            "entries": entries,
        }
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: v for k, v in report.items() if k != "entries"}))

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
        工具 = 构 / "auxiliary-ui-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        头 = 构 / "auxiliary-ui-shim/SDL3/SDL_timer.h"
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
                str(Path(__file__).with_name("auxiliary_ui_oracle.cpp")),
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
                "direct original HelpScreen and tile_popup, external real maps/art/font, "
                "complete text/pages/buttons/sounds and World DAT read-only, "
                "source bounding-box picking approximation; not full Application or desktop"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "smoke" if arg_预检 else "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "tile_pick.py",
                    "tile_popup.py",
                    "help_screen.py",
                    "help_topics.py",
                    "screen_draw.py",
                    "message_overlay.py",
                    "native_frame.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/help_screen.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            commands = cls._预检命令() if arg_预检 else 自._命令()
            for i, 行 in enumerate(commands):
                报["last_command"], 报["last_index"] = 行, i
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "T") else b""
                if 行[:1] in ("D", "T") and len(cpp) != 614400:
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
                raise ValueError("参考辅助界面故障：" + 错)
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
    参数.add_argument("--resources", action="store_true")
    选项 = 参数.parse_args()
    if 选项.resources:
        辅助屏幕差分_类.api_资源预检(选项.assets, 选项.report)
    else:
        辅助屏幕差分_类.api_执行(
            选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.smoke
        )
