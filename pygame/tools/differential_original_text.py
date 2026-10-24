# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import collections
import hashlib
import json
import subprocess
from pathlib import Path

from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
class 原文字差分_类:
    """
    对照固定C++生成表与外部原EXE，仅公开数量/哈希，不落盘台词。

    更新日志：
    2026.10.24 - 覆盖三角色表空槽、新闻/命运/神明和店员变体。
    """

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_程序: Path,
        arg_报告: Path,
    ) -> None:
        版 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        arg_构建.mkdir(parents=True, exist_ok=True)
        exe = arg_构建 / "original-text-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("original_text_oracle.cpp")),
                "-o",
                str(exe),
            ],
            check=True,
        )
        原 = 原版程序_类.api_读取(arg_程序)
        文 = 原版文字_类(原)
        报 = {
            "reference": 版,
            "exe_filename": arg_程序.name,
            "exe_sha256": hashlib.sha256(原.数据).hexdigest(),
            "exe_size": len(原.数据),
            "python_source_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/original_text.py").read_bytes()
            ).hexdigest(),
            "status": "running",
            "scope": (
                "external read-only PE strings versus fixed C++ literals; "
                "no text or asset data published"
            ),
        }
        计, 空, 摘, 变体 = collections.Counter(), collections.Counter(), hashlib.sha256(), 0
        try:
            行表 = subprocess.check_output([str(exe)], text=True).splitlines()
            for i, 行 in enumerate(行表):
                k, c, s, v, h = 行.split()
                c, s, v = int(c), int(s), int(v)
                预 = bytes.fromhex(h).decode() if h != "-" else ""
                if k in "ETC":
                    台 = 文.api_台词({"E": "event", "T": "tool", "C": "card"}[k], c, s)
                    实, 声 = ("", 0) if 台 is None else (台.文字, 台.声音)
                    空[k] += int(台 is None)
                elif k == "G":
                    实, 声 = 文.api_神明(s), -1
                else:
                    版号 = int(k == "V" and v == 89 and 变体 > 0)
                    台 = 文.api_配音(v, 版号)
                    变体 += int(k == "V" and v == 89)
                    实, 声 = 台.文字, 台.声音
                if 实 != 预 or 声 != v:
                    报["failure"] = {
                        "step": i,
                        "table": k,
                        "character": c,
                        "slot": s,
                        "expected_voice": v,
                        "actual_voice": 声,
                        "expected_sha256": hashlib.sha256(预.encode()).hexdigest(),
                        "actual_sha256": hashlib.sha256(实.encode()).hexdigest(),
                    }
                    raise ValueError(f"原文差分失败：step={i} table={k} character={c} slot={s}")
                摘.update((行 + "\n").encode())
                计[k] += 1
            报.update(
                status="passed",
                entries=len(行表),
                tables=dict(计),
                empty_slots=dict(空),
                indexed_voice_ids=len(文.配音),
                state_sha256=摘.hexdigest(),
                native_bank_89_variants=变体,
            )
        except (ValueError, KeyError):
            报["status"] = "failed"
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": 报["status"], "entries": len(行表), "tables": dict(计)}))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "exe", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    原文字差分_类.api_执行(选项.source, 选项.build, 选项.exe, 选项.report)
