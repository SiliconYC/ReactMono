# ◑ 导入
import argparse
import hashlib
import json
import random
import struct
import subprocess
from collections import Counter
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.minigames import 企鹅_类, 图框_类, 天降_类, 小游戏_类, 小游戏阶段_类, 气球_类
from rich4.numeric import 数值范围错误_类
from rich4.random import 随机数_类


# ◕ 功能
class 小游戏差分_类:
    """
    只用真实输入驱动原小游戏，逐命令比较全部公开状态、场景及声音。

    更新日志：
    2026.10.23 - 外部Panel人物帧框只用于本机测试；公开报告仅数值/哈希。
    """

    @staticmethod
    def _动作(arg_戏: 小游戏_类 | None, arg_行: str) -> tuple[小游戏_类, str]:
        op, *列 = arg_行.split()
        n = list(map(int, 列))
        状态, 值 = 0, 0
        try:
            if op == "n":
                if n[0] == 0:
                    arg_戏 = 企鹅_类(n[1])
                elif n[0] == 1:
                    arg_戏 = 气球_类(n[1])
                else:
                    框 = [图框_类(*n[5 + i * 4 : 9 + i * 4]) for i in range(n[4])]
                    arg_戏 = 天降_类(n[1], n[2], 框, n[3])
            elif op == "t":
                arg_戏.api_帧()
            elif op == "b":
                arg_戏.api_开始()
            elif op == "p":
                if isinstance(arg_戏, 天降_类):
                    arg_戏.api_目标(n[0])
                else:
                    值 = int(arg_戏.api_点击(n[0], n[1]))
            elif op == "a":
                if isinstance(arg_戏, 企鹅_类):
                    arg_戏.api_任意点击()
            elif op == "d":
                值 = 天降_类.api_漂移(n[0])
            elif op == "v":
                值 = int(企鹅_类.api_有效(n[0], n[1]))
            else:
                raise RuntimeError("未知小游戏差分命令")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        if arg_戏 is None:
            raise ValueError("测试未先建立有效小游戏")
        戏 = arg_戏
        类 = 0 if isinstance(戏, 企鹅_类) else 1 if isinstance(戏, 气球_类) else 2
        数 = [状态, 值, 类, int(戏.阶段), 戏.随机.次数, 戏.随机.随机.状态, 戏.剩余帧]
        if isinstance(戏, 企鹅_类):
            数 += [戏.api_得分(), *戏.位置, int(戏.空闲), int(戏.分数显示), *戏.发现, len(戏.洞)]
            数 += [v for 对 in 戏.洞 for v in 对]
            数 += [v for 行 in 戏.格子 for 格 in 行 for v in (格.x, 格.y, 格.标志)]
        elif isinstance(戏, 气球_类):
            数 += [戏.api_得分(), 戏.冻结, 戏.变速]
            数 += [v for 槽 in 戏.槽 for v in (槽.x, 槽.y, 槽.种类)]
        elif isinstance(戏, 天降_类):
            数 += [戏.api_得分(), 戏.接者x, 戏.财神x, *戏.接到, int(戏.爆炸)]
            if 戏.爆炸:
                数 += [戏.爆x, 戏.爆龄]
            数 += [v for 槽 in 戏.槽 for v in (槽.x, 槽.y, 槽.位, 槽.vy)]
        数 += [len(戏.场景)]
        数 += [v for 精 in 戏.场景 for v in (ord(精.库), 精.条目, 精.帧, 精.x, 精.y, 精.缩放)]
        声 = 戏.api_取声音()
        数 += [len(声)] + [v for 项 in 声 for v in (项.操作, 项.音效)]
        return 戏, " ".join(map(str, 数))

    @classmethod
    def _一局(
        cls,
        arg_令: str,
        arg_策略: int,
        arg_工具: Path,
        arg_生: random.Random,
        arg_目标: tuple[int, int] | None = None,
    ) -> dict:
        令, 预, 阶段, 戏, 弹种, 问号 = [], [], Counter(), None, Counter(), Counter()
        爆炸, 爆前 = 0, False

        def 执行(arg_行: str) -> None:
            nonlocal 戏, 爆炸, 爆前
            前槽 = [(槽.x, 槽.y, 槽.种类) for 槽 in 戏.槽] if isinstance(戏, 气球_类) else []
            观察随 = 随机数_类(戏.随机.随机.状态) if isinstance(戏, 气球_类) else None
            戏, 文 = cls._动作(戏, arg_行)
            if arg_行.startswith("p ") and isinstance(戏, 气球_类):
                for 前, 后 in zip(前槽, 戏.槽):
                    if 前[0] and not 前[2] & 0xF0 and 后.种类 == 0x3C:
                        弹种[str(前[2])] += 1
                        if 前[2] == 11:
                            问号[str(观察随.api_下一个() % 6)] += 1
            if isinstance(戏, 天降_类):
                if 戏.爆炸 and not 爆前:
                    爆炸 += 1
                爆前 = 戏.爆炸
            令.append(arg_行)
            预.append(文)
            阶段[str(int(戏.阶段))] += 1

        执行(arg_令)
        if isinstance(戏, 企鹅_类):
            候 = [
                (x, y)
                for y, 行 in enumerate(戏.格子)
                for x, 格 in enumerate(行)
                if 格.标志 & 15 > 1
            ]
            炸 = next(
                (x, y)
                for y, 行 in enumerate(戏.格子)
                for x, 格 in enumerate(行)
                if 格.标志 & 15 == 1 and (x, y) != (2, 6)
            )
        for i in range(1200):
            if 戏.阶段 == 小游戏阶段_类.完成:
                break
            if 戏.阶段 == 小游戏阶段_类.准备:
                for _ in range(arg_生.randrange(1, 5)):
                    执行("t")
                执行("b")
            if isinstance(戏, 企鹅_类):
                if 戏.空闲:
                    if arg_目标 is not None:
                        if i < 15:
                            执行(f"p {arg_目标[0]} {arg_目标[1]}")
                    elif arg_策略 == 0 and 候:
                        x, y = 候.pop(0)
                        执行(f"p {x} {y}")
                    elif arg_策略 == 1:
                        执行(f"p {炸[0]} {炸[1]}")
                    elif arg_策略 == 2:
                        执行(f"p {arg_生.randrange(-1, 10)} {arg_生.randrange(-1, 10)}")
                if 戏.阶段 == 小游戏阶段_类.结算 and arg_策略 == 1:
                    执行("a")
            elif isinstance(戏, 气球_类):
                if arg_策略 == 0:
                    点 = [
                        (槽.x, 槽.y) for 槽 in 戏.槽 if 槽.x and not 槽.种类 & 0xF0 and 槽.y < 380
                    ]
                    for x, y in 点:
                        执行(f"p {x} {y}")
                elif arg_策略 == 1 and i % 3 == 0:
                    执行(f"p {arg_生.randrange(-50, 690)} {arg_生.randrange(-50, 440)}")
            elif isinstance(戏, 天降_类):
                if arg_策略 in (0, 1):
                    候槽 = [
                        槽
                        for 槽 in 戏.槽
                        if 槽.x and ((槽.位 & 15) == 4 if arg_策略 == 1 else (槽.位 & 15) != 4)
                    ]
                    if 候槽:
                        执行(f"p {max(候槽, key=lambda 槽: 槽.y).x} 0")
                else:
                    执行(f"p {100 if i % 80 < 40 else 540} 0")
            执行("t")
        if 戏.阶段 != 小游戏阶段_类.完成:
            raise ValueError("小游戏未在真实输入下结束")
        for _ in range(3):
            执行("t")
            执行("b")
        for x in (-1000000, -1000, 0, 110, 278, 320, 362, 530, 1000, 1000000):
            执行(f"d {x}")
        for x, y in ((-1, 0), (0, -1), (4, 4), (2, 6), (8, 8), (9, 9)):
            执行(f"v {x} {y}")
        if isinstance(戏, 天降_类):
            执行("n 2 1 0 19 0")
        cp = subprocess.run(
            [str(arg_工具)], input="\n".join(令) + "\n", text=True, capture_output=True, check=True
        )
        实 = cp.stdout.splitlines()
        if len(实) != len(预):
            raise ValueError("小游戏oracle行数不同")
        for i, (c, p) in enumerate(zip(实, 预)):
            if c != p:
                位置 = (
                    next(j for j, (a, b) in enumerate(zip(c.split(), p.split())) if a != b)
                    if len(c.split()) == len(p.split())
                    else -1
                )
                raise ValueError(
                    f"{arg_令}/策略{arg_策略}/目标{arg_目标}/步{i}/{令[i]} "
                    f"不同字段{位置}: C++={c} Python={p}"
                )
        return {
            "constructor_sha256": hashlib.sha256(arg_令.encode()).hexdigest(),
            "game": int(预[0].split()[2]),
            "seed": int(arg_令.split()[2]),
            "strategy": arg_策略,
            "initial_target": arg_目标,
            "commands": len(令),
            "operations": dict(Counter(s.split()[0] for s in 令)),
            "statuses": dict(Counter(s.split()[0] for s in 预)),
            "stages": dict(阶段),
            "score": 戏.api_得分(),
            "draws": 戏.随机.次数,
            "balloon_popped_kinds": dict(弹种),
            "balloon_question_effects": dict(问号),
            "caught_bombs": 爆炸,
            "found": 戏.发现
            if isinstance(戏, 企鹅_类)
            else 戏.接到
            if isinstance(戏, 天降_类)
            else [],
            "input_sha256": hashlib.sha256("\n".join(令).encode()).hexdigest(),
            "output_sha256": hashlib.sha256("\n".join(预).encode()).hexdigest(),
        }

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_报告: Path) -> None:
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
        工具 = arg_构建.resolve() / "minigames-oracle"
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("minigames_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
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
            "generator_seed": 2026102315,
            "status": "running",
            "scope": (
                "real mini-game input timelines, public state, draw order, cues and RNG; "
                "no full-game or pixel acceptance"
            ),
            "episodes": [],
        }
        生 = random.Random(报告["generator_seed"])
        try:
            局 = []
            for y in range(9):
                for x in range(9):
                    if 企鹅_类.api_有效(x, y):
                        局.append(("n 0 3", 3, (x, y)))
            for 种 in (0, 1, 2, 5, 42, 99, 0x7FFFFFFF, 0xFFFFFFFF, 0xDEADBEEF):
                for 策 in range(4):
                    局.append((f"n 0 {种}", 策, None))
            for 种 in range(32):
                for 策 in range(3):
                    局.append((f"n 1 {种}", 策, None))
            包 = 资源包_类(arg_素材 / "panel.mkf")
            for 角 in range(12):
                数据 = 包.api_解码(100 + 角)
                数 = struct.unpack_from("<I", 数据, 4)[0]
                框 = [struct.unpack_from("<hhhh", 数据, 12 + i * 12) for i in range(数)]
                if 数据[:4] not in (b"SPR\0", b"SMP\0") or 数 < 5:
                    raise ValueError("外部人物精灵帧框不符")
                后 = " ".join(str(v) for 组 in 框 for v in 组)
                for 种 in (0, 77, 0xFFFFFFFF):
                    for 策 in range(3):
                        局.append((f"n 2 {种} {角} {1 if 策 == 1 else 19} {数} {后}", 策, None))
            for i, (令, 策, 目标) in enumerate(局):
                组 = cls._一局(令, 策, 工具, 生, 目标)
                报告["episodes"].append(组)
                if i % 16 == 0:
                    print(
                        f"episode={i + 1}/{len(局)} game={组['game']} score={组['score']} matched",
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
                    "commands": sum(e["commands"] for e in 报告["episodes"]),
                }
            )
        )


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    小游戏差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
