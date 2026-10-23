# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/game.cpp 147..372；语音门控仍消费原共享随机流。
# ◑ 导入
from copy import deepcopy

from rich4.cards import 卡片用法_类, 卡片目标_类, 目标种类_类
from rich4.events import 事件_类
from rich4.game_types import (
    公告种类_类,
    决策_类,
    决策种类_类,
    决策选项_类,
    效果_类,
    效果点_类,
    效果种类_类,
    游戏事件_类,
    游戏事件种类_类,
    游戏阶段_类,
    语句表_类,
)
from rich4.gods import 神明_类
from rich4.stocks import 股市_类
from rich4.world_player import 玩家状态_类


# ◕ 功能
class 会话表现_类:
    """
    原会话事件/效果/语音/服装与阶段接口，真实规则由同一会话其它部分完成。

    更新日志：
    2026.10.24 - amount_voice/absence_voice原随机消费保留在会话。
    """

    def _发事件(self, arg_种: 游戏事件种类_类, arg_消息: str, arg_额: int = 0) -> None:
        self.事件队列.append(游戏事件_类(arg_种, self._当前(), arg_额, self._玩家().节点, arg_消息))

    def _效果(
        self, arg_种: 效果种类_类, arg_槽: int, arg_目标: 效果点_类, arg_地产: int = 0
    ) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽).记录
        self.效果队列.append(
            效果_类(arg_种, arg_槽, 人.节点, arg_目标, 地产=arg_地产, 事件位=len(self.事件队列))
        )

    def _地图影片(
        self,
        arg_种: 效果种类_类,
        arg_槽: int,
        arg_目标: 效果点_类,
        arg_起点: 效果点_类 | None,
        arg_变体: int = 0,
    ) -> None:
        self._效果(arg_种, arg_槽, arg_目标)
        self.效果队列[-1].起点, self.效果队列[-1].物件种类 = arg_起点, arg_变体 & 255

    def _在场(self, arg_槽: int) -> bool:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        状 = 人.状态
        return bool(
            人.记录.控制标志
            and (人.记录.x or 人.记录.y)
            and (
                not (状.酒店天数 | 状.消失天数 | 状.监狱天数 | 状.医院天数)
                or 人.记录.控制标志 & 0x20
            )
        )

    def _服装键(self, arg_槽: int) -> int:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        return (
            人.记录.交通 | (0x100 if 人.状态.梦游天数 else 0) | (0x200 if 人.状态.睡眠天数 else 0)
        )

    def _结束服装(self, arg_槽: int) -> None:
        if 0 <= arg_槽 < len(self.服装):
            self.服装[arg_槽] = 0

    def _刷新服装(self) -> None:
        for 槽 in range(min(len(self.服装), len(self.世界.玩家))):
            if self.服装[槽] and self.服装键[槽] != self._服装键(槽):
                self.服装[槽] = 0

    def _角色点(self, arg_槽: int) -> 效果点_类:
        人 = 事件_类._取(self.世界.玩家, arg_槽).记录
        return 效果点_类(人.x, 人.y)

    def _地产点(self, arg_码: int) -> 效果点_类:
        点 = self._实例位置(arg_码)
        return 效果点_类(点.x, 点.y)

    def _地产层(self, arg_码: int) -> int:
        if 2000 < arg_码 < 4000 and arg_码 - 2000 < len(self.世界.地产):
            return self.世界.地产[arg_码 - 2000].经济.等级
        if 4000 < arg_码 < 6000 and arg_码 - 4000 < len(self.世界.设施):
            return self.世界.设施[arg_码 - 4000].等级
        return 0

    def _顶楼闪光(self, arg_码: int, arg_原层: int) -> None:
        if arg_原层 < 5 and self._地产层(arg_码) == 5:
            self._效果(效果种类_类.顶楼闪光, self._当前(), self._地产点(arg_码), arg_码)

    def _道具效果(self, arg_物: int, arg_目标: int) -> None:
        if not 2 <= arg_物 <= 4 or not 0 < arg_目标 < len(self.世界.节点):
            return
        节 = self.世界.节点[arg_目标]
        self.效果队列.append(
            效果_类(
                效果种类_类.抛物,
                self._当前(),
                arg_目标,
                效果点_类(节.x, 节.y),
                self._角色点(self._当前()),
                arg_物 + 14,
                事件位=len(self.事件队列),
            )
        )

    def _卡片效果(self, arg_卡: int, arg_目标: 卡片目标_类 | None) -> None:
        if arg_卡 not in (11, 12):
            return
        目标 = arg_目标 if arg_目标 is not None else self.选定卡目标
        if 目标 is None or 目标.种类 != 目标种类_类.地产:
            return
        self._效果(
            效果种类_类.拆屋 if arg_卡 == 12 else 效果种类_类.怪兽,
            self._当前(),
            self._地产点(目标.数值),
            目标.数值,
        )

    def _抛卡(self, arg_用: 卡片用法_类) -> None:
        飞 = (4, 5, 9, 10, 11, 12, 13, 14, 16, 17, 23, 26, 27, 28, 29, 30)
        if self._人类() or arg_用.目标 is None or arg_用.卡片 not in 飞:
            return
        目标, 点 = arg_用.目标, None
        值 = 目标.数值
        if 目标.种类 == 目标种类_类.角色 and 0 <= 值 < len(self.世界.玩家):
            点 = self._角色点(值)
        elif 目标.种类 == 目标种类_类.地产:
            点 = self._地产点(值)
        elif 目标.种类 == 目标种类_类.物件 and 0 < 值 <= len(self.世界.物件):
            节 = self.世界.物件[值 - 1].节点
            if 0 < 节 < len(self.世界.节点):
                点 = 效果点_类(self.世界.节点[节].x, self.世界.节点[节].y)
        if 点 is None:
            return
        self._效果(效果种类_类.抛卡, self._当前(), 点, 值 if 目标.种类 == 目标种类_类.地产 else 0)
        self.效果队列[-1].起点 = self._角色点(self._当前())

    def _公告(self, arg_种: 公告种类_类, arg_槽: int, arg_号: int = 0) -> 游戏事件_类:
        事 = 游戏事件_类(
            游戏事件种类_类.提示,
            arg_槽,
            节点=事件_类._取(self.世界.玩家, arg_槽).记录.节点,
            公告=arg_种,
            公告号=arg_号 & 255,
        )
        self.事件队列.append(事)
        return 事

    def _语句(self, arg_槽: int, arg_表: 语句表_类, arg_行: int, arg_表情: int) -> None:
        if not 0 <= arg_槽 < len(self.世界.玩家):
            return
        状 = self.世界.玩家[arg_槽].状态
        if 状.消失天数 or 状.梦游天数 or 状.睡眠天数:
            return
        self.事件队列.append(
            游戏事件_类(
                游戏事件种类_类.提示,
                arg_槽,
                节点=self.世界.玩家[arg_槽].记录.节点,
                语句表=arg_表,
                语句槽=arg_行 & 255,
                表情=arg_表情 & 255,
            )
        )

    def _卡片语句(self, arg_槽: int, arg_行: int, arg_卡: int, arg_表情: int) -> None:
        self._语句(arg_槽, 语句表_类.卡片, arg_行 * 30 + arg_卡 - 1, arg_表情)

    def _开始卡片(self, arg_用: 卡片用法_类) -> None:
        self.选定卡目标, self.使用中卡, self.卡图已示 = None, deepcopy(arg_用), False

    def _卡图(self) -> None:
        if self.使用中卡 is None or self.卡图已示:
            return
        self.卡图已示 = True
        self._卡片效果(self.使用中卡.卡片, self.使用中卡.目标)

    def _语音(self, arg_槽: int, arg_类: int) -> None:
        self.事件队列.append(
            游戏事件_类(
                游戏事件种类_类.提示,
                arg_槽,
                节点=事件_类._取(self.世界.玩家, arg_槽).记录.节点,
                语音类别=arg_类 & 255,
            )
        )

    def _音效(self, arg_槽: int, arg_效: int) -> None:
        节 = self.世界.玩家[arg_槽].记录.节点 if 0 <= arg_槽 < len(self.世界.玩家) else 0
        self.事件队列.append(游戏事件_类(游戏事件种类_类.提示, arg_槽, 节点=节, 音效=arg_效 & 255))

    def _公告免租(self, arg_主: 玩家状态_类, arg_主槽: int, arg_临时: int, arg_地产: int) -> None:
        因 = (
            0
            if arg_临时 & 0xF0 and arg_临时 & 15
            else 1
            if arg_主.盟友 == self._当前() + 1
            else 2
            if arg_主.神明信息 == 15
            else 3
            if arg_主.酒店天数
            else 4
            if arg_主.消失天数
            else 5
            if arg_主.监狱天数
            else 6
            if arg_主.医院天数
            else 7
            if arg_主.睡眠天数
            else 8
        )
        框 = self._公告(公告种类_类.免租, self._当前(), 因)
        框.主体, 框.地产 = arg_主槽, arg_地产
        self._语音(self._当前(), 13)

    def _金额语音(self, arg_槽: int, arg_额: int, arg_类: int) -> None:
        if arg_额 <= 0:
            return
        if arg_额 >= 股市_类._回绕(9000 * self.世界.头.物价):
            self._语音(arg_槽, arg_类)
        elif arg_额 >= 股市_类._回绕(5000 * self.世界.头.物价):
            self._语音(arg_槽, arg_类 + (self.随机.api_下一个() & 1))
        elif arg_类 != 6 or arg_额 >= 股市_类._回绕(2000 * self.世界.头.物价):
            self._语音(arg_槽, arg_类 + 2)

    def _缺席语音(self, arg_槽: int, arg_天: int) -> None:
        if arg_天 > 6:
            self._语音(arg_槽, 3)
        elif arg_天 > 3:
            self._语音(arg_槽, 3 + (self.随机.api_下一个() & 1))
        elif arg_天 > 0:
            self._语音(arg_槽, 5)

    def _置阶段(self, arg_阶段: 游戏阶段_类) -> None:
        self.阶段, self.阶段毫秒 = arg_阶段, 0

    def _结束回合(self) -> None:
        if self.阶段 == 游戏阶段_类.结束:
            return
        if self.地产待处理:
            self.地产待处理 = False
            已购, self.已购地产 = self.已购地产, False

            def 动作() -> None:
                if 已购:
                    self._检查神明(
                        神明_类.api_购地后(
                            self.世界, self.随机, self._当前(), self._玩家().节点, self._神明回调()
                        )
                    )
                self._检查神明(
                    神明_类.api_地产后(self.世界, self._当前(), self._玩家().节点, self._神明回调())
                )
                self._工程车拆屋()

            self._执行规则(动作)
            return
        self.待决策, self.动画 = None, None
        if self.地产落点:
            self.地产落点 = False
            self._暂停(8)
        self._置阶段(游戏阶段_类.推进回合)

    def _暂停(self, arg_tick: int) -> None:
        self._效果(效果种类_类.暂停, self._当前(), self._角色点(self._当前()))
        self.效果队列[-1].物件种类 = arg_tick & 255

    def _不支持(self, arg_消息: str, arg_恢复: 游戏阶段_类 = 游戏阶段_类.推进回合) -> None:
        self.未支持恢复 = arg_恢复
        self._发事件(游戏事件种类_类.未支持事件, arg_消息)
        if self._人类():
            self.待决策 = 决策_类(
                决策种类_类.提示, self._当前(), 提示="本次事件略過。", 选项=[决策选项_类("繼續", 0)]
            )
            self._置阶段(游戏阶段_类.等待决策)
        else:
            self._结束回合()
