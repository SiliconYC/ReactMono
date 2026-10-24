# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from rich4.menu_random import 菜单随机_类


# ◕ 功能
class 菜单随机差分_类:
    """
    原新局std::mt19937原始序列及整个状态的对照，覆盖多次624词换块。

    更新日志：
    2026.10.24 - 不把UI引擎混入核心Watcom流。
    """

    @staticmethod
    def api_执行(arg_构建: Path, arg_报告: Path) -> None:
        arg_构建.mkdir(parents=True, exist_ok=True)
        exe = (arg_构建 / "menu-random-oracle").resolve()
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                str(Path(__file__).with_name("menu_random_oracle.cpp")),
                "-o",
                str(exe),
            ],
            check=True,
        )
        seeds = [0, 1, 5489, 123456789, 0x80000000, 0xFFFFFFFF]
        count = 10000
        out = (
            subprocess.check_output(
                [str(exe)], input="".join(f"{s} {count}\n" for s in seeds).encode()
            )
            .decode()
            .splitlines()
        )
        h = hashlib.sha256()
        for i, seed in enumerate(seeds):
            r = 菜单随机_类(seed)
            values = [r.api_取() for _ in range(count)]
            if values != list(map(int, out[2 * i].split())):
                raise ValueError(f"菜单随机输出不符：种子{seed}")
            # libc++的流输出将环状态按下一输出位置旋转，而非暴露其私有数组。
            state = list(map(int, out[2 * i + 1].split()))
            if state != r._词[r._位 :] + r._词[: r._位]:
                raise ValueError(f"菜单随机完整状态不符：种子{seed}")
            h.update(out[2 * i].encode())
            h.update(out[2 * i + 1].encode())
        report = {
            "status": "passed",
            "scope": "raw std::mt19937 used by original menus.cpp; "
            "outputs and libc++ full serialized states",
            "seeds": seeds,
            "outputs": count * len(seeds),
            "state_sha256": h.hexdigest(),
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/menu_random.py").read_bytes()
            ).hexdigest(),
        }
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    菜单随机差分_类.api_执行(选项.build, 选项.report)
