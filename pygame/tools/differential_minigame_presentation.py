# ◑ 导入
import argparse
import hashlib
import json
import random
import shlex
import subprocess
import tempfile
from array import array
from collections import Counter
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.minigame_presentation import 小游戏演出_类
from rich4.minigames import 企鹅_类, 天降_类, 小游戏种类_类, 小游戏阶段_类, 气球_类


# ◕ 功能
class 小游戏画面差分_类:
    """
    直接调用固定原生MiniGames屏幕，对照真实像素/输入/时钟/声音/结果。

    更新日志：
    2026.10.23 - 无SDL或隐藏运行后端，所有商业像素只留临时目录。
    """

    @staticmethod
    def _像素(arg_画) -> bytes:
        色 = array("H", arg_画.像素)
        if byteorder != "little":
            色.byteswap()
        return 色.tobytes()

    @classmethod
    def _一局(
        cls,
        arg_美术: 美术_类,
        arg_工具: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_类: int,
        arg_种: int,
        arg_角: int,
        arg_自动: bool,
        arg_生: random.Random,
    ) -> dict:
        声, 命令, 预, 快照 = [], [], [], []
        演 = 小游戏演出_类(arg_美术, 小游戏种类_类(arg_类), arg_种, arg_角, 声.append, arg_自动)
        阶段, 上次阶段, 准备帧, 爆帧, 结果 = Counter(), -1, -1, -1, None

        def 记录(arg_行: str, arg_果=None) -> None:
            数 = [int(arg_果 is not None)]
            if arg_果:
                数 += [arg_果.分数, arg_果.随机次数]
            数 += [len(声)] + [v for s in 声 for v in (s.操作, s.音效)]
            声.clear()
            命令.append(arg_行)
            预.append(" ".join(map(str, 数)))

        记录(f"n {arg_类} {arg_种} {arg_角} {int(arg_自动)}")
        for i in range(1800):
            dt = (0, 16, 50, 100, 17, 114, 33)[i % 7]
            px, down = (-1, 0) if arg_自动 else (100 if i % 80 < 40 else 540, 1)
            画, 果 = 演.api_帧(dt, px, bool(down))
            记录(f"t {dt} {px} {down}", 果)
            if 果:
                结果 = 果
            状 = int(演.逻辑.阶段)
            阶段[str(状)] += 1
            准备 = 演.准备片.已解帧 if 演.准备片 else -1
            爆 = 演.爆帧
            if i % 7 == 0 or 状 != 上次阶段 or 准备 != 准备帧 or 爆 != 爆帧:
                快照.append(cls._像素(画))
                记录(f"s {len(快照) - 1}")
            上次阶段, 准备帧, 爆帧 = 状, 准备, 爆
            if not arg_自动:
                点 = None
                戏 = 演.逻辑
                if isinstance(戏, 企鹅_类) and 戏.空闲:
                    候 = [(格.x, 格.y - 8) for 行 in 戏.格子 for 格 in 行 if 格.标志 & 15 > 1]
                    if 候:
                        点 = 候[0]
                elif isinstance(戏, 气球_类) and i % 3 == 0:
                    候 = [(槽.x, 槽.y) for 槽 in 戏.槽 if 槽.x and not 槽.种类 & 0xF0]
                    点 = 候[0] if 候 else (arg_生.randrange(640), arg_生.randrange(480))
                elif isinstance(戏, 天降_类) and i % 17 == 0:
                    点 = (arg_生.randrange(640), arg_生.randrange(480))
                if 点:
                    演.api_点击(*点)
                    记录(f"p {点[0]} {点[1]}")
            if 演.逻辑.阶段 == 小游戏阶段_类.完成:
                break
        if 结果 is None:
            raise ValueError("原屏幕时间线未完成")
        for _ in range(2):
            _, 果 = 演.api_帧(100)
            记录("t 100 -1 0", 果)
        with tempfile.TemporaryDirectory(prefix="rich4-mini-pixels-") as 临:
            路 = Path(临)
            cp = subprocess.run(
                [str(arg_工具), str(arg_素材), str(arg_字体), str(路)],
                input="\n".join(命令) + "\n",
                text=True,
                capture_output=True,
                check=True,
            )
            实 = cp.stdout.splitlines()
            if 实 != 预:
                i = (
                    next(i for i, (c, p) in enumerate(zip(实, 预)) if c != p)
                    if len(实) == len(预)
                    else -1
                )
                raise ValueError(
                    f"屏幕结果/声音不同，命令{i}: {命令[i] if i >= 0 else '行数'} / "
                    f"{实[i] if i >= 0 else len(实)} / {预[i] if i >= 0 else len(预)}"
                )
            for i, 像素 in enumerate(快照):
                c = (路 / f"{i}.bin").read_bytes()
                if c != 像素:
                    位 = next(j for j, (a, b) in enumerate(zip(c, 像素)) if a != b)
                    raise ValueError(
                        f"种类{arg_类}/种子{arg_种}/人物{arg_角}/自动{arg_自动}/快照{i}，"
                        f"首像素{位 // 2 % 640},{位 // 2 // 640}不同"
                    )
        摘 = hashlib.sha256()
        for 图 in 快照:
            摘.update(图)
        return {
            "game": arg_类,
            "seed": arg_种,
            "character": arg_角,
            "bot": arg_自动,
            "commands": len(命令),
            "operations": dict(Counter(s.split()[0] for s in 命令)),
            "snapshots": len(快照),
            "stages": dict(阶段),
            "score": 结果.分数,
            "draws": 结果.随机次数,
            "pixels_sha256": 摘.hexdigest(),
            "input_sha256": hashlib.sha256("\n".join(命令).encode()).hexdigest(),
            "output_sha256": hashlib.sha256("\n".join(预).encode()).hexdigest(),
        }

    @classmethod
    def api_执行(
        cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_字体: Path, arg_报告: Path
    ) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "cmake",
                "-S",
                str(arg_源码),
                "-B",
                str(arg_构建),
                "-DRICH4_BUILD_GAME=OFF",
                "-DRICH4_BUILD_VIEWER=OFF",
                "-DBUILD_TESTING=OFF",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["cmake", "--build", str(arg_构建), "--target", "rich4_core", "--parallel", "6"],
            check=True,
            capture_output=True,
        )
        工具 = arg_构建.resolve() / "minigame-presentation-oracle"
        标志 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("minigame_presentation_oracle.cpp")),
                str(arg_源码 / "tools/screens/minigames.cpp"),
                str(arg_源码 / "tools/screens/draw.cpp"),
                str(arg_构建 / "librich4_core.a"),
                *标志,
                "-liconv",
                "-o",
                str(工具),
            ],
            text=True,
            capture_output=True,
        )
        if 编.returncode:
            raise RuntimeError(编.stderr)
        报告 = {
            "reference": 版本,
            "generator_seed": 2026102316,
            "scope": (
                "original native mini-game screen, selected full RGB555 canvases, "
                "audio requests and real input timelines; no audible or desktop acceptance"
            ),
            "status": "running",
            "episodes": [],
        }
        try:
            美术 = 美术_类(arg_素材)
            生 = random.Random(报告["generator_seed"])
            局 = [
                (类, 种, 角, 自)
                for 类 in range(3)
                for 种 in (42, 77)
                for 角 in ((0, 7, 11) if 类 == 2 else (0,))
                for 自 in (False, True)
            ]
            for 类, 种, 角, 自 in 局:
                组 = cls._一局(美术, 工具, arg_素材, arg_字体, 类, 种, 角, 自, 生)
                报告["episodes"].append(组)
                print(
                    f"game={类} seed={种} character={角} bot={自} "
                    f"snapshots={组['snapshots']} matched",
                    flush=True,
                )
            报告["status"] = "passed"
        except Exception as 错:
            报告["status"], 报告["failure"] = "failed", str(错)
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "status": 报告["status"],
                    "episodes": len(报告["episodes"]),
                    "snapshots": sum(e["snapshots"] for e in 报告["episodes"]),
                }
            )
        )


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--font", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    小游戏画面差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
