# ◑ 导入
import argparse
import hashlib
import json
import random
import struct
import subprocess
from pathlib import Path

from rich4.numeric import 扩展数_类


# ◕ 功能
class 数值差分_类:
    """
    固定 C++ 软件 x87 模型与 Python 的扩展状态、落盘位和整数转换差分。

    更新日志：
    2026.10.23 - 覆盖生成表达式、舍入边界与异常域，不冒充原 EXE 硬件采样。
    """

    @staticmethod
    def _结果(
        arg_操作: int,
        arg_a: int,
        arg_b: int,
        arg_c: int,
    ) -> str:
        try:
            a, b, c = [
                扩展数_类.api_从值(struct.unpack("<d", struct.pack("<Q", v))[0])
                for v in (arg_a, arg_b, arg_c)
            ]
            if arg_操作 == 0:
                v = (a + b) * c
            elif arg_操作 == 1:
                v = (a - b) / c
            elif arg_操作 == 2:
                v = (a * b) + c
            else:
                v = (a / b) - c
        except ValueError:
            return "invalid"
        单态, 双态, 单, 双 = 0, 0, 0, 0
        try:
            单 = v.api_单精度位()
        except ValueError:
            单态 = 1
        try:
            双 = v.api_双精度位()
        except ValueError:
            双态 = 1
        return " ".join(
            map(str, [v.有效数, v.指数, int(v.负), 单态, 单, 双态, 双, v.api_整数() & 0xFFFFFFFF])
        )

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_输出: Path,
        arg_构建: Path,
    ) -> None:
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
        arg_构建.mkdir(parents=True, exist_ok=True)
        工具 = arg_构建.resolve() / "numeric-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("numeric_oracle.cpp")),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        生成器 = random.Random(2026102301)
        用例: list[tuple[int, int, int, int]] = []
        for i in range(40000):
            数 = [
                (生成器.randrange(2) << 63)
                | ((1023 + 生成器.randrange(-100, 101)) << 52)
                | 生成器.getrandbits(52)
                for _ in range(3)
            ]
            用例.append((i % 4, *数))
        边界 = [
            0,
            0x8000000000000000,
            1,
            0x0010000000000000,
            0x7FEFFFFFFFFFFFFF,
            0x7FF0000000000000,
            0x7FF8000000000001,
            *(
                struct.unpack("<Q", struct.pack("<d", v))[0]
                for v in [1, -1, 2**53, 2**64, 2**-24, 2**-63, 2147483648, -2147483648]
            ),
        ]
        for op in range(4):
            for a in 边界:
                for b in 边界:
                    用例.append((op, a, b, struct.unpack("<Q", struct.pack("<d", 3))[0]))
        输入 = "\n".join(" ".join(map(str, 行)) for 行 in 用例) + "\n"
        cpp = subprocess.run([str(工具)], input=输入, text=True, capture_output=True, check=True)
        输出 = cpp.stdout.splitlines()
        报告: dict = {
            "reference": 版本,
            "scope": "pinned C++ software Extended model; not original EXE/x87 capture",
            "cases": len(用例),
            "generator_seed": 2026102301,
            "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
            "oracle_output_sha256": hashlib.sha256(cpp.stdout.encode()).hexdigest(),
            "status": "passed",
        }
        if len(输出) != len(用例):
            raise ValueError("数值 oracle 行数不匹配")
        for i, (行, cpp行) in enumerate(zip(用例, 输出)):
            python行 = cls._结果(*行)
            if cpp行 != python行:
                报告.update(status="failed", index=i, input=行, cpp=cpp行, python=python行)
                break
        arg_输出.parent.mkdir(parents=True, exist_ok=True)
        arg_输出.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        if 报告["status"] != "passed":
            raise ValueError(f"数值差分失败，见 {arg_输出}")
        print(f"[完成] {len(用例)} 个软件 x87 表达式完整状态与落盘/整数结果一致。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    数值差分_类.api_执行(选项.source, 选项.report, 选项.build)
