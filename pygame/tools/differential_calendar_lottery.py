# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.calendar import 日期_类
from rich4.holidays import 节日_类
from rich4.lottery import 开奖结果_类, 彩票_类, 彩票状态错误_类
from rich4.random import 随机数_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 日历彩票差分_类:
    """
    历史农历与八图节日逐日比较，彩票按每步完整世界及返回值比较。

    更新日志：
    2026.10.23 - 只调用测试 C++，不把模块动作称为完整游戏。
    """

    @staticmethod
    def _打包(arg_日: tuple[int, int, int]) -> int:
        年, 月, 日 = arg_日
        return 年 << 16 | 月 << 8 | 日

    @classmethod
    def _日历(cls, arg_工具: Path) -> dict:
        用例 = []
        for 天 in range(日期_类(2030, 12, 31).api_天数() + 1):
            日期 = 日期_类.api_从天数(天)
            for 图 in range(8):
                用例.append((天, 图, int(日期.日 == 1)))
        for 日期 in (
            日期_类(2100, 2, 28),
            日期_类(2100, 2, 29),
            日期_类(2100, 3, 1),
            日期_类(65535, 12, 31),
        ):
            用例.extend((日期.api_天数(), 图, 0) for 图 in range(8))
        输入 = "\n".join(f"{天} {图} {贷}" for 天, 图, 贷 in 用例) + "\n"
        cpp = subprocess.run(
            [str(arg_工具), "--calendar"], input=输入, text=True, capture_output=True, check=True
        )
        行 = cpp.stdout.splitlines()
        if len(行) != len(用例):
            raise ValueError("日历 oracle 行数不同")
        for i, ((天, 图, 贷), cpp行) in enumerate(zip(用例, 行)):
            日期 = 日期_类.api_从天数(天)
            图号, 阶段 = 图 % 4, 图 // 4
            农历 = 节日_类.api_农历(日期)
            节行 = 节日_类.api_节日行(日期, 图号, 阶段)
            图片 = 节日_类.api_节日图片(日期, 图号, 阶段)
            庆祝 = 节日_类.api_庆祝(日期, 图号, 阶段)
            到期 = 节日_类.api_贷款到期(日期, 图号, 阶段) if 贷 else None
            结果 = [
                cls._打包(农历) if 农历 else 0,
                -1 if 节行 is None else 节行,
                -1 if 图片 is None else 图片,
                int(节日_类.api_休市(日期, 图号, 阶段)),
                int(庆祝 is not None),
                庆祝.影片 if 庆祝 else 0,
                庆祝.音效 if 庆祝 else 0,
                庆祝.音乐 if 庆祝 else 0,
                cls._打包((到期.年, 到期.月, 到期.日)) if 到期 else 0,
            ]
            if 结果 != list(map(int, cpp行.split())):
                raise ValueError(f"日历{i} 天{天}/图{图}不一致：{结果}/{cpp行}")
        return {
            "cases": len(用例),
            "loan_dates": sum(贷 for _, _, 贷 in 用例),
            "dates": "1998-01-01..2030-12-31 daily, plus 2100 leap and 65535 boundary",
            "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
            "output_sha256": hashlib.sha256(cpp.stdout.encode()).hexdigest(),
        }

    @staticmethod
    def _动作(arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str) -> list[int]:
        op, *部分 = arg_行.split()
        数 = list(map(int, 部分))
        状态 = 值 = 0
        结果 = 开奖结果_类()
        号码: list[int] = []
        try:
            if op == "b":
                值 = int(彩票_类.api_购票(arg_世, *数))
            elif op == "r":
                选择 = 彩票_类.api_随机购票(arg_世, arg_随机, *数)
                值 = -1 if 选择 is None else 选择
            elif op == "c":
                彩票_类.api_退票(arg_世, *数)
            elif op == "d":
                结果 = 彩票_类.api_开奖(arg_世, arg_随机)
            elif op == "v":
                号码 = 彩票_类.api_可售号码(arg_世)
            elif op == "t":
                i, 业主 = 数
                if not 0 <= i < 36:
                    raise IndexError("测试票索引越界")
                arg_世.彩票[i] = 业主 & 255
            elif op == "f":
                arg_世.公共基金 = 数[0]
            elif op == "p":
                槽, 钱, 控制, 收入 = 数
                if not 0 <= 槽 < len(arg_世.玩家):
                    raise IndexError("测试玩家越界")
                玩家 = arg_世.玩家[槽]
                玩家.记录.现金 = 钱
                玩家.记录.控制标志 = 控制 & 255
                玩家.状态.累计收入 = 收入
            elif op == "q":
                值 = int(彩票_类.api_开奖日((数[0] & 255, 10, 2026)))
            else:
                raise RuntimeError("未知彩票测试动作")
        except 彩票状态错误_类:
            状态 = 3
        except IndexError:
            状态 = 2
        return [
            状态,
            值,
            结果.号码,
            -1 if 结果.赢家 is None else 结果.赢家,
            结果.奖金,
            int(结果.已开奖),
            int(结果.仅售出票),
            arg_随机.状态,
            len(号码),
            *号码,
        ]

    @staticmethod
    def _命令(arg_生成: random.Random) -> list[str]:
        命令 = ["v", "r 0", "b 0 36", "b 1 36", "b 0 1", "d", "f 15000"]
        命令 += [f"t {i} 1" for i in range(10, 20)]
        命令 += ["t 0 0", "t 35 0", "d", "t 20 1", "t 30 3", "d", "t 0 5", "v", "d", "t 0 0"]
        命令 += ["q 14", "q 15", "q 16", "p 1 2147483647 2 4294967280", "t 0 2", "d"]
        for _ in range(457):
            op = arg_生成.choice("bbrrddccvvtpf")
            p = arg_生成.randrange(5)
            if op == "b":
                命令.append(f"b {p} {arg_生成.randrange(38)}")
            elif op in "rc":
                命令.append(f"{op} {p}")
            elif op in "dv":
                命令.append(op)
            elif op == "t":
                命令.append(f"t {arg_生成.randrange(37)} {arg_生成.randrange(6)}")
            elif op == "f":
                命令.append(f"f {arg_生成.choice([-2147483648, -1, 0, 1000, 2147483647])}")
            else:
                钱 = arg_生成.choice([-1, 0, 999, 1000, 1001, 50000, 2147483647])
                命令.append(f"p {p} {钱} {arg_生成.randrange(4)} {arg_生成.randrange(1 << 32)}")
        return 命令

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
        工具 = arg_构建.resolve() / "calendar-lottery-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("calendar_lottery_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "generator_seed": 2026102304,
            "scope": "calendar outputs and lottery module actions, not game long runs",
            "status": "running",
            "lottery": [],
        }
        生成 = random.Random(报告["generator_seed"])
        try:
            报告["calendar"] = cls._日历(工具)
            print("[完成] 逐日日历/节日与按月贷款到期一致。", flush=True)
            包 = 资源包_类(arg_地图包)
            for 图 in (0, 3, 4, 7):
                数据 = 包.api_解码(图 * 2 + 1)
                for 种子 in (0, 1, 0xFFFFFFFF):
                    世 = 世界_类.api_从地图(
                        数据, 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种子)
                    )
                    for i, 玩家 in enumerate(世.玩家):
                        玩家.记录.现金 = [1000, 1001, 2147483647, -1][i]
                        玩家.状态.累计收入 = 0xFFFFFFF0
                    原 = 世.api_导出()
                    动作 = cls._命令(生成)
                    输入 = "\n".join(动作) + "\n"
                    with tempfile.TemporaryDirectory(prefix="rich4-lottery-") as 临时:
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
                            raise ValueError("彩票 oracle 行数不同")
                        随机 = 随机数_类(种子)
                        摘要 = hashlib.sha256()
                        拒绝数 = 0
                        for i, (命令, cpp行) in enumerate(zip(动作, 行)):
                            预期 = cls._动作(世, 随机, 命令)
                            if 预期 != list(map(int, cpp行.split())):
                                raise ValueError(
                                    f"图{图}/种{种子}/动作{i}/{命令}返回或RNG不同：{预期}/{cpp行}"
                                )
                            字节 = 世.api_导出()
                            if 字节 != (路径 / "out" / f"{i}.dat").read_bytes():
                                raise ValueError(f"图{图}/种{种子}/动作{i}/{命令} DAT不同")
                            摘要.update(字节)
                            拒绝数 += int(预期[0] != 0)
                    报告["lottery"].append(
                        {
                            "map": 图,
                            "seed": 种子,
                            "steps": len(动作),
                            "exception_rejections": 拒绝数,
                            "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
                            "states_sha256": 摘要.hexdigest(),
                        }
                    )
                print(f"[完成] 地图{图}彩票模块完整状态一致。", flush=True)
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
    日历彩票差分_类.api_执行(选项.source, 选项.build, 选项.map, 选项.report)
