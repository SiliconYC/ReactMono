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
from rich4.gods import 神明_类, 神明回调_类, 神明结果_类, 金钱转盘_类
from rich4.random import 随机数_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 神明差分_类:
    """
    原数字转盘逐帧与八图神明模块逐动作差分，钩子仅观察/注入测试状态。

    更新日志：
    2026.10.23 - 保存完整DAT/RNG/回值/顺序哈希，商业素材不进入报告。
    """

    @staticmethod
    def _动作(arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str) -> str:
        op, *列 = arg_行.split()
        槽, 物号, 节, 类, 神, 附, 交, 缺, 节旗, 码, 主, 级, 价, 租, 钱, 升, 掩, 终, 改, 修, 自动 = (
            map(int, 列)
        )
        if 0 <= 槽 < len(arg_世.玩家):
            人 = arg_世.玩家[槽]
            人.记录.节点, 人.记录.交通 = 节, 交
            人.状态.神明信息, 人.状态.酒店天数, 人.状态.附身炸弹 = 神, 缺, 0
            人.状态.神运修正 = 人.状态.财运修正 = 人.状态.其他运修正 = 修
        if 1 <= 物号 <= len(arg_世.物件):
            物 = arg_世.物件[物号 - 1]
            物.种类, 物.附身玩家, 物.节点 = 类, 附, 节
        if 0 <= 节 < len(arg_世.节点):
            arg_世.节点[节].标志, arg_世.节点[节].类型索引 = 节旗, 码
        if 2000 < 码 < 4000 and 码 - 2000 < len(arg_世.地产):
            地 = arg_世.地产[码 - 2000]
            地.经济.业主, 地.经济.等级, 地.地价 = 主, 级, 价
        if 4000 < 码 < 6000 and 码 - 4000 < len(arg_世.设施):
            地 = arg_世.设施[码 - 4000]
            地.业主, 地.等级, 地.地价 = 主, 级, 价
        arg_世.租约模式 = 租
        调用: list[int] = []

        def 记(arg_类: int, arg_a: int = 0, arg_b: int = 0, arg_c: int = 0, arg_d: int = 0) -> None:
            调用.extend([arg_类, arg_a, arg_b, arg_c, arg_d])

        def 移除(arg_号: int) -> None:
            记(1, arg_号)
            if 改:
                for 玩家 in arg_世.玩家:
                    if 玩家.状态.神明信息 == arg_号:
                        玩家.状态.神明信息 = 0
                物 = 神明_类._取(arg_世.物件, arg_号 - 1)
                物.节点 = 物.附身玩家 = 0

        def 金额(arg_类: int) -> int:
            金 = 神明_类.api_自动金额(arg_类, arg_随机) if 自动 else 钱
            记(2, arg_类, 金)
            return 金

        次 = 0

        def 结束() -> bool:
            nonlocal 次
            已终 = 次 >= 终
            次 += 1
            记(4, int(已终))
            return 已终

        def 医院(arg_槽: int, arg_天: int) -> None:
            记(5, arg_槽, arg_天)
            if 改:
                arg_世.玩家[arg_槽].状态.医院天数 = arg_天

        钩 = 神明回调_类(
            移除物件=移除 if 掩 & 1 else None,
            金额=金额 if 掩 & 2 else None,
            付款=(lambda *a: 记(3, *a)) if 掩 & 4 else None,
            游戏结束=结束 if 掩 & 8 else None,
            医院=医院 if 掩 & 16 else None,
            语音=(lambda *a: 记(6, *a)) if 掩 & 32 else None,
            升级=(lambda a: 记(7, a, 升) or 升) if 掩 & 64 else None,
            降级=(lambda a: 记(8, a)) if 掩 & 128 else None,
            敌意=(lambda *a: 记(9, *a)) if 掩 & 256 else None,
            现身=(lambda *a: 记(10, *a)) if 掩 & 512 else None,
            到达=(lambda *a: 记(11, *a)) if 掩 & 1024 else None,
            离开=(lambda *a: 记(12, *a)) if 掩 & 2048 else None,
            声音=(lambda *a: 记(13, *a)) if 掩 & 4096 else None,
            狗=(lambda a, b: 记(14, a, int(b))) if 掩 & 8192 else None,
        )
        状态, 返回, 结果 = 0, 0, 神明结果_类()
        try:
            if op == "a":
                结果 = 神明_类.api_附身(arg_世, arg_随机, 槽, 物号, 节, 钩)
            elif op == "d":
                结果 = 神明_类.api_脱离(arg_世, 槽, 钩)
            elif op == "t":
                结果 = 神明_类.api_接触(arg_世, arg_随机, 槽, 物号, bool(升 & 1), 钩)
            elif op == "p":
                结果 = 神明_类.api_地产后(arg_世, 槽, 节, 钩)
            elif op == "b":
                结果 = 神明_类.api_购地后(arg_世, arg_随机, 槽, 节, 钩)
            elif op == "q":
                返回 = int(神明_类.api_可附身(arg_世, 物号))
            else:
                raise RuntimeError("未知神明测试操作")
        except IndexError:
            状态 = 2
        except ValueError:
            状态 = 1
        值 = [
            状态,
            arg_随机.状态,
            int(结果.支持),
            int(结果.已应用),
            int(结果.停止移动),
            返回,
            len(调用) // 5,
            *调用,
        ]
        return " ".join(map(str, 值)) + "|" + 结果.消息

    @staticmethod
    def _命令(arg_世: 世界_类, arg_生: random.Random, arg_i: int) -> str:
        生 = arg_生
        op = 生.choice(["a", "a", "d", "t", "t", "p", "p", "b", "q"])
        槽, 物, 节 = (
            生.choice([0, 1, 2, 3, 4]),
            生.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 27, 37, 46, 47]),
            生.choice([0, 1, 1, 1, 65535]),
        )
        类, 神, 附, 交, 缺 = (
            生.randrange(21),
            生.choice([0, 0, 1, 3, 4, 5, 9, 10, 12, 16, 255]),
            生.choice([0, 0, 0, 1]),
            生.choice([0, 1, 2, 3, 128, 255]),
            生.choice([0, 0, 0, 1, 128]),
        )
        码组 = [0, 2000, 4000, 6000, 7999]
        if len(arg_世.地产) > 1:
            码组.append(2001)
        if len(arg_世.设施) > 1:
            码组.append(4001)
        码 = 生.choice(码组)
        主, 级, 价, 租 = (
            生.randrange(5),
            生.randrange(6),
            生.choice([0, 1, 1000, 32749, 65535]),
            生.randrange(8),
        )
        钱 = 生.choice([-2147483648, -1, 0, 50, 51, 100, 101, 701, 5000, 9000, 2147483647])
        升, 掩, 终, 改, 修, 自动 = (
            生.choice([0, 1, 128, 129]),
            生.choice([16383, 16383, 16383, 0, 生.randrange(16384)]),
            生.choice([0, 1, 2, 99]),
            生.randrange(2),
            生.choice([-32768, -32700, 0, 32700, 32767]),
            生.randrange(2),
        )
        if arg_i < 76:
            op, 槽, 物, 节, 类, 神, 附, 缺, 掩, 终 = (
                "t",
                arg_i // 19,
                1,
                1,
                arg_i % 19,
                0,
                0,
                0,
                16383,
                99,
            )
            升 = 1
        return " ".join(
            map(
                str,
                [
                    op,
                    槽,
                    物,
                    节,
                    类,
                    神,
                    附,
                    交,
                    缺,
                    0xFF010F04,
                    码,
                    主,
                    级,
                    价,
                    租,
                    钱,
                    升,
                    掩,
                    终,
                    改,
                    修,
                    自动,
                ],
            )
        )

    @staticmethod
    def _转盘(arg_工具: Path) -> dict:
        例 = [
            (类, 种, 停, 电脑)
            for 类 in (1, 2, 5, 6)
            for 种 in (0, 1, 42, 0xFFFFFFFF, 0xDEADBEEF)
            for 停, 电脑 in [
                (0, 0),
                (1, 0),
                (9, 0),
                (10, 0),
                (19, 0),
                (20, 0),
                (39, 0),
                (40, 0),
                (41, 0),
                (99, 0),
                (199, 0),
                (999, 1),
            ]
        ]
        cpp = subprocess.run(
            [str(arg_工具), "spinner"],
            input="\n".join(" ".join(map(str, 项)) for 项 in 例) + "\n",
            text=True,
            capture_output=True,
            check=True,
        )
        组 = cpp.stdout.split("end\n")
        if len(组) != len(例) + 1:
            raise ValueError("转盘oracle批次数不同")
        摘, 帧总, 阶段 = hashlib.sha256(), 0, set()
        for 参, 行组 in zip(例, 组):
            类, 种, 停, 电脑 = 参
            盘, 随机 = 金钱转盘_类(类), 随机数_类(种)
            for 帧, cp in enumerate(行组.splitlines()):
                if 帧 == 停:
                    盘.api_停止()
                盘.api_步进(随机, bool(电脑))
                py = " ".join(map(str, [帧, 盘.阶段, 盘.金额, 随机.状态, *盘.数字]))
                if cp != py:
                    raise ValueError(f"转盘{参}/帧{帧}不同：{cp}/{py}")
                阶段.add(盘.阶段)
                帧总 += 1
                摘.update((py + "\n").encode())
        return {
            "cases": len(例),
            "frames_compared": 帧总,
            "phases_seen": sorted(阶段),
            "frame_sha256": 摘.hexdigest(),
        }

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
        工具 = arg_构建.resolve() / "gods-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("gods_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告 = {
            "reference": 版本,
            "generator_seed": 2026102308,
            "scope": (
                "god module, spinner frames and observing/injecting hooks; "
                "not real finance, respawn or full game"
            ),
            "status": "running",
            "episodes": [],
        }
        生 = random.Random(报告["generator_seed"])
        try:
            报告["spinner"] = cls._转盘(工具)
            包 = 资源包_类(arg_素材 / "map.mkf")
            for 图 in range(8):
                for 种 in (0, 1, 0xFFFFFFFF):
                    世 = 世界_类.api_从地图(
                        包.api_解码(图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                    )
                    for i, 人 in enumerate(世.玩家):
                        人.记录.控制标志 = 2 if i != 2 else 0
                        人.记录.现金, 人.状态.累计收入 = 2147483647, 0xFFFFFFFA
                        人.记录.卡片[:] = list(range(1, 16))
                        人.记录.道具[:13] = [255 if i == 0 else 9 if i == 1 else 0] * 13
                    世.卡供应[:] = [255] * 30
                    世.道具供应[:] = [5] * 8
                    世.头.物价, 世.头.当前玩家, 世.头.日期 = 2147483647, 2, (31, 1, 2026)
                    原, 随机 = 世.api_导出(), 随机数_类(种)
                    命令, 预期, 字节 = [], [], []
                    for i in range(700):
                        行 = cls._命令(世, 生, i)
                        命令.append(行)
                        预期.append(cls._动作(世, 随机, 行))
                        字节.append(世.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-god-") as 临:
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
                            raise ValueError("神明oracle行数不同")
                        摘 = hashlib.sha256()
                        for i, (令, c, p, 存) in enumerate(zip(命令, 行组, 预期, 字节)):
                            if c != p:
                                raise ValueError(
                                    f"图{图}/种{种}/步{i}/{令} 返回/RNG/钩子不同：{c}/{p}"
                                )
                            if 存 != (路 / "out" / f"{i}.dat").read_bytes():
                                raise ValueError(f"图{图}/种{种}/步{i}/{令} 完整DAT不同")
                            摘.update(存)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种,
                            "actions": len(命令),
                            "exceptions": sum(行.startswith(("1 ", "2 ")) for 行 in 预期),
                            "unsupported": sum(行.split()[2] == "0" for 行 in 预期),
                            "applied": sum(行.split()[3] == "1" for 行 in 预期),
                            "messages": dict(Counter(行.split("|")[1] for 行 in 预期)),
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
                    "spinner": 报告["spinner"],
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
    神明差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
