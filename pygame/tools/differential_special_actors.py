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
from rich4.numeric import 数值范围错误_类
from rich4.random import 随机数_类
from rich4.special_actors import 特殊回调_类, 特殊结果_类, 特殊行动_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 特殊差分_类:
    """
    八图逐动作比较；钩子只观察与注入可复现状态变化，不伪装完整游戏结算。

    更新日志：
    2026.10.23 - 比较返回、异常、回调顺序、RNG和完整DAT，含全部状态字节。
    """

    @staticmethod
    def _动作(arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str) -> str:
        op, *列 = arg_行.split()
        槽, 节, 前, 主, 闲, 旗, 睡, 梦, 停, 龟, 节旗, 码, 类, 掩, 终, 改, 靠 = map(int, 列)
        if 4 <= 槽 <= 7:
            人 = arg_世.特殊角色[槽 - 4]
            人.节点, 人.上次节点, 人.业主, 人.不活跃状态 = 节, 前, 主, 闲
            人.标志, 人.睡眠天数, 人.梦游天数, 人.停留天数, 人.龟行天数 = 旗, 睡, 梦, 停, 龟
        if 0 <= 节 < len(arg_世.节点):
            arg_世.节点[节].标志, arg_世.节点[节].类型索引 = 节旗, 码
        arg_世.物件[0].种类 = 类
        调用: list[int] = []

        def 记(arg_类: int, arg_a: int = 0, arg_b: int = 0, arg_c: int = 0, arg_d: int = 0) -> None:
            调用.extend([arg_类, arg_a, arg_b, arg_c, arg_d])

        def 移除(arg_号: int) -> None:
            记(2, arg_号)
            if 改 and 0 <= 节 < len(arg_世.节点):
                arg_世.节点[节].标志 &= 0xFF00FFFF

        def 收容(arg_类: int, arg_槽: int, arg_天: int) -> None:
            记(arg_类, arg_槽, arg_天)
            if 改:
                arg_世.特殊角色[arg_槽 - 4].不活跃状态 = 2

        次 = 0

        def 结束() -> bool:
            nonlocal 次
            已终 = 次 >= 终
            次 += 1
            记(6, int(已终))
            return 已终

        def 步后(arg_槽: int, arg_节: int) -> None:
            记(7, arg_槽, arg_节)
            if 改 and arg_节 % 17 == 0:
                arg_世.特殊角色[arg_槽 - 4].不活跃状态 = 1

        钩 = 特殊回调_类(
            付款=(lambda *a: 记(1, *a)) if 掩 & 1 else None,
            移除物件=移除 if 掩 & 2 else None,
            监狱=(lambda *a: 收容(3, *a)) if 掩 & 4 else None,
            医院=(lambda *a: 收容(4, *a)) if 掩 & 8 else None,
            语音=(lambda *a: 记(5, *a)) if 掩 & 16 else None,
            游戏结束=结束 if 掩 & 32 else None,
            步后=步后 if 掩 & 64 else None,
        )
        状态, 返回, 结果 = 0, 0, 特殊结果_类()
        try:
            if op == "m":
                返回 = 特殊行动_类.api_单步(arg_世, arg_随机, 槽)
            elif op == "i":
                结果 = 特殊行动_类.api_交互(arg_世, arg_随机, 槽, bool(靠), 钩)
            elif op == "t":
                结果 = 特殊行动_类.api_回合(arg_世, arg_随机, 槽, 钩)
            elif op == "a":
                特殊行动_类.api_老化(特殊行动_类._角色(arg_世, 槽))
            else:
                raise RuntimeError("未知特殊角色测试操作")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        值 = [
            状态,
            arg_随机.状态,
            int(结果.支持),
            int(结果.停止移动),
            结果.计划步数,
            结果.已走步数,
            返回,
            len(结果.效果),
        ]
        for 项 in 结果.效果:
            值.extend([项.种类, 项.角色, 项.目标, 项.金额, 项.节点])
        值.extend([len(调用) // 5, *调用])
        return " ".join(map(str, 值)) + "|" + 结果.消息

    @staticmethod
    def _设置(arg_世: 世界_类) -> None:
        arg_世.头.物价 = 2147483647
        for i, 人 in enumerate(arg_世.玩家):
            人.记录.控制标志 = 2 if i != 2 else 0
            人.记录.点券 = 65530 - i
            人.记录.银行 = [-2147483648, 10003, 0, 2147483647][i]
            人.记录.卡片[:] = list(range(1, 16))
            人.记录.道具[:13] = [9 if i == 0 else 0] * 13
        arg_世.卡供应[:] = [255] * 30
        arg_世.道具供应[:] = [5] * 8
        for i, 地 in enumerate(arg_世.地产[1:]):
            地.经济.业主, 地.已移除建筑 = i % 4 + 1, 0xFFFFFFF9
        for i, 地 in enumerate(arg_世.设施[1:]):
            地.业主, 地.已移除建筑 = i % 4 + 1, 0x80000001
        for 司 in arg_世.公司[1:]:
            司.业主, 司.资金 = 2, -17

    @staticmethod
    def _命令(arg_世: 世界_类, arg_生: random.Random, arg_i: int) -> str:
        槽 = 4 + arg_i // 256 if arg_i < 1024 else arg_生.choice([4, 5, 6, 7, 3, 8])
        op = "a" if arg_i < 1024 else arg_生.choice(["i", "i", "i", "t", "m"])
        节 = arg_生.randrange(1, len(arg_世.节点))
        前 = arg_生.choice([0, 65535, *arg_世.节点[节].邻居])
        类 = arg_生.randrange(21)
        节旗 = arg_生.choice([0, 4, 5, 14]) | arg_生.randrange(16) << 8
        节旗 |= (1 << 16) if 类 else 0
        节旗 |= arg_生.randrange(16) << 27
        码组 = [0, 2000, 4000, 6000, 7999]
        if len(arg_世.地产) > 1:
            码组.append(2000 + arg_生.randrange(1, len(arg_世.地产)))
        if len(arg_世.设施) > 1:
            码组.append(4000 + arg_生.randrange(1, len(arg_世.设施)))
        if len(arg_世.公司) > 1:
            码组.append(6000 + arg_生.randrange(1, len(arg_世.公司)))
        状态 = (
            [arg_i % 256] * 4
            if op == "a"
            else [arg_生.choice([0, 0, 0, 1, 2, 128, 255]) for _ in range(4)]
        )
        if op == "i":
            状态[1] = arg_生.choice([0, 0, 0, 128])
        return " ".join(
            map(
                str,
                [
                    op,
                    槽,
                    节,
                    前,
                    arg_生.choice([0, 1, 2, 3, 4, 255]),
                    arg_生.choice([0, 0, 0, 2]),
                    arg_生.choice([0, 1, 2, 129, 130]),
                    *状态,
                    节旗,
                    arg_生.choice(码组),
                    类,
                    arg_生.choice([127, 127, 127, 0, arg_生.randrange(128)]),
                    arg_生.randrange(4),
                    arg_生.randrange(2),
                    arg_生.randrange(2),
                ],
            )
        )

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
        工具 = arg_构建.resolve() / "special-actors-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("special_actors_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告 = {
            "reference": 版本,
            "generator_seed": 2026102307,
            "scope": (
                "special actor module, observing/injecting callbacks only; "
                "not game finance, UI or long play"
            ),
            "status": "running",
            "episodes": [],
        }
        生 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_素材 / "map.mkf")
            for 图 in range(8):
                for 种 in [0, 1, 0xFFFFFFFF]:
                    世 = 世界_类.api_从地图(
                        包.api_解码(图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                    )
                    cls._设置(世)
                    原, 随机 = 世.api_导出(), 随机数_类(种)
                    命令, 预期, 字节 = [], [], []
                    for i in range(1800):
                        行 = cls._命令(世, 生, i)
                        命令.append(行)
                        预期.append(cls._动作(世, 随机, 行))
                        字节.append(世.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-npc-") as 临:
                        路 = Path(临)
                        (路 / "input.dat").write_bytes(原)
                        cpp = subprocess.run(
                            [str(工具), str(路 / "input.dat"), str(路 / "out"), str(种)],
                            input="\n".join(命令) + "\n",
                            text=True,
                            check=True,
                            capture_output=True,
                        )
                        行组 = cpp.stdout.splitlines()
                        if len(行组) != len(命令):
                            raise ValueError("NPC oracle行数不同")
                        摘 = hashlib.sha256()
                        for i, (令, cp, py, 存) in enumerate(zip(命令, 行组, 预期, 字节)):
                            if cp != py:
                                raise ValueError(
                                    f"图{图}/种{种}/步{i}/{令} 返回/RNG/回调不同：{cp}/{py}"
                                )
                            if 存 != (路 / "out" / f"{i}.dat").read_bytes():
                                raise ValueError(f"图{图}/种{种}/步{i}/{令} 完整DAT不同")
                            摘.update(存)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种,
                            "actions": len(命令),
                            "status_byte_cases": 1024,
                            "exceptions": sum(行.startswith(("1 ", "2 ")) for 行 in 预期),
                            "unsupported": sum(行.split()[2] == "0" for 行 in 预期),
                            "effect_kinds": dict(
                                Counter(
                                    int(项[8 + 5 * j])
                                    for 行 in 预期
                                    for 项 in [行.split("|")[0].split()]
                                    for j in range(int(项[7]))
                                )
                            ),
                            "moved_steps": sum(int(行.split()[5]) for 行 in 预期),
                            "input_sha256": hashlib.sha256("\n".join(命令).encode()).hexdigest(),
                            "state_sha256": 摘.hexdigest(),
                        }
                    )
                    print(f"map={图} seed={种} actions={len(命令)} matched", flush=True)
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
                    "actions": sum(组["actions"] for 组 in 报告["episodes"]),
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
    特殊差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
