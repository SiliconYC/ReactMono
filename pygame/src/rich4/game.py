# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ game.cpp::GameSession/Impl；各规则组件组成同一独立Python会话。
# ◑ 导入
from copy import deepcopy

from rich4.calendar import 日期_类
from rich4.cards import 卡片_类, 卡片状态_类, 卡片用法_类, 卡片目标_类, 电脑卡片记忆_类
from rich4.game_actions import 会话动作_类
from rich4.game_actors import 会话角色_类
from rich4.game_finance import 会话金融_类
from rich4.game_landing import 会话落点_类
from rich4.game_motion import 会话移动_类
from rich4.game_presentation import 会话表现_类
from rich4.game_property import 会话地产_类
from rich4.game_transactions import 会话事务_类
from rich4.game_types import (
    决策种类_类,
    托管设置_类,
    未支持规则异常_类,
    游戏事件_类,
    游戏事件种类_类,
    游戏阶段_类,
)
from rich4.lottery import 彩票_类, 购票结果_类
from rich4.random import 随机数_类
from rich4.save import 存档_类
from rich4.save_records import 玩家记录_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类, 走势_类
from rich4.tools import 道具_类
from rich4.trading import 交易_类, 挂单_类
from rich4.world import 世界_类
from rich4.world_player import 玩家状态_类


