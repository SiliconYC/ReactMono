# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/game.cpp::drop_replayed/run_rule；仅回滚源指定字段。
# ◑ 导入
from bisect import bisect_left
from copy import deepcopy
from dataclasses import replace
from typing import Callable

from rich4.game_types import 已展示_类, 待选择异常_类, 未支持规则异常_类, 游戏阶段_类


# ◕ 功能
class 会话事务_类:
    """
    选择时回滚真实规则、保留已展示内容并带答案续行，不捕获其它异常。

    更新日志：
    2026.10.24 - 由完整GameSession持有世界与队列；本类不提供替代规则。
    """

    def _去重表现(self, arg_事件数: int, arg_效果数: int, arg_已示: 已展示_类) -> None:
        删除 = []
        for i in range(arg_事件数, len(self.事件队列)):
            if len(删除) >= len(arg_已示.事件):
                break
            if self.事件队列[i] == arg_已示.事件[len(删除)]:
                删除.append(i)
        if 删除 and len(删除) == len(arg_已示.事件):
            for i in reversed(删除):
                del self.事件队列[i]
            for 效 in self.效果队列[arg_效果数:]:
                效.事件位 -= bisect_left(删除, 效.事件位)
        删除 = []
        for i in range(arg_效果数, len(self.效果队列)):
            if len(删除) >= len(arg_已示.效果):
                break
            旧 = arg_已示.效果[len(删除)]
            if replace(self.效果队列[i], 事件位=旧.事件位) == 旧:
                删除.append(i)
        if 删除 and len(删除) == len(arg_已示.效果):
            for i in reversed(删除):
                del self.效果队列[i]

    def _执行规则(
        self,
        arg_动作: Callable[[], None],
        arg_首次: bool = True,
        arg_结束后: bool = True,
        arg_成功: Callable[[], None] | None = None,
        arg_已示: 已展示_类 | None = None,
    ) -> None:
        if arg_首次:
            self.事件选择.clear()
            self.选择随机状态.clear()
        完成 = False
        self.选择序列 = 0
        世界, 种子, 记忆 = deepcopy(self.世界), self.随机.状态, deepcopy(self.卡片电脑记忆)
        事件数, 效果数, 旧阶段 = len(self.事件队列), len(self.效果队列), self.阶段

        def 恢复() -> None:
            self.世界.api_覆盖(世界)
            self.随机.状态 = 种子
            del self.事件队列[事件数:]
            del self.效果队列[效果数:]
            self.阶段 = 旧阶段
            self.卡片电脑记忆.参数0, self.卡片电脑记忆.参数1, self.卡片电脑记忆.参数2 = (
                记忆.参数0,
                记忆.参数1,
                记忆.参数2,
            )

        try:
            arg_动作()
            if arg_已示 is not None:
                self._去重表现(事件数, 效果数, arg_已示)
            self.待续 = None
            self.事件选择.clear()
            self.选择随机状态.clear()
            完成 = True
            if self.阶段 != 游戏阶段_类.结束 and (
                arg_结束后 or self.阶段 not in (游戏阶段_类.掷骰, 游戏阶段_类.移动)
            ):
                if arg_结束后:
                    self._结束回合()
                else:
                    self.待决策 = None
                    self._置阶段(游戏阶段_类.人类待命)
        except 待选择异常_类 as 选:
            if arg_已示 is not None:
                self._去重表现(事件数, 效果数, arg_已示)
            新事件 = deepcopy(self.事件队列[事件数:])
            新效果 = deepcopy(self.效果队列[效果数:])
            恢复()
            self.事件队列.extend(新事件)
            self.效果队列.extend(新效果)
            已示 = deepcopy(arg_已示) if arg_已示 is not None else 已展示_类()
            已示.事件.extend(deepcopy(新事件))
            已示.效果.extend(deepcopy(新效果))
            self.待决策, self.待选择键 = 选.决策, 选.键
            self.待续 = lambda: self._执行规则(arg_动作, False, arg_结束后, arg_成功, 已示)
            self._置阶段(游戏阶段_类.等待决策)
        except 未支持规则异常_类 as 错:
            恢复()
            self.待续 = None
            self.事件选择.clear()
            self._不支持(错.消息, 游戏阶段_类.推进回合 if arg_结束后 else 游戏阶段_类.人类待命)
        if 完成 and arg_成功:
            arg_成功()
