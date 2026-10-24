# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
import zlib
from array import array
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.endgame_screen import 结局屏幕_类
from rich4.endgame_types import 结局动作_类, 过关资料_类
from rich4.flc import 动画_类
from rich4.graphics import 图像_类
from rich4.intro_player import 开局演出_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.screen_draw import 屏幕宿主_类


# ◕ 功能
class 开结局差分_类:
    """
    直接原开局与结局、真实电影/画布、全部私有状态和声音/动作请求。

    更新日志：
    2026.10.24 - 不触发规则或伪造胜负，正式游戏入口接线另验。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        self.开, self.结 = 开局演出_类(self.美术), 结局屏幕_类()
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[tuple[int, int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append((0, n)))
        self.动作 = 结局动作_类(
            lambda: self.调用.append((1, 0)),
            lambda ok: self.调用.append((2, int(ok))),
            lambda m: self.调用.append((3, m)),
            lambda: self.调用.append((4, 0)),
        )
        self.预检: dict[str, list[int]] = {}
        for lib, n in [("j", n) for n in range(46, 71)] + [("d", 556)]:
            d = 动画_类(self.美术.api_解码(lib, n))
            while d.api_下一帧():
                pass
            if not d.帧数 or d.已解帧 != d.帧数:
                raise ValueError("开局/倒闭电影未完整解码")
            self.预检[f"{lib}:{n}"] = [d.帧数, d.间隔毫秒, d.宽, d.高]

    @staticmethod
    def _字节(arg_像素: list[int]) -> bytes:
        raw = array("H", arg_像素)
        if byteorder != "little":
            raw.byteswap()
        return raw.tobytes()

    @classmethod
    def _图(cls, arg_图: 图像_类) -> list[int]:
        im = arg_图
        return [
            im.宽,
            im.高,
            im.原点x,
            im.原点y,
            len(im.像素),
            zlib.crc32(cls._字节(im.像素)),
            len(im.不透明),
            zlib.crc32(im.不透明),
        ]

    @classmethod
    def _电影(cls, arg_片: 动画_类 | None) -> list[int]:
        if arg_片 is None:
            return [0]
        d = arg_片
        return [
            1,
            d.宽,
            d.高,
            d.帧数,
            d.间隔毫秒,
            d.已解帧,
            d.游标,
            zlib.crc32(d.像素索引),
            zlib.crc32(cls._字节(d.调色板)),
        ]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        f = self.框
        if op == "N":
            self.开, self.结 = 开局演出_类(self.美术), 结局屏幕_类()
            f.按钮.clear()
        elif op == "S":
            count, *chars = map(int, 列)
            if count != len(chars):
                raise ValueError("角色输入长度不符")
            self.开.api_开始(chars)
        elif op == "K":
            self.开.api_跳过()
        elif op == "O":
            self.结.api_再玩()
        elif op == "G":
            stage, m, ch, cleared, single, seed = map(int, 列)
            self.结.api_过关(过关资料_类(stage, m, ch, cleared, bool(single), seed))
        elif op == "C":
            self.结.api_关闭()
        elif op == "B":
            for _ in range(int(列[0])):
                self.结._过关步()
        elif op in ("D", "I"):
            f.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            f.按钮.clear()
            if op == "I":
                self.开.api_绘制(f.画布, int(列[0]), lambda n: self.调用.append((0, n)))
            else:
                tick, x, y, down, hold, instant = map(int, 列)
                f.时钟, f.指针x, f.指针y, f.按下, self.宿.即时 = (
                    tick,
                    x,
                    y,
                    bool(down),
                    bool(instant),
                )
                self.结.api_绘制(self.宿, bool(hold), self.动作)
        elif op == "X":
            id = int(列[0])
            for b in f.按钮:
                if b.编号 == id and b.启用:
                    action = b.动作
                    f.按钮.clear()
                    action()
                    break
            else:
                raise ValueError(f"预期结局按钮不存在：{id}")
        else:
            raise ValueError(op)
        i, s = self.开, self.结
        out = [
            -1,
            int(i.api_活跃()),
            len(i._镜头),
            i._索引,
            i._已过,
            i._间隔,
            int(i._已开始),
            int(i._已响),
            *self._电影(i._电影),
            *self._图(i._帧),
        ]
        for shot in i._镜头:
            out += [
                shot.影片,
                shot.x,
                shot.y,
                shot.起声,
                shot.帧声,
                shot.响帧,
                shot.停留毫秒,
                *self._图(shot.底图),
            ]
        out += [
            int(s._种类),
            int(s.api_活跃()),
            s.api_退出按钮(),
            s._上时,
            int(s._已开始),
            int(s._步骤),
            s._倒数毫秒,
            s._电影毫秒,
            *self._电影(s._电影),
            *self._图(s._电影帧),
        ]
        info = s._资料
        out += [
            info.阶段,
            info.地图,
            info.角色,
            info.已清,
            int(info.单人),
            info.种子,
            s._随机状态,
            s._步毫秒,
            s._滚动,
            s._跑x,
            s._跑y,
            int(s._向左),
            s._胜者帧,
            s._财神帧,
            s._面板y,
            s._面板速,
            s._已选,
            s._选余步,
            int(s._离开),
        ]
        for im in (s._底图, s._面板):
            out.append(int(im is not None))
            if im is not None:
                out += self._图(im)
        for im in s._图牌:
            out += self._图(im)
        out.append(len(f.按钮))
        for b in f.按钮:
            out += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        out.append(len(self.调用))
        for c in self.调用:
            out += c
        return " ".join(map(str, out)), self._字节(f.画布.像素) if op in ("D", "I") else b""

    def _命令(self) -> list[str]:
        groups = []
        for chars in [[n] for n in range(12)] + [[0, 3, 6, 9], [11, 8, 5, 2], [], [255, 12]]:
            groups += ["N", f"S {len(chars)} " + " ".join(map(str, chars)), "I 9999"]
            total = 400 + self.预检["j:46"][0] * (self.预检["j:46"][1] or 100)
            for ch in chars:
                for n in (47 + ch % 12, 59 + ch % 12):
                    frames, delay, _, _ = self.预检[f"j:{n}"]
                    total += frames * (delay or 100)
            groups += ["I 14"] * (total // 14 + 2) + ["I 0", "K"]
        for ch in range(12):
            groups += [
                "N",
                f"S 4 {ch} {(ch + 1) % 12} {(ch + 2) % 12} {(ch + 3) % 12}",
                "I 0",
                "I 399",
                "I 100",
                "K",
                "I 100",
                "S 0",
                "I 0",
                "K",
            ]
        groups += ["N", "O", "D 0 -1 -1 0 1 0", "D 1000 -1 -1 0 0 0"]
        groups += [f"D {1100 + k * 100} -1 -1 0 0 0" for k in range(101)]
        for instant in (0, 1):
            groups += [
                "O",
                f"D 20000 -1 -1 0 0 {instant}",
                "X 1100",
                f"D 20100 -1 -1 0 1 {instant}",
            ]
            frames, delay, _, _ = self.预检["d:556"]
            groups += [
                f"D {20200 + k * 35} -1 -1 0 0 {instant}"
                for k in range(frames * max(1, delay) // 35 + 3)
            ]
        for stage in range(2):
            for m in range(4):
                for ch in range(12):
                    cleared = 1 << m
                    groups += [
                        "N",
                        f"G {stage} {m} {ch} {cleared} 1 {ch + 1}",
                        "D 100 -1 -1 0 1 0",
                        "D 200 -1 -1 0 0 0",
                    ]
                    groups += [
                        f"D {300 + k * 100} 320 {300 + 40 * (ch % 4)} 1 0 0" for k in range(13)
                    ]
                    choice = next(i for i in range(4) if not cleared & (1 << i))
                    groups += [f"X {1101 + choice}"]
                    groups += [f"D {1600 + k * 50} -1 -1 0 0 0" for k in range(11)]
        for seed in (0, 1, 2147483647, 2147483648, 4294967295):
            groups += ["N", f"G 1 3 11 15 1 {seed}", "D 0 -1 -1 0 0 0"]
            groups += [f"D {100 + k * 100} -1 -1 0 0 0" for k in range(200)]
            groups += ["X 1105", "C"]
        for cleared in range(16):
            for single in (0, 1):
                groups += ["N", f"G 0 0 0 {cleared} {single} 42", "D 100 -1 -1 0 0 1"]
                button = (
                    1105
                    if not single or cleared == 15
                    else 1101 + next(i for i in range(4) if not cleared & (1 << i))
                )
                groups += [f"X {button}", "D 101 -1 -1 0 0 1", "C", "D 0 -1 -1 0 0 0"]
        groups += [
            "N",
            "G 0 0 0 1 1 1",
            "D 1 -1 -1 0 0 0",
            "D 0 -1 -1 0 0 0",
            "D 1 -1 -1 0 0 0",
            "D 10000 -1 -1 0 0 0",
            "D 9999 -1 -1 0 0 0",
            "B 10000",
            "D 10000 -1 -1 0 0 0",
            "C",
            "O",
            "D 10001 -1 -1 0 0 0",
        ]
        return groups

    @staticmethod
    def _预检命令() -> list[str]:
        return [
            "N",
            "S 2 0 1",
            "I 100",
            "I 100",
            "K",
            "O",
            "D 100 -1 -1 0 0 0",
            "X 1100",
            "D 200 -1 -1 0 0 0",
            "G 1 2 11 4 1 42",
            "D 300 -1 -1 0 0 1",
            "X 1101",
            "D 400 -1 -1 0 0 1",
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
        工具 = 构 / "intro-endgame-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        头 = 构 / "intro-endgame-shim/SDL3/SDL_timer.h"
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
                str(Path(__file__).with_name("intro_endgame_oracle.cpp")),
                str(arg_源码 / "tools/screens/messages.cpp"),
                str(arg_源码 / "tools/screens/draw.cpp"),
                str(构 / "librich4_core.a"),
                *链,
                "-liconv",
                "-lz",
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
                "direct original IntroPlayer and EndgameScreen, external real movies/art/font, "
                "complete private state/decoded CRC32 and full RGB555 canvas/sounds/actions; "
                "no World/GameSession mutated or supplied; "
                "not actual Application integration/desktop"
            ),
            "movies_preflight": 自.预检,
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "smoke" if arg_预检 else "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "intro_player.py",
                    "endgame_types.py",
                    "endgame_replay.py",
                    "endgame_stage.py",
                    "endgame_screen.py",
                    "screen_draw.py",
                    "flc.py",
                    "native_frame.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/intro_player.py").read_bytes()
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
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "I") else b""
                if 行[:1] in ("D", "I") and len(cpp) != 614400:
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
                raise ValueError("参考开局/结局故障：" + 错)
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
    开结局差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report, 选项.smoke)
