# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.random import 随机数_类
from rich4.services import 商店_类, 服务_类, 魔法回调_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 服务差分_类:
    """
    每步比较回值、货架、RNG、回调顺序和完整 DAT；回调观测不冒充会话规则。

    更新日志：
    2026.10.23 - 覆盖八图、三种库存条件和商店/魔法全部公开规则入口。
    """

    def __init__(self, arg_世: 世界_类, arg_种子: int) -> None:
        self.世界 = arg_世
        self.随机 = 随机数_类(arg_种子)
        self.店 = 商店_类()

    def api_动作(self, arg_行: str) -> list[int]:
        部分 = arg_行.split()
        op = 部分[0]
        数 = list(map(int, 部分[1:]))
        状态 = 值 = 其他 = 0
        目标: list[int] = []
        事件: list[tuple[int, int, int, int]] = []
        世, 随机 = self.世界, self.随机
        try:
            if op == "o":
                self.店 = 服务_类.api_开店(世, 随机, *数)
            elif op == "b":
                值 = int(服务_类.api_买卡(世, self.店, *数))
            elif op == "t":
                值 = int(服务_类.api_买道具(世, self.店, *数))
            elif op == "s":
                值 = int(服务_类.api_卖卡(世, self.店, *数))
            elif op == "u":
                值 = int(服务_类.api_卖道具(世, self.店, *数))
            elif op == "c":
                服务_类.api_关店(世, self.店, *数)
            elif op == "r":
                值 = 服务_类.api_随机卡(世, 随机, *数)
            elif op == "q":
                值 = 服务_类.api_随机道具(世, 随机, *数)
            elif op == "m":
                目标 = 服务_类.api_魔法目标(世, *数)
            elif op == "a":
                选择 = 服务_类.api_电脑魔法(世, 随机, *数)
                值, 其他 = (-1, -1) if 选择 is None else (选择.类别, 选择.效果)
            elif op == "x":
                演员, 效果, 掩码, 转移, 数量, *目标组 = 数
                if 数量 != len(目标组):
                    raise RuntimeError("测试目标长度不匹配")
                回调 = 魔法回调_类()
                if 掩码 & 1:
                    回调.命运 = lambda p: 事件.append((0, p, 0, 0))
                if 掩码 & 2:

                    def 防御(arg_p: int) -> int:
                        结果 = arg_p if 转移 == -2 else 转移
                        事件.append((1, arg_p, 结果, 0))
                        return 结果

                    回调.防御 = 防御
                if 掩码 & 4:
                    回调.敌意 = lambda p, q, n: 事件.append((2, p, q, n))
                if 掩码 & 8:
                    回调.监狱 = lambda p, n: 事件.append((3, p, n, 0))
                if 掩码 & 16:
                    回调.医院 = lambda p, n: 事件.append((4, p, n, 0))
                if 掩码 & 32:
                    回调.升级 = lambda p: 事件.append((5, p, 0, 0))
                if 掩码 & 64:
                    回调.降级 = lambda p: 事件.append((6, p, 0, 0))
                if 掩码 & 128:
                    回调.拍卖 = lambda p, q: 事件.append((7, p, q, 0))
                if 掩码 & 256:
                    回调.转向 = lambda p: 事件.append((8, p, 0, 0))
                值 = int(服务_类.api_施法(世, 随机, 演员, 目标组, 效果, 回调))
            else:
                raise RuntimeError("未知测试动作")
        except IndexError:
            状态 = 2
        except ValueError:
            状态 = 1
        店 = self.店
        return [
            状态,
            值,
            其他,
            随机.状态,
            len(目标),
            *目标,
            len(事件),
            *(n for e in 事件 for n in e),
            店.收入,
            店.赠卡,
            店.赠道具,
            int(店.已关闭),
            len(店.卡片),
            *店.卡片,
            len(店.道具),
            *店.道具,
        ]

    @staticmethod
    def _设置(arg_世: 世界_类, arg_模式: int) -> None:
        for i, 玩家 in enumerate(arg_世.玩家):
            p = 玩家.记录
            p.控制标志 = [1, 2, 3, 0][i]
            p.点券 = [0, 99, 1000, 65530][i]
            p.节点 = i + 1
            p.交通 = [0, 0x81, 2, 3][i]
            p.卡片[:] = [(j * 7 + i) % 30 + 1 for j in range(15)]
            p.道具[:] = [0, 1, 2, 8, 9, 255, 0, 1, 2, 3, 4, 5, 6, 7, 8]
            玩家.状态.救援策略 = i % 3
            玩家.状态.停留天数 = 255
            玩家.状态.神明信息 = i
        arg_世.节点[1].类型索引 = 2001
        arg_世.节点[2].类型索引 = 4001
        arg_世.节点[3].类型索引 = 6001
        arg_世.节点[4].类型索引 = 5999
        arg_世.公司[1].业主 = 1
        arg_世.公司[1].资金 = arg_世.公司[1].资金变化 = 2147483647
        if len(arg_世.地产) > 1:
            arg_世.地产[1].经济.业主 = 2
            arg_世.地产[1].经济.等级 = 3
        if len(arg_世.设施) > 1:
            arg_世.设施[1].业主 = 3
            arg_世.设施[1].等级 = 1
        if arg_模式 == 1:
            arg_世.卡供应[:] = [0] * 30
            arg_世.道具供应[:] = [0] * 8
            arg_世.玩家[1].状态.酒店天数 = 2
            arg_世.玩家[2].状态.医院天数 = 3
        elif arg_模式 == 2:
            arg_世.卡供应[:] = [255, 1] + [0] * 28
            arg_世.道具供应[:] = [255, 1] + [0] * 6
            for 玩家 in arg_世.玩家:
                玩家.记录.现金 = -1000
                玩家.记录.银行 = -1
                玩家.记录.贷款 = 0

    @staticmethod
    def _命令(arg_生成: random.Random) -> list[str]:
        命令 = [f"m {i}" for i in range(12)]
        for 效果 in range(12):
            命令.extend([f"x 0 {效果} 0 -2 0", f"x 0 {效果} 511 -2 4 0 1 2 3"])
        命令 += ["o 0 6001", "c 6001", "c 6001", "o 1 0", "o 2 0", "o 0 0"]
        for _ in range(258):
            op = arg_生成.choice("ooobttssuurqmax")
            p = arg_生成.randrange(5)
            if op == "o":
                命令.append(f"o {p} {arg_生成.choice([0, 0, 6001, 6000, 7999])}")
            elif op in "bts":
                命令.append(f"{op} {p} {arg_生成.randrange(33 if op != 't' else 15)}")
            elif op == "u":
                命令.append(
                    f"u {p} {arg_生成.randrange(15)} {arg_生成.choice([0, 1, 2, 9, 255, 256])}"
                )
            elif op in "rqma":
                命令.append(f"{op} {arg_生成.randrange(14) if op == 'm' else p}")
            else:
                目标 = [arg_生成.randrange(5) for _ in range(arg_生成.randrange(6))]
                效果 = arg_生成.randrange(14)
                掩码 = arg_生成.choice([0, 511, 511, 511 ^ (1 << arg_生成.randrange(9))])
                转移 = arg_生成.choice([-2, -1, 0, 3])
                尾 = " ".join(map(str, 目标))
                命令.append(f"x {p} {效果} {掩码} {转移} {len(目标)} {尾}")
        return 命令

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_地图包: Path, arg_报告: Path) -> None:
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
        工具 = arg_构建.resolve() / "services-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("services_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "scope": "service module, hook observation only; not a game session",
            "generator_seed": 2026102303,
            "status": "running",
            "episodes": [],
        }
        生成 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_地图包)
            for 图 in range(8):
                数据 = 包.api_解码(图 * 2 + 1)
                for 模式 in range(3):
                    种子 = [0, 1, 0xFFFFFFFF][模式]
                    世 = 世界_类.api_从地图(
                        数据, 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种子)
                    )
                    cls._设置(世, 模式)
                    原 = 世.api_导出()
                    动作 = cls._命令(生成)
                    输入 = "\n".join(动作) + "\n"
                    with tempfile.TemporaryDirectory(prefix="rich4-service-") as 临时:
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
                            raise ValueError("服务 oracle 行数不同")
                        状态 = cls(世, 种子)
                        摘要 = hashlib.sha256()
                        拒绝数 = 0
                        for i, (命令, cpp行) in enumerate(zip(动作, 行)):
                            预期 = 状态.api_动作(命令)
                            if list(map(int, cpp行.split())) != 预期:
                                raise ValueError(
                                    f"图{图} 模式{模式} 动作{i} {命令} "
                                    f"回值/RNG/货架/钩子不同：{cpp行}/{预期}"
                                )
                            字节 = 世.api_导出()
                            if 字节 != (路径 / "out" / f"{i}.dat").read_bytes():
                                raise ValueError(f"图{图} 模式{模式} 动作{i} {命令} DAT不同")
                            摘要.update(字节)
                            拒绝数 += int(预期[0] != 0)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "mode": 模式,
                            "seed": 种子,
                            "steps": len(动作),
                            "exception_rejections": 拒绝数,
                            "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
                            "initial_sha256": hashlib.sha256(原).hexdigest(),
                            "states_sha256": 摘要.hexdigest(),
                        }
                    )
                print(f"[完成] 地图{图}三组商店与魔法动作一致。", flush=True)
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
    服务差分_类.api_执行(选项.source, 选项.build, 选项.map, 选项.report)
