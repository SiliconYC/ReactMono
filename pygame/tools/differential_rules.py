# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path

from rich4.calendar import 日期_类
from rich4.direction import 方向_类
from rich4.economy import 地产经济_类, 经济_类
from rich4.inventory import 库存_类
from rich4.random import 随机数_类


# ◕ 功能
class 规则差分_类:
    """
    生成固定输入并逐行比较原 C++ API；测试随机流与正式游戏完全分离。

    更新日志：
    2026.10.23 - RNG、日期、方向、库存动作与地产租金批量差分。
    """

    @staticmethod
    def api_执行(arg_源码: Path, arg_构建: Path, arg_报告: Path) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++ 版本不符")
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
        工具 = arg_构建.resolve() / "rules-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("rules_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        用例: list[tuple[str, list[int]]] = []
        生成器 = random.Random(20261023)
        for 种子 in [0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]:
            随机 = 随机数_类(种子)
            结果 = [随机.api_下一个() for _ in range(10000)] + [随机.状态]
            用例.append((f"random {种子} 10000", 结果))
        for 天 in (
            list(range(0, 1500))
            + [日期_类(65535, 12, 31).api_天数()]
            + [生成器.randrange(20000000) for _ in range(2000)]
        ):
            日期 = 日期_类.api_从天数(天)
            用例.append(
                (f"calendar {天}", [日期.年, 日期.月, 日期.日, 日期.api_星期(), 日期.api_天数()])
            )
        for _ in range(3000):
            日期, 间隔 = 生成器.randrange(2**32), 生成器.randrange(2**32)
            用例.append((f"packed {日期} {间隔}", [日期_类.api_打包间隔(日期, 间隔)]))
        for x in [
            -2147483648,
            -2147483647,
            -2048,
            -850,
            -849,
            -848,
            -1,
            0,
            1,
            848,
            849,
            850,
            2048,
            2147483647,
        ]:
            for y in [
                -2147483648,
                -2048,
                -850,
                -849,
                -848,
                -1,
                0,
                1,
                848,
                849,
                850,
                2048,
                2147483647,
            ]:
                用例.append((f"direction {x} {y}", [方向_类.api_计算(x, y)]))
        for _ in range(10000):
            x, y = 生成器.randrange(-(2**31), 2**31), 生成器.randrange(-(2**31), 2**31)
            用例.append((f"direction {x} {y}", [方向_类.api_计算(x, y)]))
        for _ in range(50):
            库存 = 库存_类()
            库存.卡价[:] = [生成器.randrange(256) for _ in range(30)]
            库存.卡供应[:] = [生成器.randrange(256) for _ in range(30)]
            库存.道具供应[:] = [生成器.randrange(256) for _ in range(8)]
            库存.道具价格[:] = [生成器.randrange(256) for _ in range(13)]
            初值 = 库存.卡价 + 库存.卡供应 + 库存.道具供应 + 库存.道具价格
            动作 = []
            预期 = []
            for _ in range(300):
                操作 = 生成器.choice("rrrrchRRRCsS")
                编号 = 生成器.randrange(1, 14 if 操作 in "RCS" else 31)
                动作.extend([操作, str(编号)])
                结果 = 0
                if 操作 == "r":
                    库存.api_收卡(编号)
                elif 操作 == "c":
                    结果 = int(库存.api_用卡(编号))
                elif 操作 == "h":
                    结果 = int(库存.api_丢半手())
                elif 操作 == "s":
                    结果 = 库存.api_卖卡()
                elif 操作 == "R":
                    结果 = int(库存.api_收道具(编号))
                elif 操作 == "C":
                    结果 = int(库存.api_用道具(编号))
                elif 操作 == "S":
                    结果 = 库存.api_卖库存道具()
                预期.extend([结果] + 库存.卡片 + 库存.卡供应 + 库存.道具 + 库存.道具供应)
            输入 = "inventory " + " ".join(map(str, 初值)) + " 300 " + " ".join(动作)
            用例.append((输入, 预期))
        for _ in range(3000):
            地产 = []
            记录 = []
            for _ in range(生成器.randrange(1, 40)):
                名, 链, 主, 级 = (生成器.randrange(n) for n in [4, 3, 5, 6])
                租金 = tuple(生成器.randrange(65536) for _ in range(6))
                地产.append(地产经济_类(str(名).encode(), 链, 主, 级, 租金))
                记录.extend([名, 链, 主, 级, *租金])
            主 = 生成器.randrange(5)
            价 = 生成器.choice([-2147483648, -1, 0, 1, 2, 5, 2147483647])
            街 = 生成器.randrange(-1, 4)
            值 = 经济_类.api_通行费(地产, 主, 价, None if 街 < 0 else str(街).encode())
            输入 = f"economy {len(地产)} {主} {价} {街} " + " ".join(map(str, 记录))
            用例.append((输入, [经济_类.api_连锁数(地产, 主), 值]))
        输入串 = "\n".join(输入 for 输入, _ in 用例) + "\n"
        cpp = subprocess.run([str(工具)], input=输入串, text=True, capture_output=True, check=True)
        行 = cpp.stdout.splitlines()
        报告: dict = {
            "reference": 版本,
            "generator_seed": 20261023,
            "cases": len(用例),
            "input_sha256": hashlib.sha256(输入串.encode()).hexdigest(),
            "oracle_sha256": hashlib.sha256(工具.read_bytes()).hexdigest(),
            "status": "passed",
            "inventory_actions": 15000,
            "rng_values": 50000,
            "modules": ["random", "calendar", "direction", "inventory", "economy"],
        }
        if len(行) != len(用例):
            raise ValueError(f"C++ 输出 {len(行)} 行，输入 {len(用例)} 条")
        for 序号, ((输入, 预期), 输出) in enumerate(zip(用例, 行)):
            实际 = list(map(int, 输出.split()))
            if 实际 != 预期:
                报告.update(status="failed", case_index=序号, input=输入, cpp=实际, python=预期)
                break
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        if 报告["status"] != "passed":
            raise ValueError(f"规则差分失败，见 {arg_报告}")
        print(f"[完成] {len(用例)} 批规则输入全部一致，含 15000 库存动作和 50000 随机值。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    规则差分_类.api_执行(选项.source, 选项.build, 选项.report)
