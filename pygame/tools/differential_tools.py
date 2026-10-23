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
from rich4.random import 随机数_类
from rich4.save import 存档_类
from rich4.tools import 道具_类, 道具回调_类, 道具结果_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 道具差分_类:
    """
    八图道具动作、选择位、回调次序和完整世界差分，不假装完整会话恢复。

    更新日志：
    2026.10.23 - 包含原世界恢复测试、附身对象传送和异常字段。
    """

    @staticmethod
    def _动作(
        arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str, arg_原: bytes
    ) -> tuple[str, 世界_类]:
        op, *列 = arg_行.split()
        槽, 物, 目, 目的地, 掩, 恢复值, 新玩家, 改 = map(int, 列)
        调用: list[int] = []

        def 记(arg_类: int, arg_a: int = 0, arg_b: int = 0, arg_c: int = 0) -> None:
            调用.extend([arg_类, arg_a, arg_b, arg_c])

        def 机器人(arg_a: int) -> None:
            记(1, arg_a)
            if 改:
                人 = 道具_类._取(arg_世.玩家, arg_a).记录
                人.点券 = (人.点券 + 1) & 65535

        def 遥控(arg_a: int, arg_b: int) -> None:
            记(2, arg_a, arg_b)
            if 改:
                arg_世.头.当前玩家 = 新玩家

        def 恢复() -> bool:
            记(3, 恢复值, 新玩家)
            if 恢复值:
                arg_世.头.当前玩家 = 新玩家
            return bool(恢复值)

        def 传送前(arg_a: int) -> None:
            记(6, arg_a)
            if 改:
                arg_世.头.当前玩家 = 新玩家

        钩 = 道具回调_类(
            机器人=机器人 if 掩 & 1 else None,
            遥控骰=遥控 if 掩 & 2 else None,
            恢复上次=恢复 if 掩 & 4 else None,
            升级=(lambda a: 记(4, a)) if 掩 & 8 else None,
            爆炸=(lambda a, b, c: 记(5, a, int(b), c)) if 掩 & 16 else None,
            传送前=传送前 if 掩 & 32 else None,
            语音=(lambda *a: 记(7, *a)) if 掩 & 64 else None,
        )
        状态, 返回, 结果 = 0, 0, 道具结果_类()
        try:
            if op == "u":
                结果 = 道具_类.api_使用(arg_世, arg_随机, 槽, 物, 目, 目的地, 钩)
            elif op == "s":
                返回 = 道具_类.api_选择位(物, 目)
            elif op == "d":
                返回 = int(道具_类.api_下车(arg_世, 槽))
            elif op == "r":
                arg_世 = 世界_类.api_从存档(存档_类.api_解码(arg_原))
            else:
                raise RuntimeError("未知道具测试操作")
        except IndexError:
            状态 = 2
        except ValueError:
            状态 = 1
        值 = [状态, arg_随机.状态, int(结果.支持), int(结果.已应用), 返回, len(调用) // 4, *调用]
        return " ".join(map(str, 值)) + "|" + 结果.消息, arg_世

    @staticmethod
    def _设置(arg_世: 世界_类, arg_条件: int) -> None:
        for i, 人 in enumerate(arg_世.玩家):
            人.记录.控制标志 = [1, 2, 0, 2][i]
            人.记录.道具[:13] = [2] * 13
            人.记录.道具[4] = 人.记录.道具[5] = 255 if arg_条件 == 1 else 2
            人.记录.交通 = [0, 2, 31, 128][(i + arg_条件) % 4]
            人.记录.骰数 = 3
            人.记录.方向 = 255 if arg_条件 == 2 else i * 2
            人.记录.点券 = 65535
        arg_世.道具供应[:] = [255] * 8
        for i, 地 in enumerate(arg_世.地产[1:], 1):
            地.经济.业主 = 1 if i % 2 else 0
            地.经济.等级 = 3 if i % 2 else 0
            地.经济.连锁 = i % 2
            地.到期日, 地.已移除建筑 = 0x7EA021F, 0xFFFFFFF9
        for i, 地 in enumerate(arg_世.设施[1:], 1):
            地.业主, 地.等级, 地.类型 = (1, 3, 1) if i % 2 else (0, 0, 0)
            地.到期日, 地.已移除建筑 = 0x7EA021F, 0x80000000
        for i, 物 in enumerate(arg_世.物件):
            物.节点 = 0 if i >= 16 else 2
            物.附身玩家 = 2 if i == 0 and arg_条件 == 1 else 0
        arg_世.节点[1].标志 &= 0xFF0000FF
        if arg_条件 == 2:
            arg_世.节点[1].邻居[0] = 65535
        for 人 in arg_世.特殊角色:
            人.节点, 人.方向 = 2, 7

    @staticmethod
    def _命令(arg_世: 世界_类, arg_生: random.Random) -> list[str]:
        组 = []
        for 物 in range(16):
            for 源 in [0, 1, 1999, 2000, 2001, 3999, 4000, 4001, 5999, 6000, 0x8001, 0x8100, 65535]:
                组.append(f"s 0 {物} {源} 0 127 1 1 1")
        for 槽 in range(4):
            for 物 in range(1, 14):
                目 = (
                    6
                    if 物 == 8
                    else 2001
                    if 物 == 9 and len(arg_世.地产) > 1
                    else 4001
                    if 物 == 9
                    else 0x8001
                    if 物 == 11
                    else 1
                )
                组.extend(["r 0 0 0 0 0 0 0 0", f"u {槽} {物} {目} 1 127 1 1 1"])
        特 = [
            0,
            1,
            2,
            3,
            65535,
            2000,
            4000,
            6000,
            *[0x8000 | (1 << i) for i in range(8)],
            *[0x8000 | (i << 8) for i in [0, 1, 11, 13, 14, 16, 17, 27, 37, 46, 47, 63]],
        ]
        特 += [2000 + i for i in range(1, min(len(arg_世.地产), 4))]
        特 += [4000 + i for i in range(1, min(len(arg_世.设施), 4))]
        for _ in range(400):
            op = arg_生.choice(["u", "u", "u", "d", "s", "r"])
            槽, 物 = arg_生.randrange(-1, 5), arg_生.randrange(16)
            目 = arg_生.choice(特 + [arg_生.randrange(1, len(arg_世.节点))])
            目的地 = arg_生.choice(特 + [arg_生.randrange(1, len(arg_世.节点))])
            掩 = arg_生.choice([127, 127, 0, arg_生.randrange(128)])
            组.append(
                f"{op} {槽} {物} {目} {目的地} {掩} {arg_生.randrange(2)} "
                f"{arg_生.randrange(4)} {arg_生.randrange(2)}"
            )
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
        工具 = arg_构建.resolve() / "tools-oracle"
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("tools_oracle.cpp")),
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
            "generator_seed": 2026102310,
            "scope": (
                "tool module, selection flags, callback observer/injector; "
                "no real robot, rewind or blasts"
            ),
            "status": "running",
            "episodes": [],
        }
        生 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_素材 / "map.mkf")
            for 图 in range(8):
                for 条件, 种 in enumerate((0, 1, 0xFFFFFFFF)):
                    世 = 世界_类.api_从地图(
                        包.api_解码(图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                    )
                    cls._设置(世, 条件)
                    原, 随机 = 世.api_导出(), 随机数_类(种)
                    命令, 预期, 字节 = cls._命令(世, 生), [], []
                    for 行 in 命令:
                        返回, 世 = cls._动作(世, 随机, 行, 原)
                        预期.append(返回)
                        字节.append(世.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-tools-") as 临:
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
                            raise ValueError("道具oracle行数不同")
                        摘 = hashlib.sha256()
                        for i, (令, c, p, 存) in enumerate(zip(命令, 行组, 预期, 字节)):
                            if c != p:
                                raise ValueError(
                                    f"图{图}/种{种}/步{i}/{令} 返回/RNG/钩子不同：{c}/{p}"
                                )
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
                            "applied_tools": dict(
                                Counter(
                                    令.split()[2]
                                    for 令, 行 in zip(命令, 预期)
                                    if 令[0] == "u" and 行.split()[3] == "1"
                                )
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
    道具差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