# ◕ 功能
class 游戏会话_类(
    会话落点_类,
    会话移动_类,
    会话地产_类,
    会话金融_类,
    会话动作_类,
    会话角色_类,
    会话表现_类,
    会话事务_类,
):
    """
    原公开GameSession操作与时钟，规则、随机、决策和表现由同一世界推进。

    更新日志：
    2026.10.24 - 独立Python主会话，原DAT保存不宣称含RNG或未完成决策。
    """

    def __init__(
        self, arg_世界: 世界_类, arg_种子: int = 1, arg_捕获轮次起点: bool = False
    ) -> None:
        self.世界 = deepcopy(arg_世界)
        # 仅桌面自动存档需要；测试和无界面的核心会话不支付额外快照成本。
        self.捕获轮次起点 = arg_捕获轮次起点
        self.轮次起点: tuple[int, bytes, int] | None = None
        self._轮次起点轮: int | None = None
        self.随机 = 随机数_类(self.世界.初始随机状态 if self.世界.有初始随机状态 else arg_种子)
        self.阶段, self.阶段毫秒 = 游戏阶段_类.人类待命, 0
        self.待决策 = self.动画 = self.选定卡目标 = self.使用中卡 = None
        self.骰面, self.事件队列, self.效果队列 = [], [], []
        self.地雷待处理 = self.卡图已示 = False
        self.剩余步, self.下节点, self.完成天数, self.胜者 = 0, 0, 0, None
        self.恢复移动 = self.银行后遭遇 = False
        self.事件选择, self.选择随机状态, self.待续 = {}, {}, None
        self.待选择键, self.选择序列 = 0, 0
        self.轮盘游标 = self.轮盘毫秒 = self.轮盘种类 = self.轮盘设施 = 0
        self.救援医院, self.商店, self.商店地产, self.魔法类别 = False, None, 0, 0
        self.上次行动接受, self.未支持恢复, self.强制骰 = False, 游戏阶段_类.推进回合, None
        self.上一回合, self.待托管 = [None] * 4, [None] * 4
        self.金钱转盘, self.转盘随机, self.转盘毫秒 = None, 随机数_类(0), 0
        self.卡片电脑记忆 = 电脑卡片记忆_类()
        self.地产待处理 = self.已购地产 = self.地产落点 = self.互动小游戏 = False
        self.服装, self.服装键 = [0] * 4, [0] * 4
        if not 1 <= len(self.世界.玩家) <= 4 or not 0 <= self._当前() < len(self.世界.玩家):
            raise ValueError("invalid native game player table")
        日, 月, 年 = self.世界.头.日期
        日期_类(年, 月, 日)
        for 人 in self.世界.玩家:
            if not 0 <= 人.记录.节点 < len(self.世界.节点) or not 0 <= 人.记录.上次节点 < len(
                self.世界.节点
            ):
                raise ValueError("player node outside native world")
        if not self.世界.有初始随机状态 and self._检查终局():
            return
        if self.世界.有初始随机状态:
            for 号 in (1, 3, 5, 7, 9, 11, 13, 14):
                self._放现有物件(号 - 1, self._随机空节点())
            股市_类.api_刷新限额(self.世界, self.随机)
        self._开始回合(False)

    def _当前(self) -> int:
        return self.世界.头.当前玩家

    def _玩家(self) -> 玩家记录_类:
        return self.世界.玩家[self._当前()].记录

    def _状态(self) -> 玩家状态_类:
        return self.世界.玩家[self._当前()].状态

    def _人类(self) -> bool:
        return self._玩家().控制标志 == 1

    def api_设相机(self, arg_旋转: int) -> None:
        if not 0 <= arg_旋转 <= 7:
            raise ValueError("camera rotation must be 0..7")
        self.世界.相机旋转 = arg_旋转

    def api_设骰数(self, arg_数: int) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        交 = self._玩家().交通 & 3
        上限 = 2 if 交 == 1 else 3 if 交 == 2 else 1
        if not 0 < arg_数 <= 上限:
            return False
        self._玩家().骰数 = arg_数
        return True

    def api_掷骰(self) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        self._开始掷骰()
        return True

    def api_卡片目标(self, arg_卡: int) -> list[卡片目标_类]:
        return 卡片_类.api_合法目标(self.世界, self._当前(), arg_卡, self._卡片回调())

    def api_用卡(self, arg_用: 卡片用法_类) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        self.上次行动接受 = True
        用 = deepcopy(arg_用)

        def 动作() -> None:
            self._开始卡片(用)
            果 = 卡片_类.api_使用(self.世界, self.随机, self._当前(), 用, self._卡片回调())
            self.上次行动接受 = 果.已使用
            if 果.状态 == 卡片状态_类.缺回调:
                raise 未支持规则异常_类(果.消息)
            if 果.已使用:
                self._卡图()
                self._发事件(游戏事件种类_类.提示, "使用" + 服务_类.卡名[用.卡片 - 1])
                self.事件队列[-1].卡片 = 用.卡片

        self._执行规则(动作, True, False)
        return self.上次行动接受 or self.阶段 == 游戏阶段_类.等待决策

    def api_用道具(self, arg_物: int, arg_目标: int = 0, arg_目的: int = 0) -> bool:
        if (
            self.阶段 != 游戏阶段_类.人类待命
            or not 1 <= arg_物 <= 13
            or not self._玩家().道具[arg_物 - 1]
        ):
            return False
        self.上次行动接受 = True

        def 动作() -> None:
            对, 去 = arg_目标, arg_目的
            要选 = 道具_类.api_选择位(arg_物) != 0 or arg_物 == 8
            if 要选 and not 对:
                对 = self._选择道具目标(arg_物, 0)
            if 要选 and not 对:
                self.上次行动接受 = False
                return
            if arg_物 == 11 and not 去:
                去 = self._选择道具目标(arg_物, 对)
            if arg_物 == 11 and not 去:
                self.上次行动接受 = False
                return
            if 道具_类.api_选择位(arg_物) != 0 and 对 not in self._道具目标(arg_物):
                self.上次行动接受 = False
                return
            if arg_物 == 11 and 去 not in self._道具目标(arg_物, 对):
                self.上次行动接受 = False
                return
            果 = 道具_类.api_使用(
                self.世界, self.随机, self._当前(), arg_物, 对, 去, self._道具回调()
            )
            self.上次行动接受 = 果.已应用
            if not 果.支持:
                raise 未支持规则异常_类(果.消息)
            if 果.已应用:
                self._道具效果(arg_物, 对)
                self._发事件(游戏事件种类_类.提示, "使用" + 服务_类.道具名[arg_物 - 1])

        self._执行规则(动作, True, False)
        return self.上次行动接受 or self.阶段 == 游戏阶段_类.等待决策

    def api_下车(self) -> bool:
        return self.阶段 == 游戏阶段_类.人类待命 and 道具_类.api_下车(self.世界, self._当前())

    def api_买股票(self, arg_股: int, arg_数: int) -> bool:
        if (
            self.阶段 != 游戏阶段_类.人类待命
            or not 0 <= arg_股 < len(self.世界.股票)
            or arg_数 <= 0
            or self._卡片回调().休市()
        ):
            return False
        股 = self.世界.股票[arg_股]
        if 股.停牌天数 or 股市_类.api_走势(self.世界, arg_股) == 走势_类.涨停 or arg_数 > 股.标志10:
            return False
        try:
            果 = 股市_类.api_买入(self.世界, self._当前(), arg_股, arg_数, True)
            self._发事件(游戏事件种类_类.银行转账, "买入股票", 果.费用)
            return True
        except (ValueError, IndexError):
            return False

    def api_卖股票(self, arg_股: int, arg_数: int) -> bool:
        if (
            self.阶段 != 游戏阶段_类.人类待命
            or not 0 <= arg_股 < len(self.世界.股票)
            or arg_数 <= 0
            or self._卡片回调().休市()
        ):
            return False
        股 = self.世界.股票[arg_股]
        if 股.停牌天数 or 股市_类.api_走势(self.世界, arg_股) == 走势_类.跌停:
            return False
        try:
            果 = 股市_类.api_卖出(self.世界, self._当前(), arg_股, arg_数, True)
            self._发事件(游戏事件种类_类.银行转账, "卖出股票", 果.收入)
            return True
        except (ValueError, IndexError):
            return False

    def api_关股市(self) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        self._执行规则(lambda: self._对账融资(False), True, False)
        return True

    def api_开交易(self) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        交易_类.api_清理(self.世界)
        return True

    def api_挂牌(self, arg_单: 挂单_类) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        果 = 交易_类.api_挂牌(self.世界, self._当前(), arg_单)
        if 果.已应用:
            self._发事件(游戏事件种类_类.提示, "出售报价已发布", arg_单.价格)
        return 果.已应用

    def api_撤单(self, arg_索: int) -> bool:
        return self.阶段 == 游戏阶段_类.人类待命 and 交易_类.api_取消(
            self.世界, self._当前(), arg_索
        )

    def api_买报价(self, arg_卖: int, arg_索: int) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        果 = 交易_类.api_购买(self.世界, self._当前(), arg_卖, arg_索)
        if 果.已应用:
            self._发事件(游戏事件种类_类.提示, "购买出售物品完成")
        return 果.已应用

    def api_关交易(self) -> bool:
        if self.阶段 != 游戏阶段_类.人类待命:
            return False
        self._执行规则(lambda: self._对账融资(False), True, False)
        return True

    def api_回答(self, arg_选: int, arg_额: int = 0) -> bool:
        if (
            self.阶段 != 游戏阶段_类.等待决策
            or self.待决策 is None
            or not 0 <= arg_选 < len(self.待决策.选项)
        ):
            return False
        决 = deepcopy(self.待决策)
        值, 类 = 决.选项[arg_选].值, 决.种类
        if 类 == 决策种类_类.金额转盘:
            if self.金钱转盘 is None:
                return False
            self.金钱转盘.api_停止()
            return True
        if self.待续 is not None:
            if 类 == 决策种类_类.轮盘:
                值 = self._轮盘值(self.轮盘种类, self.轮盘游标 + 12)
                self._停止轮盘效果(决, 值)
            if 类 == 决策种类_类.初级股票 and 值:
                if not 0 < arg_额 <= 决.金额上限:
                    return False
                值 = arg_额
            self.事件选择[self.待选择键] = 值
            self.待决策 = None
            续, self.待续 = self.待续, None
            续()
            return True
        if 类 == 决策种类_类.彩票:
            if 值 and 彩票_类.api_购票(self.世界, self._当前(), 值) != 购票结果_类.成功:
                return False
            if 值:
                self._发事件(游戏事件种类_类.提示, f"购买彩票{值}", 彩票_类.票价)
            self._结束回合()
            return True
        if 类 == 决策种类_类.商店:
            return self._商店行动(值, arg_额 if arg_额 > 0 else 1)
        if 类 == 决策种类_类.魔法类别:
            self._魔法效果提示(值)
            return True
        if 类 == 决策种类_类.魔法效果:
            if 值 < 0:
                self._开魔法()
            else:
                self._施魔法(值)
            return True
        if 类 == 决策种类_类.银行:
            人 = self._玩家()
            if 值 == 0:
                self._离银行()
                return True
            if arg_额 <= 0:
                return False
            if 值 in (3, 4, 5, 6):
                成 = (
                    self._借款(arg_额)
                    if 值 == 3
                    else self._还款(arg_额, True)
                    if 值 == 4
                    else self._变更融资(arg_额, 值 == 5)
                )
                if 成:
                    self._开银行(self.恢复移动)
                return 成
            if 值 == 1 and arg_额 <= 人.现金:
                人.现金, 人.银行 = self._回绕(人.现金 - arg_额), self._回绕(人.银行 + arg_额)
            elif 值 == 2 and arg_额 <= 人.银行:
                人.银行, 人.现金 = self._回绕(人.银行 - arg_额), self._回绕(人.现金 + arg_额)
            else:
                return False
            self._发事件(游戏事件种类_类.银行转账, "存款完成" if 值 == 1 else "提款完成", arg_额)
            if 值 == 2:
                self._执行规则(
                    lambda: self._对账融资(True),
                    True,
                    False,
                    lambda: self._开银行(self.恢复移动) if self.阶段 != 游戏阶段_类.结束 else None,
                )
            return True
        self.待决策 = None
        if 类 == 决策种类_类.救援:
            if 值 >= 0:
                if self._玩家().点券 < (30 if 值 < 4 else 300):
                    self.待决策 = 决
                    return False
                self._救援(值, self.救援医院, True)
            self._结束回合()
        elif 类 == 决策种类_类.轮盘:
            型 = self.世界.设施[决.地产].类型
            倍 = self._轮盘值(型, self.轮盘游标 + 12)
            self._停止轮盘效果(决, 倍)
            self._设施收费(决.地产, 倍)
        elif 类 in (决策种类_类.购买设施, 决策种类_类.建造设施, 决策种类_类.升级设施):
            if 值 == 0 and 类 != 决策种类_类.建造设施:
                self._结束回合()
            else:
                操 = 0 if 类 == 决策种类_类.购买设施 else 1 if 类 == 决策种类_类.建造设施 else 2
                self._购买设施(决.地产, 操, 值)
        elif 类 in (决策种类_类.购地, 决策种类_类.升级地产):
            if 值 == 1:
                self._购买地产(决.地产, 类 == 决策种类_类.升级地产)
            else:
                self._结束回合()
        elif 类 == 决策种类_类.提示 and self.未支持恢复 == 游戏阶段_类.人类待命:
            self._置阶段(游戏阶段_类.人类待命)
        else:
            self._结束回合()
        return True

    def api_互动小游戏(self, arg_开: bool) -> None:
        self.互动小游戏 = arg_开

    def api_提交小游戏(self, arg_分: int, arg_随机次数: int) -> bool:
        if (
            self.阶段 != 游戏阶段_类.等待决策
            or self.待决策 is None
            or self.待决策.种类 != 决策种类_类.小游戏
            or arg_分 < 0
            or not 0 <= arg_随机次数 <= 10000000
        ):
            return False
        self.待决策 = None
        for _ in range(arg_随机次数):
            self.随机.api_下一个()
        self._玩家().点券 = (self._玩家().点券 + arg_分) & 65535
        self._发事件(游戏事件种类_类.得点券, f"小游戏获得{arg_分}点", arg_分)
        self._结束回合()
        return True

    def api_步进(self, arg_毫秒: int) -> None:
        if not 0 <= arg_毫秒 <= 0xFFFFFFFF:
            raise ValueError("elapsed milliseconds must fit unsigned32")
        if self.阶段 == 游戏阶段_类.等待决策 and self.待决策 is not None:
            if self.待决策.种类 == 决策种类_类.金额转盘:
                self.转盘毫秒 = (self.转盘毫秒 + arg_毫秒) & 0xFFFFFFFF
                while self.转盘毫秒 >= 30 and not self.金钱转盘.完成:
                    self.转盘毫秒 -= 30
                    self.金钱转盘.api_步进(self.转盘随机)
                self.待决策.金额 = self.金钱转盘.金额
                if self.待决策.转盘 is not None:
                    self.待决策.转盘.数位 = self.金钱转盘.数字[:]
                    self.待决策.转盘.阶段 = self.金钱转盘.阶段 & 255
                if self.金钱转盘.完成:
                    self.事件选择[self.待选择键] = self.金钱转盘.金额
                    self.选择随机状态[self.待选择键] = self.转盘随机.状态
                    self.金钱转盘 = self.待决策 = None
                    续, self.待续 = self.待续, None
                    续()
                return
            if self.待决策.种类 == 决策种类_类.轮盘:
                self.轮盘毫秒 = (self.轮盘毫秒 + arg_毫秒) & 0xFFFFFFFF
                self.轮盘游标 = (self.轮盘游标 + self.轮盘毫秒 // 36) % 12
                self.轮盘毫秒 %= 36
                self.待决策.金额 = self._轮盘值(self.轮盘种类, self.轮盘游标)
                if self.待决策.转盘 is not None:
                    self.待决策.转盘.游标 = self.轮盘游标 & 255
                return
        for _ in range(4096):
            if self.阶段 in (游戏阶段_类.人类待命, 游戏阶段_类.等待决策, 游戏阶段_类.结束):
                return
            if self.阶段 == 游戏阶段_类.推进回合:
                self._下一回合()
                continue
            时长 = 350 if self.阶段 == 游戏阶段_类.掷骰 else 160
            需 = (时长 - self.阶段毫秒) & 0xFFFFFFFF
            用 = min(arg_毫秒, 需)
            self.阶段毫秒, arg_毫秒 = (self.阶段毫秒 + 用) & 0xFFFFFFFF, arg_毫秒 - 用
            if self.动画 is not None:
                self.动画.已过毫秒 = self.阶段毫秒
            if self.阶段毫秒 < 时长:
                return
            if self.阶段 == 游戏阶段_类.掷骰:
                if self.剩余步 > 0:
                    self._开始一步()
                else:
                    self._落点()
            else:
                self._完成一步()
            if not arg_毫秒:
                return
        raise RuntimeError("native game exceeded one tick's transition limit")

    def api_服装(self, arg_槽: int) -> int:
        if not 0 <= arg_槽 < min(len(self.服装), len(self.世界.玩家)):
            return 0
        return self.服装[arg_槽] if self.服装键[arg_槽] == self._服装键(arg_槽) else 0

    def api_取事件(self) -> list[游戏事件_类]:
        self._刷新服装()
        输出, self.事件队列 = self.事件队列, []
        return 输出

    def api_取效果(self) -> list:
        输出, self.效果队列 = self.效果队列, []
        return 输出

    def api_托管设置(self, arg_槽: int) -> 托管设置_类 | None:
        if not 0 <= arg_槽 < len(self.世界.玩家) or not self.世界.玩家[arg_槽].记录.控制标志 & 1:
            return None
        if arg_槽 < len(self.待托管) and self.待托管[arg_槽] is not None:
            return deepcopy(self.待托管[arg_槽])
        人 = self.世界.玩家[arg_槽]
        return 托管设置_类(
            bool(人.记录.控制标志 & 4),
            人.状态.卡片策略,
            人.状态.救援策略,
            人.状态.初始现金比例,
            人.状态.股票投资比例,
        )

    def api_设置托管(self, arg_槽: int, arg_设: 托管设置_类) -> bool:
        if (
            not 0 <= arg_槽 < min(len(self.世界.玩家), len(self.待托管))
            or not self.世界.玩家[arg_槽].记录.控制标志 & 1
            or not 0 <= arg_设.卡片策略 <= 3
            or not 0 <= arg_设.性格 <= 2
            or not 0 <= arg_设.现金比例 <= 100
            or not 0 <= arg_设.股票比例 <= 100
        ):
            return False
        if self.阶段 not in (游戏阶段_类.人类待命, 游戏阶段_类.结束):
            self.待托管[arg_槽] = deepcopy(arg_设)
            return True
        self.待托管[arg_槽] = None
        self._应用托管(arg_槽, arg_设)
        if self.阶段 == 游戏阶段_类.人类待命 and arg_槽 == self._当前() and not self._人类():
            if self._玩家().控制标志 & 0x30:
                self._开始掷骰()
            else:
                self._开始电脑回合()
        return True

    def api_可保存(self) -> bool:
        return self.阶段 in (游戏阶段_类.人类待命, 游戏阶段_类.结束)

    def api_导出存档(self) -> 存档_类:
        if not self.api_可保存():
            raise RuntimeError("save requires a settled native game turn")
        return 存档_类.api_解码(self.世界.api_导出())
