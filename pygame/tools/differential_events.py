# ◑ 导入
import argparse
import hashlib
import json
import random
import struct
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.events import 事件_类, 事件回调_类, 事件结果_类, 事件选择_类
from rich4.random import 随机数_类
from rich4.save import 存档_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 待选错误_类(RuntimeError):
    """
    测试真实选择边界抛出后的游标与部分状态，不作为正式游戏异常类型。

    更新日志：
    2026.10.23 - 对应测试适配器ChoicePending。
    """


class 事件差分_类:
    """
    逐新闻/命运有效编号、准入、牌堆及回调次序，商业世界仅在临时目录。

    更新日志：
    2026.10.23 - 包含缺依赖、待选择、状态注入和完整DAT/RNG比较。
    """

    @staticmethod
    def _动作(
        arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str, arg_初始: bytes
    ) -> tuple[str, 世界_类]:
        op, *列 = arg_行.split()
        槽, 号, 掩, 选, 目标, 改 = map(int, 列)
        调用: list[int] = []

        def 记(arg_类: int, arg_a: int = 0, arg_b: int = 0, arg_c: int = 0, arg_d: int = 0) -> None:
            调用.extend([arg_类, arg_a, arg_b, arg_c, arg_d])

        def 付款(arg_a: int, arg_b: int, arg_c: int, arg_d: int) -> None:
            记(2, arg_a, arg_b, arg_c, arg_d)
            if 改 and 0 <= arg_a < len(arg_世.玩家) and arg_c & 1:
                arg_世.玩家[arg_a].记录.控制标志 = 0

        def 收容(arg_类: int, arg_a: int, arg_b: int, arg_c: int = 0) -> None:
            记(arg_类, arg_a, arg_b, arg_c)
            if 改:
                人 = 事件_类._取(arg_世.玩家, arg_a)
                setattr(人.状态, {3: "监狱天数", 4: "医院天数", 5: "消失天数"}[arg_类], arg_b)

        def 防御(arg_a: int) -> int:
            记(6, arg_a, 目标)
            if 目标 == -2:
                raise 待选错误_类("choice")
            return 目标

        def 到期(arg_a: int) -> None:
            记(7, arg_a)
            if 改:
                事件_类._取(arg_世.玩家, arg_a).状态.贷款到期 = 0x7EA021F

        def 拍卖(arg_a: int) -> None:
            记(9, arg_a)
            if 选 == -2:
                raise 待选错误_类("choice")

        def 选卡(arg_a: int, arg_b: int) -> int:
            记(10, arg_a, arg_b, 选)
            if 选 == -2:
                raise 待选错误_类("choice")
            return 事件_类._取(arg_世.玩家, arg_b).记录.卡片[0] if 选 == 1 else 31 if 选 == 2 else 0

        钩 = 事件回调_类(
            语音=(lambda *a: 记(1, *a)) if 掩 & 1 else None,
            付款=付款 if 掩 & 2 else None,
            监狱=(lambda *a: 收容(3, *a)) if 掩 & 4 else None,
            医院=(lambda *a: 收容(4, *a)) if 掩 & 8 else None,
            消失=(lambda *a: 收容(5, *a)) if 掩 & 16 else None,
            防御=防御 if 掩 & 32 else None,
            贷款到期=到期 if 掩 & 64 else None,
            卖股=(lambda a, b, c, d: 记(8, a, b, c, int(d))) if 掩 & 128 else None,
            拍卖=拍卖 if 掩 & 256 else None,
            选卡=选卡 if 掩 & 512 else None,
            范围损坏=(lambda a, b, c, d: 记(11, a, b, c, int(d))) if 掩 & 1024 else None,
            更新股票=(lambda a: 记(12, a)) if 掩 & 2048 else None,
            新闻画面=(lambda *a: 记(13, *a)) if 掩 & 4096 else None,
        )
        状态, 返回, 结果, 选择 = 0, -1, 事件结果_类(), 事件选择_类()
        try:
            if op == "n":
                结果 = 事件_类.api_新闻编号(arg_世, arg_随机, 号, 钩)
            elif op == "f":
                结果 = 事件_类.api_命运编号(arg_世, arg_随机, 槽, 号, 钩)
            elif op == "N":
                结果 = 事件_类.api_新闻(arg_世, arg_随机, 钩)
            elif op == "F":
                结果 = 事件_类.api_命运(arg_世, arg_随机, 槽, 钩)
            elif op == "e":
                返回 = int(事件_类.api_新闻可用(arg_世, 号))
            elif op == "g":
                可 = 事件_类.api_命运可用(arg_世, 槽, 号)
                返回 = -1 if 可 is None else 可
            elif op == "s":
                选择 = 事件_类.api_选新闻(arg_世)
            elif op == "t":
                选择 = 事件_类.api_选命运(arg_世, 槽)
            elif op == "r":
                arg_世 = 世界_类.api_从存档(存档_类.api_解码(arg_初始))
            elif op == "u":
                if 槽 == 0:
                    arg_世.新闻游标 = 号
                else:
                    arg_世.命运游标 = 号
            elif op == "d":
                if 槽 == 0:
                    arg_世.新闻牌堆[:] = [号] * 36
                else:
                    arg_世.命运牌堆[:] = [号] * 37
            else:
                raise RuntimeError("未知事件差分操作")
        except 待选错误_类:
            状态 = 3
        except IndexError:
            状态 = 2
        except ValueError:
            状态 = 1
        值 = [
            状态,
            arg_随机.状态,
            int(结果.支持),
            结果.事件,
            结果.地产,
            结果.主体,
            结果.公司,
            结果.数值,
            结果.玩家掩码,
            *结果.玩家金额,
            返回,
            选择.来源,
            选择.事件,
            选择.下一游标,
            选择.跳过,
            len(调用) // 5,
            *调用,
        ]
        return " ".join(map(str, 值)) + "|" + 结果.消息, arg_世

    @staticmethod
    def _设置(arg_世: 世界_类, arg_种: int) -> None:
        for i, 人 in enumerate(arg_世.玩家):
            人.记录.控制标志 = 1 if i == 0 else 2
            人.记录.现金 = [-2147483648, -41, 1000000009, 2147483647][i]
            人.记录.银行 = [2147483647, 1000000009, -1000000009, 0][i]
            人.记录.贷款 = 0 if i & 1 else 10000
            人.记录.交通 = [0, 1, 2, 128][i]
            人.记录.卡片[:] = list(range(1, 16))
            人.记录.道具[:13] = [255 if i == 0 else 9] * 13
            人.记录.点券 = 65530
            人.状态.财运修正 = [0, 75, 150, -100][(i + arg_种) % 4]
            人.状态.其他运修正 = [150, -100, 0, 75][(i + arg_种) % 4]
            人.状态.保险天数 = 1
            人.状态.银行拒绝天数 = 250
            人.状态.酒店天数 = 4
            人.状态.监狱天数 = 人.状态.医院天数 = 127
            for j, 股 in enumerate(人.持仓):
                股.数量 = [0, 1, 1000000009, -1][(i + j) % 4]
        arg_世.监狱名单[:4] = [1, 1, 1, 1]
        arg_世.医院名单[:4] = [1, 1, 1, 1]
        arg_世.卡供应[:] = [255] * 30
        arg_世.道具供应[:] = [255] * 8
        arg_世.头.物价 = [1, 3, 2147483647][arg_种]
        arg_世.股史游标 = [0, -2147483648, 144][arg_种]
        for i, 股 in enumerate(arg_世.股票):
            股.停牌天数 = i % 2
            股.浮点位[1] = 0x41200000
            股.浮点位[2] = struct.unpack("<I", struct.pack("<f", [0.1, 123.456, 1e20][arg_种]))[0]
        for i, 地 in enumerate(arg_世.地产[1:], 1):
            地.经济.业主, 地.经济.等级, 地.经济.连锁 = i % 5, i % 6, i % 2
            地.地价, 地.每级造价 = 100, 65535
        for i, 地 in enumerate(arg_世.设施[1:], 1):
            地.业主, 地.等级, 地.类型 = i % 5, i % 6, 1
            地.地价, 地.每级造价 = 100, 65535
        for i, 司 in enumerate(arg_世.公司[1:], 1):
            司.业主, 司.类型 = i % 4 + 1, 4 if i == 1 else 司.类型
            司.资金, 司.资金变化, 司.股票索引 = 2147483647, 2147483647, (i - 1) % 12

    @staticmethod
    def _命令(arg_生: random.Random) -> list[str]:
        组 = []
        for 号 in range(38):
            组.append(f"e 0 {号} 8191 1 0 1")
        for 槽 in range(5):
            for 号 in range(39):
                组.append(f"g {槽} {号} 8191 1 {槽} 1")
        for op, 数量 in [("n", 36), ("f", 49)]:
            for 槽 in range(1 if op == "n" else 4):
                for 号 in range(数量):
                    组 += ["r 0 0 0 0 0 0", f"{op} {槽} {号} 8191 1 {槽} 1"]
        for _ in range(200):
            op = arg_生.choice(["n", "f", "N", "F", "s", "t", "r", "u", "d"])
            槽, 号 = arg_生.randrange(5), arg_生.randrange(55)
            掩 = arg_生.choice([8191, 8191, 0, arg_生.randrange(8192)])
            组.append(
                f"{op} {槽} {号} {掩} {arg_生.choice([-2, 0, 1, 2])} "
                f"{arg_生.choice([-2, -1, 0, 1, 2, 3, 255])} {arg_生.randrange(2)}"
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
        工具 = arg_构建.resolve() / "events-oracle"
        编译 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("events_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            text=True,
            capture_output=True,
        )
        if 编译.returncode:
            raise RuntimeError(编译.stderr)
        报告 = {
            "reference": 版本,
            "generator_seed": 2026102309,
            "scope": (
                "news/fortune module actions with observer/injector hooks; "
                "not complete finance, area damage or game play"
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
                    命令 = cls._命令(生)
                    预期, 字节 = [], []
                    for 行 in 命令:
                        返回, 世 = cls._动作(世, 随机, 行, 原)
                        预期.append(返回)
                        字节.append(世.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-events-") as 临:
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
                            raise ValueError("事件oracle行数不同")
                        摘 = hashlib.sha256()
                        for i, (令, c, p, 存) in enumerate(zip(命令, 行组, 预期, 字节)):
                            if c != p:
                                raise ValueError(
                                    f"图{图}/种{种}/步{i}/{令} 返回/RNG/钩子不同：{c}/{p}"
                                )
                            实 = (路 / "out" / f"{i}.dat").read_bytes()
                            if 存 != 实:
                                首 = next(j for j, (a, b) in enumerate(zip(存, 实)) if a != b)
                                raise ValueError(
                                    f"图{图}/种{种}/步{i}/{令} DAT不同offset={首} "
                                    f"Python={存[首]} C++={实[首]}"
                                )
                            摘.update(存)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种,
                            "actions": len(命令),
                            "exceptions": dict(Counter(行.split()[0] for 行 in 预期)),
                            "unsupported": sum(
                                令.split()[0] in ("n", "f", "N", "F")
                                and 行.split()[2] == "0"
                                and 行.split()[0] == "0"
                                for 令, 行 in zip(命令, 预期)
                            ),
                            "applied_news": sorted(
                                {
                                    int(行.split()[3])
                                    for 令, 行 in zip(命令, 预期)
                                    if 令[0] in ("n", "N") and 行.split()[2] == "1"
                                }
                            ),
                            "applied_fortune": sorted(
                                {
                                    int(行.split()[3])
                                    for 令, 行 in zip(命令, 预期)
                                    if 令[0] in ("f", "F") and 行.split()[2] == "1"
                                }
                            ),
                            "state_sha256": 摘.hexdigest(),
                            "input_sha256": hashlib.sha256("\n".join(命令).encode()).hexdigest(),
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
    事件差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
