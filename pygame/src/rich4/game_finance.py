# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ game.cpp 的支付/破产、银行和每日/月结财务。
# ◑ 导入
from copy import deepcopy

from rich4.calendar import 日期_类
from rich4.events import 事件_类
from rich4.game_types import (
    公告种类_类,
    决策_类,
    决策种类_类,
    决策选项_类,
    效果_类,
    效果种类_类,
    月报_类,
    游戏事件_类,
    游戏事件种类_类,
    游戏阶段_类,
    股利行_类,
)
from rich4.holidays import 节日_类
from rich4.lottery import 彩票_类
from rich4.numeric import 扩展数_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类


# ◕ 功能
class 会话金融_类:
    """
    保留原扣款次序、结局早退、融资与软件x87结算，不委托C++运行。

    更新日志：
    2026.10.24 - 同一会话提供真实防御、收容、拍卖与移动回调。
    """

    _回绕 = staticmethod(股市_类._回绕)

    @staticmethod
    def _零截除(arg_数: int, arg_除: int) -> int:
        return (abs(arg_数) // abs(arg_除)) * (-1 if (arg_数 < 0) != (arg_除 < 0) else 1)

    def _付款(self, arg_从: int, arg_到: int, arg_额: int, arg_标志: int) -> int:
        if arg_额 <= 0:
            return 0
        付 = arg_额
        if arg_从 > 100:
            公 = 事件_类._取(self.世界.公司, arg_从 - 100)
            公.资金, 公.资金变化 = self._回绕(公.资金 - 付), self._回绕(公.资金变化 - 付)
        else:
            人 = 事件_类._取(self.世界.玩家, arg_从).记录
            付 = min(arg_额, max(0, 人.现金 + 人.银行))
            首, 次 = ("银行", "现金") if arg_标志 & 4 else ("现金", "银行")
            首付 = min(max(getattr(人, 首), 0), 付)
            setattr(人, 首, self._回绕(getattr(人, 首) - 首付))
            setattr(人, 次, self._回绕(getattr(人, 次) - (付 - 首付)))
            if 付 < arg_额:
                self._破产(arg_从)
            状 = self.世界.玩家[arg_从].状态
            状.累计支出 = (状.累计支出 + 付) & 0xFFFFFFFF
        if arg_到 == -1:
            self.世界.公共基金 = self._回绕(self.世界.公共基金 + 付)
        elif arg_到 > 100:
            公 = 事件_类._取(self.世界.公司, arg_到 - 100)
            公.资金, 公.资金变化 = self._回绕(公.资金 + 付), self._回绕(公.资金变化 + 付)
        else:
            人 = 事件_类._取(self.世界.玩家, arg_到)
            户 = "现金" if arg_标志 & 1 else "银行"
            setattr(人.记录, 户, self._回绕(getattr(人.记录, 户) + 付))
            人.状态.累计收入 = (人.状态.累计收入 + 付) & 0xFFFFFFFF
        return 付

    def _更新敌意(self, arg_从: int, arg_到: int, arg_额: int) -> None:
        if arg_从 == arg_到:
            return
        状 = 事件_类._取(self.世界.玩家, arg_从).状态
        旧 = self._回绕(事件_类._取(状.敌意, arg_到))
        if arg_额 < 0 and 旧 == 0:
            return
        状.敌意[arg_到] = max(self._回绕(旧 + arg_额), 0)
        if arg_额 > 0 and 状.盟友 == arg_到 + 1:
            状.盟友 = 状.结盟天数 = 0

    def _选择付租者(
        self, arg_额: int, arg_主: int, arg_强制缺席: bool = False, arg_可免: bool = True
    ) -> tuple[int, int]:
        def 可防御() -> bool:
            return arg_额 >= self._回绕(2000 * self.世界.头.物价) or arg_额 > self._回绕(
                self._玩家().现金 + self._玩家().银行
            )

        if arg_可免 and 可防御() and self._尝试免付卡(self._当前(), arg_主, arg_额):
            arg_额 = 0
        人 = self._当前()
        if 可防御():
            对 = self._尝试嫁祸卡(self._当前(), 1, arg_额)
            if 对 >= 0:
                人 = 对
        if arg_额 or arg_强制缺席:
            for i, 另 in enumerate(self.世界.玩家):
                if i != 人 and 另.记录.控制标志 and 另.状态.神明信息 in (14, 15):
                    人 = i
                    break
        return 人, arg_额

    def _付租(
        self,
        arg_主: int,
        arg_额: int,
        arg_人: int,
        arg_盟: int | None = None,
        arg_盟额: int = 0,
        arg_地: int = 0,
        arg_类: int = 0,
        arg_倍: int = 0,
    ) -> None:
        框 = self._公告(公告种类_类.租金, arg_人, arg_类)
        框.地产, 框.主体, 框.次主体 = arg_地, arg_主, arg_盟 if arg_盟 is not None else -1
        框.金额, 框.值 = arg_额, arg_倍
        最恨, 最大 = -1, 0
        for i, 人 in enumerate(self.世界.玩家):
            if i == arg_人 or not 人.记录.控制标志:
                continue
            恨 = self._回绕(self.世界.玩家[arg_人].状态.敌意[i])
            if 恨 > 最大:
                最大, 最恨 = 恨, i
        敌话 = False
        if 最恨 == arg_主 and arg_额 >= self._回绕(5000 * self.世界.头.物价):
            敌话 = bool(self.随机.api_下一个() & 1)
            if 敌话:
                self._语音(arg_人, 18)
        if not 敌话:
            self._金额语音(arg_人, arg_额, 9)
        主额 = self._回绕(arg_额 - arg_盟额)
        self._金额语音(arg_主, 主额, 6)
        已付 = self._付款(arg_人, arg_主, 主额, 0)
        if arg_盟 is not None:
            已付 = self._回绕(已付 + self._付款(arg_人, arg_盟, arg_盟额, 0))
        if 已付:
            self._发事件(游戏事件种类_类.已付租, f"玩家{arg_人 + 1}支付租金", 已付)

    def _检查终局(self) -> bool:
        活跃 = [i for i, 人 in enumerate(self.世界.玩家) if 人.记录.控制标志]
        人类 = any(人.记录.控制标志 & 1 for 人 in self.世界.玩家)
        if 人类 and len(活跃) > 1:
            return False
        self.胜者 = 活跃[0] if len(活跃) == 1 and 人类 else None
        self.事件队列.append(
            游戏事件_类(
                游戏事件种类_类.游戏结束,
                self.胜者 if self.胜者 is not None else self._当前(),
                节点=self._玩家().节点,
                消息=f"玩家{self.胜者 + 1}获胜" if self.胜者 is not None else "游戏结束",
            )
        )
        self._置阶段(游戏阶段_类.结束)
        return True

    def _破产(self, arg_槽: int) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽).记录
        人.控制标志 = 0
        节 = 事件_类._取(self.世界.节点, 人.节点)
        人.x, 人.y, 节.标志 = 节.x & 65535, 节.y & 65535, 节.标志 | (0x100 << arg_槽)
        状 = self.世界.玩家[arg_槽].状态
        for 物 in (状.神明信息, 状.附身炸弹):
            if 物:
                self._移除物件(物)
        for i in range(4):
            特 = self.世界.特殊角色[i]
            if not 特.不活跃状态 and 特.业主 == arg_槽:
                self._收容(i + 4, 0, i >= 2)
        self.世界.api_清破产字段(arg_槽)
        self.世界.监狱名单[arg_槽] = self.世界.医院名单[arg_槽] = 0
        for 另 in self.世界.玩家:
            另.状态.敌意[arg_槽] = 0
            if 另.状态.盟友 == arg_槽 + 1:
                另.状态.盟友 = 另.状态.结盟天数 = 0
        self.事件队列.append(
            游戏事件_类(
                游戏事件种类_类.玩家破产, arg_槽, 节点=人.节点, 消息=f"玩家{arg_槽 + 1}破产"
            )
        )
        self._效果(效果种类_类.破产, arg_槽, self._角色点(arg_槽))
        if self._检查终局():
            return
        地产 = []
        for 地 in self.世界.地产:
            if 地.经济.业主 == arg_槽 + 1:
                地.经济.业主 = 地.到期日 = 0
                地产.append((2000 + 地.编号) & 65535)
        for 设 in self.世界.设施:
            if 设.业主 == arg_槽 + 1:
                设.业主 = 设.到期日 = 0
                地产.append((4000 + 设.编号) & 65535)
        for 公 in self.世界.公司:
            if 公.业主 == arg_槽 + 1:
                公.业主 = 0
        for i in range(12):
            数 = self.世界.玩家[arg_槽].持仓[i].数量
            if 数:
                股市_类.api_卖出(self.世界, arg_槽, i, 数, False)
        交通 = 人.交通 & 3
        if 交通:
            索 = 11 if 交通 == 3 else 交通 + 3
            人.道具[索] = (人.道具[索] + 1) & 255
        人.交通, 人.骰数 = 0, 1
        库 = 服务_类._库存(self.世界, arg_槽)
        库.api_卖库存道具()
        库.api_卖卡()
        彩票_类.api_退票(self.世界, arg_槽)
        if len(地产) > 3:
            for _ in range(3):
                while True:
                    选 = self.随机.api_下一个() % len(地产)
                    if 地产[选]:
                        break
                self._拍卖(地产[选], -1)
                地产[选] = 0

    def _保险赔偿(self, arg_槽: int, arg_额: int) -> None:
        if not 事件_类._取(self.世界.玩家, arg_槽).状态.保险天数:
            return
        for i in range(1, len(self.世界.公司)):
            if self.世界.公司[i].类型 == 4:
                self._付款(i + 100, arg_槽, arg_额, 1)
                return

    def _收银债(self, arg_槽: int, arg_额: int) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽).记录
        人.银行 = self._回绕(人.银行 - arg_额)
        if 人.银行 >= 0:
            return
        人.现金, 人.银行 = self._回绕(人.现金 + 人.银行), 0
        if 人.现金 < 0:
            人.现金 = 0
            self._破产(arg_槽)

    def _日期(self) -> 日期_类:
        日, 月, 年 = self.世界.头.日期
        return 日期_类(年, 月, 日)

    @staticmethod
    def _打包日期(arg_日: 日期_类) -> int:
        return (arg_日.年 << 16) | (arg_日.月 << 8) | arg_日.日

    @staticmethod
    def _解贷款日(arg_值: int) -> 日期_类 | None:
        try:
            return 日期_类((arg_值 >> 16) & 65535, (arg_值 >> 8) & 255, arg_值 & 255)
        except ValueError:
            return None

    def _收到期贷款(self) -> None:
        日 = self._解贷款日(self._状态().贷款到期)
        if 日 is None:
            return
        剩 = self._日期().api_日期差(日)
        if 剩 == 0:
            数 = self._玩家().贷款
            self._收银债(self._当前(), 数)
            self._玩家().贷款 = self._状态().贷款到期 = 0
            self._发事件(游戏事件种类_类.银行转账, "贷款到期，银行收回贷款", 数)
        elif 0 < 剩 <= 3:
            self._发事件(游戏事件种类_类.提示, f"贷款将在{剩}天后到期")

    def _对账融资(self, arg_撤款后: bool) -> None:
        主 = -1
        for 公 in self.世界.公司[1:]:
            if 公.类型 == 7 and 公.业主:
                主 = 公.业主 - 1
        if arg_撤款后:
            if 主 < 0 or 主 == self._当前():
                return
            人 = 事件_类._取(self.世界.玩家, 主).记录
            if not 人.特殊融资:
                return
            银总 = 0
            for i, 另 in enumerate(self.世界.玩家):
                if i != 主 and 另.记录.控制标志:
                    银总 = self._回绕(银总 + 另.记录.银行)
            if 银总 < 人.特殊融资:
                数 = self._回绕(人.特殊融资 - 银总)
                self._收银债(主, 数)
                人.特殊融资 = max(0, self._回绕(人.特殊融资 - 数))
        else:
            for i, 另 in enumerate(self.世界.玩家):
                人 = 另.记录
                if i != 主 and 人.控制标志 and 人.特殊融资:
                    self._收银债(i, 人.特殊融资)
                    人.特殊融资 = 0

    def _设置贷款日(self, arg_槽: int) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        if not 人.状态.贷款到期:
            人.状态.贷款到期 = self._打包日期(
                节日_类.api_贷款到期(self._日期(), self.世界.头.地图, self.世界.头.阶段)
            )

    def _借款(self, arg_额: int) -> bool:
        if (
            arg_额 <= 0
            or self._状态().银行禁贷天数
            or arg_额 > self._回绕(self._财富(self._当前()) - self._玩家().贷款)
        ):
            return False
        self._玩家().贷款 = self._回绕(self._玩家().贷款 + arg_额)
        self._玩家().银行 = self._回绕(self._玩家().银行 + arg_额)
        self._设置贷款日(self._当前())
        self._发事件(游戏事件种类_类.银行转账, "贷款已存入银行", arg_额)
        return True

    def _还款(self, arg_额: int, arg_清日期: bool) -> bool:
        人 = self._玩家()
        if arg_额 <= 0 or arg_额 > 人.贷款 or 人.现金 + 人.银行 < arg_额:
            return False
        银 = min(max(人.银行, 0), arg_额)
        人.银行, 人.现金 = self._回绕(人.银行 - 银), self._回绕(人.现金 - (arg_额 - 银))
        人.贷款 = self._回绕(人.贷款 - arg_额)
        if not 人.贷款 and arg_清日期:
            self._状态().贷款到期 = 0
        self._发事件(游戏事件种类_类.银行转账, "偿还贷款", arg_额)
        return True

    def _电脑银行贷款(self) -> None:
        人, 状 = self._玩家(), self._状态()
        if 人.贷款:
            日 = self._解贷款日(状.贷款到期)
            剩 = self._日期().api_日期差(日) if 日 is not None else 0
            总 = self._回绕(人.现金 + 人.银行)
            if 人.银行 > self._回绕(人.贷款 * 2) or (剩 <= 6 and 总 >= 人.贷款 * 1.1):
                self._还款(人.贷款, False)
        else:
            尝试 = self.随机.api_下一个() % 10 == 0
            if (
                (尝试 or self._回绕(人.现金 + 人.银行) < 30000)
                and not 状.银行禁贷天数
                and 状.贷款比例
            ):
                数 = self._零截除(self._回绕(状.贷款比例 * self._财富(self._当前())), 100)
                if 数 > 0:
                    人.贷款, 人.银行 = 数, self._回绕(人.银行 + 数)
                    self._设置贷款日(self._当前())
                    self._发事件(游戏事件种类_类.银行转账, "电脑玩家办理贷款", 数)

    def _拥有当前银行(self) -> bool:
        码 = 事件_类._取(self.世界.节点, self._玩家().节点).类型索引
        return (
            6000 < 码 < 8000
            and 码 - 6000 < len(self.世界.公司)
            and self.世界.公司[码 - 6000].业主 == self._当前() + 1
        )

    def _融资上限(self) -> int:
        总 = 0
        for i, 人 in enumerate(self.世界.玩家):
            if i != self._当前():
                总 = self._回绕(总 + 人.记录.银行)
        return self._回绕(总 - self._玩家().特殊融资)

    def _变更融资(self, arg_额: int, arg_借: bool) -> bool:
        if arg_额 <= 0 or not self._拥有当前银行() or self.恢复移动:
            return False
        人 = self._玩家()
        if arg_借:
            if self._状态().银行禁贷天数 or arg_额 > self._融资上限():
                return False
            人.银行, 人.特殊融资 = self._回绕(人.银行 + arg_额), self._回绕(人.特殊融资 + arg_额)
        else:
            if arg_额 > 人.特殊融资 or arg_额 > self._回绕(人.现金 + 人.银行):
                return False
            self._收银债(self._当前(), arg_额)
            人.特殊融资 = self._回绕(人.特殊融资 - arg_额)
        self._发事件(
            游戏事件种类_类.银行转账, "银行融资已存入账户" if arg_借 else "归还银行融资", arg_额
        )
        return True

    def _开银行(self, arg_经过: bool) -> None:
        self.恢复移动 = arg_经过
        if self._状态().银行拒绝天数:
            self._发事件(游戏事件种类_类.提示, "银行暂停办理这位玩家的业务")
            self._离银行()
            return
        if self._人类():
            选 = [决策选项_类("存款", 1)]
            if not self._状态().银行禁贷天数:
                选.append(决策选项_类("提款", 2))
            if not arg_经过:
                if not self._状态().银行禁贷天数:
                    选.append(决策选项_类("貸款", 3))
                if self._玩家().贷款 > 0:
                    选.append(决策选项_类("還貸", 4))
                if self._拥有当前银行():
                    if not self._状态().银行禁贷天数 and self._融资上限() > 0:
                        选.append(决策选项_类("銀行融資", 5))
                    if self._玩家().特殊融资 > 0:
                        选.append(决策选项_类("歸還融資", 6))
            选.append(决策选项_类("離開", 0))
            self.待决策 = 决策_类(决策种类_类.银行, self._当前(), 提示="辦理存款或提款", 选项=选)
            self._置阶段(游戏阶段_类.等待决策)
            return

        def 动作() -> None:
            E = 扩展数_类.api_从值
            人 = self._玩家()
            总 = self._回绕(人.现金 + 人.银行)
            比 = (E(人.现金) / E(总)).api_单精度() if 总 else 0.0
            目标 = (E(self._状态().初始现金比例) / E(100)).api_单精度()
            日 = self.世界.头.日期[0]
            if 日 <= 7:
                目标 = (E(目标) * E(1.5)).api_单精度()
            elif 日 >= 26:
                目标 = (E(目标) * E(0.5)).api_单精度()
            if 目标 >= 1:
                目标 = 股市_类._单(0.9)
            if 目标 <= 0:
                目标 = 股市_类._单(0.1)
            差 = 比 - 目标
            if (总 and (差 >= 0.25 or 差 <= -0.25)) or 人.现金 == 0:
                人.现金 = (E(总) * E(目标)).api_整数()
                人.银行 = self._回绕(总 - 人.现金)
                self._发事件(游戏事件种类_类.银行转账, "电脑玩家调整现金与存款")
                self._对账融资(True)
            if not arg_经过 and self.阶段 != 游戏阶段_类.结束:
                self._电脑银行贷款()

        def 成功() -> None:
            if self.阶段 != 游戏阶段_类.结束:
                self._离银行()

        self._执行规则(动作, True, False, 成功)

    def _离银行(self) -> None:
        self.待决策 = None
        if self.银行后遭遇:
            self.银行后遭遇 = self.恢复移动 = False
            self._逐步遭遇()
        elif self.恢复移动 and self.剩余步 > 0:
            self.恢复移动 = False
            self._开始一步()
        else:
            self.恢复移动 = False
            self._结束回合()

    def _财富(self, arg_槽: int) -> int:
        return 股市_类.api_财富(self.世界, arg_槽)

    def _更新物价(self) -> None:
        总, 活跃 = 0, 0
        for i, 人 in enumerate(self.世界.玩家):
            if 人.记录.控制标志:
                总, 活跃 = self._回绕(总 + self._财富(i)), 活跃 + 1
        if 活跃 and self.世界.头.初始资金 > 0:
            指 = self._零截除(self._零截除(总, 活跃), self.世界.头.初始资金)
            self.世界.头.物价 = max(self.世界.头.物价, 指)

    def _月报快照(self) -> 月报_类:
        报 = 月报_类()
        for i, 人 in enumerate(self.世界.玩家[:4]):
            if 人.记录.控制标志:
                报.活跃 |= 1 << i
            报.人物[i] = 人.记录.角色
        return 报

    def _月报效果(self, arg_种: 效果种类_类, arg_报: 月报_类) -> None:
        self.效果队列.append(
            效果_类(
                arg_种,
                self._当前(),
                self._玩家().节点,
                self._角色点(self._当前()),
                事件位=len(self.事件队列),
                月报=deepcopy(arg_报),
            )
        )

    def _派发股利(self) -> None:
        报, 总, E = self._月报快照(), [0] * 4, 扩展数_类.api_从值
        for i, 股 in enumerate(self.世界.股票[:12]):
            号 = 股.标志4
            if not 号 or 号 >= len(self.世界.公司):
                continue
            公, 股数 = self.世界.公司[号], 0
            for 人 in self.世界.玩家:
                if 人.记录.控制标志:
                    股数 = self._回绕(股数 + 人.持仓[i].数量)
            行 = 股利行_类(股票=i, 盈余=公.资金)
            for 槽, 人 in enumerate(self.世界.玩家[:4]):
                持 = 人.持仓[i].数量
                if not 人.记录.控制标志 or not 持:
                    continue
                比 = (E(持) / E(股数)).api_单精度()
                行.派发[槽] = (E(公.资金) * E(比)).api_整数()
                总[槽] = self._回绕(总[槽] + 行.派发[槽])
            if 股数:
                公.资金 = 0
            报.股利.append(行)
        if not 报.股利:
            return
        self._月报效果(效果种类_类.股利, 报)
        for 槽, 另 in enumerate(self.世界.玩家[:4]):
            人 = 另.记录
            if not 人.控制标志:
                continue
            人.银行 = self._回绕(人.银行 + 总[槽])
            if 人.银行 >= 0:
                continue
            人.现金, 人.银行 = self._回绕(人.现金 + 人.银行), 0
            if 人.现金 < 0:
                人.现金 = 0
                self._破产(槽)

    def _结月(self) -> None:
        报, E = self._月报快照(), 扩展数_类.api_从值
        for 槽, 人 in enumerate(self.世界.玩家[:4]):
            报.存款[槽] = 人.记录.银行
            报.利息[槽] = (E(人.记录.银行) * E(0.1)).api_整数()
            if 人.记录.贷款:
                报.贷款 |= 1 << 槽
            报.倒霉天[槽], 报.支出[槽], 报.收入[槽] = (
                人.状态.冬眠总天数,
                人.状态.累计支出,
                人.状态.累计收入,
            )
        for 人 in self.世界.玩家:
            if 人.记录.控制标志 and 人.记录.贷款 == 0:
                人.记录.银行 = (E(人.记录.银行) * E(1.1)).api_整数()
        self._月奖项(报)
        for 人 in self.世界.玩家:
            人.状态.冬眠总天数 = 人.状态.累计支出 = 人.状态.累计收入 = 0
        self._发事件(游戏事件种类_类.银行转账, "月结完成，无贷款玩家获得存款利息")
        self._月报效果(效果种类_类.月报, 报)

    def _月奖项(self, arg_报: 月报_类) -> None:
        最富, 分 = 0, [0] * 4
        arg_报.冠军 = -1
        for 槽, 人 in enumerate(self.世界.玩家[:4]):
            if not (arg_报.活跃 >> 槽) & 1:
                continue
            arg_报.现金[槽], arg_报.余额[槽], arg_报.总资产[槽] = (
                人.记录.现金,
                人.记录.银行,
                self._财富(槽),
            )
            if arg_报.冠军 < 0:
                arg_报.冠军 = 槽
            if arg_报.总资产[槽] > 最富:
                最富, arg_报.冠军 = arg_报.总资产[槽], 槽
            状 = 人.状态
            分[槽] = self._回绕(
                self._回绕(
                    self._回绕(状.累计支出 - 状.累计收入)
                    + self._回绕(self._回绕(状.冬眠总天数 * self.世界.头.物价) * 2500)
                )
                + self._回绕(状.神运修正 * 10)
            )
        高, 次, 最高槽 = 0, 0, -1
        for 槽 in range(4):
            if (arg_报.活跃 >> 槽) & 1 and 分[槽] > 高:
                高, 最高槽 = 分[槽], 槽
        for 槽 in range(4):
            if (arg_报.活跃 >> 槽) & 1 and 分[槽] != 高 and 分[槽] > 次:
                次 = 分[槽]
        arg_报.悲情 = 最高槽 if 高 and 次 and (高 - 次) / 高 > 0.4 else -1

    def _租约到期(self) -> int:
        间隔 = (0, 0x20000, 0x10000, 0x600, 0x300, 0x100)
        if not 0 <= self.世界.租约模式 < len(间隔):
            raise RuntimeError("invalid lease mode")
        量 = 间隔[self.世界.租约模式]
        return 日期_类.api_打包间隔(self._打包日期(self._日期()), 量) if 量 else 0

    def _地产到期(self) -> None:
        今 = self._打包日期(self._日期())
        for 地 in self.世界.地产 + self.世界.设施:
            if 地.临时状态 & 0xF0:
                地.临时状态 = (地.临时状态 - 0x10) & 255
                if not 地.临时状态 & 0xF0:
                    地.临时状态 = 0
            if 地.到期日 == 今:
                if hasattr(地, "经济"):
                    地.经济.业主 = 0
                else:
                    地.业主 = 0
                地.到期日 = 0
