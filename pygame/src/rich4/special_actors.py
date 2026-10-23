# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/special_actors.cpp；槽8机器人由独立规则处理。
# ◑ 导入
from copy import copy
from dataclasses import dataclass, field
from typing import Callable

from rich4.direction import 方向_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.services import 服务_类
from rich4.world import 世界_类
from rich4.world_actors import 特殊角色_类


# ◕ 功能
@dataclass
class 特殊效果_类:
    """
    原EffectKind编号及请求金额，结算由真实游戏会话回调负责。

    更新日志：
    2026.10.23 - 对应special_actors::Effect。
    """

    种类: int
    角色: int = 4
    目标: int = -1
    金额: int = 0
    节点: int = 0


@dataclass
class 特殊结果_类:
    """
    保留原支持状态、移动计划与顺序效果。

    更新日志：
    2026.10.23 - 对应special_actors::Result。
    """

    支持: bool = True
    停止移动: bool = False
    计划步数: int = 0
    已走步数: int = 0
    消息: str = ""
    效果: list[特殊效果_类] = field(default_factory=list)


@dataclass
class 特殊回调_类:
    """
    融资、物件归还/再生、特殊角色收容和表现接口，缺失依赖显式报告。

    更新日志：
    2026.10.23 - 对应Callbacks；不以空回调冒充已执行游戏规则。
    """

    付款: Callable[[int, int, int, int], None] | None = None
    移除物件: Callable[[int], None] | None = None
    监狱: Callable[[int, int], None] | None = None
    医院: Callable[[int, int], None] | None = None
    语音: Callable[[int, int], None] | None = None
    游戏结束: Callable[[], bool] | None = None
    步后: Callable[[int, int], None] | None = None


