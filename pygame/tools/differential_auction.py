# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.auction import 拍卖会话_类
from rich4.random import 随机数_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 拍卖差分_类:
    """
    暂停/继续拍卖每一步比较公开状态、世界字节和随机流，覆盖估价与结算。

    更新日志：
    2026.10.23 - 真实八图和多种控制/资金/状态/租期的确定性测试。
    """

    @staticmethod
    def _状态(
        arg_拍卖: 拍卖会话_类 | None, arg_随机: 随机数_类, arg_状态: int, arg_应用: int
    ) -> list[int]:
        结果 = [arg_状态, arg_随机.状态]
        if arg_拍卖 is None:
            return 结果
        拍卖 = arg_拍卖
        结果 += [
            arg_应用,
            int(拍卖.已结束),
            拍卖.起价,
            拍卖.价格,
            -1 if 拍卖.结果.赢家 is None else 拍卖.结果.赢家,
            拍卖.结果.价格,
            拍卖.结果.地产,
        ]
        for 槽 in range(5):
            上限 = 拍卖.api_电脑上限(槽)
            结果.append(-2147483649 if 上限 is None else 上限)
        决策 = 拍卖.api_决策()
        结果.append(int(决策 is not None))
        if 决策:
            结果 += [决策.玩家, 决策.价格, 决策.已退出, len(决策.行动), *map(int, 决策.行动)]
        return 结果

    @staticmethod
    def _设置(arg_世: 世界_类, arg_序: int, arg_生成: random.Random) -> tuple[int, int, int | None]:
        地产 = [2000 + i for i in range(1, len(arg_世.地产))]
        地产 += [4000 + i for i in range(1, len(arg_世.设施))]
        编码 = arg_生成.choice(地产)
        if arg_序 % 17 == 0:
            编码 = arg_生成.choice([2000, 4000, 6001, 65535])
        arg_世.头.日期 = (31, 1, 2000)
        arg_世.头.物价 = arg_生成.choice([0, 1, 1, 2, 5, 99, 2147483647])
        arg_世.租约模式 = arg_序 % 7
        arg_世.公共基金 = 2147483647
        for 地 in arg_世.地产[1:]:
            地.经济.街道名 = arg_生成.choice([b"A", b"B"])
            地.经济.业主 = arg_生成.randrange(5)
            地.经济.等级 = arg_生成.randrange(6)
            地.地价 = arg_生成.choice([0, 1, 1001, 5000, 65535])
            地.到期日 = 0x12345678
        for 地 in arg_世.设施[1:]:
            地.业主 = arg_生成.randrange(5)
            地.等级 = arg_生成.randrange(6)
            地.地价 = arg_生成.choice([0, 1, 1001, 2000, 65535])
            地.到期日 = 0x12345678
        组合 = ([1, 1, 1, 1], [2, 2, 2, 2], [1, 2, 0, 2], [3, 4, 5, 8], [0, 0, 0, 0])
        for i, 玩家 in enumerate(arg_世.玩家):
            玩家.记录.控制标志 = 组合[arg_序 % len(组合)][i]
            玩家.记录.现金 = arg_生成.choice([-1, 0, 1000, 1001, 5000, 100000, 2147483647])
            玩家.记录.银行 = 2147483647
            玩家.状态.累计收入 = 玩家.状态.累计支出 = 0xFFFFFFF0
            if arg_序 % 3 == 0 and i == arg_序 % 4:
                setattr(
                    玩家.状态,
                    arg_生成.choice(
                        ["酒店天数", "医院天数", "监狱天数", "消失天数", "睡眠天数", "梦游天数"]
                    ),
                    128,
                )
        租期 = arg_生成.choice([None, None, 0, 0x100, 0x20000, 0xFFFFFFFF])
        卖家 = arg_生成.choice([-2, -1, -1, 0, 1, 3, 4])
        if arg_序 % 2:
            arg_世.头.物价 = arg_生成.choice([1, 2, 5])
            arg_世.租约模式 = arg_序 % 6
            for 玩家 in arg_世.玩家:
                玩家.记录.现金 = 1000000
            卖家 = -1
        return 编码, 卖家, 租期

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_地图包: Path, arg_报告: Path) -> None:
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
        工具 = arg_构建.resolve() / "auction-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("auction_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "generator_seed": 2026102305,
            "scope": "auction sessions; no presentation timer/announcer animation",
            "status": "running",
            "maps": [],
        }
        生成 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_地图包)
            for 图 in range(8):
                数据 = 包.api_解码(图 * 2 + 1)
                总步数 = 拒绝数 = 成交数 = 0
                输入摘要, 状态摘要 = hashlib.sha256(), hashlib.sha256()
                for 序 in range(100):
                    种子 = 生成.randrange(1 << 32)
                    世 = 世界_类.api_从地图(
                        数据, 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种子)
                    )
                    编码, 卖家, 租期 = cls._设置(世, 序, 生成)
                    原 = 世.api_导出()
                    随机 = 随机数_类(种子)
                    拍卖 = None
                    状态 = 0
                    try:
                        拍卖 = 拍卖会话_类(世, 随机, 编码, 卖家, 租期)
                    except IndexError:
                        状态 = 2
                    except ValueError:
                        状态 = 1
                    预期 = [cls._状态(拍卖, 随机, 状态, -1)]
                    字节组 = [世.api_导出()]
                    动作: list[str] = []
                    while 拍卖 is not None and not 拍卖.已结束 and len(动作) < 1000:
                        if 生成.randrange(5) == 0:
                            码 = 生成.randrange(9)
                            动作.append(f"b {码}")
                            应用 = int(拍卖.api_竞价(码))
                        else:
                            决策 = 拍卖.api_决策()
                            if 决策:
                                码 = int(生成.choice(决策.行动))
                                动作.append(f"b {码}")
                                应用 = int(拍卖.api_竞价(码))
                            else:
                                动作.append("t")
                                应用 = int(拍卖.api_推进())
                        预期.append(cls._状态(拍卖, 随机, 状态, 应用))
                        字节组.append(世.api_导出())
                    if 拍卖 is not None:
                        if not 拍卖.已结束:
                            raise ValueError(f"图{图}/序{序}拍卖1000步仍未结束")
                        成交数 += int(拍卖.结果.赢家 is not None)
                        动作 += ["t", "b 1"]
                        for 命令 in 动作[-2:]:
                            应用 = 拍卖.api_推进() if 命令 == "t" else 拍卖.api_竞价(1)
                            预期.append(cls._状态(拍卖, 随机, 状态, int(应用)))
                            字节组.append(世.api_导出())
                    输入 = "\n".join(动作) + ("\n" if 动作 else "")
                    输入摘要.update(原)
                    输入摘要.update(f"{种子}/{编码}/{卖家}/{租期}\n{输入}".encode())
                    with tempfile.TemporaryDirectory(prefix="rich4-auction-") as 临时:
                        路径 = Path(临时)
                        初始 = 路径 / "input.dat"
                        初始.write_bytes(原)
                        cpp = subprocess.run(
                            [
                                str(工具),
                                str(初始),
                                str(路径 / "out"),
                                str(种子),
                                str(编码),
                                str(卖家),
                                "-1" if 租期 is None else str(租期),
                            ],
                            input=输入,
                            text=True,
                            capture_output=True,
                            check=True,
                        )
                        行 = cpp.stdout.splitlines()
                        if len(行) != len(预期):
                            raise ValueError(f"图{图}/序{序}拍卖输出行数不同")
                        for i, (cpp行, py行, 字节) in enumerate(zip(行, 预期, 字节组)):
                            if list(map(int, cpp行.split())) != py行:
                                raise ValueError(f"图{图}/序{序}/步{i}拍卖不同：{cpp行}/{py行}")
                            if 字节 != (路径 / "out" / f"{i}.dat").read_bytes():
                                raise ValueError(f"图{图}/序{序}/步{i}完整DAT不同")
                            状态摘要.update(字节)
                            状态摘要.update(cpp行.encode())
                    总步数 += len(预期)
                    拒绝数 += int(状态 != 0)
                报告["maps"].append(
                    {
                        "map": 图,
                        "cases": 100,
                        "snapshots": 总步数,
                        "rejected_constructors": 拒绝数,
                        "sales": 成交数,
                        "input_sha256": 输入摘要.hexdigest(),
                        "states_sha256": 状态摘要.hexdigest(),
                    }
                )
                print(f"[完成] 图{图}一百组拍卖初始/逐步/结算状态一致。", flush=True)
            报告["status"] = "passed"
        except (ValueError, IndexError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--map", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    拍卖差分_类.api_执行(选项.source, 选项.build, 选项.map, 选项.report)
