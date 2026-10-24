# SPDX-License-Identifier: GPL-3.0-or-later
# 原EXE只作为离线文本来源，输出UTF-8 JSON，不复制或执行商业程序。
# ◑ 导入
import ast
from dataclasses import asdict
from pathlib import Path

from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
class 开放文字导入_类:
    """
    将既有原文字公开查询和指针表导出为普通Unicode文本索引。

    更新日志：
    2026.10.24 - 原声音变体继续由公开规则处理；空台词与地址查询均保留。
    """

    @staticmethod
    def api_导出(arg_来源: Path) -> dict:
        exe = next(p for p in arg_来源.iterdir() if p.name.lower() == "rich4.exe")
        source = 原版程序_类.api_读取(exe)
        text = 原版文字_类(source)
        addresses = set(text.股票地址) | set(text.神明地址)
        addresses.update(0x4635C6 + 13 * i for i in range(8))
        tables = dict(text.表)
        pointers = {}
        for address, count in (
            *((address, 12 * width) for address, width in tables.values()),
            (0x47517C, 4),
            (0x475ED8, 6),
            (0x47ED7A, 6),
            (0x475CF8, 4),
        ):
            values = source.api_指针表(address, count)
            pointers[str(address)] = list(values)
            addresses.update(v for v in values if v)
        # 既有规则中的固定VA也是文字索引契约；只读取已映射的实际NUL原串。
        for path in Path(__file__).parents[1].joinpath("src/rich4").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and type(node.value) is int
                    and 0x400000 <= node.value < 0x500000
                ):
                    try:
                        source.api_原串(node.value)
                    except ValueError:
                        continue
                    addresses.add(node.value)
        result = {
            "version": 1,
            "strings": {str(address): text.api_原文(address) for address in sorted(addresses)},
            "pointer_tables": pointers,
            "speech": {str(i): asdict(v) for i, v in sorted(text.配音.items())},
            "dialogue": {
                name: [
                    [
                        asdict(line) if (line := text.api_台词(name, person, slot)) else None
                        for slot in range(width)
                    ]
                    for person in range(12)
                ]
                for name, (_, width) in tables.items()
            },
        }
        return result
