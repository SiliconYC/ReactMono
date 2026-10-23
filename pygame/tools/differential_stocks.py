# ◑ 导入
import argparse
import hashlib
import json
import random
import struct
import subprocess
import tempfile
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.numeric import 数值范围错误_类
from rich4.random import 随机数_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 股票差分_类:
    """
    股价纯函数及模块动作序列后逐字节比较整个世界，不把市场更新称为游戏长局。

    更新日志：
    2026.10.23 - 覆盖交易/拒绝、公司排名、财富、每日/强制行情与随机限额。
    """

    @staticmethod
    def _位(arg_值: float) -> int:
        return struct.unpack("<I", struct.pack("<f", arg_值))[0]

    @classmethod
    def _价格(cls, arg_工具: Path, arg_生成: random.Random) -> dict:
        用例 = [
            (cls._位(arg_生成.random() * 10000), cls._位(arg_生成.uniform(-10, 10)))
            for _ in range(20000)
        ]
        for 前 in [0, 1, 4.5, 5, 14.5, 15, 49, 50, 149, 150, 9999, 10000]:
            for 差 in [-1, 0, 1]:
                for 幅 in [-10, -5, -0.00001, 0, 0.00001, 5, 10, 11]:
                    用例.append(((cls._位(前) + 差) & 0xFFFFFFFF, cls._位(幅)))
        输入 = "\n".join(f"{a} {b}" for a, b in 用例) + "\n"
        cpp = subprocess.run(
            [str(arg_工具), "--prices"], input=输入, text=True, capture_output=True, check=True
        )
        行 = cpp.stdout.splitlines()
        if len(行) != len(用例):
            raise ValueError("股价 oracle 行数不同")
        for i, ((a, b), 结果) in enumerate(zip(用例, 行)):
            前, 幅 = [struct.unpack("<f", struct.pack("<I", v))[0] for v in (a, b)]
            try:
                预期 = str(cls._位(股市_类.api_调整股价(前, 幅)))
            except 数值范围错误_类:
                预期 = "range"
            except ValueError:
                预期 = "invalid"
            if 预期 != 结果:
                raise ValueError(f"股价差分失败 {i}，输入{a}/{b}，CPP={结果}，Python={预期}")
        return {
            "cases": len(用例),
            "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
            "output_sha256": hashlib.sha256(cpp.stdout.encode()).hexdigest(),
        }

    @staticmethod
    def _动作(arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str) -> tuple[int, int, int, int]:
        部分 = arg_行.split()
        op = 部分[0]
        数 = list(map(int, 部分[1:]))
        状态 = 值 = 改 = 0
        try:
            if op == "b":
                p, s, n, f = 数
                结果 = 股市_类.api_买入(arg_世, p, s, n, bool(f))
                值, 改 = 结果.费用, int(结果.公司易主)
            elif op == "s":
                p, s, n, f = 数
                卖 = 股市_类.api_卖出(arg_世, p, s, n, bool(f))
                值, 改 = 卖.收入, int(卖.公司易主)
            elif op == "d":
                值 = int(股市_类.api_日更新(arg_世, arg_随机, bool(数[0])))
            elif op == "l":
                股市_类.api_刷新限额(arg_世, arg_随机)
            elif op == "f":
                值 = 股市_类.api_强制行情(arg_世, 数[0])
            elif op == "w":
                值 = 股市_类.api_财富(arg_世, 数[0])
            elif op == "t":
                值 = int(股市_类.api_走势(arg_世, 数[0]))
            elif op == "o":
                值 = int(股市_类.api_更新业主(arg_世, 数[0], 数[1]))
            elif op == "e":
                arg_世.新闻影响天数 = 数[0]
            elif op == "n":
                s, n, f = 数
                if not 0 <= s < len(arg_世.股票):
                    raise IndexError("测试股票索引越界")
                arg_世.股票[s].新闻走势 = n & 255
                arg_世.股票[s].停牌天数 = f & 255
            else:
                raise RuntimeError("未知测试动作")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        return 状态, 值, 改, arg_随机.状态

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_地图包: Path,
        arg_报告: Path,
    ) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++ 版本不符")
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
        工具 = arg_构建.resolve() / "stocks-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("stocks_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "scope": "stock-module actions, not full-game long runs",
            "status": "running",
            "episodes": [],
        }
        生成 = random.Random(2026102302)
        try:
            报告["prices"] = cls._价格(工具, 生成)
            地图包 = 资源包_类(arg_地图包)
            for 图 in [0, 3, 4, 7]:
                图数据 = 地图包.api_解码(图 * 2 + 1)
                for 种子 in [0, 1, 0xFFFFFFFF]:
                    世 = 世界_类.api_从地图(
                        图数据, 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种子)
                    )
                    for i, 玩家 in enumerate(世.玩家):
                        玩家.记录.现金 = 20000000 + i * 31
                        玩家.记录.银行 = 10000000 + i * 17
                        for j, 持仓 in enumerate(玩家.持仓):
                            持仓.数量 = 1000 - i * 100
                            持仓.成本位 = 世.股票[j].浮点位[2]
                    for 公司 in 世.公司[1:]:
                        公司.股东排名[:] = [1, 2, 3, 4]
                        公司.业主 = 1
                    原 = 世.api_导出()
                    动作 = ["l"]
                    for _ in range(199):
                        op = 生成.choice("bbsddllfwwtooen")
                        p = 生成.randrange(5)
                        s = 生成.randrange(13)
                        if op in "bs":
                            n = 生成.choice([-1, 0, 1, 3, 10, 100, 1000, 30000, 2147483647])
                            动作.append(f"{op} {p} {s} {n} {生成.randrange(2)}")
                        elif op == "d":
                            动作.append(f"d {int(生成.randrange(7) == 0)}")
                        elif op == "l":
                            动作.append("l")
                        elif op == "f":
                            动作.append(f"f {生成.randrange(14)}")
                        elif op in "wt":
                            动作.append(f"{op} {p if op == 'w' else s}")
                        elif op == "o":
                            动作.append(f"o {p} {s}")
                        elif op == "e":
                            动作.append(f"e {生成.choice([0, 0, 0, 1])}")
                        else:
                            变动 = 生成.choice([0, 1, 16, 17, 255])
                            停牌 = 生成.choice([0, 0, 1, 5])
                            动作.append(f"n {s} {变动} {停牌}")
                    输入 = "\n".join(动作) + "\n"
                    with tempfile.TemporaryDirectory(prefix="rich4-stock-") as 临时:
                        路径 = Path(临时)
                        初始 = 路径 / "input.dat"
                        初始.write_bytes(原)
                        cpp = subprocess.run(
                            [str(工具), str(初始), str(路径 / "out"), str(种子)],
                            input=输入,
                            text=True,
                            capture_output=True,
                            check=True,
                        )
                        行 = cpp.stdout.splitlines()
                        if len(行) != len(动作):
                            raise ValueError("股市动作结果行数不同")
                        随机 = 随机数_类(种子)
                        错误数 = 0
                        for i, (命令, cpp行) in enumerate(zip(动作, 行)):
                            预期 = cls._动作(世, 随机, 命令)
                            if tuple(map(int, cpp行.split())) != 预期:
                                raise ValueError(
                                    f"图{图} 种子{种子} 动作{i} {命令} 返回/RNG不同：{cpp行}/{预期}"
                                )
                            if 世.api_导出() != (路径 / "out" / f"{i}.dat").read_bytes():
                                raise ValueError(
                                    f"图{图} 种子{种子} 动作{i} {命令} 完整世界字节不同"
                                )
                            错误数 += int(预期[0] != 0)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种子,
                            "steps": len(动作),
                            "rejected_actions": 错误数,
                            "initial_sha256": hashlib.sha256(原).hexdigest(),
                            "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
                        }
                    )
                print(f"[完成] 地图{图}三组股市动作完整状态和随机数一致。", flush=True)
            报告["status"] = "passed"
        except (ValueError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print("[完成] 股价与2400个股市模块动作逐步差分通过。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--map", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    股票差分_类.api_执行(选项.source, 选项.build, 选项.map, 选项.report)
