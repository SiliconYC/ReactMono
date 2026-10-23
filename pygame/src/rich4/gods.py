# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/gods.cpp；神明移除/再生和融资由真实会话接入。
# ◑ 导入
from dataclasses import dataclass
from typing import Callable

from rich4.calendar import 日期_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.services import 服务_类
from rich4.world import 世界_类


# ◕ 功能
class 金钱转盘_类:
    """
    原四位十进制转盘，步进由调用者按原30ms时钟驱动，停止不是固定结果。

    更新日志：
    2026.10.23 - 对应MoneySpinner的所有阶段、半数字位置和逐位减速。
    """

    def __init__(self, arg_种类: int) -> None:
        if arg_种类 not in (1, 2, 5, 6):
            raise ValueError("该神明没有金钱转盘")
        self.省位 = arg_种类 & 1
        self.数字 = [0] * 4
        self.阶段, self.帧数 = 1, 0
        self.减速周期 = self.减速累计 = self.上次减速位 = 0

    @property
    def 完成(self) -> bool:
        return self.阶段 == 10

    @property
    def 金额(self) -> int:
        钱 = self.数字[1] // 2 * 100 + self.数字[2] // 2 * 10 + self.数字[3] // 2
        return 钱 if self.省位 else 钱 + self.数字[0] // 2 * 1000

    def api_停止(self) -> None:
        if self.阶段 == 1:
            self.阶段 = 2

    def _转位(self, arg_掩码: int, arg_慢位: int) -> bool:
        if arg_慢位:
            if self.上次减速位 != arg_慢位 and self.数字[4 - arg_慢位] & 1:
                self.减速周期, self.减速累计, self.上次减速位 = 1, 0, arg_慢位
            if self.减速周期:
                if self.减速周期 <= self.减速累计:
                    self.减速累计 = 0
                    self.减速周期 += 1
                self.减速累计 += 1
        for 反 in range(4 - self.省位):
            位 = 3 - 反
            if not arg_掩码 & (1 << 反):
                continue
            if 4 - 位 == arg_慢位 and self.减速周期 > self.减速累计:
                continue
            self.数字[位] = (self.数字[位] + 1) % 20
        if self.减速周期 == 8:
            self.减速周期 = self.减速累计 = 0
            return True
        return False

    def api_步进(self, arg_随机: 随机数_类, arg_电脑: bool = False) -> None:
        if self.完成:
            return
        if self.阶段 < 3 and self.帧数 % 10 == 0:
            self.数字[:] = [arg_随机.api_下一个() % 10 * 2 + 1 for _ in range(4)]
        self.帧数 = (self.帧数 + 1) & 0xFFFFFFFF
        if arg_电脑 and self.帧数 >= 40 and self.阶段 == 1:
            self.阶段 = 2
        if self.阶段 == 1:
            self._转位(15, 0)
        elif self.阶段 == 2:
            self._转位(15, 0)
            self.阶段, self.帧数 = 3, 0
        elif self.阶段 == 3:
            self._转位(15, 0)
            if self.帧数 == 4:
                self.阶段 = 4
        elif self.阶段 in (4, 5, 6, 7):
            if self._转位((15, 14, 12, 8)[self.阶段 - 4], self.阶段 - 3):
                self.阶段 = self.省位 + 7 if self.阶段 == 6 else self.阶段 + 1
        elif self.阶段 == 8:
            self.阶段, self.帧数 = 9, 0
        elif self.阶段 == 9:
            if self.帧数 == 40:
                self.阶段 = 10
        else:
            raise RuntimeError("非法转盘阶段")


@dataclass
class 神明结果_类:
    """
    神明操作的支持、应用和停止移动标志。

    更新日志：
    2026.10.23 - 对应gods::Result。
    """

    支持: bool = True
    已应用: bool = False
    停止移动: bool = False
    消息: str = ""


