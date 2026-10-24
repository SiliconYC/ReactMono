# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定screens/minigames.cpp::MiniGames::draw_decision/run/input的主游戏接线。
# ◑ 导入
from collections.abc import Callable

from rich4.artwork import 美术_类
from rich4.game_types import 决策_类, 决策种类_类
from rich4.minigame_presentation import 小游戏演出_类, 小游戏结算_类
from rich4.minigames import 声音请求_类, 小游戏种类_类
from rich4.native_frame import 画框_类


# ◕ 功能
class 小游戏屏幕_类:
    """
    原待决策→真实小游戏→单次结果交接，模态全屏命中编号902。

    更新日志：
    2026.10.24 - 按原游戏/种子重启，人物变化不重启；时钟倒退按uint64封顶100毫秒。
    """

    def __init__(
        self,
        arg_美术: 美术_类,
        arg_声音: Callable[[声音请求_类], None] | None = None,
    ) -> None:
        self._美术, self._声音 = arg_美术, arg_声音
        self._演出: 小游戏演出_类 | None = None
        self._上次 = 0

    @staticmethod
    def api_处理(arg_决策: 决策_类) -> bool:
        return arg_决策.种类 == 决策种类_类.小游戏 and arg_决策.小游戏 is not None

    def api_活跃(self) -> bool:
        return self._演出 is not None

    def api_清空(self) -> None:
        if self._演出 is not None:
            self._演出.api_关闭()
            self._演出 = None

    def _点击(self, arg_框: 画框_类) -> None:
        if self._演出 is not None:
            self._演出.api_点击(arg_框.指针x, arg_框.指针y)

    def api_绘决策(self, arg_框: 画框_类, arg_决策: 决策_类) -> 小游戏结算_类 | None:
        if not self.api_处理(arg_决策):
            raise ValueError("原小游戏界面需要小游戏待决策")
        state = arg_决策.小游戏
        if self._演出 is None or self._演出.种子 != state.种子 or self._演出.种类 != state.游戏:
            self.api_清空()
            self._演出 = 小游戏演出_类(
                self._美术,
                小游戏种类_类(state.游戏 % 3),
                state.种子,
                state.人物,
                self._声音,
            )
            self._上次 = arg_框.时钟
        elapsed = min((arg_框.时钟 - self._上次) & 0xFFFFFFFFFFFFFFFF, 100)
        self._上次 = arg_框.时钟
        image, result = self._演出.api_帧(elapsed, arg_框.指针x, arg_框.按下)
        arg_框.画布.像素[:] = image.像素
        arg_框.按钮.clear()
        arg_框.api_命中(902, (0, 0, 640, 480), lambda: self._点击(arg_框))
        arg_框.按钮[-1].点击声音 = False
        if result is not None:
            self.api_清空()
        return result
