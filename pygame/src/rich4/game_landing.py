# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ game.cpp 的事件/商店/魔法/落点与逐日、逐回合推进。
# ◑ 导入
from copy import deepcopy
from typing import Callable

from rich4.events import 事件_类, 事件结果_类
from rich4.game_types import (
    公告种类_类,
    决策_类,
    决策种类_类,
    决策选项_类,
    小游戏状态_类,
    待选择异常_类,
    托管设置_类,
    效果种类_类,
    未支持规则异常_类,
    游戏事件_类,
    游戏事件种类_类,
    游戏阶段_类,
)
from rich4.holidays import 节日_类
from rich4.lottery import 彩票_类
from rich4.services import 服务_类, 魔法回调_类
from rich4.special_actors import 特殊回调_类, 特殊行动_类
from rich4.stocks import 股市_类


# ◕ 功能
class 会话落点_类:
    """
    原节点分发、真实服务/事件嵌套与日期边界，不创建替代事件或固定规则结果。

    更新日志：
    2026.10.24 - 保留屏幕先于处理器、月结次序及原关闭小游戏模式。
    """

    def _公告事件(self, arg_新闻: bool, arg_槽: int, arg_果: 事件结果_类, arg_位: int) -> None:
        事 = 游戏事件_类(
            游戏事件种类_类.提示, arg_槽, 节点=事件_类._取(self.世界.玩家, arg_槽).记录.节点
        )
        事.公告 = 公告种类_类.新闻 if arg_新闻 else 公告种类_类.命运
        事.公告号, 事.地产, 事.主体, 事.公司, 事.值 = (
            arg_果.事件,
            arg_果.地产,
            arg_果.主体,
            arg_果.公司,
            arg_果.数值,
        )
        事.玩家掩码, 事.玩家金额 = arg_果.玩家掩码, deepcopy(arg_果.玩家金额)
        self.事件队列.insert(min(arg_位, len(self.事件队列)), 事)

    def _先屏幕(self, arg_处理: Callable[[], 事件结果_类]) -> 事件结果_类:
        事, 效 = len(self.事件队列), len(self.效果队列)
        try:
            return arg_处理()
        except 待选择异常_类:
            del self.事件队列[事:]
            del self.效果队列[效:]
            raise

    def _处理事件(self, arg_新闻: bool) -> None:
        def 动作() -> None:
            位, 效 = len(self.事件队列), len(self.效果队列)
            果 = self._先屏幕(
                lambda: 事件_类.api_新闻(self.世界, self.随机, self._事件回调())
                if arg_新闻
                else 事件_类.api_命运(self.世界, self.随机, self._当前(), self._事件回调())
            )
            if not 果.支持:
                raise 未支持规则异常_类(果.消息)
            self._公告事件(arg_新闻, self._当前(), 果, 位)
            for 项 in self.效果队列[效:]:
                if 项.事件位 >= 位:
                    项.事件位 += 1
            self._发事件(游戏事件种类_类.提示, 果.消息)

        self._执行规则(动作)

    def _商店提示(self) -> None:
        决 = 决策_类(决策种类_类.商店, self._当前(), 提示="商店：選擇購買或出售的物品")
        for 卡 in self.商店.卡片:
            决.选项.append(
                决策选项_类(
                    f"買 {事件_类._取(服务_类.卡名, 卡 - 1)} {事件_类._取(服务_类.卡价, 卡 - 1)}點",
                    100 + 卡,
                )
            )
        for 物 in self.商店.道具:
            决.选项.append(
                决策选项_类(
                    f"買 {事件_类._取(服务_类.道具名, 物 - 1)} "
                    f"{事件_类._取(服务_类.道具价, 物 - 1)}點",
                    200 + 物,
                )
            )
        for 卡 in self._玩家().卡片:
            if 卡 and not any(项.值 == 300 + 卡 for 项 in 决.选项):
                决.选项.append(决策选项_类("賣 " + 事件_类._取(服务_类.卡名, 卡 - 1), 300 + 卡))
        for i, 名 in enumerate(服务_类.道具名):
            if self._玩家().道具[i]:
                决.选项.append(决策选项_类("賣 " + 名, 401 + i))
        决.选项.append(决策选项_类("離開", 0))
        self.待决策 = 决
        self._置阶段(游戏阶段_类.等待决策)

    def _开商店(self, arg_码: int) -> None:
        self.商店地产 = arg_码
        self.商店 = 服务_类.api_开店(self.世界, self.随机, self._当前(), arg_码)
        if self._人类():
            self._商店提示()
        else:
            服务_类.api_关店(self.世界, self.商店, arg_码)
            self.商店 = None
            self._结束回合()

    def _商店行动(self, arg_行: int, arg_数: int) -> bool:
        if self.商店 is None:
            return False
        if arg_行 == 0:
            服务_类.api_关店(self.世界, self.商店, self.商店地产)
            self.商店 = None
            self._结束回合()
            return True
        成 = False
        if 100 < arg_行 <= 130:
            成 = 服务_类.api_买卡(self.世界, self.商店, self._当前(), arg_行 - 100)
        elif 200 < arg_行 <= 213:
            成 = 服务_类.api_买道具(self.世界, self.商店, self._当前(), arg_行 - 200)
        elif 300 < arg_行 <= 330:
            成 = 服务_类.api_卖卡(self.世界, self.商店, self._当前(), arg_行 - 300)
        elif 400 < arg_行 <= 413:
            成 = 服务_类.api_卖道具(self.世界, self.商店, self._当前(), arg_行 - 400, arg_数)
        if 成:
            self._发事件(游戏事件种类_类.提示, "购买完成" if arg_行 < 300 else "出售完成")
            self._商店提示()
        return 成

    def _魔法回调(self) -> 魔法回调_类:
        def 命运(arg_槽: int) -> None:
            位 = len(self.事件队列)
            果 = self._先屏幕(
                lambda: 事件_类.api_命运(self.世界, self.随机, arg_槽, self._事件回调())
            )
            if not 果.支持:
                raise 未支持规则异常_类(果.消息)
            self._公告事件(False, arg_槽, 果, 位)
            self._发事件(游戏事件种类_类.提示, 果.消息)

        return 魔法回调_类(
            命运=命运,
            防御=self._尝试防御卡,
            敌意=self._更新敌意,
            监狱=lambda 槽, 天: self._收容(槽, 天, False),
            医院=lambda 槽, 天: self._收容(槽, 天, True),
            升级=lambda 码: self._改建筑(码, True),
            降级=lambda 码: self._改建筑(码, False),
            转向=self._掉头,
            拍卖=self._拍卖,
        )

    def _施魔法(self, arg_效: int) -> None:
        类 = self.魔法类别

        def 动作() -> None:
            if not self._人类():
                self._发事件(游戏事件种类_类.提示, "魔法屋施法")
                self.事件队列[-1].值, self.事件队列[-1].次主体 = arg_效, 类
            对 = 服务_类.api_魔法目标(self.世界, 类)
            if not 服务_类.api_施法(
                self.世界, self.随机, self._当前(), 对, arg_效, self._魔法回调()
            ):
                raise 未支持规则异常_类("这项魔法的效果尚未完成")
            self._发事件(游戏事件种类_类.提示, 事件_类._取(服务_类.魔法效果, arg_效))

        self._执行规则(动作)

    def _魔法效果提示(self, arg_类: int) -> None:
        self.魔法类别 = arg_类
        选 = [决策选项_类(名, i) for i, 名 in enumerate(服务_类.魔法效果)]
        选.append(决策选项_类("重新選擇角色", -1))
        self.待决策 = 决策_类(决策种类_类.魔法效果, self._当前(), 提示="選擇魔法效果", 选项=选)
        self._置阶段(游戏阶段_类.等待决策)

    def _开魔法(self) -> None:
        if not self._人类():
            选 = 服务_类.api_电脑魔法(self.世界, self.随机, self._当前())
            if 选 is None:
                self._结束回合()
                return
            self.魔法类别 = 选.类别
            self._施魔法(选.效果)
            return
        选 = [
            决策选项_类(名, i)
            for i, 名 in enumerate(服务_类.魔法分类)
            if 服务_类.api_魔法目标(self.世界, i)
        ]
        if not 选:
            self._结束回合()
            return
        self.待决策 = 决策_类(
            决策种类_类.魔法类别, self._当前(), 提示="選擇魔法作用的角色", 选项=选
        )
        self._置阶段(游戏阶段_类.等待决策)

    def _落点(self) -> None:
        节 = 事件_类._取(self.世界.节点, self._玩家().节点)
        类, 码 = 节.标志 & 255, 节.类型索引
        if 类 != 0 and self._状态().梦游天数:
            self._结束回合()
            return
        if 类 == 0:
            self.地产待处理, self.已购地产, self.地产落点 = True, False, 码 != 0
            if 2000 < 码 < 4000:
                self._普通地产(码 - 2000)
            elif 4000 < 码 < 6000:
                self._特殊设施(码 - 4000)
            elif 6000 < 码 < 8000:
                self._商业公司(码 - 6000)
            else:
                self._结束回合()
        elif 类 == 1:
            self._结束回合()
        elif 类 in (2, 3):
            self._处理事件(类 == 2)
        elif 类 in (4, 5):
            self._探望收容(类 == 5)
        elif 类 == 9:
            self._开彩票()
        elif 类 == 13:
            self._效果(效果种类_类.问号箱, self._当前(), self._角色点(self._当前()))
            self._收随机卡()
        elif 类 == 15:
            self._开商店(码)
        elif 类 == 16:
            self._开魔法()
        elif 6 <= 类 <= 8 and self.互动小游戏 and self._人类():
            self.待决策 = 决策_类(
                决策种类_类.小游戏,
                self._当前(),
                提示="小遊戲",
                小游戏=小游戏状态_类(类 - 6, self._玩家().角色, self.随机.状态),
            )
            self._置阶段(游戏阶段_类.等待决策)
        elif 6 <= 类 <= 8:
            赏 = self.随机.api_下一个() % 20 + 50
            声 = self.随机.api_下一个() & 1
            self._玩家().点券 = (self._玩家().点券 + 赏) & 65535
            self._公告(公告种类_类.小游戏点券, self._当前()).金额 = 赏
            self._发事件(游戏事件种类_类.得点券, f"小游戏获得{赏}点", 赏)
            self._语音(self._当前(), 声)
            self._结束回合()
        elif 10 <= 类 <= 12:
            赏 = 50 if 类 == 10 else 30 if 类 == 11 else 10
            self._玩家().点券 = (self._玩家().点券 + 赏) & 65535
            self._效果(效果种类_类.点券, self._当前(), self._角色点(self._当前()))
            self._公告(公告种类_类.点券, self._当前()).金额 = 赏
            if 类 == 10:
                self._语音(self._当前(), self.随机.api_下一个() & 1)
            elif 类 == 11:
                self._语音(self._当前(), 2)
            self._发事件(游戏事件种类_类.得点券, f"获得{赏}点", 赏)
            self._结束回合()
        elif 类 == 14:
            self._开银行(False)
        else:
            self._结束回合()

    def _应用托管(self, arg_槽: int, arg_设: 托管设置_类) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        if not 人.记录.控制标志 & 1:
            return
        人.记录.控制标志 = ((人.记录.控制标志 & ~4) | (4 if arg_设.自动 else 0)) & 255
        人.状态.卡片策略, 人.状态.救援策略 = arg_设.卡片策略, arg_设.性格
        人.状态.初始现金比例, 人.状态.股票投资比例 = arg_设.现金比例, arg_设.股票比例

    def _下一回合(self) -> None:
        for i, 设 in enumerate(self.待托管):
            if 设 is not None:
                self._应用托管(i, 设)
                self.待托管[i] = None
        后, 绕 = self._当前(), False
        for _ in range(len(self.世界.玩家)):
            后 += 1
            if 后 == len(self.世界.玩家):
                后, 绕 = 0, True
            if self.世界.玩家[后].记录.控制标志:
                break
        if not self.世界.玩家[后].记录.控制标志:
            self._发事件(游戏事件种类_类.游戏结束, "游戏结束")
            self._置阶段(游戏阶段_类.结束)
            return
        if not 绕:
            self.世界.头.当前玩家 = 后
            self._开始回合()
            return

        def 动作() -> None:
            钩 = 特殊回调_类(
                付款=self._付款,
                移除物件=self._移除物件,
                监狱=lambda 槽, 天: self._收容(槽, 天, False),
                医院=lambda 槽, 天: self._收容(槽, 天, True),
                语音=self._语音,
                游戏结束=lambda: self.阶段 == 游戏阶段_类.结束,
            )
            for 槽 in range(4, 8):
                if self.阶段 == 游戏阶段_类.结束:
                    break
                果 = 特殊行动_类.api_回合(self.世界, self.随机, 槽, 钩)
                if not 果.支持:
                    raise 未支持规则异常_类(果.消息)
                for 效 in 果.效果:
                    self.事件队列.append(
                        游戏事件_类(游戏事件种类_类.提示, 槽, 效.金额, 效.节点, "特殊角色完成行动")
                    )

        def 成功() -> None:
            if self.阶段 != 游戏阶段_类.结束:
                self.世界.头.当前玩家 = 后
                self._推进日期()
                self._开始回合()

        self._执行规则(动作, True, False, 成功)

    def _推进日期(self) -> None:
        日, 换月 = self._日期().api_下一天()
        self.世界.头.日期 = (日.日, 日.月, 日.年)
        self.完成天数, self.世界.轮数 = (
            (self.完成天数 + 1) & 0xFFFFFFFFFFFFFFFF,
            (self.世界.轮数 + 1) & 0xFFFFFFFF,
        )
        self._更新物价()
        if self.世界.新闻影响天数 & 128:
            self.世界.新闻影响天数 = 0
        elif self.世界.新闻影响天数:
            self.世界.新闻影响天数 = self._回绕(self.世界.新闻影响天数 - 1)
            if self.世界.新闻影响天数 == 0:
                self.世界.新闻影响天数 = 128
        for 股 in self.世界.股票:
            if 股.停牌天数:
                股.停牌天数 -= 1
            if 股.新闻走势 & 0xF0:
                股.新闻走势 = (股.新闻走势 - 0x10) & 255
            if 股.新闻走势 & 15:
                股.新闻走势 -= 1
        股市_类.api_日更新(
            self.世界, self.随机, 节日_类.api_休市(日, self.世界.头.地图, self.世界.头.阶段)
        )
        if 日.日 == 15:
            self._派发股利()
        庆 = 节日_类.api_庆祝(日, self.世界.头.地图, self.世界.头.阶段)
        if 庆 is not None and 庆.影片:
            self._效果(
                效果种类_类.圣诞 if 庆.影片 == 554 else 效果种类_类.节日烟花,
                self._当前(),
                self._角色点(self._当前()),
            )
        if 彩票_类.api_开奖日(self.世界.头.日期):
            报 = self._月报快照()
            报.票, 报.奖池 = self.世界.彩票[:], self.世界.公共基金
            开 = 彩票_类.api_开奖(self.世界, self.随机)
            if 开.已开奖:
                self._发事件(游戏事件种类_类.提示, f"彩票开奖：{开.号码}", 开.奖金)
                报.号码, 报.赢家 = 开.号码, 开.赢家 if 开.赢家 is not None else -1
                self._月报效果(效果种类_类.彩票开奖, 报)
        if 换月:
            self.世界.月数 = (self.世界.月数 + 1) & 0xFFFFFFFF
            self._结月()
            for 号 in (13, 14):
                旧 = self.世界.物件[号 - 1].节点
                self._移除物件(号)
                self._放现有物件(号 - 1, self._随机空节点(旧))
        self._地产到期()
        self._发事件(游戏事件种类_类.日期改变, f"{日.年}年{日.月}月{日.日}日")
