# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path

from rich4.board_models import 玩家精灵_类, 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.projection_tables import 投影表_类


# ◕ 功能
class 投影差分_类:
    """
    遍历全部格点、小数和负坐标，比较反投影及全角色姿态选择。

    更新日志：
    2026.10.23 - 固定表哈希另行验证；此处比较实际函数返回和拒绝。
    """

    @staticmethod
    def _整数(arg_值: int) -> int:
        return ((arg_值 + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    @classmethod
    def _用例(cls) -> list[str]:
        用例 = []
        for 旋 in range(8):
            for 小数 in (0, 15, 31):
                中x, 中y = -1024 + 小数, 1024 + 31 - 小数
                for y in range(-14, 15):
                    for x in range(-14, 15):
                        用例.append(
                            f"P {旋} {中x} {中y} 0 40 440 480 {中x + x * 32} {中y + y * 32}"
                        )
        生成 = random.Random(2026102308)
        for _ in range(30000):
            旋 = 生成.randrange(9)
            中x, 中y = [
                生成.choice([-2147483648, 2147483647, 生成.randrange(-100000, 100000)])
                for _ in range(2)
            ]
            世界x, 世界y = [cls._整数(中 + 生成.randrange(-600, 600)) for 中 in (中x, 中y)]
            框 = 生成.choice(["0 40 440 480", "10 20 333 456", "100 200 8192 8192", "0 0 0 480"])
            用例.append(f"P {旋} {中x} {中y} {框} {世界x} {世界y}")
        for _ in range(3000):
            旋 = 生成.randrange(9)
            中x, 中y = [生成.randrange(-10000, 10000) for _ in range(2)]
            屏x, 屏y = 生成.randrange(-10, 450), 生成.randrange(30, 490)
            用例.append(f"U {旋} {中x} {中y} 0 40 440 480 {屏x} {屏y}")
        for 人 in range(13):
            for 交通 in range(5):
                for 位 in range(32):
                    状态 = [(位 >> n) & 1 for n in range(5)]
                    for 姿态 in (0, 12, 19, 20, 255):
                        用例.append("R " + " ".join(map(str, [人, 交通, *状态, 姿态])))
        return 用例

    @staticmethod
    def _执行(arg_行: str) -> str:
        op, *部分 = arg_行.split()
        数 = list(map(int, 部分))
        try:
            if op in ("P", "U"):
                旋, x, y, 左, 顶, 右, 底, px, py = 数
                相机 = 相机_类((x, y), 旋, (左, 顶, 右, 底))
                结果 = (
                    棋盘投影_类.api_投影((px, py), 相机)
                    if op == "P"
                    else 棋盘投影_类.api_反投影((px, py), 相机)
                )
                return "0 0" if 结果 is None else f"0 1 {结果[0]} {结果[1]}"
            人, 交通, 走, 水, 梦, 伤, 骰, 姿 = 数
            玩家 = 玩家精灵_类(
                角色=人,
                交通=交通,
                走动=bool(走),
                踩水=bool(水),
                梦游=bool(梦),
                受伤=bool(伤),
                投骰=bool(骰),
                特殊姿态=姿,
            )
            return f"0 {棋盘投影_类.api_角色资源(玩家)}"
        except ValueError:
            return "1"

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_报告: Path) -> None:
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
        工具 = arg_构建.resolve() / "projection-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("projection_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        用例 = cls._用例()
        输入 = "\n".join(用例) + "\n"
        报告 = {
            "reference": 版本,
            "scope": "lookup projection, inverse tile hit-test and pose selector only",
            "generator_seed": 2026102308,
            "raw_table_sha256": 投影表_类.原始哈希,
            "status": "running",
        }
        try:
            cpp = subprocess.run(
                [str(工具)], input=输入, text=True, capture_output=True, check=True
            )
            行 = cpp.stdout.splitlines()
            if len(行) != len(用例):
                raise ValueError("投影输出数量不同")
            for i, (命令, cpp行) in enumerate(zip(用例, 行)):
                py行 = cls._执行(命令)
                if py行 != cpp行:
                    raise ValueError(f"投影用例{i}/{命令}不同：{py行}/{cpp行}")
            报告.update(
                status="passed",
                cases=len(用例),
                projection=sum(行.startswith("P ") for 行 in 用例),
                unprojection=sum(行.startswith("U ") for 行 in 用例),
                poses=sum(行.startswith("R ") for 行 in 用例),
                rejections=行.count("1"),
                input_sha256=hashlib.sha256(输入.encode()).hexdigest(),
                output_sha256=hashlib.sha256(cpp.stdout.encode()).hexdigest(),
            )
        except (ValueError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print(f"[完成] {len(用例)}个投影/反投影/姿态结果一致。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    投影差分_类.api_执行(选项.source, 选项.build, 选项.report)
