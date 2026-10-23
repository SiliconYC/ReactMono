# ◑ 导入
import argparse
import hashlib
import re
import struct
import subprocess
from pathlib import Path


# ◕ 功能
class 投影表提取_类:
    """
    从固定公开C++表提取Python字面量，并复核原逆向表的原始字节哈希。

    更新日志：
    2026.10.23 - 保留8×841格点、8×304遍历和8×4小数基底。
    """

    @staticmethod
    def api_执行(arg_源码: Path, arg_输出: Path) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++版本不符")
        文 = (arg_源码 / "src/board_projection_tables.inc").read_text()
        段 = [
            文.split(名 + "{{", 1)[1].split("}};", 1)[0]
            for 名 in ("camera_grid", "ground_order", "fractional_basis")
        ]
        格, 序 = [
            [tuple(map(int, 对)) for 对 in re.findall(r"Point\{(-?\d+),\s*(-?\d+)\}", 区)]
            for 区 in 段[:2]
        ]
        基 = [
            tuple(map(int, re.findall(r"-?\d+", 行)))
            for 行 in re.findall(r"\{\{([^{}]+)\}\}", 段[2])
        ]
        if (len(格), len(序), len(基)) != (8 * 841, 8 * 304, 8) or any(len(项) != 4 for 项 in 基):
            raise ValueError("投影表维度变化")
        原字节 = b"".join(struct.pack("<hh", y, x) for x, y in 格)
        原字节 += b"".join(struct.pack("bb", y, x) for x, y in 序)
        原字节 += b"".join(struct.pack("bbbb", *项) for 项 in 基)
        摘要 = hashlib.sha256(原字节).hexdigest()
        if 摘要 != "396188ec0d57d5fd4b5fa021890d0cc57b2ffb0cf42d53a65623a08fadafe1d7":
            raise ValueError("逆向投影常量原始字节哈希变化")
        行组 = [
            "# SPDX-License-Identifier: GPL-3.0-or-later",
            "# 原Iru Cai/mytbk逆向常量，固定C++ board_projection_tables.inc；禁止浮点矩阵替换。",
            "# 由tools/extract_projection_tables.py提取并复核原始字节哈希。",
            "# ◕ 功能",
            "class 投影表_类:",
            '    """',
            "    原离散格点、地面遍历次序与小数舍入基底，所有点为(x,y)。",
            "",
            "    更新日志：",
            "    2026.10.23 - 从固定GPL公开源码逐值提取，原始常量哈希校验通过。",
            '    """',
            "",
            f'    原始哈希 = "{摘要}"',
            "",
            "    # 保留紧凑查表布局，避免格式化器把每个数值展开为独立行。",
            "    # fmt: off",
        ]
        for 名, 表, 步长 in [("相机网格", 格, 841), ("地面次序", 序, 304)]:
            行组.append(f"    {名} = (")
            for 视角 in range(8):
                行组.append("        (")
                项组 = 表[视角 * 步长 : (视角 + 1) * 步长]
                for 起 in range(0, len(项组), 5):
                    行组.append("            " + ", ".join(map(str, 项组[起 : 起 + 5])) + ",")
                行组.append("        ),")
            行组.append("    )")
        行组.append("    分数基底 = (")
        行组.extend(f"        {项}," for 项 in 基)
        行组.extend(["    )", "    # fmt: on", ""])
        arg_输出.write_text("\n".join(行组))
        print(f"[完成] 投影/遍历/基底 {len(格)}/{len(序)}/{len(基)} 项，原字节哈希一致。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--output", type=Path, required=True)
    选项 = 参数.parse_args()
    投影表提取_类.api_执行(选项.source, 选项.output)