@dataclass
class 神明回调_类:
    """
    真实规则与原出入场表现边界；可选表现不消费随机数。

    更新日志：
    2026.10.23 - 对应gods::Callbacks，移除物件负责撤回运势并再生。
    """

    移除物件: Callable[[int], None] | None = None
    金额: Callable[[int], int] | None = None
    付款: Callable[[int, int, int, int], None] | None = None
    游戏结束: Callable[[], bool] | None = None
    医院: Callable[[int, int], None] | None = None
    语音: Callable[[int, int], None] | None = None
    升级: Callable[[int], int] | None = None
    降级: Callable[[int], None] | None = None
    敌意: Callable[[int, int, int], None] | None = None
    现身: Callable[[int, int], None] | None = None
    到达: Callable[[int, int], None] | None = None
    离开: Callable[[int, int], None] | None = None
    声音: Callable[[int, int], None] | None = None
    狗: Callable[[int, bool], None] | None = None


class 神明_类:
    """
    原神明附身、离开、地上对象接触及地产前后置效果。

    更新日志：
    2026.10.23 - 对应gods模块；保留对象ID/类型差异与双精度低字敌意。
    """

    神运 = (0, -100, -200, -100, -200, 100, 200, 100, 200, -100, 100, 0, -500, 0, 0, 1000, 0, 0)
    财运 = (0, 100, 150, 0, 0, -60, -100, 0, 0, 60, -60, 0, 0, 0, 0, -200, 0, 0)
    其他运 = (0, 0, 0, 100, 150, 0, 0, -60, -100, 60, -60, 0, 0, 0, 0, -200, 0, 0)

    @staticmethod
    def _取(arg_表: list, arg_号: int):
        if not 0 <= arg_号 < len(arg_表):
            raise IndexError("神明引用索引越界")
        return arg_表[arg_号]

    @staticmethod
    def _缺(arg_文: str) -> 神明结果_类:
        return 神明结果_类(支持=False, 消息=arg_文)

    @staticmethod
    def _语音(arg_钩: 神明回调_类, arg_槽: int, arg_类: int) -> None:
        if arg_钩.语音:
            arg_钩.语音(arg_槽, arg_类)

    @classmethod
    def _奖语音(cls, arg_随机: 随机数_类, arg_钩: 神明回调_类, arg_槽: int, arg_钱: int) -> None:
        if arg_钱 > 100:
            cls._语音(arg_钩, arg_槽, 0)
        elif arg_钱 > 50:
            cls._语音(arg_钩, arg_槽, arg_随机.api_下一个() & 1)
        elif arg_钱:
            cls._语音(arg_钩, arg_槽, 2)

    @classmethod
    def _收入语音(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_钩: 神明回调_类, arg_槽: int, arg_钱: int
    ) -> None:
        if arg_钱 >= 服务_类._整数(9000 * arg_世.头.物价):
            cls._语音(arg_钩, arg_槽, 6)
        elif arg_钱 >= 服务_类._整数(5000 * arg_世.头.物价):
            cls._语音(arg_钩, arg_槽, 6 + (arg_随机.api_下一个() & 1))
        elif arg_钱 >= 服务_类._整数(2000 * arg_世.头.物价):
            cls._语音(arg_钩, arg_槽, 8)

    @staticmethod
    def _结束(arg_钩: 神明回调_类) -> bool:
        return bool(arg_钩.游戏结束 and arg_钩.游戏结束())

    @staticmethod
    def api_自动金额(arg_类: int, arg_随机: 随机数_类) -> int:
        盘 = 金钱转盘_类(arg_类)
        for 帧 in range(1002):
            if 盘.完成:
                return 盘.金额
            if 帧 > 1000:
                raise RuntimeError("金钱转盘未停止")
            盘.api_步进(arg_随机, True)
        raise RuntimeError("金钱转盘阶段不一致")

    @classmethod
    def api_可附身(cls, arg_世: 世界_类, arg_物: int) -> bool:
        if not arg_物:
            return False
        类 = cls._取(arg_世.物件, arg_物 - 1).种类
        return 1 <= 类 <= 10 or 类 in (12, 15)

    @classmethod
    def api_脱离(cls, arg_世: 世界_类, arg_槽: int, arg_钩: 神明回调_类) -> 神明结果_类:
        状 = cls._取(arg_世.玩家, arg_槽).状态
        if not 状.神明信息:
            return 神明结果_类()
        if not arg_钩.移除物件:
            return cls._缺("神明移除规则尚未接入")
        类 = cls._取(arg_世.物件, 状.神明信息 - 1).种类
        缺席 = bool(状.酒店天数 or 状.消失天数 or 状.监狱天数 or 状.医院天数)
        arg_钩.移除物件(状.神明信息)
        if arg_钩.声音:
            arg_钩.声音(arg_槽, 54)
        if arg_钩.离开:
            arg_钩.离开(arg_槽, 类)
        if not 缺席 and (5 <= 类 <= 8 or 类 == 15):
            cls._语音(arg_钩, arg_槽, 23)
        return 神明结果_类(True, True, False, "神明离开")

    @classmethod
    def api_附身(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_槽: int,
        arg_物: int,
        arg_源节点: int,
        arg_钩: 神明回调_类,
    ) -> 神明结果_类:
        人 = cls._取(arg_世.玩家, arg_槽)
        if not cls.api_可附身(arg_世, arg_物):
            return 神明结果_类()
        if not 0 <= arg_源节点 < len(arg_世.节点):
            raise IndexError("神明来源节点越界")
        物 = cls._取(arg_世.物件, arg_物 - 1)
        类 = 物.种类
        if 人.状态.神明信息 and not arg_钩.移除物件:
            return cls._缺("旧神明移除规则尚未接入")
        if 类 in (1, 2, 5, 6) and not arg_钩.金额:
            return cls._缺("神明数字转盘尚未接入")
        if 类 in (1, 5, 6) and not arg_钩.付款:
            return cls._缺("神明资金结算尚未接入")
        物.节点 = 0
        if 人.状态.神明信息:
            结果 = cls.api_脱离(arg_世, arg_槽, arg_钩)
            if not 结果.支持:
                return 结果
        人.状态.神明信息 = arg_物 & 255
        物.节点, 物.附身玩家, 物.剩余天数 = 人.记录.节点, (arg_槽 + 1) & 255, 13 if 类 == 15 else 7
        if arg_源节点:
            arg_世.节点[arg_源节点].标志 &= ~0x00FF0000 & 0xFFFFFFFF
        for 名, 表 in (("神运修正", cls.神运), ("财运修正", cls.财运), ("其他运修正", cls.其他运)):
            setattr(人.状态, 名, ((getattr(人.状态, 名) + 表[类] + 32768) & 65535) - 32768)
        if 类 in (5, 6, 7, 8, 15):
            cls._语音(arg_钩, arg_槽, 22)
        if arg_钩.现身:
            arg_钩.现身(arg_槽, 类)
        if arg_钩.到达:
            arg_钩.到达(arg_槽, 类)
        if 类 in (1, 5):
            钱 = arg_钩.金额(类)
            for 别, 玩家 in enumerate(arg_世.玩家):
                if cls._结束(arg_钩):
                    break
                if 别 == arg_槽 or not 玩家.记录.控制标志:
                    continue
                arg_钩.付款(别, arg_槽, 钱, 1) if 类 == 1 else arg_钩.付款(arg_槽, 别, 钱, 0)
            if 类 == 1 and 钱 > 700 and not cls._结束(arg_钩):
                cls._语音(arg_钩, arg_槽, 8)
        elif 类 == 2:
            钱 = arg_钩.金额(类)
            人.记录.现金 = 服务_类._整数(人.记录.现金 + 钱)
            人.状态.累计收入 = (人.状态.累计收入 + 钱) & 0xFFFFFFFF
            if 钱 >= 服务_类._整数(5000 * arg_世.头.物价):
                cls._收入语音(arg_世, arg_随机, arg_钩, arg_槽, 钱)
        elif 类 in (3, 4):
            价值 = 0
            for _ in range(1 if 类 == 3 else 2):
                卡 = 服务_类.api_随机卡(arg_世, arg_随机, arg_槽)
                if 卡:
                    价值 += 服务_类.卡价[卡 - 1]
            cls._奖语音(arg_随机, arg_钩, arg_世.头.当前玩家, 价值)
        elif 类 == 6:
            arg_钩.付款(arg_槽, -1, arg_钩.金额(类), 0)
        elif 类 == 7:
            包 = 服务_类._库存(arg_世, arg_槽)
            数 = 包.api_卡数()
            if 数:
                包.api_用卡(人.记录.卡片[arg_随机.api_下一个() % 数])
        elif 类 == 8:
            服务_类._库存(arg_世, arg_槽).api_丢半手()
        elif 类 == 15:
            交通 = 人.记录.交通 & 3
            if 交通:
                号 = 11 if 交通 == 3 else 交通 + 3
                人.记录.道具[号] = (人.记录.道具[号] + 1) & 255
            人.记录.交通, 人.记录.骰数 = 0, 1
            包 = 服务_类._库存(arg_世, arg_槽)
            包.api_卖库存道具()
            包.api_卖卡()
        return 神明结果_类(True, True, False, "神明附身")

    @classmethod
    def api_接触(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_槽: int,
        arg_物: int,
        arg_停靠: bool,
        arg_钩: 神明回调_类,
    ) -> 神明结果_类:
        人 = cls._取(arg_世.玩家, arg_槽)
        if not arg_物 or not 人.记录.控制标志:
            return 神明结果_类()
        物 = cls._取(arg_世.物件, arg_物 - 1)
        类 = 物.种类
        if 类 == 0 or 类 > 18:
            raise ValueError("遇到未知对象类型")
        if 物.附身玩家 or 类 == 15 or (not arg_停靠 and 类 != 16):
            return 神明结果_类()
        if cls.api_可附身(arg_世, arg_物):
            return cls.api_附身(arg_世, arg_随机, arg_槽, arg_物, 人.记录.节点, arg_钩)
        if 类 == 18:
            if 人.状态.附身炸弹:
                return 神明结果_类()
            人.状态.附身炸弹 = arg_物 & 255
            物.附身玩家, 物.剩余天数 = (arg_槽 + 1) & 255, 38
            cls._取(arg_世.节点, 人.记录.节点).标志 &= ~0x00FF0000 & 0xFFFFFFFF
            return 神明结果_类(True, True, False, "定时炸弹附着")
        if not arg_钩.移除物件:
            return cls._缺("地上对象移除规则尚未接入")
        if (类 == 17 or (类 == 11 and 人.记录.交通 == 0)) and not arg_钩.医院:
            return cls._缺("对象碰撞受伤规则尚未接入")
        if 类 == 11:
            arg_钩.移除物件(11)
            if arg_钩.狗:
                arg_钩.狗(arg_槽, 人.记录.交通 == 0)
            if 人.记录.交通 == 0:
                arg_钩.医院(arg_槽, 3)
                return 神明结果_类(True, True, True, "碰撞受伤住院")
            return 神明结果_类(True, True, False, "乘车避过碰撞")
        if 类 == 13:
            物号 = 服务_类.api_随机道具(arg_世, arg_随机, arg_槽)
            if not 物号:
                return 神明结果_类()
            arg_钩.移除物件(13)
            if arg_钩.声音:
                arg_钩.声音(arg_槽, 35)
            cls._奖语音(arg_随机, arg_钩, arg_槽, 服务_类.道具价[物号 - 1])
            return 神明结果_类(True, True, False, "获得道具")
        if 类 == 14:
            arg_钩.移除物件(14)
            if arg_钩.声音:
                arg_钩.声音(arg_槽, 36)
            人.记录.点券 = (人.记录.点券 + 500) & 65535
            cls._语音(arg_钩, arg_槽, 0)
            return 神明结果_类(True, True, False, "获得500点")
        arg_钩.移除物件(arg_物)
        if 类 == 17:
            arg_钩.医院(arg_槽, 3)
        return 神明结果_类(True, True, True, "遇到路障" if 类 == 16 else "踩中地雷住院")

    @classmethod
    def api_地产后(
        cls, arg_世: 世界_类, arg_槽: int, arg_节点: int, arg_钩: 神明回调_类
    ) -> 神明结果_类:
        人 = cls._取(arg_世.玩家, arg_槽)
        if 人.状态.酒店天数 or not 人.记录.控制标志:
            return 神明结果_类()
        神 = 人.状态.神明信息
        if 神 not in (9, 10, 12):
            return 神明结果_类()
        码 = cls._取(arg_世.节点, arg_节点).类型索引
        if 神 == 9:
            if not arg_钩.升级:
                return cls._缺("神明房屋升级规则尚未接入")
            结果 = arg_钩.升级(码)
            return 神明结果_类(True, bool(结果 & 1), False, "神明帮助房屋升级" if 结果 & 1 else "")
        if 2000 < 码 < 4000:
            地 = cls._取(arg_世.地产, 码 - 2000)
            经济 = 地.经济
        elif 4000 < 码 < 6000:
            地 = 经济 = cls._取(arg_世.设施, 码 - 4000)
        else:
            return 神明结果_类()
        业主, 级, 基价 = 经济.业主, 经济.等级, 地.地价
        if (神 == 10 and 级 == 0) or (神 == 12 and 业主 == arg_槽 + 1):
            return 神明结果_类()
        if 业主 and not arg_钩.敌意:
            return cls._缺("神明地产敌意规则尚未接入")
        if 神 == 10:
            if not arg_钩.降级:
                return cls._缺("神明房屋降级规则尚未接入")
            if 业主:
                arg_钩.敌意(
                    业主 - 1, arg_槽, 服务_类._整数((60 if 码 < 4000 else 30) * arg_世.头.物价)
                )
            arg_钩.降级(码)
            return 神明结果_类(True, True, False, "神明破坏房屋")
        if 业主:
            比 = (扩展数_类.api_从值(级) + 扩展数_类.api_从值(2.0)) / 扩展数_类.api_从值(5.0)
            值 = 扩展数_类.api_从值(服务_类._整数(基价 * arg_世.头.物价)) * 比
            # 原函数把x87落binary64后的低32位当整数参数；不得换成数学上的金额。
            arg_钩.敌意(业主 - 1, arg_槽, 服务_类._整数(值.api_双精度位() & 0xFFFFFFFF))
        elif arg_世.租约模式:
            间隔 = (0, 0x20000, 0x10000, 0x600, 0x300, 0x100)
            if not 0 <= arg_世.租约模式 < len(间隔):
                raise ValueError("非法原租约模式")
            日, 月, 年 = arg_世.头.日期
            地.到期日 = 日期_类.api_打包间隔(年 << 16 | 月 << 8 | 日, 间隔[arg_世.租约模式])
        经济.业主 = (arg_槽 + 1) & 255
        cls._语音(arg_钩, arg_世.头.当前玩家, 0)
        return 神明结果_类(True, True, False, "神明取得地产")

    @classmethod
    def api_购地后(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_节点: int, arg_钩: 神明回调_类
    ) -> 神明结果_类:
        if cls._取(arg_世.玩家, arg_槽).状态.神明信息 not in (3, 4):
            return 神明结果_类()
        if not arg_钩.升级:
            return cls._缺("福神房屋升级规则尚未接入")
        结果 = arg_钩.升级(cls._取(arg_世.节点, arg_节点).类型索引)
        if 结果 & 1:
            cls._语音(arg_钩, arg_槽, 15 if 结果 & 128 else arg_随机.api_下一个() & 1)
        return 神明结果_类(True, bool(结果 & 1), False, "福神帮助房屋升级" if 结果 & 1 else "")
