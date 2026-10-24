# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/native_game.cpp::observe/pump_presentation的有序分发；真实屏幕由宿主绑定。
# ◑ 导入
from collections import deque
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass

from rich4.game import 游戏会话_类
from rich4.game_types import 效果_类, 效果种类_类, 游戏事件_类, 游戏事件种类_类
from rich4.main_scene import 表现步_类


# ◕ 功能
@dataclass
class 呈现宿主_类:
    """
    必须绑定的真实表现组件接口；测试可观察路由，正式应用不得以空回调替代屏幕。

    更新日志：
    2026.10.24 - 忙碌回调合并原消息/电影/骰子/专属屏幕及其它模态状态。
    """

    忙碌: Callable[[], bool]
    观察事件: Callable[[游戏事件_类], None]
    呈现事件: Callable[[游戏事件_类], None]
    转盘: Callable[[效果_类], None]
    月报: Callable[[效果_类], None]
    电影: Callable[[list[效果_类], 游戏会话_类], None]


class 呈现队列_类:
    """
    原事件位置交错、顺序呈现、80毫秒暂停及核心可推进门控。

    更新日志：
    2026.10.24 - 只读规则已产生的输出，声音/动画/专属界面不得重新结算结果。
    """

    def __init__(self, arg_宿主: 呈现宿主_类) -> None:
        self.宿主 = arg_宿主
        self.步骤: deque[表现步_类] = deque()
        self.等待毫秒 = 0
        self.呈现玩家: int | None = None
        self.破产音乐 = False

    def api_忙碌(self) -> bool:
        return self.等待毫秒 > 0 or self.宿主.忙碌()

    def api_可推进(self) -> bool:
        return not self.步骤 and not self.api_忙碌()

    def api_消费等待(self, arg_毫秒: int) -> None:
        self.等待毫秒 -= min(self.等待毫秒, arg_毫秒 & 0xFFFFFFFF)

    def api_入队(self, arg_效果: list[效果_类], arg_事件: list[游戏事件_类]) -> None:
        效果, 事件 = deepcopy(arg_效果), deepcopy(arg_事件)
        下效 = 0

        def 补效(arg_事件位: int) -> None:
            nonlocal 下效
            # 依原头部顺序推进，不排序；after_events为同批事件的位置。
            while 下效 < len(效果) and 效果[下效].事件位 <= arg_事件位:
                self.步骤.append(表现步_类(效果=效果[下效]))
                下效 += 1

        for i, e in enumerate(事件):
            补效(i)
            self.步骤.append(表现步_类(事件=e))
            self.宿主.观察事件(e)
        补效(len(事件))

    def api_观察会话(
        self, arg_会话: 游戏会话_类, arg_托管重放: bool = False, arg_播放效果: bool = True
    ) -> None:
        效果 = arg_会话.api_取效果()
        事件 = arg_会话.api_取事件()
        self.api_入队(效果, 事件)
        self.api_泵(arg_会话, arg_托管重放, arg_播放效果)

    def api_泵(
        self,
        arg_会话: 游戏会话_类 | None,
        arg_托管重放: bool = False,
        arg_播放效果: bool = True,
    ) -> None:
        while arg_会话 is not None and self.步骤 and not self.api_忙碌():
            步 = self.步骤.popleft()
            e = 步.效果
            if e is not None:
                if e.种类 == 效果种类_类.暂停:
                    if not (arg_托管重放 and not arg_播放效果):
                        self.等待毫秒 = e.物件种类 * 80
                elif e.转盘 is not None and e.种类 in (效果种类_类.金额转盘, 效果种类_类.轮盘):
                    self.宿主.转盘(e)
                elif e.月报 is not None and e.种类 in (
                    效果种类_类.股利,
                    效果种类_类.彩票开奖,
                    效果种类_类.月报,
                ):
                    self.宿主.月报(e)
                else:
                    if e.种类 == 效果种类_类.破产:
                        self.破产音乐 = True
                    self.宿主.电影([e], arg_会话)
            else:
                e = 步.事件
                if e is None:
                    raise ValueError("原表现步必须包含事件或效果")
                if e.种类 == 游戏事件种类_类.回合开始:
                    self.呈现玩家 = e.玩家
                if e.种类 == 游戏事件种类_类.玩家破产:
                    self.破产音乐 = True
                self.宿主.呈现事件(e)
