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
from rich4.tools_ai import 选择缓冲_类, 道具电脑_类, 道具电脑回调_类, 道具电脑结果_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 道具电脑差分_类:
    """
    真实策略及投影选择缓冲逐命令比较；显式重置与字段设置仅属测试输入。

    更新日志：
    2026.10.23 - 原生参考默认EDX残值0，额外覆盖显式残值输入。
    """

    @staticmethod
    def _动作(
        arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str, arg_原: bytes
    ) -> tuple[str, 世界_类]:
        op, *列 = arg_行.split()
        n = list(map(int, 列))
        状态, 值, 调用, 果 = 0, [], [], 道具电脑结果_类()
        掩 = n[2] if op == "e" else n[1] if op == "u" else 0
        扫 = n[3] if op == "e" else n[2] if op == "u" else 1
        残 = n[4] if op == "e" else n[3] if op == "u" else 0

        def 实例(arg_槽: int) -> list[int]:
            调用.extend([1, arg_槽, 扫])
            if 扫 == 3:
                return []
            表 = [0x8000 | (1 << i) for i in range(8)]
            表 += [2000 + i for i in range(1, len(arg_世.地产))]
            表 += [4000 + i for i in range(1, len(arg_世.设施))]
            return (
                list(reversed(表))
                if 扫 == 2
                else [0x8103, 0x8000, 2001, 4001]
                if 扫 == 4
                else [2001, 4001]
                if 扫 == 5
                else 表
            )

        def 残值() -> int:
            调用.extend([2, 残, 0])
            return 残

        def 人(arg_槽: int):
            if not 0 <= arg_槽 < min(4, len(arg_世.玩家)):
                raise ValueError("probe actor")
            return arg_世.玩家[arg_槽]

        钩 = 道具电脑回调_类(实例 if 掩 & 1 else None, 残值 if 掩 & 2 else None)
        try:
            if op == "e":
                果 = 道具电脑_类.api_评估(arg_世, arg_随机, n[0], n[1], 钩)
            elif op == "u":
                果 = 道具电脑_类.api_选择(arg_世, arg_随机, n[0], 钩)
            elif op == "p":
                人(n[0])
                路 = 道具电脑_类._前瞻(arg_世, arg_随机, n[0], n[1], bool(n[2]))
                值 = [int(路.经过路口), len(路.节点), *路.节点]
            elif op == "v":
                人(n[0])
                值 = 道具电脑_类._可见道路(arg_世, n[0])
            elif op == "a":
                人(n[0])
                if n[3] > 220:
                    raise ValueError("probe radius")
                值 = 道具电脑_类._占地范围(arg_世, n[0], (n[1], n[2]), n[3])
            elif op == "m":
                if n[2] > 220:
                    raise ValueError("probe radius")
                缓 = 选择缓冲_类(arg_世, (n[0], n[1]))
                for i in range(3, len(n), 3):
                    缓.api_插入((n[i], n[i + 1]), n[i + 2])
                值 = 缓.api_扫描(n[2])
            elif op == "o":
                人(n[0])
                值 = [道具电脑_类._敌手(arg_世, arg_随机, n[0])]
            elif op == "t":
                if not 道具电脑_类._地码(arg_世, n[0]):
                    raise ValueError("probe land")
                值 = [道具电脑_类._通行费(arg_世, n[0])]
            elif op == "r":
                arg_世 = 世界_类.api_从存档(存档_类.api_解码(arg_原))
            elif op == "s":
                arg_随机.状态 = n[0]
            elif op == "g":
                arg_世.相机旋转, arg_世.头.物价 = n
            elif op == "c":
                p = 事件_类._取(arg_世.玩家, n[0])
                (
                    p.记录.控制标志,
                    p.状态.卡片策略,
                    p.状态.救援策略,
                    p.记录.交通,
                    p.记录.现金,
                    p.记录.银行,
                    p.记录.点券,
                    p.状态.财运修正,
                    p.状态.睡眠天数,
                    p.状态.神明信息,
                    p.记录.节点,
                    p.记录.上次节点,
                    p.记录.x,
                    p.记录.y,
                ) = n[1:]
            elif op == "h":
                p = 事件_类._取(arg_世.玩家, n[0])
                事件_类._取(p.状态.敌意, n[1])
                p.状态.敌意[n[1]] = n[2]
            elif op == "i":
                p = 事件_类._取(arg_世.玩家, n[0])
                事件_类._取(p.记录.道具, n[1])
                p.记录.道具[n[1]] = n[2]
            elif op == "d":
                if 道具电脑_类._地码(arg_世, n[0]):
                    p = arg_世.地产[n[0] - 2000]
                    p.经济.业主, p.经济.等级, p.经济.连锁, p.地价, p.每级造价 = [
                        v & 65535 if i >= 3 else v for i, v in enumerate(n[1:])
                    ]
                elif 道具电脑_类._设施码(arg_世, n[0]):
                    p = arg_世.设施[n[0] - 4000]
                    p.业主, p.等级, p.类型, p.地价 = [*n[1:4], n[4] & 65535]
                    p.各级租金[0] = n[5] & 65535
                else:
                    raise ValueError("probe property")
            elif op == "n":
                p = 事件_类._取(arg_世.节点, n[0])
                p.标志, p.类型索引 = n[1:3]
                p.邻居[:] = n[3:7]
                p.x, p.y = n[7:]
            elif op == "j":
                p = 事件_类._取(arg_世.物件, n[0] - 1)
                p.种类, p.节点, p.附身玩家 = n[1:]
            elif op == "z":
                表 = arg_世.监狱名单 if n[0] == 0 else arg_世.医院名单
                事件_类._取(表, n[1])
                表[n[1]] = n[2]
            elif op == "b":
                p = 事件_类._取(arg_世.玩家, n[0]).状态
                p.酒店天数, p.消失天数, p.监狱天数, p.医院天数 = n[1:]
            else:
                raise RuntimeError("未知道具电脑差分命令")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        数 = [状态, arg_随机.状态, int(果.支持), int(果.决策 is not None)]
        if 果.决策:
            数 += [果.决策.道具, 果.决策.目标, 果.决策.目的地]
        数 += [len(值), *值, len(调用), *调用]
        return " ".join(map(str, 数)) + "|" + 果.消息, arg_世

    @staticmethod
    def _设置(arg_世: 世界_类) -> None:
        arg_世.头.物价 = 1
        for i, 人 in enumerate(arg_世.玩家):
            人.记录.控制标志, 人.状态.卡片策略, 人.状态.救援策略 = 2, 2, 2
            人.记录.交通, 人.记录.现金, 人.记录.银行, 人.记录.点券 = 0, 100000, 100000, 300
            人.状态.财运修正, 人.状态.睡眠天数, 人.状态.神明信息 = 0, 0, 0
            人.状态.敌意[:] = [0, 100, 0, 0] if i == 0 else [0] * 4
            人.记录.节点, 人.记录.上次节点 = 1, 8
            人.记录.x, 人.记录.y = (64, 64) if i == 0 else (4000, 4000)
            人.记录.道具[:] = [1] * 15
        for i in range(1, 9):
            p = arg_世.节点[i]
            p.标志, p.类型索引 = 0, 0
            p.邻居[:] = [i % 8 + 1, (i - 2) % 8 + 1, 0, 0]
            p.x, p.y = 32 + i * 32, 64
        for 地 in arg_世.地产[1:]:
            地.经济.业主, 地.经济.等级, 地.经济.连锁 = 0, 0, 0
        for 地 in arg_世.设施[1:]:
            地.业主, 地.等级 = 0, 0
        for i, 地 in enumerate(arg_世.地产[1:5]):
            地.经济.业主, 地.经济.等级 = [0, 1, 1, 2][i], [3, 2, 2, 1][i]
            地.经济.街道名 = b"AI-test"
            地.经济.各级租金 = (0, 1000, 5000, 9000, 12000, 20000)
            地.地价, 地.每级造价 = 1000, 500
            地.x, 地.y = (4000, 4000) if i == 3 else (96 + i * 32, 64)
        arg_世.节点[2].类型索引 = 2001
        arg_世.节点[3].标志 = 5 << 16
        arg_世.节点[4].标志 = 4
        arg_世.监狱名单[0] = 1

    @staticmethod
    def _命令(arg_世: 世界_类, arg_生: random.Random) -> list[str]:
        组 = []
        for 工 in range(1, 14):
            组 += ["r", "s 0", f"e 0 {工} 3 1 0"]
        for 转 in range(8):
            组 += [f"g {转} 1", "v 0", "a 0 4000 4000 100", "a 0 4000 4000 -1"]
        for _ in range(700):
            op = arg_生.choice(
                [
                    "e",
                    "e",
                    "e",
                    "u",
                    "p",
                    "v",
                    "a",
                    "m",
                    "o",
                    "t",
                    "g",
                    "c",
                    "h",
                    "i",
                    "d",
                    "n",
                    "j",
                    "z",
                    "b",
                    "r",
                    "s",
                ]
            )
            槽 = arg_生.randrange(5)
            if op == "e":
                行 = (
                    f"e {槽} {arg_生.randrange(15)} {arg_生.randrange(4)} "
                    f"{arg_生.randrange(1, 6)} {arg_生.choice([0, 1, 4294967295])}"
                )
            elif op == "u":
                行 = (
                    f"u {槽} {arg_生.randrange(4)} {arg_生.randrange(1, 6)} "
                    f"{arg_生.choice([0, 1, 4294967295])}"
                )
            elif op == "p":
                行 = f"p {槽} {arg_生.randrange(17)} {arg_生.randrange(2)}"
            elif op in ("v", "o"):
                行 = f"{op} {槽}"
            elif op == "a":
                行 = (
                    f"a {槽} {arg_生.choice([64, 4000, 65535])} "
                    f"{arg_生.choice([64, 4000, 65535])} "
                    f"{arg_生.choice([-1, 0, 1, 100, 220, 221])}"
                )
            elif op == "m":
                x, y = arg_生.choice([(64, 64), (4000, 4000), (32768, 65535)])
                数 = [x, y, arg_生.choice([-1, 0, 1, 100, 220, 221])]
                for _ in range(16):
                    数 += [
                        x + arg_生.choice([0, 0, -200, -1, 1, 200, 1000]),
                        y + arg_生.choice([0, 0, -200, -1, 1, 200, 1000]),
                        arg_生.choice([0, 1, 2, 2001, 4001, 32769, 65535]),
                    ]
                行 = "m " + " ".join(map(str, 数))
            elif op == "t":
                行 = f"t {arg_生.choice([0, 2001, 2002, 2000 + len(arg_世.地产), 4001])}"
            elif op == "g":
                行 = f"g {arg_生.randrange(256)} {arg_生.choice([1, 2, 100, 2147483647])}"
            elif op == "c":
                数 = [
                    槽,
                    arg_生.choice([0, 1, 2, 4, 6]),
                    arg_生.choice([0, 1, 2, 3, 255]),
                    arg_生.choice([0, 1, 2, 255]),
                    arg_生.choice([0, 1, 2, 3, 128, 255]),
                    *arg_生.choices([-10000, 0, 10000, 100000, 2147483647], k=2),
                    arg_生.choice([0, 300, 65535]),
                    arg_生.choice([-1, 0, 1]),
                    arg_生.choice([0, 1, 128]),
                    arg_生.choice([0, 7, 8, 15, 255]),
                    arg_生.randrange(len(arg_世.节点)),
                    arg_生.randrange(len(arg_世.节点)),
                    arg_生.choice([64, 4000, 65535]),
                    arg_生.choice([64, 4000, 65535]),
                ]
                行 = "c " + " ".join(map(str, 数))
            elif op == "h":
                行 = (
                    f"h {槽} {arg_生.randrange(5)} "
                    f"{arg_生.choice([0, 1, 100, 2147483647, 2147483648, 4294967295])}"
                )
            elif op == "i":
                行 = f"i {槽} {arg_生.randrange(16)} {arg_生.choice([0, 1, 15, 255])}"
            elif op == "d":
                码 = arg_生.choice([2001, 2002, 2003, 4001, 4002, 0])
                行 = (
                    f"d {码} {arg_生.randrange(5)} {arg_生.randrange(6)} {arg_生.randrange(6)} "
                    f"{arg_生.choice([0, 1000, 100000, 2147483647])} "
                    f"{arg_生.choice([0, 500, 10000])}"
                )
            elif op == "n":
                i = arg_生.randrange(1, 9)
                行 = (
                    f"n {i} "
                    f"{arg_生.choice([0, 4, 5, 15, 5 << 16, 16 << 16, 0x40000000, 0x003FFF00])} "
                    f"{arg_生.choice([0, 2001, 2002, 4001])} {i % 8 + 1} {(i - 2) % 8 + 1} "
                    f"{arg_生.choice([0, 7])} 0 {32 + i * 32} 64"
                )
            elif op == "j":
                行 = (
                    f"j {arg_生.randrange(1, 47)} {arg_生.randrange(20)} "
                    f"{arg_生.randrange(1, 9)} {arg_生.randrange(4)}"
                )
            elif op == "z":
                行 = f"z {arg_生.randrange(2)} {arg_生.randrange(9)} {arg_生.randrange(5)}"
            elif op == "b":
                行 = f"b {槽} " + " ".join(map(str, arg_生.choices([0, 0, 0, 1, 128], k=4)))
            elif op == "s":
                行 = f"s {arg_生.randrange(4294967296)}"
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
        工具 = arg_构建.resolve() / "tools-ai-oracle"
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "src"),
                str(Path(__file__).with_name("tools_ai_oracle.cpp")),
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
            "generator_seed": 2026102313,
            "scope": (
                "tool AI decisions, sparse selection and validated-domain private probes; "
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
                    with tempfile.TemporaryDirectory(prefix="rich4-tool-ai-") as 临:
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
                            raise ValueError("道具电脑oracle行数不同")
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
                                Counter(行.split()[4] for 行 in 预期 if 行.split()[3] == "1")
                            ),
                            "unsupported": sum(行.split()[2] == "0" for 行 in 预期),
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
    道具电脑差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
