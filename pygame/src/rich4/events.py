# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/events.cpp；嵌套融资/收容/范围破坏由真实会话回调接入。
# ◑ 导入
import struct
from dataclasses import dataclass, field
from typing import Callable

from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.services import 服务_类
from rich4.world import 世界_类
from rich4.world_player import 世界玩家_类


# ◕ 功能
@dataclass
class 事件选择_类:
    """
    原牌堆来源编号、重映射事件及下一游标，选择本身只读世界。

    更新日志：
    2026.10.23 - 对应EventSelection。
    """

    来源: int = 0
    事件: int = 0
    下一游标: int = 0
    跳过: int = 0


@dataclass
class 事件结果_类:
    """
    原事件结果及供正文/头像行使用的参数，不以文字代替规则。

    更新日志：
    2026.10.23 - 对应EventResult全部字段。
    """

    支持: bool = False
    事件: int = 0
    消息: str = ""
    地产: int = 0
    主体: int = -1
    公司: int = -1
    数值: int = 0
    玩家掩码: int = 0
    玩家金额: list[int] = field(default_factory=lambda: [0] * 4)


@dataclass
class 事件回调_类:
    """
    同一世界上的原融资/伤病/选卡/拍卖/范围损坏和表现边界。

    更新日志：
    2026.10.23 - 对应EventCallbacks；原语音类别已确定，不得另抽规则随机数。
    """

    语音: Callable[[int, int], None] | None = None
    付款: Callable[[int, int, int, int], None] | None = None
    监狱: Callable[[int, int], None] | None = None
    医院: Callable[[int, int], None] | None = None
    消失: Callable[[int, int, int], None] | None = None
    防御: Callable[[int], int] | None = None
    贷款到期: Callable[[int], None] | None = None
    卖股: Callable[[int, int, int, bool], None] | None = None
    拍卖: Callable[[int], None] | None = None
    选卡: Callable[[int, int], int] | None = None
    范围损坏: Callable[[int, int, int, bool], None] | None = None
    更新股票: Callable[[int], None] | None = None
    新闻画面: Callable[[int, int], None] | None = None


@dataclass(frozen=True)
class 事件地产_类:
    """
    事件选择时的地产快照，效果和回调之后仍使用原业主/坐标。

    更新日志：
    2026.10.23 - 对应内部Property值类型。
    """

    码: int
    x: int
    y: int
    业主: int
    等级: int


