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
from rich4.trading import 交易_类, 交易结果_类, 报价_类, 挂单_类, 电脑交易结果_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 交易差分_类:
    """
    逐步比较所有交易返回值及完整DAT；测试生成器不参与正式规则随机流。

    更新日志：
    2026.10.23 - 八图三种子，含私下股权/资产交易、电脑策略和拒绝操作。
    """

    @staticmethod
    def _位(arg_值: float) -> int:
        return struct.unpack("<I", struct.pack("<f", arg_值))[0]

    @staticmethod
    def _报价(arg_报: 报价_类) -> list[int]:
        项 = arg_报.出售项
        return [
            arg_报.卖家,
            arg_报.索引,
            项.种类,
            项.标志,
            项.项目,
            项.价格,
            项.数量,
            项.地产类型,
            项.地产等级,
        ]

    @classmethod
    def _动作(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str) -> str:
        op, *部分 = arg_行.split()
        数 = list(map(int, 部分))
        状态 = 0
        结果, 电脑 = 交易结果_类(), 电脑交易结果_类()
        值 = []
        try:
            if op == "i":
                项组 = 交易_类.api_可售项目(arg_世, *数)
                值 = [len(项组), *(n for 项 in 项组 for n in (项.种类, 项.编号, 项.最大数量))]
            elif op == "l":
                限 = 交易_类.api_限价(arg_世, *数)
                值 = [0] if 限 is None else [1, 限.参考价, 限.最高价]
            elif op == "q":
                报组 = 交易_类.api_报价(arg_世)
                值 = [len(报组), *(n for 报 in 报组 for n in cls._报价(报))]
            elif op == "p":
                卖家, 类, 号, 价, 数量 = 数
                结果 = 交易_类.api_挂牌(arg_世, 卖家, 挂单_类(类, 号, 价, 数量))
            elif op == "c":
                值 = [int(交易_类.api_取消(arg_世, *数))]
            elif op == "n":
                值 = [交易_类.api_清理(arg_世)]
            elif op == "b":
                结果 = 交易_类.api_购买(arg_世, *数)
            elif op == "a":
                电脑 = 交易_类.api_电脑回合(arg_世, arg_随机, *数)
            elif op == "h":
                槽, 股, 量, 位 = 数
                if not 0 <= 槽 < len(arg_世.玩家) or not 0 <= 股 < 12:
                    raise IndexError("测试持仓索引越界")
                持仓 = arg_世.玩家[槽].持仓[股]
                持仓.数量, 持仓.成本位 = 量, 位
            else:
                raise RuntimeError("未知交易测试动作")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        返回 = [
            状态,
            arg_随机.状态,
            int(结果.已应用),
            int(结果.公司易主),
            电脑.移除,
            电脑.挂牌,
            电脑.改价,
            int(电脑.购买 is not None),
        ]
        if 电脑.购买:
            返回 += cls._报价(电脑.购买)
        返回 += [len(值), *值]
        return " ".join(map(str, 返回)) + "|" + 结果.消息

    @classmethod
    def _设置(cls, arg_世: 世界_类, arg_种子: int) -> None:
        arg_世.头.物价 = 2
        for i, 玩家 in enumerate(arg_世.玩家):
            玩家.记录.控制标志 = 1 if i == 0 else 2
            玩家.记录.现金, 玩家.记录.银行 = 1000000, 2147483647
            玩家.记录.卡片[:] = [1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0, 0]
            玩家.记录.道具[:13] = [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
            玩家.状态.救援策略 = i % 3
            玩家.状态.累计收入 = 玩家.状态.累计支出 = 0xFFFFFFF0
            for 持仓 in 玩家.持仓:
                持仓.数量 = [400, 100, 200, 300][i]
                持仓.成本位 = cls._位(12.375)
        for 股 in arg_世.股票:
            股.浮点位[2] = cls._位(20.25)
        for 公司 in arg_世.公司[1:]:
            公司.业主, 公司.股东排名[:] = 1, [1, 4, 3, 2]
        for i, 地 in enumerate(arg_世.地产[1:]):
            地.经济.业主 = i % 4 + 1
            地.经济.等级 = 2
            地.到期日 = 0x12345678
        for i, 地 in enumerate(arg_世.设施[1:]):
            地.业主 = i % 4 + 1
            地.等级 = 3
            地.到期日 = 0x12345678
        arg_世.卡供应[:] = [3] * 30
        arg_世.道具供应[:] = [255 if arg_种子 == 1 else 10] * 8
        for 列 in arg_世.出售表:
            for 项 in 列:
                项.数量, 项.地产类型, 项.地产等级 = 4321, 77, 88

    @classmethod
    def _命令(cls, arg_世: 世界_类, arg_生成: random.Random, arg_序: int) -> str:
        if arg_序 < 4:
            return f"i {arg_序}"
        基准 = [
            "p 0 3 1 1 0",
            "b 1 0 0",
            "q",
            "p 0 1 0 1001 100",
            "b 1 0 0",
            f"p 0 2 {2001 if len(arg_世.地产) > 1 else 4001} 1 0",
            "b 2 0 0",
            "p 0 4 3 1 0",
            "b 2 0 0",
            "c 0 0",
            "n",
        ]
        if arg_序 < 4 + len(基准):
            return 基准[arg_序 - 4]
        op = arg_生成.choice("ppppbbbccaaiilqnnh")
        p = arg_生成.randrange(5)
        if op == "p":
            项组 = 交易_类.api_可售项目(arg_世, p)
            if 项组 and arg_生成.randrange(5):
                项 = arg_生成.choice(项组)
                数量 = arg_生成.choice([1, min(100, 项.最大数量)]) if 项.种类 == 1 else 0
                限 = 交易_类.api_限价(arg_世, p, 项.种类, 项.编号, 数量)
                价 = arg_生成.choice([1, 100, 限.参考价, 限.最高价]) if 限 else 100
                return f"p {p} {项.种类} {项.编号} {价} {数量}"
            return f"p {p} {arg_生成.randrange(6)} {arg_生成.randrange(35)} 1 0"
        if op == "b":
            报组 = 交易_类.api_报价(arg_世)
            if 报组 and arg_生成.randrange(5):
                报 = arg_生成.choice(报组)
                return f"b {p} {报.卖家} {报.索引}"
            return f"b {p} {arg_生成.randrange(5)} {arg_生成.randrange(8)}"
        if op == "c":
            return f"c {p} {arg_生成.randrange(8)}"
        if op in "ai":
            return f"{op} {p}"
        if op == "l":
            return (
                f"l {p} {arg_生成.randrange(6)} {arg_生成.randrange(35)} {arg_生成.randrange(500)}"
            )
        if op == "h":
            股 = arg_生成.randrange(13)
            量 = arg_生成.choice([-1, 0, 1, 100, 65535, 2147483647])
            位 = arg_生成.choice([cls._位(12.375), cls._位(-1), 0, 0x7FC01234, 0x7F800000])
            return f"h {p} {股} {量} {位}"
        return op

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
        工具 = arg_构建.resolve() / "trading-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("trading_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "generator_seed": 2026102306,
            "scope": "private-market module actions; no UI or game long runs",
            "status": "running",
            "episodes": [],
        }
        生成 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_地图包)
            for 图 in range(8):
                数据 = 包.api_解码(图 * 2 + 1)
                for 种子 in [0, 1, 0xFFFFFFFF]:
                    世 = 世界_类.api_从地图(
                        数据, 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种子)
                    )
                    cls._设置(世, 种子)
                    原 = 世.api_导出()
                    随机 = 随机数_类(种子)
                    动作, 预期, 字节组 = [], [], []
                    for i in range(400):
                        命令 = cls._命令(世, 生成, i)
                        动作.append(命令)
                        预期.append(cls._动作(世, 随机, 命令))
                        字节组.append(世.api_导出())
                    输入 = "\n".join(动作) + "\n"
                    with tempfile.TemporaryDirectory(prefix="rich4-trade-") as 临时:
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
                            raise ValueError("交易 oracle 行数不同")
                        摘要 = hashlib.sha256()
                        成功挂牌 = 成功购买 = 0
                        for i, (命令, cpp行, py行, 字节) in enumerate(zip(动作, 行, 预期, 字节组)):
                            if cpp行 != py行:
                                raise ValueError(
                                    f"图{图}/种{种子}/步{i}/{命令} 返回/RNG不同：{cpp行}/{py行}"
                                )
                            if 字节 != (路径 / "out" / f"{i}.dat").read_bytes():
                                raise ValueError(f"图{图}/种{种子}/步{i}/{命令} 完整DAT不同")
                            摘要.update(字节)
                            状态列 = list(map(int, py行.split("|")[0].split()))
                            成功挂牌 += int(命令.startswith("p ") and 状态列[2] == 1) + 状态列[5]
                            成功购买 += int(命令.startswith("b ") and 状态列[2] == 1) + 状态列[7]
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种子,
                            "steps": len(动作),
                            "posted": 成功挂牌,
                            "purchased": 成功购买,
                            "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
                            "states_sha256": 摘要.hexdigest(),
                        }
                    )
                print(f"[完成] 图{图}交易/电脑市场三组逐步状态一致。", flush=True)
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
    交易差分_类.api_执行(选项.source, 选项.build, 选项.map, 选项.report)
