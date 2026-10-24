# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ game.cpp 373..842及lookahead；原规则调用顺序不按UI帧重排。
# ◑ 导入
from copy import deepcopy

from rich4.cards import 卡片_类, 卡片前瞻_类, 卡片状态_类, 目标种类_类
from rich4.cards_ai import 卡片电脑_类
from rich4.direction import 方向_类
from rich4.events import 事件_类
from rich4.game_types import (
    公告种类_类,
    效果种类_类,
    未支持规则异常_类,
    游戏事件种类_类,
    游戏阶段_类,
    移动动画_类,
    语句表_类,
)
from rich4.gods import 神明_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类
from rich4.stocks_ai import 股票电脑_类
from rich4.tools import 道具_类
from rich4.tools_ai import 道具电脑_类, 道具电脑回调_类
from rich4.trading import 交易_类


# ◕ 功能
class 会话移动_类:
    """
    原出场/状态老化/AI回合/掷骰/逐格移动与途中遭遇，同一会话调用真实结算。

    更新日志：
    2026.10.24 - 完整保留高位计数器、随机消费和选择事务边界。
    """

    def _按需出场(self) -> None:
        人 = self._玩家()
        if 人.x != 0:
            return
        候 = []
        for i, 节 in enumerate(self.世界.节点[1:], 1):
            if not 节.标志 & 0x80FFFF00 and any(节.邻居):
                if i > 255:
                    raise RuntimeError("original spawn candidate exceeds byte node ID")
                候.append(i)
        if not 候:
            raise RuntimeError("world has no unoccupied spawn node")
        人.节点 = 候[self.随机.api_下一个() % len(候)]
        节 = self.世界.节点[人.节点]
        前 = []
        for 邻 in 节.邻居:
            if 邻:
                if 邻 >= len(self.世界.节点):
                    raise RuntimeError("spawn neighbor outside table")
                前.append(邻)
        人.上次节点 = 前[self.随机.api_下一个() % len(前)]
        人.x, 人.y = 节.x & 65535, 节.y & 65535
        上 = self.世界.节点[人.上次节点]
        人.方向 = 方向_类.api_计算(节.x - 上.x, 节.y - 上.y)
        节.标志 |= 0x100 << self._当前()
        self._地图影片(效果种类_类.降落伞, self._当前(), self._角色点(self._当前()), None, 人.角色)

    @staticmethod
    def _老化天数(arg_值: int) -> int:
        值 = arg_值 & 127
        return 128 if 值 == 1 else 值 - 1 if 值 else 0

    def _更新状态(self) -> None:
        状 = self._状态()
        离楼 = bool((状.酒店天数 | 状.监狱天数 | 状.医院天数) & 128)
        返回 = 状.消失天数 if 状.消失天数 & 128 else None
        if (状.监狱天数 | 状.医院天数) & 128:
            self._结束服装(self._当前())
        已释放 = False
        for 名 in ("酒店天数", "消失天数", "监狱天数", "医院天数"):
            天 = getattr(状, 名)
            if 天 & 128:
                setattr(状, 名, 0)
                已释放 = True
            elif 天:
                天 -= 1
                掩 = 63 if 名 == "消失天数" else 127
                if not 天 & 掩:
                    天 = 128 | (天 & ~掩 & 127)
                setattr(状, 名, 天)
        if 已释放:
            if not 状.监狱天数:
                self.世界.监狱名单[self._当前()] = 0
            if not 状.医院天数:
                self.世界.医院名单[self._当前()] = 0
            人 = self._玩家()
            节 = 事件_类._取(self.世界.节点, 人.节点)
            人.控制标志 &= 15
            人.方向 = 状.保存方向 if 状.保存方向 < 8 else 方向_类.api_计算(节.x - 人.x, 节.y - 人.y)
            人.x, 人.y = 节.x & 65535, 节.y & 65535
            节.标志 |= 0x100 << self._当前()
            if 返回 is not None:
                self._结束服装(self._当前())
                self._地图影片(
                    效果种类_类.飞碟 if 返回 & 64 else 效果种类_类.飞机,
                    self._当前(),
                    self._角色点(self._当前()),
                    None,
                    1,
                )
        if not (状.酒店天数 | 状.消失天数 | 状.监狱天数 | 状.医院天数):
            if 状.梦游天数 & 128:
                前 = 状.标志102 & 3
                人 = self._玩家()
                if 前 == 3 or (前 == 1 and 人.道具[4]) or (前 == 2 and 人.道具[5]):
                    人.交通, 人.骰数 = 状.标志102, 状.标志103
                    if 前 in (1, 2):
                        人.道具[前 + 3] -= 1
                else:
                    人.交通, 人.骰数 = 0, 1
            for 名 in ("睡眠天数", "梦游天数", "龟行天数"):
                setattr(状, 名, self._老化天数(getattr(状, 名)))
        if 状.结盟天数 & 128:
            if 0 < 状.盟友 <= len(self.世界.玩家):
                友 = self.世界.玩家[状.盟友 - 1].状态
                友.盟友 = 友.结盟天数 = 0
            状.盟友 = 0
        elif 状.结盟天数 and 0 < 状.盟友 <= len(self.世界.玩家):
            额 = 股市_类._回绕(-股市_类._回绕(20 * self.世界.头.物价))
            self._更新敌意(self._当前(), 状.盟友 - 1, 额)
            self._更新敌意(状.盟友 - 1, self._当前(), 额)
        for 名 in ("停留天数", "银行拒绝天数", "银行禁贷天数", "结盟天数", "保险天数"):
            setattr(状, 名, self._老化天数(getattr(状, 名)))
        if 状.神明信息:
            神 = 事件_类._取(self.世界.物件, 状.神明信息 - 1)
            神.剩余天数 = (神.剩余天数 - 1) & 255
            if 神.剩余天数 == 0:
                self._检查神明(神明_类.api_脱离(self.世界, self._当前(), self._神明回调()))
        人 = self._玩家()
        if 人.交通 & 3 == 3:
            人.交通 = (人.交通 - 4) & 255
            if not 人.交通 & 0xFC:
                前 = 状.标志100 & 3
                if (前 == 1 and 人.道具[4]) or (前 == 2 and 人.道具[5]):
                    人.交通, 人.骰数 = 状.标志100, 状.标志101
                    人.道具[前 + 3] -= 1
                else:
                    人.交通, 人.骰数 = 0, 1
        if 离楼:
            self._检查神明(
                神明_类.api_地产后(self.世界, self._当前(), self._玩家().节点, self._神明回调())
            )
            self._工程车拆屋()

    def _开始回合(self, arg_更新: bool = True) -> None:
        self.地产落点 = False
        self._按需出场()
        self.待决策 = self.动画 = None
        self.剩余步 = 0
        if arg_更新:

            def 动作() -> None:
                股市_类.api_刷新限额(self.世界, self.随机)
                self._收到期贷款()
                if self.阶段 != 游戏阶段_类.结束 and self._玩家().控制标志:
                    self._更新状态()

            self._执行规则(动作, True, False, self._进入回合)
        else:
            self._进入回合()

    def _进入回合(self) -> None:
        if self.阶段 == 游戏阶段_类.结束:
            return
        if not self._玩家().控制标志:
            self._结束回合()
            return
        槽 = self._当前()
        self._发事件(游戏事件种类_类.回合开始, f"玩家{槽 + 1}的回合")
        状 = self._状态()
        if 状.酒店天数 or 状.消失天数 or 状.监狱天数 or 状.医院天数 or 状.睡眠天数:
            类 = (
                0
                if 状.酒店天数
                else 1
                if 状.消失天数
                else 2
                if 状.监狱天数
                else 3
                if 状.医院天数
                else 4
            )
            原 = (
                状.酒店天数
                if 类 == 0
                else 状.消失天数 & 63
                if 类 == 1
                else 状.监狱天数
                if 类 == 2
                else 状.医院天数
                if 类 == 3
                else 状.睡眠天数
            )
            if 类 >= 2:
                self._语音(槽, 19 if 类 == 2 else 20 if 类 == 3 else 21)
            self._公告(公告种类_类.缺席状态, 槽, 类).值 = 原 & 127
            self._发事件(游戏事件种类_类.提示, f"玩家{槽 + 1}本回合休息")
            self._结束回合()
        elif self._人类() and not 状.梦游天数:
            self._置阶段(游戏阶段_类.人类待命)
        elif 状.梦游天数 or self._玩家().控制标志 & 0x30:
            self._开始掷骰()
        else:
            self._开始电脑回合()

    def _电脑骰数(self) -> None:
        人, 状 = self._玩家(), self._状态()
        交 = 人.交通 & 3
        if 交 not in (1, 2):
            return
        人.骰数 = 交 + 1
        if 状.附身炸弹:
            if 事件_类._取(self.世界.物件, 状.附身炸弹 - 1).剩余天数 < 15:
                人.骰数 = 1
            return
        路, 好, 坏 = self._前瞻(self._当前(), 5), 0, 0
        for i in 路.节点:
            码 = 事件_类._取(self.世界.节点, i).类型索引
            主, 地产 = 0, False
            if 2000 < 码 < 4000:
                主, 地产 = 事件_类._取(self.世界.地产, 码 - 2000).经济.业主, True
            elif 4000 < 码 < 6000:
                主, 地产 = 事件_类._取(self.世界.设施, 码 - 4000).业主, True
            if 地产:
                if not 主 or 主 == self._当前() + 1:
                    好 += 1
                else:
                    坏 += 1
        if 好 >= 2 and 坏 <= 1:
            人.骰数 = 1
        elif 交 == 2 and not 好 and 坏 > 2:
            人.骰数 = 2 + (self.随机.api_下一个() & 1)

    def _开始电脑回合(self) -> None:
        def 动作() -> None:
            关 = self._卡片回调().休市()
            for 交 in 股票电脑_类.api_买入(self.世界, self.随机, self._当前(), 关):
                self._发事件(
                    游戏事件种类_类.提示, f"电脑买入股票{交.股票 + 1}，{交.数量}股", 交.金额
                )
            for 交 in 股票电脑_类.api_卖出(self.世界, self.随机, self._当前(), 关):
                self._发事件(
                    游戏事件种类_类.提示, f"电脑卖出股票{交.股票 + 1}，{交.数量}股", 交.金额
                )
            self._对账融资(False)
            if self.阶段 == 游戏阶段_类.结束 or not self._玩家().控制标志:
                return
            价 = 交易_类.api_电脑回合(self.世界, self.随机, self._当前())
            if 价.挂牌:
                self._发事件(游戏事件种类_类.提示, "电脑发布出售报价")
            if 价.购买 is not None:
                self._发事件(游戏事件种类_类.提示, "电脑购买出售物品", 价.购买.出售项.价格)
            self._对账融资(False)
            if self.阶段 == 游戏阶段_类.结束 or not self._玩家().控制标志:
                return
            if self.随机.api_下一个() & 1:
                钩 = self._卡片回调()
                用 = 卡片电脑_类.api_选择(self.世界, self.随机, self._当前(), 钩, self.卡片电脑记忆)
                if 用 is not None:
                    self._开始卡片(用)
                    self._抛卡(用)
                    果 = 卡片_类.api_使用(self.世界, self.随机, self._当前(), 用, 钩)
                    if 果.状态 == 卡片状态_类.缺回调:
                        raise 未支持规则异常_类(果.消息)
                    if 果.状态 == 卡片状态_类.已用:
                        self._卡图()
                        if (
                            用.卡片 in (24, 25)
                            and 用.目标 is not None
                            and 用.目标.种类 == 目标种类_类.股票
                        ):
                            self._公告(
                                公告种类_类.股票卡, self._当前(), 用.卡片
                            ).主体 = 用.目标.数值
                        self._发事件(
                            游戏事件种类_类.提示,
                            "电脑使用" + 事件_类._取(服务_类.卡名, 用.卡片 - 1),
                        )
                        self.事件队列[-1].卡片 = 用.卡片
            else:

                def 实例(arg_槽: int) -> list[int]:
                    人 = 事件_类._取(self.世界.玩家, arg_槽).记录
                    return self._实例编码(人.x, 人.y, -1)

                选 = 道具电脑_类.api_选择(
                    self.世界, self.随机, self._当前(), 道具电脑回调_类(附近实例=实例)
                )
                if not 选.支持:
                    raise 未支持规则异常_类(选.消息)
                if 选.决策 is not None:
                    用 = 选.决策
                    self._公告(公告种类_类.用道具, self._当前(), 用.道具 & 255)
                    果 = 道具_类.api_使用(
                        self.世界,
                        self.随机,
                        self._当前(),
                        用.道具,
                        用.目标,
                        用.目的地,
                        self._道具回调(),
                    )
                    if not 果.支持:
                        raise 未支持规则异常_类(果.消息)
                    if 果.已应用:
                        self._道具效果(用.道具, 用.目标)
                        self._发事件(
                            游戏事件种类_类.提示,
                            "电脑使用" + 事件_类._取(服务_类.道具名, 用.道具 - 1),
                        )

        def 成功() -> None:
            if self.阶段 in (游戏阶段_类.结束, 游戏阶段_类.掷骰, 游戏阶段_类.移动):
                return
            状 = self._状态()
            if (
                not self._玩家().控制标志
                or 状.酒店天数
                or 状.消失天数
                or 状.监狱天数
                or 状.医院天数
                or 状.睡眠天数
                or 状.梦游天数
            ):
                self._结束回合()
                return
            self._电脑骰数()
            self._开始掷骰()

        self._执行规则(动作, True, False, 成功)

    def _开始掷骰(self) -> None:
        人, 状, 槽 = self._玩家(), self._状态(), self._当前()
        if 人.控制标志 & 1 and not 人.控制标志 & 0x30:
            self.上一回合[槽] = deepcopy(self.世界)
        self.骰面.clear()
        self.剩余步 = 0
        if 人.控制标志 & 0x30:
            self.剩余步 = 1
        elif 状.停留天数:
            self._暂停(2)
            self._落点()
            return
        elif self.强制骰 is not None:
            self.剩余步 = self.强制骰
            self.骰面.append(self.强制骰 & 255)
            self.强制骰 = None
        elif 状.龟行天数:
            self.剩余步 = 1
        else:
            for _ in range(人.骰数):
                点 = self.随机.api_下一个() % 6 + 1
                self.骰面.append(点)
                self.剩余步 += 点
        self._发事件(游戏事件种类_类.骰子结果, f"玩家{槽 + 1}前进{self.剩余步}步", self.剩余步)
        if self.骰面:
            self._效果(效果种类_类.掷骰, 槽, self._角色点(槽))
            self.效果队列[-1].骰子 = self.骰面.copy()
        self._置阶段(游戏阶段_类.掷骰)

    def _开始一步(self) -> None:
        人 = self._玩家()
        节 = 事件_类._取(self.世界.节点, 人.节点)
        候 = []
        for i, 邻 in enumerate(节.邻居):
            if 邻 and 邻 != 人.上次节点 and not 节.标志 & (0x40000000 >> i):
                if 邻 >= len(self.世界.节点):
                    raise RuntimeError("map link outside node table")
                候.append(邻)
        self.下节点 = 人.上次节点 if not 候 else 候[self.随机.api_下一个() % len(候)]
        if self.下节点 >= len(self.世界.节点):
            raise RuntimeError("fallback node outside table")
        后 = self.世界.节点[self.下节点]
        self.动画 = 移动动画_类(self._当前(), 人.x, 人.y, 后.x, 后.y, 0, 160)
        self._置阶段(游戏阶段_类.移动)

    def _完成一步(self) -> None:
        人 = self._玩家()
        旧 = 人.节点
        后 = 事件_类._取(self.世界.节点, self.下节点)
        事件_类._取(self.世界.节点, 旧).标志 &= ~(0x100 << self._当前()) & 0xFFFFFFFF
        后.标志 |= 0x100 << self._当前()
        人.上次节点, 人.节点 = 旧, self.下节点
        人.方向 = 方向_类.api_计算(后.x - 人.x, 后.y - 人.y)
        人.x, 人.y = 后.x & 65535, 后.y & 65535
        self._同步附身(self._当前())
        self.剩余步 -= 1
        self.动画 = None
        self._发事件(游戏事件种类_类.已移动, f"玩家{self._当前() + 1}到达道路{self.下节点}")
        物 = 后.标志 >> 16 & 255
        if (
            self.剩余步 > 0
            and 后.标志 & 255 == 14
            and not self._状态().梦游天数
            and (not 物 or 事件_类._取(self.世界.物件, 物 - 1).种类 != 16)
        ):
            self.银行续遭遇 = True
            self._开银行(True)
            return
        self._逐步遭遇()

    def _逐步遭遇(self) -> None:
        物 = 事件_类._取(self.世界.节点, self._玩家().节点).标志 >> 16 & 255

        def 动作() -> None:
            占 = (
                (事件_类._取(self.世界.节点, self._玩家().节点).标志 >> 8)
                & 15
                & ~(1 << self._当前())
            )
            if 占 and self.剩余步 == 0:
                另 = (占 & -占).bit_length() - 1
                if 另 < len(self.世界.玩家) and not self.世界.玩家[另].记录.控制标志:
                    self._付款(self._当前(), -1, 股市_类._回绕(1000 * self.世界.头.物价), 0)
                    self._搬走破产者(另)
                    if self.阶段 == 游戏阶段_类.结束:
                        return
            状 = self._状态()
            if 状.附身炸弹:
                号 = 状.附身炸弹
                炸 = 事件_类._取(self.世界.物件, 号 - 1)
                炸.剩余天数 = (炸.剩余天数 - 1) & 255
                if 炸.剩余天数 == 0:
                    self._移除物件(号)
                    self._改建筑(事件_类._取(self.世界.节点, self._玩家().节点).类型索引, False)
                    self._效果(效果种类_类.爆炸, self._当前(), self._角色点(self._当前()))
                    self._受伤(self._当前())
                    self._收容(self._当前(), 5, True)
                    self.剩余步 = 0
                    return
                if 占:
                    另 = (占 & -占).bit_length() - 1
                    if (
                        另 < len(self.世界.玩家)
                        and self.世界.玩家[另].记录.控制标志
                        and not self.世界.玩家[另].状态.附身炸弹
                    ):
                        self.世界.玩家[另].状态.附身炸弹 = 号
                        炸.附身玩家, 状.附身炸弹 = (另 + 1) & 255, 0
            if 物:
                类 = 事件_类._取(self.世界.物件, 物 - 1).种类
                self.地雷待处理 = 类 == 17
                try:
                    果 = 神明_类.api_接触(
                        self.世界, self.随机, self._当前(), 物, self.剩余步 == 0, self._神明回调()
                    )
                    self._检查神明(果)
                    if 果.已应用 and 类 == 16:
                        self._语句(self._当前(), 语句表_类.道具, 14, 1)
                    if 果.已应用 and 类 == 18:
                        self._语句(self._当前(), 语句表_类.道具, 16, 2)
                    if 果.停止移动:
                        self.剩余步 = 0
                finally:
                    self.地雷待处理 = False

        def 成功() -> None:
            if self.阶段 == 游戏阶段_类.结束:
                return
            状 = self._状态()
            if 状.医院天数 or 状.监狱天数 or 状.消失天数:
                self._结束回合()
            elif self.剩余步 > 0:
                self._开始一步()
            else:
                self._暂停(5)
                self._落点()

        self._执行规则(动作, True, False, 成功)

    def _前瞻(self, arg_槽: int, arg_数: int) -> 卡片前瞻_类:
        if not 0 <= arg_数 <= 8:
            raise ValueError("lookahead exceeds original eight nodes")
        人 = 事件_类._取(self.世界.玩家, arg_槽).记录
        前, 今, 路 = 人.上次节点, 人.节点, 卡片前瞻_类([0] * arg_数)
        for n in range(arg_数):
            节 = 事件_类._取(self.世界.节点, 今)
            候 = [
                邻
                for i, 邻 in enumerate(节.邻居)
                if 邻 and 邻 != 前 and not 节.标志 & (0x40000000 >> i)
            ]
            后 = 前
            if len(候) == 1:
                后 = 候[0]
            elif len(候) > 1:
                后 = 候[self.随机.api_下一个() % len(候)]
                路.经过路口 = True
            前, 今 = 今, 后
            路.节点[n] = 后
        return 路