class 事件_类:
    """
    固定新闻和命运牌堆准入、游标选择及真实规则分发。

    更新日志：
    2026.10.23 - 按原次序翻译events.cpp，回调未接入时不伪造结果。
    """

    @staticmethod
    def _取(arg_表: list, arg_号: int):
        if not 0 <= arg_号 < len(arg_表):
            raise IndexError("事件索引越界")
        return arg_表[arg_号]

    @staticmethod
    def _活(arg_人: 世界玩家_类) -> bool:
        return arg_人.记录.控制标志 != 0

    @classmethod
    def _在图(cls, arg_人: 世界玩家_类) -> bool:
        状 = arg_人.状态
        return cls._活(arg_人) and not (状.酒店天数 or 状.消失天数 or 状.监狱天数 or 状.医院天数)

    @staticmethod
    def _除(arg_数: int, arg_分母: int) -> int:
        return -(abs(arg_数) // arg_分母) if arg_数 < 0 else arg_数 // arg_分母

    @staticmethod
    def _比例(arg_金额: int, arg_位: int) -> int:
        指数 = arg_位 >> 23 & 255
        if 指数 == 255:
            return -2147483648
        负 = (arg_金额 < 0) != bool(arg_位 >> 31)
        有效数 = (arg_位 & 0x7FFFFF) | (0 if 指数 == 0 else 0x800000)
        积, 移 = abs(arg_金额) * 有效数, (1 if 指数 == 0 else 指数) - 150
        if 移 >= 0:
            if 移 >= 63 or 积 > 0x80000000 >> 移:
                return -2147483648
            积 <<= 移
        else:
            积 = 0 if 移 <= -64 else 积 >> -移
        if 积 > (0x80000000 if 负 else 0x7FFFFFFF):
            return -2147483648
        return -积 if 负 else 积

    @classmethod
    def _收入(cls, arg_世: 世界_类, arg_槽: int, arg_钱: int, arg_现金: bool = True) -> None:
        人 = cls._取(arg_世.玩家, arg_槽)
        if arg_现金:
            人.记录.现金 = 服务_类._整数(人.记录.现金 + arg_钱)
        else:
            人.记录.银行 = 服务_类._整数(人.记录.银行 + arg_钱)
        人.状态.累计收入 = (人.状态.累计收入 + arg_钱) & 0xFFFFFFFF

    @staticmethod
    def _语音(arg_钩: 事件回调_类, arg_槽: int, arg_类: int) -> None:
        if arg_钩.语音:
            arg_钩.语音(arg_槽, arg_类)

    @classmethod
    def _钱语音(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_钱: int,
        arg_槽: int,
        arg_基: int,
        arg_钩: 事件回调_类,
    ) -> None:
        if arg_钱 >= 服务_类._整数(9000 * arg_世.头.物价):
            cls._语音(arg_钩, arg_槽, arg_基)
        elif arg_钱 >= 服务_类._整数(5000 * arg_世.头.物价):
            cls._语音(arg_钩, arg_槽, arg_基 + (arg_随机.api_下一个() & 1))
        elif arg_钱 >= (服务_类._整数(2000 * arg_世.头.物价) if arg_基 == 6 else 1):
            cls._语音(arg_钩, arg_槽, arg_基 + 2)

    @staticmethod
    def _运势(arg_人: 世界玩家_类, arg_随机: 随机数_类, arg_身体: bool, arg_不利: bool) -> int:
        抗 = arg_人.状态.其他运修正 if arg_身体 else arg_人.状态.财运修正
        if arg_身体 or arg_不利:
            return 1 if 抗 > 100 else arg_随机.api_下一个() & 1 if 抗 > 50 else 2 if 抗 < 0 else 0
        return 2 if 抗 > 100 else (arg_随机.api_下一个() & 1) * 2 if 抗 > 50 else 1 if 抗 < 0 else 0

    @classmethod
    def _保险(cls, arg_世: 世界_类, arg_槽: int, arg_钱: int, arg_钩: 事件回调_类) -> None:
        if cls._取(arg_世.玩家, arg_槽).状态.保险天数 == 0:
            return
        for 司, 公司 in enumerate(arg_世.公司[1:], 1):
            if 公司.类型 == 4:
                arg_钩.付款(司 + 100, arg_槽, arg_钱, 1)
                return
        raise ValueError("保险事件在地图上找不到原保险公司")

    @staticmethod
    def _缺(arg_号: int, arg_功能: str) -> 事件结果_类:
        return 事件结果_类(False, arg_号, "Event requires " + arg_功能)

    @staticmethod
    def _成(arg_号: int, arg_消息: str, arg_数值: int = 0) -> 事件结果_类:
        return 事件结果_类(True, arg_号, arg_消息, 数值=arg_数值)

    @staticmethod
    def _地产(arg_世: 世界_类) -> list[事件地产_类]:
        return [
            事件地产_类(2000 + i, 地.x, 地.y, 地.经济.业主, 地.经济.等级)
            for i, 地 in enumerate(arg_世.地产[1:], 1)
        ] + [
            事件地产_类(4000 + i, 地.x, 地.y, 地.业主, 地.等级)
            for i, 地 in enumerate(arg_世.设施[1:], 1)
        ]

    @staticmethod
    def _选(arg_候选: list, arg_随机: 随机数_类):
        if not arg_候选:
            raise ValueError("原事件候选清单为空")
        return arg_候选[arg_随机.api_下一个() % len(arg_候选)]

    @classmethod
    def _释放酒店(cls, arg_世: 世界_类) -> None:
        for 人 in arg_世.玩家:
            if cls._活(人) and 人.状态.酒店天数:
                人.状态.酒店天数 = 128

    @classmethod
    def _损坏(cls, arg_世: 世界_类, arg_码: int, arg_没收: bool) -> None:
        if 2000 < arg_码 < 4000:
            地 = cls._取(arg_世.地产, arg_码 - 2000)
            if arg_没收:
                地.经济.业主 = 地.经济.等级 = 地.经济.连锁 = 地.到期日 = 0
            elif 地.经济.等级:
                地.经济.等级 -= 1
                if 地.经济.连锁:
                    地.经济.等级 = 地.经济.连锁 = 0
        elif 4000 < arg_码 < 6000:
            地 = cls._取(arg_世.设施, arg_码 - 4000)
            if arg_没收:
                地.业主 = 地.等级 = 地.类型 = 地.到期日 = 0
                cls._释放酒店(arg_世)
            elif 地.等级:
                地.等级 -= 1
                if 地.等级 == 0:
                    地.类型 = 0
                    cls._释放酒店(arg_世)
        else:
            raise ValueError("事件地产编码无效")

    @classmethod
    def _调地价(cls, arg_世: 世界_类, arg_地: 事件地产_类, arg_涨: bool) -> None:
        def 新价(arg_价: int) -> int:
            return (
                arg_价 * 13 // 10
                if arg_涨
                else arg_价 * 7 // 10 - int(arg_价 != 0 and arg_价 % 10 == 0)
            ) & 65535

        if arg_地.码 < 4000:
            名 = cls._取(arg_世.地产, arg_地.码 - 2000).经济.街道名
            for 地 in arg_世.地产[1:]:
                if 地.经济.街道名 == 名:
                    地.地价 = 新价(地.地价)
        else:
            地 = cls._取(arg_世.设施, arg_地.码 - 4000)
            地.地价 = 新价(地.地价)

    @classmethod
    def api_新闻可用(cls, arg_世: 世界_类, arg_号: int) -> bool:
        if not 0 <= arg_号 < 36:
            raise ValueError("新闻牌堆事件编号无效")
        if arg_号 < 4:
            return any((arg_世.监狱名单 if arg_号 < 2 else arg_世.医院名单)[:4])
        if arg_号 in (4, 5, 15):
            return any(地.等级 != 0 and (arg_号 != 15 or 地.码 < 4000) for 地 in cls._地产(arg_世))
        if arg_号 == 7:
            return any(地.业主 == 0 for 地 in cls._地产(arg_世))
        if arg_号 in (8, 9, 12):
            return any(地.业主 != 0 for 地 in cls._地产(arg_世))
        if arg_号 in (10, 13):
            return any(cls._活(人) and any(股.数量 != 0 for 股 in 人.持仓) for 人 in arg_世.玩家)
        if arg_号 in (16, 17):
            return any(
                cls._活(人) and (人.记录.交通 == 0 if arg_号 == 16 else 人.记录.交通 != 0)
                for 人 in arg_世.玩家
            )
        if arg_号 == 28:
            return any(股.停牌天数 != 0 for 股 in arg_世.股票)
        if arg_号 == 29:
            return any(
                0 < 司.业主 <= len(arg_世.玩家) and cls._在图(arg_世.玩家[司.业主 - 1])
                for 司 in arg_世.公司[1:]
            )
        if arg_号 == 35:
            return any(司.资金 > 10000 for 司 in arg_世.公司[1:])
        return True

    @classmethod
    def api_命运可用(cls, arg_世: 世界_类, arg_槽: int, arg_号: int) -> int | None:
        if not 0 <= arg_号 < 37:
            raise ValueError("命运牌堆基础事件编号无效")
        人 = cls._取(arg_世.玩家, arg_槽)
        if arg_号 in (0, 1):
            return (
                arg_号
                if any(
                    地.经济.业主 == arg_槽 + 1
                    and (地.经济.等级 != 0 if arg_号 == 0 else 地.经济.等级 == 0)
                    for 地 in arg_世.地产[1:]
                )
                else None
            )
        if arg_号 == 5:
            return (
                arg_号
                if any(i != arg_槽 and any(另.记录.卡片) for i, 另 in enumerate(arg_世.玩家))
                else None
            )
        if arg_号 in (8, 9):
            return arg_号 if any(股.数量 != 0 for 股 in 人.持仓) else None
        if arg_号 in (10, 11):
            return 9 + 人.记录.交通 if 人.记录.交通 in (1, 2) else None
        if arg_号 in (12, 13):
            return 12 + 人.记录.交通 if 人.记录.交通 <= 1 else None
        if arg_号 in (14, 15, 16):
            return 14 + 人.记录.交通 if 人.记录.交通 <= 2 else None
        if arg_号 >= 33:
            if arg_世.头.阶段 != 0:
                return None
            if arg_世.头.地图 > 3:
                raise ValueError("命运地域事件地图无效")
            return arg_号 + arg_世.头.地图 * 4
        return arg_号

    @classmethod
    def api_选新闻(cls, arg_世: 世界_类) -> 事件选择_类:
        if not 0 <= arg_世.新闻游标 < len(arg_世.新闻牌堆):
            raise ValueError("新闻游标越界")
        游 = arg_世.新闻游标
        for 跳 in range(len(arg_世.新闻牌堆)):
            号, 游 = arg_世.新闻牌堆[游], (游 + 1) % 36
            if cls.api_新闻可用(arg_世, 号):
                return 事件选择_类(号, 号, 游, 跳)
        raise ValueError("新闻牌堆没有可用事件")

    @classmethod
    def api_选命运(cls, arg_世: 世界_类, arg_槽: int) -> 事件选择_类:
        if not 0 <= arg_世.命运游标 < len(arg_世.命运牌堆):
            raise ValueError("命运游标越界")
        游 = arg_世.命运游标
        for 跳 in range(len(arg_世.命运牌堆)):
            号, 游 = arg_世.命运牌堆[游], (游 + 1) % 37
            事件 = cls.api_命运可用(arg_世, arg_槽, 号)
            if 事件 is not None:
                return 事件选择_类(号, 事件, 游, 跳)
        raise ValueError("命运牌堆没有可用事件")

    @classmethod
    def api_新闻(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_钩: 事件回调_类) -> 事件结果_类:
        结果 = 事件结果_类()
        for _ in range(len(arg_世.新闻牌堆)):
            选 = cls.api_选新闻(arg_世)
            结果 = cls.api_新闻编号(arg_世, arg_随机, 选.事件, arg_钩)
            arg_世.新闻游标 = 选.下一游标
            if 结果.支持:
                break
        return 结果

    @classmethod
    def api_命运(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_钩: 事件回调_类
    ) -> 事件结果_类:
        结果 = 事件结果_类()
        for _ in range(len(arg_世.命运牌堆)):
            选 = cls.api_选命运(arg_世, arg_槽)
            结果 = cls.api_命运编号(arg_世, arg_随机, arg_槽, 选.事件, arg_钩)
            arg_世.命运游标 = 选.下一游标
            if 结果.支持:
                break
        return 结果

    @classmethod
    def api_新闻编号(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_号: int, arg_钩: 事件回调_类
    ) -> 事件结果_类:
        号, 世, 随机, 钩 = arg_号, arg_世, arg_随机, arg_钩
        if not 0 <= 号 < 36:
            raise ValueError("新闻处理编号无效")
        if 号 in (4, 20) and not 钩.范围损坏:
            return cls._缺(号, "original square-area damage")
        if 号 == 7 and not 钩.拍卖:
            return cls._缺(号, "property auction choice")
        if 11 <= 号 <= 13 and not 钩.付款:
            return cls._缺(号, "payment and bankruptcy handling")
        if (号 in (24, 25) or 号 >= 30) and not 钩.更新股票:
            return cls._缺(号, "stock price update")
        if 号 == 29 and (not 钩.防御 or not 钩.监狱):
            return cls._缺(号, "prison/card handling")
        if 号 < 4:
            名单 = 世.监狱名单 if 号 < 2 else 世.医院名单
            位 = 0
            for 槽 in range(min(len(世.玩家), 4)):
                if 名单[槽]:
                    位 |= 1 << 槽
                    状 = 世.玩家[槽].状态
                    名 = "监狱天数" if 号 < 2 else "医院天数"
                    if 号 & 1:
                        setattr(状, 名, (getattr(状, 名) + 3) & 127)
                    else:
                        setattr(状, 名, 128)
                        名单[槽] = 0
            结果 = cls._成(
                号,
                ("新闻：大赦释放", "新闻：刑期延长三天", "新闻：康复出院", "新闻：住院延长三天")[
                    号
                ],
                3,
            )
            结果.玩家掩码 = 位
            return 结果
        if 号 in (4, 20):
            候 = [地 for 地 in cls._地产(世) if 号 == 20 or 地.等级 != 0]
            if not 候:
                return cls._缺(号, "a valid disaster target")
            地 = cls._选(候, 随机)
            钩.范围损坏(地.x, 地.y, 1 if 号 == 4 else 0, 号 == 4)
            if 钩.新闻画面:
                钩.新闻画面(号, 地.码)
            结果 = cls._成(
                号, "新闻：灾害袭击，区域受损" if 号 == 4 else "新闻：地震，区域建筑降级"
            )
            结果.地产 = 地.码
            return 结果
        if 号 in (5, 15, 19, 21):
            候 = [
                地
                for 地 in cls._地产(世)
                if 号 not in (5, 15) or (地.等级 != 0 and (号 != 15 or 地.码 < 4000))
            ]
            if not 候:
                return cls._缺(
                    号, "a built ordinary land (original event 15 otherwise divides by zero)"
                )
            地 = cls._选(候, 随机)
            cls._损坏(世, 地.码, 号 in (5, 19))
            if 号 != 19 and 钩.新闻画面:
                钩.新闻画面(号, 地.码)
            if 地.业主:
                cls._语音(钩, 地.业主 - 1, 3 + (随机.api_下一个() & 1))
            结果 = cls._成(
                号, "新闻：地产遭到破坏并被清除" if 号 in (5, 19) else "新闻：建筑损坏，降级一层"
            )
            结果.地产 = 地.码
            return 结果
        if 号 in (6, 14):
            候 = cls._地产(世)
            if not 候:
                return cls._缺(号, "a property for land-price news")
            地 = cls._选(候, 随机)
            cls._调地价(世, 地, 号 == 6)
            结果 = cls._成(号, "新闻：地价上涨三成" if 号 == 6 else "新闻：地价下跌三成")
            结果.地产 = 地.码
            return 结果
        if 号 == 7:
            候 = [地 for 地 in cls._地产(世) if 地.业主 == 0]
            if not 候:
                return cls._缺(号, "an unowned auction property")
            码 = cls._选(候, 随机).码
            钩.拍卖(码)
            结果 = cls._成(号, "新闻：无主地产拍卖")
            结果.地产 = 码
            return 结果
        if 8 <= 号 <= 10:
            总 = [0] * 4
            if len(世.玩家) > 4:
                raise ValueError("新闻最多支持四位玩家")
            if 号 == 10:
                for 槽, 人 in enumerate(世.玩家):
                    for 股 in 人.持仓:
                        总[槽] = 服务_类._整数(总[槽] + 股.数量)
            else:
                for 地 in cls._地产(世):
                    if 0 < 地.业主 <= 4:
                        总[地.业主 - 1] += 1
            胜 = None
            for 槽, 人 in enumerate(世.玩家):
                if cls._活(人) and (
                    胜 is None or (总[槽] < 总[胜] if 号 == 9 else 总[槽] > 总[胜])
                ):
                    胜 = 槽
            if 胜 is None:
                return cls._缺(号, "a living player to receive the award")
            奖 = 服务_类._整数((5000 if 号 == 9 else 10000) * 世.头.物价)
            cls._收入(世, 胜, 奖)
            cls._语音(钩, 胜, 6 + (随机.api_下一个() & 1 if 号 == 9 else 0))
            结果 = cls._成(
                号,
                ("新闻：地产最多者获奖", "新闻：地产最少者获补助", "新闻：持股最多者获奖")[号 - 8],
                奖,
            )
            结果.主体 = 胜
            return 结果
        if 11 <= 号 <= 13:
            税 = [0] * len(世.玩家)
            for 槽, 人 in enumerate(世.玩家):
                if not cls._活(人):
                    continue
                if 号 == 11:
                    税[槽] = cls._除(人.记录.现金, 20)
                elif 号 == 12:
                    总 = 0
                    for 地 in 世.地产[1:]:
                        if 地.经济.业主 == 槽 + 1:
                            总 = 服务_类._整数(
                                总
                                + 服务_类._整数(地.地价 + 服务_类._整数(地.经济.等级 * 地.每级造价))
                            )
                    for 地 in 世.设施[1:]:
                        if 地.业主 == 槽 + 1:
                            总 = 服务_类._整数(
                                总 + 服务_类._整数(地.地价 + 服务_类._整数(地.等级 * 地.每级造价))
                            )
                    税[槽] = 服务_类._整数(cls._除(总, 20) * 世.头.物价)
                else:
                    值 = 0.0
                    for 股, 持 in enumerate(人.持仓):
                        if 持.数量 == 0:
                            continue
                        价 = struct.unpack("<f", struct.pack("<I", 世.股票[股].浮点位[2]))[0]
                        值 = (
                            扩展数_类.api_从值(持.数量) * 扩展数_类.api_从值(价)
                            + 扩展数_类.api_从值(值)
                        ).api_单精度()
                    税[槽] = 服务_类._整数(
                        (扩展数_类.api_从值(值) * 扩展数_类.api_从值(0.05)).api_整数() * 世.头.物价
                    )
            for 槽, 钱 in enumerate(税):
                if cls._活(世.玩家[槽]) and 钱 != 0:
                    钩.付款(槽, -1, 钱, 0)
                if sum(cls._活(人) for 人 in 世.玩家) <= 1:
                    break
            结果 = cls._成(
                号, ("新闻：征收现金税", "新闻：征收地产税", "新闻：征收股票税")[号 - 11]
            )
            for 槽, 钱 in enumerate(税[:4]):
                if 钱:
                    结果.玩家掩码 |= 1 << 槽
                    结果.玩家金额[槽] = 钱
            return 结果
        if 号 in (16, 17):
            for 人 in 世.玩家:
                if cls._活(人) and (人.记录.交通 == 0 if 号 == 16 else 人.记录.交通 != 0):
                    人.状态.停留天数 = 1
            return cls._成(号, "新闻：行人暂停一天" if 号 == 16 else "新闻：车辆暂停一天")
        if 号 == 18:
            候 = cls._地产(世)
            if not 候:
                return cls._缺(号, "a property for street damage")
            地 = cls._选(候, 随机)
            结果 = cls._成(号, "新闻：整条街建筑受损")
            结果.地产 = 地.码
            if 地.码 < 4000:
                名 = cls._取(世.地产, 地.码 - 2000).经济.街道名
                for i, 另 in enumerate(世.地产[1:], 1):
                    if 另.经济.街道名 == 名:
                        cls._损坏(世, 2000 + i, False)
            else:
                cls._损坏(世, 地.码, False)
            return 结果
        if 号 == 22:
            for 人 in 世.玩家:
                if cls._活(人):
                    人.状态.银行禁贷天数 = 15
            return cls._成(号, "新闻：银行暂停贷款十五天")
        if 号 == 23:
            结果 = cls._成(号, "新闻：无贷款者获得存款一成奖励")
            for 槽, 人 in enumerate(世.玩家):
                if cls._活(人) and 人.记录.贷款 == 0:
                    奖 = cls._除(人.记录.银行, 10)
                    cls._收入(世, 槽, 奖, False)
                    if 槽 < 4 and 奖:
                        结果.玩家掩码 |= 1 << 槽
                        结果.玩家金额[槽] = 奖
            return 结果
        if 号 in (24, 25):
            for 股 in 世.股票:
                股.新闻走势 = 1 if 号 == 24 else 16
            钩.更新股票(0)
            return cls._成(号, "新闻：股市下跌" if 号 == 24 else "新闻：股市上涨")
        if 号 == 26:
            世.新闻影响天数 = 10
            return cls._成(号, "新闻：市场措施持续十天")
        if 号 in (27, 28):
            候 = [i for i, 股 in enumerate(世.股票) if 号 == 27 or 股.停牌天数 != 0]
            if not 候:
                return cls._缺(号, "a suspended stock")
            i = cls._选(候, 随机)
            股 = 世.股票[i]
            股.停牌天数 = 15 if 号 == 27 else 0
            if 号 == 27:
                股.浮点位[2] = 股.浮点位[1]
                游 = 服务_类._整数(世.股史游标 - 1) % 144
                世.股史[i][游] = 股.浮点位[1]
            结果 = cls._成(
                号, "新闻：一家公司股票暂停交易十五天" if 号 == 27 else "新闻：股票恢复交易"
            )
            结果.主体 = i
            return 结果
        if 号 == 29:
            候 = [i for i, 司 in enumerate(世.公司[1:], 1) if 司.业主 != 0]
            if not 候:
                return cls._缺(号, "an owned company")
            司 = cls._选(候, 随机)
            主 = 世.公司[司].业主
            if 主 > len(世.玩家):
                raise ValueError("公司业主无效")
            目标 = 钩.防御(主 - 1)
            if 目标 >= 0:
                钩.监狱(目标, 5)
            结果 = cls._成(号, "新闻：公司负责人面临五天监禁")
            结果.公司, 结果.主体 = 司, 主 - 1
            if 0 <= 目标 < 4:
                结果.玩家掩码 = 1 << 目标
            return 结果
        if 号 >= 30:
            候 = [i for i, 司 in enumerate(世.公司[1:], 1) if 号 != 35 or 司.资金 > 10000]
            if not 候:
                return cls._缺(号, "a qualifying company")
            i = cls._选(候, 随机)
            司 = 世.公司[i]
            if 号 == 35:
                前 = 司.资金
                司.资金 = 服务_类._整数(前 + 前)
                司.资金变化 = 服务_类._整数(司.资金变化 + 司.资金)
                走势 = cls._除(前, 10000) << 4 & 255
            else:
                差 = (-10000, 20000, -20000, -10000, -5000)[号 - 30]
                司.资金, 司.资金变化 = 服务_类._整数(司.资金 + 差), 服务_类._整数(司.资金变化 + 差)
                走势 = (3, 48, 4, 3, 3)[号 - 30]
            if 司.股票索引 < len(世.股票):
                世.股票[司.股票索引].新闻走势 = 走势
                钩.更新股票(司.股票索引 + 1)
            结果 = cls._成(号, "新闻：公司业绩与股价变化")
            结果.公司 = i
            return 结果
        raise ValueError("不可达新闻分支")

    @classmethod
    def api_命运编号(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_号: int, arg_钩: 事件回调_类
    ) -> 事件结果_类:
        世, 随机, 槽, 号, 钩 = arg_世, arg_随机, arg_槽, arg_号, arg_钩
        if not 0 <= 号 < 49:
            raise ValueError("命运处理编号无效")
        人 = cls._取(世.玩家, 槽)
        if (
            号 in (2, 4) or (14 <= 号 <= 31 and (号 < 20 or 号 in (23, 24, 26, 30)))
        ) and not 钩.付款:
            return cls._缺(号, "payment and insurance handling")
        if 号 == 2 and not 钩.贷款到期:
            return cls._缺(号, "original loan due-date update")
        if 号 in (8, 9) and not 钩.卖股:
            return cls._缺(号, "original stock sale")
        if 号 in (6, 7) and (not 钩.消失 or not 钩.防御):
            return cls._缺(号, "absence/card handling")
        if (号 in (12, 13) or (号 in (15, 16) and 人.记录.交通 == 0)) and (
            not 钩.医院 or not 钩.防御
        ):
            return cls._缺(号, "hospital/card handling")
        if 号 >= 33 and (not 钩.监狱 or not 钩.防御):
            return cls._缺(号, "prison/card handling")
        if 号 == 5 and 人.记录.控制标志 == 1 and not 钩.选卡:
            return cls._缺(号, "human card selection")
        if 号 in (0, 1):
            候 = [
                地
                for 地 in cls._地产(世)
                if 地.码 < 4000
                and 地.业主 == 槽 + 1
                and (地.等级 != 0 if 号 == 0 else 地.等级 == 0)
            ]
            if not 候:
                return cls._缺(号, "an eligible owned land")
            地 = cls._选(候, 随机)
            原 = cls._取(世.地产, 地.码 - 2000)
            if 号 == 0:
                cls._收入(世, 槽, 服务_类._整数(原.经济.等级 * 原.每级造价))
                原.经济.等级 = 原.经济.连锁 = 0
            else:
                cls._收入(世, 槽, 原.地价)
                原.经济.业主 = 原.到期日 = 0
            cls._语音(钩, 槽, 3 + (随机.api_下一个() & 1))
            return cls._成(
                号,
                "命运：房屋被拆除，获得建筑补偿" if 号 == 0 else "命运：空地被征收，获得地价补偿",
            )
        if 号 in (2, 3):
            钱 = 服务_类._整数(10000 * 世.头.物价)
            修 = cls._运势(人, 随机, False, True)
            if 修 == 1:
                return cls._成(号, "命运：神明阻止了损失", 钱)
            if 号 == 2:
                if 修 == 2:
                    钱 = 服务_类._整数(钱 + 钱)
                人.记录.贷款 = 服务_类._整数(人.记录.贷款 + 钱)
                钩.贷款到期(槽)
                cls._保险(世, 槽, 钱, 钩)
            else:
                人.状态.银行拒绝天数 = (人.状态.银行拒绝天数 + 30) & 255
            return cls._成(
                号, "命运：身份遭盗用，新增贷款" if 号 == 2 else "命运：银行拒绝往来三十天", 钱
            )
        if 号 == 4:
            for 别, 玩家 in enumerate(世.玩家):
                if 别 != 槽 and cls._活(玩家) and 玩家.记录.银行 != 0:
                    钩.付款(别, 槽, cls._比例(玩家.记录.银行, 0x3DCCCCCD), 4)
            return cls._成(号, "命运：取得其他玩家存款的一成", 10)
        if 号 == 5:
            收到 = False
            for 别, 玩家 in enumerate(世.玩家):
                if 别 == 槽 or not cls._活(玩家):
                    continue
                包 = 服务_类._库存(世, 别)
                数 = 包.api_卡数()
                if not 数:
                    continue
                if 人.记录.控制标志 > 1:
                    卡 = 玩家.记录.卡片[随机.api_下一个() % 数]
                elif 人.记录.控制标志 == 1:
                    卡 = 钩.选卡(槽, 别)
                else:
                    continue
                收到 = True
                if 卡 == 0 and 人.记录.控制标志 == 1:
                    continue
                if not 1 <= 卡 <= 30 or not 包.api_有卡(卡):
                    raise ValueError("选卡不在受害者库存")
                包.api_用卡(卡)
                服务_类._库存(世, 槽).api_收卡(卡)
            if 收到:
                cls._语音(钩, 槽, 随机.api_下一个() & 1)
            return cls._成(号, "命运：从其他玩家各取得一张卡片")
        if 号 in (6, 7, 12, 13) or 号 >= 33 or (号 in (15, 16) and 人.记录.交通 == 0):
            天 = 3 + (号 - 33) % 4 * 2 if 号 >= 33 else 3
            修 = cls._运势(人, 随机, True, True)
            if 修 == 1:
                if 号 >= 33:
                    cls._语音(钩, 槽, 0)
                return cls._成(号, "命运：神明阻止了灾祸", 天)
            if 修 == 2:
                天 = 天 * 2 & 255
            目标 = 钩.防御(槽)
            if 目标 >= 0:
                if 号 in (6, 7):
                    钩.消失(目标, 天, 0 if 号 == 6 else 1)
                elif 号 >= 33:
                    钩.监狱(目标, 天)
                else:
                    钩.医院(目标, 天)
            return cls._成(
                号,
                "命运：出国旅行"
                if 号 == 6
                else "命运：被外星人带走"
                if 号 == 7
                else "命运：面临监禁"
                if 号 >= 33
                else "命运：受伤住院",
                天,
            )
        if 号 in (8, 9):
            if cls._运势(人, 随机, False, True) == 1:
                return cls._成(号, "命运：神明保护了股票")
            for 股, 持 in enumerate(人.持仓):
                钱 = cls._比例(持.数量, 0x3DCCCCCD) if 号 == 8 else 持.数量
                if 号 == 8 or 钱 != 0:
                    钩.卖股(槽, 股, 钱, 号 == 9)
            if 号 == 9:
                cls._语音(钩, 槽, 5)
            return cls._成(号, "命运：损失一成股票" if 号 == 8 else "命运：全部股票被变卖", 10)
        if 号 in (10, 11):
            if cls._运势(人, 随机, True, True) == 1:
                return cls._成(号, "命运：神明保护了交通工具")
            人.记录.交通, 人.记录.骰数 = 0, 1
            i = 4 if 号 == 10 else 5
            世.道具供应[i] = (世.道具供应[i] + 1) & 255
            cls._语音(钩, 槽, 3 + (随机.api_下一个() & 1 if 号 == 10 else 0))
            return cls._成(
                号, "命运：机车失窃，改为步行" if 号 == 10 else "命运：汽车毁损，改为步行"
            )
        if 14 <= 号 <= 31:
            名义 = (
                -3000,
                -3000,
                -3000,
                -6000,
                -600,
                -1500,
                1000,
                2000,
                3000,
                -1000,
                -2000,
                10000,
                -8000,
                4000,
                6000,
                8000,
                -5000,
                5000,
            )[号 - 14]
            不利 = 名义 < 0
            钱 = 服务_类._整数(abs(名义) * 世.头.物价)
            修 = cls._运势(人, 随机, False, 不利)
            if 修 == 1:
                if 不利:
                    cls._钱语音(世, 随机, 钱, 槽, 12, 钩)
                return cls._成(号, "命运：神明阻止了损失" if 不利 else "命运：奖励被神明阻止", 钱)
            if 修 == 2:
                钱 = 服务_类._整数(钱 + 钱)
            if not 不利:
                cls._收入(世, 槽, 钱)
                cls._钱语音(世, 随机, 钱, 槽, 6, 钩)
            else:
                钩.付款(槽, -1, 钱, 0)
                if cls._活(人) and sum(cls._活(另) for 另 in 世.玩家) > 1:
                    cls._钱语音(世, 随机, 钱, 槽, 9, 钩)
                    cls._保险(世, 槽, 钱, 钩)
            return cls._成(号, ("命运：支付 " if 不利 else "命运：获得 ") + str(钱), 钱)
        if 号 == 32:
            if cls._运势(人, 随机, True, True) == 1:
                return cls._成(号, "命运：神明保护了卡片与道具")
            if 人.记录.交通 != 0:
                交 = 人.记录.交通 & 3
                i = 4 if 交 == 1 else 5 if 交 == 2 else 11 if 交 == 3 else None
                if i is not None:
                    人.记录.道具[i] = (人.记录.道具[i] + 1) & 255
                人.记录.交通, 人.记录.骰数 = 0, 1
            包 = 服务_类._库存(世, 槽)
            点 = 包.api_卖库存道具() + 包.api_卖卡()
            人.记录.点券 = (人.记录.点券 + 点) & 65535
            cls._语音(钩, 槽, 3)
            return cls._成(号, "命运：卡片与道具全部变卖为点数")
        raise ValueError("不可达命运分支")
