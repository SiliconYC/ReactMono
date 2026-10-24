# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_game.cpp::Screen/Options；开发验收参数不改变正式默认规则。
# ◑ 导入
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path


# ◕ 功能
class 应用页面_类(IntEnum):
    """
    原稳定Screen编号，输入重放按此区分菜单和游戏。

    更新日志：
    2026.10.24 - 保留十二页面编号，不合并原专属界面。
    """

    菜单, 新局, 游戏, 设置, 查询, 卡片, 道具, 股票, 交易, 读取, 保存, 托管 = range(12)


@dataclass
class 应用设置_类:
    """
    原外部资源、字体、保存目录和可重复验收参数。

    更新日志：
    2026.10.24 - 日期缺省使用宿主当天，验证重放缺省2026-10-05，与参考入口一致。
    2026.10.24 - 种子按原uint32字段归一化，菜单/规则/结局共用同一值。
    """

    素材: Path
    字体: Path
    存档目录: Path
    种子: int = 1
    地图: int = 0
    日期: tuple[int, int, int] | None = None
    载入: Path | None = None
    输出: Path | None = None
    静音: bool = False
    验证天数: int = 0
    播放效果: bool = False
    触摸: bool = False
    界面预设: str = ""

    def __post_init__(self) -> None:
        self.种子 &= 0xFFFFFFFF
