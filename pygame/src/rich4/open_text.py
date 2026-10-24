# SPDX-License-Identifier: GPL-3.0-or-later
# 从项目内UTF-8 JSON查询商业文字，正式运行不再读取原EXE。
# ◑ 导入
import json
from pathlib import Path

from rich4.original_text import 原版文字_类, 台词_类


# ◕ 功能
class 文本指针索引_类:
    """
    原调用使用的地址只是稳定JSON键，不再映射或读取可执行文件。

    更新日志：
    2026.10.24 - 保留原轮盘/名称表的指针顺序与长度拒绝语义。
    """

    def __init__(self, arg_JSON: str) -> None:
        self._表: dict[str, list[int]] = json.loads(arg_JSON)

    def api_指针表(self, arg_地址: int, arg_数: int) -> tuple[int, ...]:
        values = self._表[str(arg_地址)]
        if not 0 <= arg_数 <= len(values):
            raise ValueError("文字索引表长度超出已导出范围")
        return tuple(values[:arg_数])


class 开放文字_类(原版文字_类):
    """
    与既有原文API相同的Unicode台词、名称和格式文字查询。

    更新日志：
    2026.10.24 - 配音变体仍复用公开规则，空表项保持None，缺失内容明确报错。
    """

    def __init__(self, arg_路径: Path) -> None:
        data = json.loads(arg_路径.read_text())
        if data["version"] != 1:
            raise ValueError("不支持的开放文字版本")
        self.程序 = 文本指针索引_类(json.dumps(data["pointer_tables"]))
        self.配音 = {int(i): 台词_类(**line) for i, line in data["speech"].items()}
        self._开放台词 = {
            name: [[台词_类(**line) if line is not None else None for line in row] for row in rows]
            for name, rows in data["dialogue"].items()
        }
        self._开放原文: dict[str, str] = data["strings"]

    def api_原文(self, arg_地址: int) -> str:
        try:
            return self._开放原文[str(arg_地址)]
        except KeyError as error:
            raise ValueError(f"开放文字未导出地址：{arg_地址:#x}") from error

    def api_神明(self, arg_索引: int) -> str:
        if not 0 <= arg_索引 < len(self.神明地址):
            raise IndexError("神明原文索引越界")
        return self.api_原文(self.神明地址[arg_索引])

    def api_台词(self, arg_表: str, arg_人物: int, arg_槽: int) -> 台词_类 | None:
        rows = self._开放台词[arg_表]
        if not 0 <= arg_人物 < 12 or not 0 <= arg_槽 < self.表[arg_表][1]:
            raise IndexError("台词人物/槽位越界")
        return rows[arg_人物][arg_槽]
