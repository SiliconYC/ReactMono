# SPDX-License-Identifier: GPL-3.0-or-later
# Pygame 自动恢复点；复用原生 DAT/RNG 的事务写入，不改游戏规则或存档格式。
from pathlib import Path

from rich4.save import 存档_类
from rich4.save_transaction import 存档事务_类


class 回合自动存档_类:
    """开局、前一回合起点、当前回合起点：三份独立事务存档。"""

    def __init__(self, arg_目录: Path) -> None:
        self.开局 = arg_目录 / "Autosave.Start.DAT"
        self.上一 = arg_目录 / "Autosave.Previous.DAT"
        self.当前 = arg_目录 / "Autosave.DAT"

    def api_初始化(self, arg_数据: bytes, arg_随机: int) -> None:
        # 每局建档顺序为开局->上一->当前；最后更新当前以供继续游戏优先读取。
        for path in (self.开局, self.上一, self.当前):
            存档事务_类(path).api_写入(arg_数据, arg_随机)

    def api_轮转(self, arg_数据: bytes, arg_随机: int, arg_缺省种子: int) -> None:
        # 先保存旧的当前，随后才提交新的当前；任何一步失败可在下次轮询重试。
        # 当前损坏时禁止将坏内容覆盖仍完好的上一代。
        try:
            previous = 存档事务_类(self.当前).api_读取(arg_缺省种子)
            save = 存档_类.api_解码(previous[0])
            if save.api_头().签名 != 0x26:
                raise ValueError("自动存档签名错误")
        except (OSError, ValueError, RuntimeError):
            previous = None
        if previous is not None:
            存档事务_类(self.上一).api_写入(*previous)
        存档事务_类(self.当前).api_写入(arg_数据, arg_随机)
