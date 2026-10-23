# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from differential_tools_ai import 道具电脑差分_类

from rich4.assets import 资源包_类
from rich4.cards import 卡片前瞻_类, 卡片回调_类, 电脑卡片记忆_类
from rich4.cards_ai import 卡片电脑_类
from rich4.events import 事件_类
from rich4.numeric import 数值范围错误_类
from rich4.random import 随机数_类
from rich4.stocks import 股市_类
from rich4.tools_ai import 道具电脑_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 卡片电脑差分_类:
    """
    原八槽入口、三十谓词及跨调用参数逐命令对照，不执行假游戏事件。

    更新日志：
    2026.10.23 - 回调、手牌及世界重置是显式测试准备，不计为自然回合。
    """

    @staticmethod
    def _扫描(arg_世: 世界_类, arg_模式: int) -> list[int]:
        表 = [0x8000 | (1 << i) for i in range(8)]
        表 += [0x8000 | (i << 8) for i in range(1, len(arg_世.物件) + 1)]
        表 += [2000 + i for i in range(1, len(arg_世.地产))]
        表 += [4000 + i for i in range(1, len(arg_世.设施))]
        return (
            list(reversed(表))
            if arg_模式 == 2
            else []
            if arg_模式 == 3
            else [0x8106, 0x8002, 0x8106, 2001, 2001, 2002, 2003, 4001]
            if arg_模式 == 4
            else [0x8100]
            if arg_模式 == 5
            else [2001] * 260 + [2002]
            if arg_模式 == 6
            else 表
        )

    @classmethod
    def _动作(
        cls, arg_世: 世界_类, arg_随: 随机数_类, arg_行: str, arg_原: bytes, arg_记: 电脑卡片记忆_类
    ) -> tuple[str, 世界_类]:
        op, *列 = arg_行.split()
        n = list(map(int, 列))
        状态, 值, 调用, 用 = 0, [], [], None
        掩 = n[2] if op == "p" else n[1] if op == "u" else 0
        扫 = n[3] if op == "p" else n[2] if op == "u" else 1
        路 = n[4] if op == "p" else n[3] if op == "u" else 0
        关 = bool(n[5] if op == "p" else n[4] if op == "u" else 0)

        def 实例(arg_槽: int) -> list[int]:
            调用.extend([1, arg_槽, 扫])
            return cls._扫描(arg_世, 扫)

        def 前瞻(arg_槽: int, arg_步: int) -> 卡片前瞻_类:
            调用.extend([2, arg_槽, arg_步])
            if 路 == 0:
                p = 道具电脑_类._前瞻(arg_世, arg_随, arg_槽, arg_步)
                return 卡片前瞻_类(p.节点, p.经过路口)
            if 路 == 4:
                return 卡片前瞻_类()
            return 卡片前瞻_类(
                [
                    65535 if 路 == 5 else 1 + (arg_步 - i - 1 if 路 == 2 else i)
                    for i in range(arg_步)
                ],
                路 == 3,
            )

        def 休市() -> bool:
            调用.extend([3, int(关), 0])
            return 关

        def 验人(arg_槽: int) -> None:
            if not 0 <= arg_槽 < min(4, len(arg_世.玩家)):
                raise ValueError("probe actor")

        钩 = 卡片回调_类(
            附近实例=实例 if 掩 & 1 else None,
            前瞻节点=前瞻 if 掩 & 2 else None,
            休市=休市 if 掩 & 4 else None,
        )
        try:
            if op == "u":
                用 = 卡片电脑_类.api_选择(arg_世, arg_随, n[0], 钩, arg_记 if n[5] else None)
            elif op == "p":
                验人(n[0])
                值 = [int(卡片电脑_类._谓词(arg_世, arg_随, n[0], n[1], 钩, arg_记, n[6]))]
            elif op == "m":
                arg_记.参数0, arg_记.参数1, arg_记.参数2 = n
            elif op == "x":
                目 = 卡片电脑_类._解码(n[0])
                值 = [int(目 is not None)] + ([int(目.种类), 目.数值] if 目 else [])
            elif op in ("v", "y", "o"):
                验人(n[0])
                if op == "v":
                    值 = [卡片电脑_类._怪兽(arg_世, n[0], cls._扫描(arg_世, n[1]))]
                elif op == "y":
                    神 = 卡片电脑_类._最近神(arg_世, n[0], cls._扫描(arg_世, n[1]))
                    值 = [int(神 is not None), 神 or 0]
                else:
                    值 = [卡片电脑_类._敌手(arg_世, n[0])]
            elif op == "t":
                if not 卡片电脑_类._地码(arg_世, n[0]) and not 卡片电脑_类._设施码(arg_世, n[0]):
                    raise ValueError("probe property")
                值 = [卡片电脑_类._购价(arg_世, n[0])]
            elif op == "l":
                持 = 事件_类._取(事件_类._取(arg_世.玩家, n[0]).持仓, n[1])
                值 = [卡片电脑_类._持仓成本(持)]
            elif op == "k":
                事件_类._取(arg_世.玩家, n[0]).记录.卡片[:] = n[1:]
            elif op == "E":
                事件_类._取(arg_世.地产, n[0]).经济.街道名 = f"AI-{n[1]}".encode()
            elif op == "f":
                p = 事件_类._取(arg_世.玩家, n[0]).状态
                p.龟行天数, p.附身炸弹, p.盟友 = n[1:]
            elif op == "q":
                p = 事件_类._取(事件_类._取(arg_世.玩家, n[0]).持仓, n[1])
                p.数量, p.成本位 = n[2:]
            elif op == "w":
                p = 事件_类._取(arg_世.股票, n[0])
                p.标志4, p.停牌天数, p.浮点位[1], p.浮点位[2] = n[1:]
            else:
                回, arg_世 = 道具电脑差分_类._动作(arg_世, arg_随, arg_行, arg_原)
                状态 = int(回.split()[0])
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        数 = [状态, arg_随.状态, arg_记.参数0, arg_记.参数1, arg_记.参数2, int(用 is not None)]
        if 用:
            数.append(用.卡片)
            for 目 in (用.目标, 用.选择):
                数 += [int(目 is not None)] + ([int(目.种类), 目.数值] if 目 else [])
        数 += [len(值), *值, len(调用), *调用]
        return " ".join(map(str, 数)), arg_世

    @staticmethod
    def _设置(arg_世: 世界_类) -> None:
        道具电脑差分_类._设置(arg_世)
        for i, 人 in enumerate(arg_世.玩家):
            人.状态.卡片策略 = 3
            人.记录.卡片[:] = [1 + (j + i * 7) % 30 for j in range(15)]
            for j, 持 in enumerate(人.持仓):
                持.数量, 持.成本位 = 1000 * (i + 1) if j == i else 0, 股市_类._位(10)
        for 股 in arg_世.股票:
            股.浮点位[1], 股.浮点位[2] = 股市_类._位(100), 股市_类._位(100)
        for i in range(1, 9):
            arg_世.节点[i].类型索引 = 2000 + 1 + (i - 1) % 4
        arg_世.物件[0].种类, arg_世.物件[0].节点 = 1, 1

    @staticmethod
    def _手牌(arg_槽: int, arg_牌: list[int]) -> str:
        return "k " + " ".join(map(str, [arg_槽, *(arg_牌 + [0] * 15)[:15]]))

    @classmethod
    def _命令(cls, arg_世: 世界_类, arg_生: random.Random) -> list[str]:
        组 = []
        for 卡 in range(1, 31):
            组 += [
                "r",
                "s 0",
                cls._手牌(0, [卡]),
                "m 32770 15 99",
                f"p 0 {卡} 7 1 0 0 8",
                "u 0 7 1 0 0 1",
            ]
        for 卡 in range(1, 31):
            if 卡 in (5, 6, 18, 19, 20, 21):
                continue
            组 += ["r", "s 0", "m 32770 15 99", cls._手牌(0, [卡])]
            组 += [f"E {i} 1" for i in range(1, 5)]
            组 += [f"d {2000 + i} 0 0 0 1000 500" for i in range(1, 5)]
            组 += ["n 1 0 2001 2 8 0 0 64 64"]
            配 = "c 0 2 3 2 0 100000 100000 300 0 0 0 1 8 64 64"
            组 += [配]
            if 卡 in (1, 2):
                组 += ["c 0 2 3 2 0 100 100000 300 0 0 0 1 8 64 64"]
            elif 卡 in (3, 8):
                组 += ["d 2001 2 3 0 1000 500"]
            elif 卡 == 4:
                组 += ["d 2001 1 1 0 1000 500", "E 4 2", "d 2004 2 3 0 2000 500"]
            elif 卡 == 7:
                组 += ["d 2001 1 1 0 1000 500", "c 0 2 3 0 0 100000 100000 300 0 0 0 1 8 64 64"]
            elif 卡 in (9, 27):
                组 += [f"d {2000 + i} 1 3 0 1000 500" for i in range(1, 4)]
            elif 卡 in (10, 28):
                组 += ["d 2001 2 3 0 1000 500", "d 2002 2 4 0 1000 500"]
            elif 卡 in (11, 12):
                组 += ["d 2004 2 4 0 1000 500"]
            elif 卡 == 14:
                组 += ["d 2001 1 2 0 1000 500"]
            elif 卡 in (16, 17):
                组 += [cls._手牌(1, [5])]
            elif 卡 == 22:
                组 += ["j 1 5 1 0", "c 0 2 3 2 0 100000 100000 300 0 0 1 1 8 64 64"]
            elif 卡 == 23:
                组 += ["j 1 1 1 0"]
            elif 卡 == 29:
                组 += [f"d {2000 + i} 3 3 0 1000 500" for i in range(1, 4)]
            组 += [f"p 0 {卡} 7 1 1 0 8", "u 0 7 1 1 0 1"]
        for 数 in (
            0,
            2000,
            2001,
            3999,
            4000,
            5999,
            6000,
            32768,
            32769,
            33024,
            33030,
            65535,
            4294967295,
        ):
            组.append(f"x {数}")
        基本 = 道具电脑差分_类._命令(arg_世, arg_生)
        for 行 in 基本:
            if 行.split()[0] in {"g", "c", "h", "i", "d", "n", "j", "z", "b", "r", "s"}:
                组.append(行)
        for _ in range(950):
            op = arg_生.choice(
                ["u", "u", "p", "p", "k", "k", "m", "f", "q", "w", "v", "y", "o", "t", "l", "r"]
            )
            槽, 卡 = arg_生.randrange(5), arg_生.randrange(32)
            if op in ("u", "p"):
                钩, 扫, 路, 关 = (
                    arg_生.randrange(8),
                    arg_生.randrange(1, 7),
                    arg_生.randrange(6),
                    arg_生.randrange(2),
                )
                行 = (
                    f"p {槽} {卡} {钩} {扫} {路} {关} {arg_生.choice([0, 1, 8, 15, 255])}"
                    if op == "p"
                    else f"u {槽} {钩} {扫} {路} {关} {arg_生.randrange(2)}"
                )
            elif op == "k":
                行 = cls._手牌(槽, [arg_生.randrange(1, 31) for _ in range(arg_生.randrange(16))])
            elif op == "m":
                行 = "m " + " ".join(
                    map(
                        str, arg_生.choices([0, 1, 15, 2001, 4001, 0x8002, 0x8100, 0xFFFFFFFF], k=3)
                    )
                )
            elif op == "f":
                行 = (
                    f"f {槽} {arg_生.choice([0, 1, 128])} "
                    f"{arg_生.choice([0, 1, 20, 46, 255])} {arg_生.randrange(5)}"
                )
            elif op == "q":
                行 = (
                    f"q {槽} {arg_生.randrange(13)} {arg_生.choice([-1, 0, 1, 1000, 2147483647])} "
                    f"{arg_生.choice([0, 1, 0x41200000, 0x7F800000, 0x7FC01234, 0xFFFFFFFF])}"
                )
            elif op == "w":
                行 = (
                    f"w {arg_生.randrange(13)} {arg_生.randrange(3)} "
                    f"{arg_生.choice([0, 1, 15])} {股市_类._位(100)} "
                    f"{arg_生.choice([股市_类._位(90), 股市_类._位(100), 股市_类._位(110)])}"
                )
            elif op in ("v", "y"):
                行 = f"{op} {槽} {arg_生.randrange(1, 7)}"
            elif op == "o":
                行 = f"o {槽}"
            elif op == "t":
                行 = f"t {arg_生.choice([0, 2001, 2002, 4001, 4002, 6001])}"
            elif op == "l":
                行 = f"l {槽} {arg_生.randrange(13)}"
            else:
                行 = "r"
            组.append(行)
        return 组

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
        工具 = arg_构建.resolve() / "cards-ai-oracle"
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "src"),
                str(Path(__file__).with_name("cards_ai_oracle.cpp")),
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
            "generator_seed": 2026102314,
            "scope": (
                "card AI decisions, persistent parameters and validated-domain private probes; "
                "explicit field/reset/RNG test commands, not game long play"
            ),
            "status": "running",
            "episodes": [],
        }
        生 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_素材 / "map.mkf")
            for 图 in range(8):
                for 种 in (0, 1, 0xFFFFFFFF):
                    世 = 世界_类.api_从地图(
                        包.api_解码(图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                    )
                    cls._设置(世)
                    原, 随机 = 世.api_导出(), 随机数_类(种)
                    命令, 预期, 字节 = cls._命令(世, 生), [], []
                    记 = 电脑卡片记忆_类()
                    for 行 in 命令:
                        返回, 世 = cls._动作(世, 随机, 行, 原, 记)
                        预期.append(返回)
                        字节.append(世.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-card-ai-") as 临:
                        路 = Path(临)
                        (路 / "input.dat").write_bytes(原)
                        cp = subprocess.run(
                            [str(工具), str(路 / "input.dat"), str(路 / "out"), str(种)],
                            input="\n".join(命令) + "\n",
                            text=True,
                            capture_output=True,
                            check=True,
                        )
                        行组 = cp.stdout.splitlines()
                        if len(行组) != len(命令):
                            raise ValueError("卡片电脑oracle行数不同")
                        摘 = hashlib.sha256()
                        for i, (令, c, p, 存) in enumerate(zip(命令, 行组, 预期, 字节)):
                            if c != p:
                                raise ValueError(f"图{图}/种{种}/步{i}/{令} 返回/RNG不同：{c}/{p}")
                            实 = (路 / "out" / f"{i}.dat").read_bytes()
                            if 存 != 实:
                                首 = next(j for j, (a, b) in enumerate(zip(存, 实)) if a != b)
                                raise ValueError(f"图{图}/种{种}/步{i}/{令} DAT不同offset={首}")
                            摘.update(存)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种,
                            "commands": len(命令),
                            "operations": dict(Counter(行.split()[0] for 行 in 命令)),
                            "statuses": dict(Counter(行.split()[0] for 行 in 预期)),
                            "decisions": dict(
                                Counter(行.split()[6] for 行 in 预期 if 行.split()[5] == "1")
                            ),
                            "state_sha256": 摘.hexdigest(),
                            "input_sha256": hashlib.sha256("\n".join(命令).encode()).hexdigest(),
                        }
                    )
                    print(f"map={图} seed={种} commands={len(命令)} matched", flush=True)
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
                    "commands": sum(组["commands"] for 组 in 报告["episodes"]),
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
    卡片电脑差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
