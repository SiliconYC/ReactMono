# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/native_audio.hpp；音频契约不拥有或调用C++游戏引擎。
# ◑ 导入
from enum import IntEnum
from typing import Protocol


# ◕ 功能
class 循环通道_类(IntEnum):
    """
    原三个独立循环声槽，语音另有单独通道。

    更新日志：
    2026.10.24 - 转盘/步行/炸弹编号0/1/2保留。
    """

    转盘, 步行, 炸弹 = range(3)


class 音乐_类(IntEnum):
    """
    原上下文Music，零代表压入静音而非没有上下文。

    更新日志：
    2026.10.24 - 原表编号和八首正常歌单另行保留。
    """

    (
        静音,
        菜单,
        新局,
        破产,
        未用04,
        银行,
        拍卖,
        商店,
        魔法,
        开奖,
        月报,
        礼物,
        气球,
        企鹅,
        圣诞,
        新年,
        监狱,
        医院,
    ) = range(18)


class 音频策略宿主_基类(Protocol):
    """
    原board_audio依赖的音乐栈/循环接口；正式应用必须绑定真实音频实现。

    更新日志：
    2026.10.24 - Protocol仅声明契约，不提供空的正式播放器。
    """

    def api_推音乐(self, arg_音乐: 音乐_类) -> None: ...
    def api_换音乐(self, arg_音乐: 音乐_类) -> None: ...
    def api_弹音乐(self) -> None: ...
    def api_播循环(self, arg_号: int, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None: ...
    def api_停循环(self, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None: ...
