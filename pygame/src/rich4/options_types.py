# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/menus.hpp::OptionsState/OptionsActions。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass


# ◕ 功能
@dataclass
class 选项状态_类:
    """
    原速度/音乐/音效/动画配置，不伪造参考没有的连续音量字段。

    更新日志：
    2026.10.24 - 动画开关仍用于正式人类小游戏。
    """

    速度: int = 1
    音乐: bool = True
    音效: bool = True
    动画: bool = True


@dataclass(frozen=True)
class 选项动作_类:
    """
    原选项应用/关闭、歌曲试听和重开/退出/说明回调。

    更新日志：
    2026.10.24 - 可选能力以None表示，按原决定灰态及是否执行。
    """

    应用: Callable[[选项状态_类], None]
    关闭: Callable[[], None]
    试曲: Callable[[int], None] | None = None
    正播放: int = 0
    重开: Callable[[], None] | None = None
    退出: Callable[[], None] | None = None
    说明: Callable[[], None] | None = None
