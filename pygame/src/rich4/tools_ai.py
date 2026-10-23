# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/tools_ai.cpp，原rich4_ai_use_tool.asm与UI访问次序。
# ◑ 导入
import math
from dataclasses import dataclass, field
from typing import Callable

from rich4.board_models import 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.economy import 经济_类
from rich4.events import 事件_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类
from rich4.world_player import 玩家状态_类


# ◕ 功能
@dataclass(frozen=True)
class 道具电脑决策_类:
    """
    原道具号及两阶段目标，传送目标是自己、目的地是道路号。

    更新日志：
    2026.10.23 - 对应tools_ai::Decision。
    """

    道具: int = 0
    目标: int = 0
    目的地: int = 0


@dataclass
class 道具电脑结果_类:
    """
    区分没有决策与缺少必要的原实例扫描。

    更新日志：
    2026.10.23 - 对应tools_ai::Result。
    """

    支持: bool = True
    决策: 道具电脑决策_类 | None = None
    消息: str = ""


@dataclass
class 道具电脑回调_类:
    """
    原渲染锚点或缓冲扫描与可选EDX残值，原生参考默认残值0。

    更新日志：
    2026.10.23 - 对应Callbacks；不把未捕获的原寄存器状态声称为已验证。
    """

    附近实例: Callable[[int], list[int]] | None = None
    所有权残值: Callable[[], int] | None = None


@dataclass
class 路径_类:
    """
    前瞻结果保留重复节点及任意分岔标志，不改变世界位置。

    更新日志：
    2026.10.23 - 对应内部Path。
    """

    节点: list[int] = field(default_factory=list)
    经过路口: bool = False


class 选择缓冲_类:
    """
    原440方形覆盖选择缓冲，以稀疏像素保存相同覆盖及行列扫描顺序。

    更新日志：
    2026.10.23 - 不使用原0x40a45c的或写入语义，位置沿原查表投影。
    """

    def __init__(self, arg_世: 世界_类, arg_中心: tuple[int, int]) -> None:
        self.相机 = 相机_类(arg_中心, arg_世.相机旋转 & 7)
        self.像素: dict[int, int] = {}

    def api_插入(self, arg_点: tuple[int, int], arg_码: int) -> None:
        屏 = 棋盘投影_类.api_投影(arg_点, self.相机)
        if 屏 is None:
            return
        x, y = 屏[0], 屏[1] - 40
        if 0 <= x < 440 and 0 <= y < 440:
            键 = y * 440 + x
            if arg_码 & 65535:
                self.像素[键] = arg_码 & 65535
            else:
                self.像素.pop(键, None)

    def api_扫描(self, arg_半径: int = -1) -> list[int]:
        首, 末 = (0, 440) if arg_半径 < 0 else (220 - arg_半径, 220 + arg_半径)
        if 首 < 0 or 末 > 440:
            raise ValueError("选择缓冲扫描超出原有效半径")
        return [
            值
            for 键, 值 in sorted(self.像素.items())
            if 首 <= 键 // 440 < 末 and 首 <= 键 % 440 < 末
        ]