class 特殊行动_类:
    """
    槽4–7状态老化、原邻居寻路、停靠交互及完整特殊角色回合。

    更新日志：
    2026.10.23 - 原序分发及回绕；不改变header.current_player。
    """

    @staticmethod
    def _取(arg_表: list, arg_号: int):
        if not 0 <= arg_号 < len(arg_表):
            raise IndexError("特殊角色引用索引越界")
        return arg_表[arg_号]

    @classmethod
    def _角色(cls, arg_世: 世界_类, arg_槽: int) -> 特殊角色_类:
        if not 4 <= arg_槽 <= 7:
            raise IndexError("特殊角色槽位必须为4..7")
        return cls._取(arg_世.特殊角色, arg_槽 - 4)

    @staticmethod
    def _缺(arg_消息: str) -> 特殊结果_类:
        return 特殊结果_类(支持=False, 消息=arg_消息)

    @staticmethod
    def api_老化(arg_人: 特殊角色_类) -> None:
        for 名 in ("睡眠天数", "梦游天数", "停留天数", "龟行天数"):
            值 = getattr(arg_人, 名)
            setattr(arg_人, 名, 0 if 值 & 128 else 128 if 值 == 1 else max(0, 值 - 1))

    @classmethod
    def api_单步(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int) -> int:
        人 = cls._角色(arg_世, arg_槽)
        if not 人.节点:
            raise IndexError("活跃特殊角色没有节点")
        前 = cls._取(arg_世.节点, 人.节点)
        候选 = [
            号
            for i, 号 in enumerate(前.邻居)
            if 号 and 号 != 人.上次节点 and not 前.标志 & (0x40000000 >> i)
        ]
        后号 = 候选[arg_随机.api_下一个() % len(候选)] if 候选 else 人.上次节点
        if not 后号:
            raise IndexError("特殊角色没有前进或返回路线")
        后 = cls._取(arg_世.节点, 后号)
        人.上次节点, 人.节点 = 人.节点, 后号
        位 = 0x1000 << (arg_槽 - 4)
        前.标志 &= ~位 & 0xFFFFFFFF
        后.标志 |= 位
        人.方向 = 方向_类.api_计算(后.x - 前.x, 后.y - 前.y)
        人.x, 人.y = 后.x & 65535, 后.y & 65535
        return 后号

    @staticmethod
    def _奖语音(arg_随机: 随机数_类, arg_钩: 特殊回调_类, arg_主: int, arg_价: int) -> None:
        类 = 0 if arg_价 > 100 else arg_随机.api_下一个() & 1 if arg_价 > 50 else 2
        if arg_价 and arg_钩.语音:
            arg_钩.语音(arg_主, 类)

    @classmethod
    def api_交互(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_槽: int,
        arg_停靠: bool,
        arg_钩: 特殊回调_类,
    ) -> 特殊结果_类:
        人 = cls._角色(arg_世, arg_槽)
        节号 = 人.节点
        节 = copy(cls._取(arg_世.节点, 节号))
        事件, 物号 = 节.标志 & 255, 节.标志 >> 16 & 255
        类 = cls._取(arg_世.物件, 物号 - 1).种类 if 物号 else 0
        主 = 人.业主
        if not 0 <= 主 < len(arg_世.玩家):
            raise IndexError("特殊角色业主越界")
        结果 = 特殊结果_类()

        def 加(arg_类: int, arg_目标: int = -1, arg_金额: int = 0) -> None:
            结果.效果.append(特殊效果_类(arg_类, arg_槽, arg_目标, arg_金额, 节号))

        拾取 = arg_槽 == 4 and 人.梦游天数 == 0
        if (类 == 11 and arg_停靠) or (类 == 17 and arg_槽 != 4 and arg_停靠):
            if not arg_钩.移除物件 or not arg_钩.医院:
                return cls._缺("特殊角色住院规则尚未接入")
            arg_钩.移除物件(11 if 类 == 11 else 物号)
            arg_钩.医院(arg_槽, 3)
            结果.停止移动 = True
            加(7, arg_金额=3)
        elif 类 in (13, 14, 16, 17, 18) and 拾取:
            if not arg_钩.移除物件:
                return cls._缺("特殊角色道具拾取规则尚未接入")
            arg_钩.移除物件(类 if 类 in (13, 14) else 物号)
            if 类 == 14:
                主记录 = arg_世.玩家[主].记录
                主记录.点券 = (主记录.点券 + 500) & 65535
                加(3, 主, 500)
                if arg_钩.语音:
                    arg_钩.语音(主, 0)
            else:
                物 = 服务_类.api_随机道具(arg_世, arg_随机, 主) if 类 == 13 else 类 - 14
                if 物:
                    if 类 != 13:
                        服务_类._库存(arg_世, 主).api_收道具(物)
                    加(2, 主, 物)
                    if 类 == 13:
                        cls._奖语音(arg_随机, arg_钩, 主, 服务_类.道具价[物 - 1])
        elif 类 == 16 and arg_槽 != 4:
            if not arg_钩.移除物件:
                return cls._缺("特殊角色路障规则尚未接入")
            arg_钩.移除物件(物号)
            结果.停止移动 = True
            加(6)
        arg_停靠 = arg_停靠 or 结果.停止移动
        if 人.不活跃状态 == 0 and 人.梦游天数 == 0:
            if arg_槽 in (4, 5):
                受害位 = (节.标志 >> 8 & 15) & ~(1 << 主)
                if 受害位:
                    受 = (受害位 & -受害位).bit_length() - 1
                    目标 = arg_世.玩家[受].记录
                    if 目标.控制标志:
                        if arg_槽 == 4:
                            点 = 目标.点券 // 2
                            if 点:
                                目标.点券 -= 点
                                主记录 = arg_世.玩家[主].记录
                                主记录.点券 = (主记录.点券 + 点) & 65535
                                加(0, 受, 点)
                        else:
                            包 = 服务_类._库存(arg_世, 受)
                            数 = 包.api_卡数()
                            if 数:
                                卡 = 目标.卡片[arg_随机.api_下一个() % 数]
                                包.api_用卡(卡)
                                服务_类._库存(arg_世, 主).api_收卡(卡)
                                加(1, 受, 卡)
                if arg_槽 == 5 and 事件 == 14:
                    if not arg_钩.付款:
                        return cls._缺("特殊角色银行结算尚未接入")
                    for 受, 玩家 in enumerate(arg_世.玩家):
                        if 受 == 主 or not 玩家.记录.控制标志:
                            continue
                        钱 = (
                            扩展数_类.api_从值(玩家.记录.银行) * 扩展数_类.api_从值(0.2)
                        ).api_整数()
                        arg_钩.付款(受, 主, 钱, 5)
                        加(4, 受, 钱)
            elif arg_停靠:
                码, 钱, 付, 收 = 节.类型索引, 0, -1, False
                if 2000 < 码 < 4000:
                    地 = cls._取(arg_世.地产, 码 - 2000)
                    if 地.经济.业主 and 地.经济.业主 != 主 + 1:
                        付 = 地.经济.业主 - 1
                        if arg_槽 == 6:
                            钱 = (
                                sum(
                                    另.地价
                                    for 另 in arg_世.地产[1:]
                                    if 另.经济.业主 == 地.经济.业主
                                    and 另.经济.街道名 == 地.经济.街道名
                                )
                                * (arg_世.头.物价 & 0xFFFFFFFF)
                                & 0xFFFFFFFF
                            )
                            收 = True
                        else:
                            钱, 收 = 地.已移除建筑, 地.已移除建筑 != 0
                elif 4000 < 码 < 6000:
                    地 = cls._取(arg_世.设施, 码 - 4000)
                    if 地.业主 and 地.业主 != 主 + 1:
                        付 = 地.业主 - 1
                        钱 = (
                            地.地价 * (arg_世.头.物价 & 0xFFFFFFFF) & 0xFFFFFFFF
                            if arg_槽 == 6
                            else 地.已移除建筑
                        )
                        收 = arg_槽 == 6 or 钱 != 0
                elif 6000 < 码 < 8000 and arg_槽 == 7:
                    司 = cls._取(arg_世.公司, 码 - 6000)
                    if 司.业主 and 司.业主 != 主 + 1:
                        付, 钱 = 码 - 5900, 司.资金 & 0xFFFFFFFF
                        收 = 钱 != 0
                if 收:
                    if not arg_钩.付款:
                        return cls._缺("特殊角色地产结算尚未接入")
                    钱 = 服务_类._整数(钱)
                    arg_钩.付款(付, 主, 钱, 0)
                    加(5, 付, 钱)
        目的 = 人.标志 & 127
        if (目的 == 1 and 事件 == 4) or (目的 == 2 and 事件 == 5):
            if 人.标志 & 128:
                收容 = arg_钩.监狱 if 目的 == 1 else arg_钩.医院
                if not 收容:
                    return cls._缺("特殊角色返回监狱或医院规则尚未接入")
                收容(arg_槽, 0)
                结果.停止移动 = True
                加(8, arg_金额=目的)
            else:
                人.标志 |= 128
        return 结果

    @classmethod
    def api_回合(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_槽: int,
        arg_钩: 特殊回调_类,
    ) -> 特殊结果_类:
        人 = cls._角色(arg_世, arg_槽)
        结果 = 特殊结果_类()
        if 人.不活跃状态:
            return 结果
        cls.api_老化(人)
        if 人.睡眠天数 or 人.停留天数:
            return 结果
        结果.计划步数 = 1 if 人.龟行天数 else arg_随机.api_下一个() % 9 + 2
        for 步 in range(结果.计划步数):
            if arg_钩.游戏结束 and arg_钩.游戏结束():
                break
            节 = cls.api_单步(arg_世, arg_随机, arg_槽)
            结果.已走步数 += 1
            着陆 = cls.api_交互(arg_世, arg_随机, arg_槽, 步 + 1 == 结果.计划步数, arg_钩)
            结果.效果.extend(着陆.效果)
            if arg_钩.步后:
                arg_钩.步后(arg_槽, 节)
            if not 着陆.支持:
                结果.支持, 结果.消息 = False, 着陆.消息
                break
            if 着陆.停止移动 or 人.不活跃状态:
                结果.停止移动 = True
                break
        return 结果
