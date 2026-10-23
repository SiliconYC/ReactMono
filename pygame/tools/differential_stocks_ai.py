# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.events import 事件_类
from rich4.numeric import 数值范围错误_类
from rich4.random import 随机数_类
from rich4.save import 存档_类
from rich4.stocks import 股市_类
from rich4.stocks_ai import 股票电脑_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 股票电脑差分_类:
    """
    真实买卖入口和经过公共边界验证的私有评分探针，完整DAT/RNG逐命令比较。

    更新日志：
    2026.10.23 - 固定源仅在测试适配器包含；正常游戏不加载C++。
    """

    @staticmethod
    def _动作(
        arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str, arg_原: bytes
    ) -> tuple[str, 世界_类]:
        op, *列 = arg_行.split()
        n = list(map(int, 列))
        状态, 成交, 值 = 0, [], []
        try:
            if op == "b":
                成交 = 股票电脑_类.api_买入(arg_世, arg_随机, n[0], bool(n[1]))
            elif op == "s":
                成交 = 股票电脑_类.api_卖出(arg_世, arg_随机, n[0], bool(n[1]))
            elif op == "r":
                arg_世 = 世界_类.api_从存档(存档_类.api_解码(arg_原))
            elif op == "t":
                arg_随机.状态 = n[0]
            elif op == "p":
                人 = 事件_类._取(arg_世.玩家, n[0])
                人.记录.现金, 人.记录.银行, 人.记录.贷款, 人.状态.股票投资比例, 人.状态.贷款到期 = (
                    n[1:]
                )
            elif op == "h":
                持 = 事件_类._取(事件_类._取(arg_世.玩家, n[0]).持仓, n[1])
                持.数量, 持.成本位 = n[2:]
            elif op == "q":
                股 = 事件_类._取(arg_世.股票, n[0])
                股.标志4, 股.可购股数, 股.标志10, 股.停牌天数 = n[1:5]
                股.浮点位[0], 股.浮点位[1], 股.浮点位[2], 股.浮点位[4] = n[5:]
            elif op == "c":
                司 = 事件_类._取(arg_世.公司, n[0])
                司.资金, 司.资金变化, 司.估值, 司.业主, 司.剩余股份 = n[1:]
            elif op == "d":
                arg_世.头.日期 = tuple(n[:3])
                arg_世.股史游标, arg_世.月数 = n[3:]
            elif op == "f":
                历 = 事件_类._取(arg_世.股史, n[0])
                for i in range(144):
                    历[i] = (
                        n[3]
                        if n[1] == 1 and i >= 138
                        else (0x80000000 if i % 2 else 0)
                        if n[1] == 2 and i % 3 == 0
                        else n[2]
                    )
            elif op == "o":
                项 = list(enumerate(n))
                股票电脑_类._原排序(项)
                值 = [v for 组 in 项 for v in 组]
            elif op == "l":
                值 = [股票电脑_类._原日序(n[0])]
            elif op == "g":
                股票电脑_类._验证(arg_世, 0)
                事件_类._取(arg_世.股票, n[0])
                值 = [股市_类._位(股票电脑_类._历史均值(arg_世, *n))]
            elif op == "k":
                股票电脑_类._验证(arg_世, n[0])
                值 = [股票电脑_类._持仓值(arg_世, n[0])]
            elif op in ("a", "e", "n"):
                股票电脑_类._验证(arg_世, n[0])
                事件_类._取(arg_世.股票, n[1])
                if op == "a":
                    值 = [股票电脑_类._公司买分(arg_世, *n)]
                elif op == "e":
                    值 = [股票电脑_类._公司卖分(arg_世, n[0], n[1], bool(n[2]))]
                else:
                    值 = [股票电脑_类._市场卖分(arg_世, n[0], n[1], bool(n[2]))]
            elif op == "m":
                股票电脑_类._验证(arg_世, 0)
                事件_类._取(arg_世.股票, n[0])
                值 = [股票电脑_类._市场买分(arg_世, n[0])]
            else:
                raise RuntimeError("未知股票电脑差分命令")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        数 = [状态, arg_随机.状态, len(成交)]
        for 项 in 成交:
            数 += [项.股票, 项.数量, 项.金额, int(项.公司易主)]
        数 += [len(值), *值]
        return " ".join(map(str, 数)), arg_世

    @staticmethod
    def _设置(arg_世: 世界_类) -> None:
        arg_世.头.日期, arg_世.头.物价, arg_世.月数, arg_世.股史游标 = (13, 1, 2000), 1, 1, 0
        for i, 人 in enumerate(arg_世.玩家):
            人.记录.控制标志, 人.记录.现金, 人.记录.银行, 人.记录.贷款 = 2, 0, 100000, 0
            人.状态.股票投资比例, 人.状态.贷款到期 = 80, 0
            for 持 in 人.持仓:
                持.数量, 持.成本位 = 0 if i == 0 else 10**i, 股市_类._位(5)
        for i, 股 in enumerate(arg_世.股票):
            股.标志4, 股.标志10, 股.可购股数, 股.停牌天数 = 1 if i == 0 else 0, 1000, 1000, 0
            股.浮点位[:] = [股市_类._位(20), 股市_类._位(10), 股市_类._位(10), 0, 股市_类._位(3)]
            arg_世.股史[i][:] = [股市_类._位(5)] * 138 + [股市_类._位(8)] * 6
        for i, 司 in enumerate(arg_世.公司[1:], 1):
            司.股票索引, 司.业主, 司.资金, 司.资金变化, 司.估值, 司.剩余股份 = (
                (i - 1) % 12,
                2,
                10000,
                10000,
                1000000,
                5000,
            )

    @staticmethod
    def _命令(arg_世: 世界_类, arg_生: random.Random) -> list[str]:
        组 = ["r", "t 0", "b 0 0", "r", "p 0 0 0 50000 80 0", "t 17"]
        组 += [f"h 0 {i} 1000 {股市_类._位(5)}" for i in range(12)]
        组 += ["s 0 0", "r", "b 0 1", "s 0 1"]
        for 码 in [
            0,
            2000 << 16 | 11 << 8 | 31,
            2000 << 16 | 12 << 8 | 1,
            1998 << 16 | 1 << 8,
            0xFFFFFFFF,
        ]:
            组.append(f"l {码}")
        for i in range(12):
            组 += [f"a 0 {i}", f"m {i}", f"e 1 {i} 0", f"n 1 {i} 1", f"g {i} 6", f"g {i} 24"]
        位 = [股市_类._位(v) for v in (0, 0.1, -1, 1, 5, 10, 50, 100, 1e20)] + [
            1,
            0x7FC01234,
            0x7F800000,
            0x80000000,
        ]
        for _ in range(700):
            op = arg_生.choice(
                [
                    "b",
                    "b",
                    "s",
                    "s",
                    "p",
                    "h",
                    "q",
                    "c",
                    "d",
                    "f",
                    "a",
                    "e",
                    "m",
                    "n",
                    "g",
                    "k",
                    "o",
                    "r",
                    "t",
                ]
            )
            槽, 股 = arg_生.randrange(5), arg_生.randrange(13)
            if op in ("b", "s"):
                行 = f"{op} {槽} {arg_生.randrange(2)}"
            elif op == "p":
                钱 = arg_生.choice([-2147483648, -10000, 0, 1000, 100000, 2147483647])
                银 = arg_生.choice([-100000, 0, 5000, 50000, 100000, 2147483647])
                贷 = arg_生.choice([0, 10000, 100000, 2147483647])
                比 = arg_生.choice([0, 1, 50, 80, 100, 255])
                到 = arg_生.choice(
                    [0, 2000 << 16 | 1 << 8 | 15, 2000 << 16 | 2 << 8 | 31, 0xFFFFFFFF]
                )
                行 = f"p {槽} {钱} {银} {贷} {比} {到}"
            elif op == "h":
                行 = (
                    f"h {槽} {股} {arg_生.choice([-1, 0, 1, 100, 5000, 2147483647])} "
                    f"{arg_生.choice(位)}"
                )
            elif op == "q":
                司 = arg_生.choice([0, 1, len(arg_世.公司) - 1, 65535])
                行 = " ".join(
                    map(
                        str,
                        [
                            "q",
                            股,
                            司,
                            arg_生.choice([0, 1, 1000, 65535]),
                            arg_生.choice([0, 1, 1000, 65535]),
                            arg_生.choice([0, 0, 15]),
                            *arg_生.choices(位, k=4),
                        ],
                    )
                )
            elif op == "c":
                司 = arg_生.choice([0, 1, len(arg_世.公司) - 1, len(arg_世.公司)])
                行 = " ".join(
                    map(
                        str,
                        [
                            "c",
                            司,
                            *arg_生.choices(
                                [-2147483648, -20000, -10000, 0, 10000, 1000000, 2147483647], k=3
                            ),
                            arg_生.randrange(6),
                            arg_生.choice([0, 5000, 2147483647]),
                        ],
                    )
                )
            elif op == "d":
                行 = (
                    f"d {arg_生.choice([1, 9, 11, 13, 15, 31])} 1 2000 "
                    f"{arg_生.choice([-1, 0, 1, 24, 143, 144])} "
                    f"{arg_生.choice([0, 1, 12, 4294967295])}"
                )
            elif op == "f":
                行 = f"f {股} {arg_生.randrange(3)} {arg_生.choice(位)} {arg_生.choice(位)}"
            elif op == "a":
                行 = f"a {槽} {股}"
            elif op in ("e", "n"):
                行 = f"{op} {槽} {股} {arg_生.randrange(2)}"
            elif op == "m":
                行 = f"m {股}"
            elif op == "g":
                行 = f"g {股} {arg_生.choice([6, 24])}"
            elif op == "k":
                行 = f"k {槽}"
            elif op == "o":
                行 = "o " + " ".join(
                    map(
                        str,
                        arg_生.choices([-2147483648, -1, 0, 0, 0, 1, 2, 3, 5, 2147483647], k=12),
                    )
                )
            elif op == "t":
                行 = f"t {arg_生.getrandbits(32)}"
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
        工具 = arg_构建.resolve() / "stocks-ai-oracle"
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "src"),
                str(Path(__file__).with_name("stocks_ai_oracle.cpp")),
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
            "generator_seed": 2026102312,
            "scope": (
                "stock AI trades and validated-domain private probes; "
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
                    for 行 in 命令:
                        返回, 世 = cls._动作(世, 随机, 行, 原)
                        预期.append(返回)
                        字节.append(世.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-stock-ai-") as 临:
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
                            raise ValueError("股票电脑oracle行数不同")
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
                            "buy_trades": sum(
                                int(行.split()[2]) for 令, 行 in zip(命令, 预期) if 令[0] == "b"
                            ),
                            "sell_trades": sum(
                                int(行.split()[2]) for 令, 行 in zip(命令, 预期) if 令[0] == "s"
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
    股票电脑差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