class 道具电脑_类:
    """
    原十三道具谓词、攻击门控和至多四次UI访问，不消耗道具或改变世界。

    更新日志：
    2026.10.23 - 保留被拒绝分岔、覆盖像素和NaN无序比较的行为。
    """

    攻击性 = (0, 1, 1, 1, 0, 0, 2, 0, 1, 2, 1, 2, 2)
    设施上限 = (1, 5, 5, 1, 5)

    @staticmethod
    def _地码(arg_世: 世界_类, arg_码: int) -> bool:
        return 2000 < arg_码 < 4000 and arg_码 - 2000 < len(arg_世.地产)

    @staticmethod
    def _设施码(arg_世: 世界_类, arg_码: int) -> bool:
        return 4000 < arg_码 < 6000 and arg_码 - 4000 < len(arg_世.设施)

    @classmethod
    def _业主(cls, arg_世: 世界_类, arg_码: int) -> int:
        return (
            arg_世.地产[arg_码 - 2000].经济.业主
            if cls._地码(arg_世, arg_码)
            else arg_世.设施[arg_码 - 4000].业主
            if cls._设施码(arg_世, arg_码)
            else 0
        )

    @classmethod
    def _层(cls, arg_世: 世界_类, arg_码: int) -> int:
        return (
            arg_世.地产[arg_码 - 2000].经济.等级
            if cls._地码(arg_世, arg_码)
            else arg_世.设施[arg_码 - 4000].等级
            if cls._设施码(arg_世, arg_码)
            else 0
        )

    @staticmethod
    def _短(arg_数: int) -> int:
        return ((arg_数 + 32768) & 65535) - 32768

    @classmethod
    def _位置(cls, arg_世: 世界_类, arg_码: int) -> tuple[int, int]:
        p = (
            arg_世.地产[arg_码 - 2000]
            if cls._地码(arg_世, arg_码)
            else 事件_类._取(arg_世.设施, arg_码 - 4000)
        )
        return cls._短(p.x), cls._短(p.y)

    @staticmethod
    def _自己码(arg_槽: int) -> int:
        return (0x8000 | (1 << arg_槽)) & 65535

    @staticmethod
    def _缺席(arg_状: 玩家状态_类) -> bool:
        return bool(arg_状.酒店天数 or arg_状.消失天数 or arg_状.监狱天数 or arg_状.医院天数)

    @staticmethod
    def _同街数(arg_世: 世界_类, arg_槽: int, arg_地: int) -> int:
        名 = arg_世.地产[arg_地].经济.街道名.split(b"\0", 1)[0]
        return sum(
            地.经济.业主 == arg_槽 + 1 and 地.经济.街道名.split(b"\0", 1)[0] == 名
            for 地 in arg_世.地产[1:]
        )

    @staticmethod
    def _通行费(arg_世: 世界_类, arg_码: int) -> int:
        地 = arg_世.地产[arg_码 - 2000].经济
        return 经济_类.api_通行费(
            [另.经济 for 另 in arg_世.地产[1:]], 地.业主, arg_世.头.物价, 地.街道名
        )

    @staticmethod
    def _前瞻(
        arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_数: int, arg_逆: bool = False
    ) -> 路径_类:
        人 = arg_世.玩家[arg_槽].记录
        今, 前 = (人.上次节点, 人.节点) if arg_逆 else (人.节点, 人.上次节点)
        结果 = 路径_类()
        for _ in range(min(arg_数, 8)):
            候 = []
            if 0 <= 今 < len(arg_世.节点):
                节 = arg_世.节点[今]
                候 = [
                    后
                    for i, 后 in enumerate(节.邻居)
                    if 后 and 后 != 前 and not 节.标志 & (0x40000000 >> i)
                ]
            后 = 前
            if len(候) == 1:
                后 = 候[0]
            elif len(候) > 1:
                后 = 候[arg_随机.api_下一个() % len(候)]
                结果.经过路口 = True
            结果.节点.append(后)
            前, 今 = 今, 后
        return 结果

    @staticmethod
    def _可见道路(arg_世: 世界_类, arg_槽: int) -> list[int]:
        人 = arg_世.玩家[arg_槽].记录
        选 = 选择缓冲_类(arg_世, (人.x, 人.y))
        for i, 节 in enumerate(arg_世.节点[1:], 1):
            if not 节.标志 & 0x00FFFF00:
                选.api_插入((节.x, 节.y), i)
        return 选.api_扫描()

    @classmethod
    def _占地范围(
        cls, arg_世: 世界_类, arg_槽: int, arg_中心: tuple[int, int], arg_半径: int
    ) -> list[int]:
        选 = 选择缓冲_类(arg_世, arg_中心)
        人 = arg_世.玩家[arg_槽]
        if not cls._缺席(人.状态):
            选.api_插入((cls._短(人.记录.x), cls._短(人.记录.y)), cls._自己码(arg_槽))
        for i, 地 in enumerate(arg_世.地产[1:], 1):
            if 地.经济.业主:
                选.api_插入(cls._位置(arg_世, 2000 + i), 2000 + i)
        for i, 地 in enumerate(arg_世.设施[1:], 1):
            if 地.业主:
                选.api_插入(cls._位置(arg_世, 4000 + i), 4000 + i)
        return 选.api_扫描(arg_半径)

    @staticmethod
    def _有收容(arg_世: 世界_类, arg_节: int) -> bool:
        类 = arg_世.节点[arg_节].标志 & 255
        名单 = arg_世.监狱名单 if 类 == 4 else arg_世.医院名单
        return 类 in (4, 5) and any(名单[:4])

    @classmethod
    def _敌手(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int) -> int:
        选, 最 = -1, 0
        for i, 人 in enumerate(arg_世.玩家):
            if i != arg_槽 and 人.记录.控制标志:
                值 = 股市_类._回绕(arg_世.玩家[arg_槽].状态.敌意[i])
                if 值 > 最:
                    选, 最 = i, 值
        if 选 != -1:
            return 选
        候 = [
            i
            for i, 人 in enumerate(arg_世.玩家)
            if i != arg_槽 and 人.记录.控制标志 and not cls._缺席(人.状态)
        ]
        return 候[arg_随机.api_下一个() % len(候)] if 候 else -1

    @staticmethod
    def _选(arg_物: int, arg_目标: int = 0, arg_目的地: int = 0) -> 道具电脑结果_类:
        return 道具电脑结果_类(True, 道具电脑决策_类(arg_物, arg_目标, arg_目的地))

    @staticmethod
    def _缺实例() -> 道具电脑结果_类:
        return 道具电脑结果_类(
            False, None, "Tool AI needs the original rendered-instance selection."
        )

    @staticmethod
    def _比率(arg_分子: int, arg_分母: int) -> float:
        if not arg_分母:
            return math.inf if arg_分子 else math.nan
        return (扩展数_类.api_从值(arg_分子) / 扩展数_类.api_从值(arg_分母)).api_单精度()

    @classmethod
    def _谓词(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_物: int, arg_钩: 道具电脑回调_类
    ) -> 道具电脑结果_类:
        世, 随, 槽, 物, 钩 = arg_世, arg_随机, arg_槽, arg_物, arg_钩
        人 = 世.玩家[槽]
        自, 钱, 运, 交 = 槽 + 1, 人.记录.现金, 人.状态.财运修正, 人.记录.交通 & 3
        资 = 股市_类._回绕(钱 + 人.记录.银行)
        if 物 in (5, 6):
            if (交 == 0 if 物 == 5 else 交 < 2) and 随.api_下一个() % 4 == 0:
                return cls._选(物)
            return 道具电脑结果_类()
        if 物 == 12:
            return (
                cls._选(物)
                if 交 != 3 and 随.api_下一个() % 15 <= 人.状态.救援策略
                else 道具电脑结果_类()
            )
        if 物 == 10:
            return 道具电脑结果_类()
        if 物 == 1:
            路 = cls._前瞻(世, 随, 槽, 4)
            if 路.经过路口:
                return 道具电脑结果_类()
            for i in 路.节点:
                if not 0 <= i < len(世.节点):
                    continue
                节 = 世.节点[i]
                号 = 节.标志 >> 16 & 63
                if not 1 <= 号 <= len(世.物件):
                    continue
                类, 码 = 世.物件[号 - 1].种类, 节.类型索引
                主 = cls._业主(世, 码)
                if 5 <= 类 <= 8 or 类 == 11 or (类 == 17 and 主 == 自):
                    return cls._选(物)
                费 = (
                    cls._通行费(世, 码)
                    if cls._地码(世, 码)
                    else 10000000
                    if cls._设施码(世, 码)
                    else 0
                )
                if 类 == 16 and 主 and 主 != 自 and 费 > 股市_类._回绕(3000 * 世.头.物价):
                    return cls._选(物)
            return 道具电脑结果_类()
        if 物 == 2:
            路 = cls._前瞻(世, 随, 槽, 4)
            if not 路.经过路口:
                for i in 路.节点:
                    if not 0 <= i < len(世.节点):
                        continue
                    节 = 世.节点[i]
                    if 节.标志 & 0x003FFF00:
                        continue
                    码, 买, 价 = 节.类型索引, False, 0
                    if cls._地码(世, 码):
                        地 = 世.地产[码 - 2000]
                        买 = not 地.经济.业主 and (
                            cls._同街数(世, 槽, 码 - 2000) >= 2 or 地.经济.等级 != 0
                        )
                        价 = 地.地价
                    elif cls._设施码(世, 码):
                        地 = 世.设施[码 - 4000]
                        买, 价 = not 地.业主, 地.地价
                    elif 节.标志 & 255 == 15 and 人.记录.点券 > 200:
                        return cls._选(物, i)
                    if (
                        买
                        and 资 > 10000
                        and 运 >= 0
                        and not 人.状态.睡眠天数
                        and 股市_类._回绕(价 * 世.头.物价) < 钱
                    ):
                        return cls._选(物, i)
        if 2 <= 物 <= 4:
            路 = cls._前瞻(世, 随, 槽, 6, True)
            候, 选, 最高 = [], 0, 0
            for i in cls._可见道路(世, 槽):
                if i not in 路.节点:
                    continue
                码 = 世.节点[i].类型索引
                主 = cls._业主(世, 码)
                if 物 == 2:
                    if cls._地码(世, 码) and 主 == 自:
                        费 = cls._通行费(世, 码)
                        if 费 > 最高 and 费 > 股市_类._回绕(6000 * 世.头.物价):
                            选, 最高 = i, 费
                elif cls._有收容(世, i):
                    return cls._选(物, i)
                elif 物 == 4 or (主 and 主 != 自):
                    候.append(i)
            if 选:
                return cls._选(物, 选)
            return cls._选(物, 候[随.api_下一个() % len(候)]) if 候 else 道具电脑结果_类()
        if 物 == 7:
            敌 = cls._敌手(世, 随, 槽)
            if 敌 < 0:
                return 道具电脑结果_类()
            if not 钩.附近实例:
                return cls._缺实例()
            目 = next((码 for 码 in 钩.附近实例(槽) if 码 & 0x8000 and 码 & (1 << 敌)), 0)
            if not 目:
                return 道具电脑结果_类()
            敌人 = 世.玩家[敌].记录
            域 = cls._占地范围(世, 槽, (敌人.x, 敌人.y), 100)
            残 = 钩.所有权残值() if 钩.所有权残值 else 0
            for 码 in 域:
                if 码 & 0x8000 or cls._业主(世, 码) == 自 or 残 == 1:
                    return 道具电脑结果_类()
            return cls._选(物, 目)
        if 物 == 8:
            if 人.状态.神明信息 in (7, 8, 15) or 人.状态.睡眠天数 or 资 < 10000 or 运 < 0:
                return 道具电脑结果_类()
            路 = cls._前瞻(世, 随, 槽, 6)
            if 路.经过路口:
                return 道具电脑结果_类()
            最高, 选 = 0, 0
            for 步, i in enumerate(路.节点):
                if not 0 <= i < len(世.节点):
                    continue
                节 = 世.节点[i]
                if 节.标志 & 0xF000:
                    continue
                号 = 节.标志 >> 16 & 63
                if 0 < 号 <= len(世.物件):
                    类 = 世.物件[号 - 1].种类
                    if 5 <= 类 <= 8 or 类 in (10, 11) or 16 <= 类 <= 18:
                        continue
                码, 骰 = 节.类型索引, 步 + 1
                if cls._地码(世, 码):
                    地 = 世.地产[码 - 2000]
                    if (
                        not 地.经济.业主
                        and cls._同街数(世, 槽, 码 - 2000) > 1
                        and float(钱) > float(地.地价) * 2.5
                    ):
                        return cls._选(物, 骰)
                    if (
                        地.经济.业主 == 自
                        and not 地.经济.连锁
                        and 地.经济.等级 < 5
                        and 地.经济.等级 > 最高
                        and cls._同街数(世, 槽, 码 - 2000) > 1
                        and float(钱) > float(地.每级造价) * 2.5
                    ):
                        最高, 选 = 地.经济.等级, 骰
                elif cls._设施码(世, 码):
                    地 = 世.设施[码 - 4000]
                    if (not 地.业主 and float(钱) > float(地.地价) * 2.5) or (
                        地.业主 == 自
                        and 地.类型 not in (0, 3)
                        and 地.等级 < 5
                        and float(钱) > float(地.每级造价) * 2.5
                    ):
                        return cls._选(物, 骰)
            return cls._选(物, 选) if 选 else 道具电脑结果_类()
        if 物 == 9:
            if not 钩.附近实例:
                return cls._缺实例()
            选, 最高 = 0, 0
            for 码 in 钩.附近实例(槽):
                费 = 0
                if cls._地码(世, 码):
                    地 = 世.地产[码 - 2000].经济
                    if 地.业主 == 自 and not 地.连锁 and 地.等级 < 5:
                        费 = 事件_类._取(地.各级租金, 地.等级)
                elif cls._设施码(世, 码):
                    地 = 世.设施[码 - 4000]
                    if (
                        地.业主 == 自
                        and 地.类型 < len(cls.设施上限)
                        and 地.等级 < cls.设施上限[地.类型]
                    ):
                        费 = 地.各级租金[地.等级]
                if 费 > 最高:
                    选, 最高 = 码, 费
            return cls._选(物, 选) if 选 else 道具电脑结果_类()
        if 物 == 11:
            选, 最高 = 0, 0
            for i in cls._可见道路(世, 槽):
                码 = 世.节点[i].类型索引
                层 = cls._层(世, 码)
                if cls._业主(世, 码) or 层 < 3 or 层 <= 最高:
                    continue
                if cls._地码(世, 码) and not 世.地产[码 - 2000].经济.连锁:
                    价 = 世.地产[码 - 2000].每级造价
                elif cls._设施码(世, 码) and 世.设施[码 - 4000].类型 != 0:
                    价 = 世.设施[码 - 4000].每级造价
                else:
                    continue
                if 股市_类._回绕(价 * 世.头.物价) < 钱:
                    最高, 选 = 层, i
            return (
                cls._选(物, cls._自己码(槽), 选)
                if 选 and 资 > 10000 and 运 >= 0
                else 道具电脑结果_类()
            )
        if 物 == 13:
            候 = [
                2000 + i
                for i, 地 in enumerate(世.地产[1:], 1)
                if 地.经济.业主 and 地.经济.业主 != 自 and 地.经济.等级
            ]
            候 += [
                4000 + i
                for i, 地 in enumerate(世.设施[1:], 1)
                if 地.业主 and 地.业主 != 自 and 地.等级
            ]
            if not 候:
                return 道具电脑结果_类()
            活 = sum(人.记录.控制标志 != 0 for 人 in 世.玩家)
            阈 = (扩展数_类.api_从值(1) / 扩展数_类.api_从值(活 + 2)).api_单精度()
            for _ in range(10):
                目 = 候[随.api_下一个() % len(候)]
                域 = cls._占地范围(世, 槽, cls._位置(世, 目), -1)
                自见 = False
                自数, 他数, 自层, 他层 = 0, 0, 0, 0
                残 = 钩.所有权残值() if 钩.所有权残值 else 0
                for 码 in 域:
                    if 码 & 0x8000:
                        自见 = True
                        break
                    if cls._业主(世, 码) == 自 or 残 == 1:
                        自数 = (自数 + 1) & 0xFFFFFFFF
                        自层 = (自层 + cls._层(世, 码)) & 0xFFFFFFFF
                    else:
                        他数 = (他数 + 1) & 0xFFFFFFFF
                        他层 = (他层 + cls._层(世, 码)) & 0xFFFFFFFF
                    残 = 0
                if not 自见 and not cls._比率(自数, 他数) >= 阈 and not cls._比率(自层, 他层) >= 阈:
                    return cls._选(物, 目)
            return 道具电脑结果_类()
        return 道具电脑结果_类()

    @classmethod
    def api_评估(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_物: int, arg_钩: 道具电脑回调_类
    ) -> 道具电脑结果_类:
        if not 0 <= arg_槽 < min(len(arg_世.玩家), 4) or not 1 <= arg_物 <= len(cls.攻击性):
            return 道具电脑结果_类(False, None, "Invalid tool AI actor or tool ID.")
        偏 = cls.攻击性[arg_物 - 1] - arg_世.玩家[arg_槽].状态.救援策略
        if 偏 >= 2 or (偏 == 1 and arg_随机.api_下一个() % 3 != 0):
            return 道具电脑结果_类()
        return cls._谓词(arg_世, arg_随机, arg_槽, arg_物, arg_钩)

    @classmethod
    def api_选择(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_钩: 道具电脑回调_类
    ) -> 道具电脑结果_类:
        if not 0 <= arg_槽 < min(len(arg_世.玩家), 4):
            return 道具电脑结果_类(False, None, "Invalid tool AI actor.")
        人 = arg_世.玩家[arg_槽]
        if not 人.记录.控制标志 & 6 or not 人.状态.卡片策略 & 2:
            return 道具电脑结果_类()
        候 = [物 for 物 in range(1, 14) if 物 != 10 and 人.记录.道具[物 - 1]]
        if not 候:
            return 道具电脑结果_类()
        i = arg_随机.api_下一个() % len(候) if len(候) > 4 else 0
        for _ in range(4):
            果 = cls.api_评估(arg_世, arg_随机, arg_槽, 候[i], arg_钩)
            if not 果.支持 or 果.决策 is not None:
                return 果
            i = (i + 1) % len(候)
        return 道具电脑结果_类()
