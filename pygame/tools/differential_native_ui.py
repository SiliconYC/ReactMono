# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import random
import shlex
import struct
import subprocess
import tempfile
from pathlib import Path

from rich4.graphics import 图像_类
from rich4.native_ui import 原生界面_类, 字体_类, 文字样式_类


# ◕ 功能
class 原生文字差分_类:
    """
    直接原Font、FreeType字形与完整RGB555画布对照，字体仅由本地显式路径读取。

    更新日志：
    2026.10.24 - 包含全部双字节CP950/坏UTF8消费及真实字体效果/裁切。
    """

    @staticmethod
    def _命令() -> list[str]:
        生 = random.Random(2026102402)
        组 = ["C -"] + [f"C {i:02x}" for i in range(256)]
        组 += [f"C {i:04x}" for i in range(65536)]
        文 = ["", "大富翁4", "張恒市 1998", "Aa jgy", "e\u0301", "第一行\n第二行\n", " ", "🀄"]
        原 = [s.encode().hex() or "-" for s in 文] + ["c080ff4180", "f8888080", "e0a0", "edbfbf"]
        组 += ["C " + s for s in 原]
        字 = [0, 10, 32, 65, 103, 0x6052, 0x4E00, 0xFFFF, 0xD800, 0x10FFFF]
        字 += [生.randrange(0x110000) for _ in range(180)]
        for ch in 字:
            for mono in (0, 1):
                组.append(f"G {ch} {生.choice([8, 12, 16, 20, 24, 32, 36])} {mono}")
        for _ in range(180):
            大, x, y = (
                生.choice([8, 12, 16, 18, 20, 24, 32, 36]),
                生.randrange(-20, 380),
                生.randrange(-30, 180),
            )
            wrap, fg, mono, bg = (
                生.choice([0, 20, 55, 120, 320]),
                生.randrange(65536),
                生.randrange(2),
                生.randrange(65536),
            )
            组.append(f"D {大} {x} {y} {wrap} {fg} {mono} {bg} {生.choice(原)}")
        for flags in range(8):
            for center in (0, 1):
                for text in 原[:8]:
                    大 = 生.choice([12, 16, 20, 24])
                    组.append(
                        f"B {大} 5 -3 32767 31 {flags & 1} {(flags >> 1) & 1} "
                        f"{(flags >> 2) & 1} 2 {center} 1234 {text}"
                    )
        return 组

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_字体: Path, arg_报告: Path) -> None:
        版 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("reference version mismatch")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        arg_构建.mkdir(parents=True, exist_ok=True)
        工具 = arg_构建.resolve() / "native-ui-oracle"
        ft = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("native_ui_oracle.cpp")),
                *ft,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        组, 字 = cls._命令(), 字体_类(arg_字体)
        报 = {
            "reference": 版,
            "generator_seed": 2026102402,
            "font_filename": arg_字体.name,
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "freetype_library": 字.库路径,
            "scope": (
                "fixed native_ui.hpp; complete byte-pair CP950 and UTF8 codepoints, "
                "actual FreeType glyphs/metrics and complete RGB555 font canvases; "
                "no graphical gameplay acceptance"
            ),
            "status": "running",
        }
        计, 摘 = {k: 0 for k in "CGDB"}, hashlib.sha256()
        try:
            with tempfile.TemporaryDirectory(prefix="rich4-font-") as tmp:
                根 = Path(tmp)
                cp = subprocess.run(
                    [str(工具), str(arg_字体), str(根)],
                    input="\n".join(组) + "\n",
                    text=True,
                    capture_output=True,
                    check=True,
                )
                结果 = cp.stdout.splitlines()
                if len(结果) != len(组):
                    raise ValueError("native font oracle line count mismatch")
                for i, (行, 实) in enumerate(zip(组, 结果)):
                    op, *列 = 行.split()
                    数据 = None
                    if op == "C":
                        文 = bytes.fromhex(列[0]) if 列[0] != "-" else b""
                        cp = 原生界面_类.api_码点(文)
                        s = 原生界面_类.api_繁中(文).encode().hex() or "-"
                        预 = " ".join(map(str, [len(cp), *cp, s]))
                    elif op == "G":
                        ch, 大, mono = map(int, 列)
                        g = 字._字形(ch, 大, bool(mono))
                        预 = f"{g.宽} {g.高} {g.左} {g.顶} {g.前进}"
                        数据, 实字节 = g.遮罩, (根 / f"{i}.mask").read_bytes()
                    else:
                        文 = bytes.fromhex(列[-1]) if 列[-1] != "-" else b""
                        n = list(map(int, 列[:-1]))
                        bg = n[-1]
                        图 = 图像_类(
                            384, 192, [(j * 1103515245 + bg) & 65535 for j in range(384 * 192)]
                        )
                        if op == "D":
                            大, x, y, wrap, fg, mono, bg = n
                            字.api_绘制(图, 文, x, y, 大, fg, wrap, bool(mono))
                            预 = " ".join(
                                map(
                                    str,
                                    [
                                        字.api_测量(文, 大, bool(mono)),
                                        *字.api_墨框(文, 大, 0, bool(mono)),
                                    ],
                                )
                            )
                        else:
                            大, x, y, fg, eff, bold, shadow, outline, gap, center, bg = n
                            式 = 文字样式_类(
                                大, fg, bool(bold), bool(shadow), bool(outline), eff, gap
                            )
                            字.api_绘块(图, 文, x, y, 式, bool(center))
                            预 = " ".join(map(str, 字.api_块范围(文, 式)))
                        数据, 实字节 = (
                            struct.pack(f"<{len(图.像素)}H", *图.像素),
                            (根 / f"{i}.555").read_bytes(),
                        )
                    if 预 != 实:
                        raise ValueError(f"step={i} cmd={行} cpp={实} py={预}")
                    if 数据 is not None:
                        if 数据 != 实字节:
                            首 = next(j for j, (a, b) in enumerate(zip(数据, 实字节)) if a != b)
                            raise ValueError(
                                f"step={i} cmd={行} binary offset={首} "
                                f"cpp={实字节[首 : 首 + 8].hex()} py={数据[首 : 首 + 8].hex()}"
                            )
                        摘.update(数据)
                    摘.update((预 + "\n").encode())
                    计[op] += 1
            报["status"], 报["commands"], 报["operations"], 报["state_sha256"] = (
                "passed",
                len(组),
                计,
                摘.hexdigest(),
            )
        except Exception as 错:
            报["status"], 报["failure"] = "failed", str(错)
            raise
        finally:
            字.api_关闭()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": 报["status"], "commands": len(组), "operations": 计}))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    原生文字差分_类.api_执行(选项.source, 选项.build, 选项.font, 选项.report)
