# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/stocks.cpp::StockMarket；买卖仍交给真实核心。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass

from rich4.calendar import 日期_类
from rich4.cards import 目标种类_类
from rich4.game_types import 决策_类
from rich4.holidays import 节日_类
from rich4.native_ui import 原生界面_类
from rich4.number_pad import 数字板_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类
from rich4.stock_screen_draw import 股票绘制_类
from rich4.stocks import 股市_类, 走势_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass(frozen=True)
class 股票动作_类:
    """
    原StockActions的强制真实买卖/关闭回调，不给假成功默认值。

    更新日志：
    2026.10.24 - 接收股票索引与数字板确认数额。
    """

    买: Callable[[int, int], bool]
    卖: Callable[[int, int], bool]
    关: Callable[[], None]


class 股票屏幕_类(股票绘制_类):
    """
    原Panel75股市、持仓与红黑卡股票目标，保留二次点击与返回层级。

    更新日志：
    2026.10.24 - 门控只限制原界面行为，合法交易由核心再次判断。
    """

    页键 = (16, 9, 125, 40)
    买键 = (128, 9, 199, 40)
    卖键 = (202, 9, 273, 40)
    讯键 = (276, 9, 411, 40)
    退键 = (552, 8, 624, 41)

    def __init__(self, arg_原文: 原版文字_类) -> None:
        super().__init__(arg_原文)
        self.api_重置()

    def api_重置(self) -> None:
        self.选中: int | None = None
        self.页, self.资讯 = 0, False
        self._弹文, self._弹止 = "", 0

    @staticmethod
    def api_休市(arg_世: 世界_类) -> bool:
        日, 月, 年 = arg_世.头.日期
        return bool(arg_世.新闻影响天数) or 节日_类.api_休市(
            日期_类(年, 月, 日), arg_世.头.地图, arg_世.头.阶段
        )

    def api_取消(self, arg_宿: 屏幕宿主_类, arg_关: Callable[[], None]) -> None:
        if arg_宿.声音:
            arg_宿.声音(4)
        if self.资讯:
            self.资讯 = False
        elif self.页 == 1:
            self.页 = 0
        else:
            arg_关()

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_人: int,
        arg_板: 数字板_类,
        arg_动: 股票动作_类,
    ) -> None:
        框, 文, hit = arg_宿.框, self._绘.api_文字, self._绘.api_命中
        原生界面_类.api_填充(框.画布, (0, 0, 640, 480), 0)
        if self.api_休市(arg_世):
            self._绘.api_背景(框, "p", 75, 0)
            文(框, "本日休市", 324, 244, 2, 屏幕字样_类(72, 0, 0, 2))
            文(框, "本日休市", 320, 240, 2, 屏幕字样_类(72, 0xF0F0F0, 0, 2))
            hit(arg_宿, 60, (0, 0, 640, 480), 2, arg_动.关)
            return
        self._绘.api_背景(框, "p", 75, self.页)
        holder, row = arg_世.玩家[arg_人], self.选中 is not None and self.页 == 0
        on, off = 屏幕字样_类(), 屏幕字样_类(16, 0xA0A0A0)
        文(框, "持有股數表" if self.页 == 0 else "股價表", 70, 24, 2, on)
        for s, x in (("買進", 163), ("賣出", 237), ("上市公司資訊", 343)):
            文(框, s, x, 24, 2, on if row else off)
        文(框, self._绘.api_货币(holder.记录.银行), 540, 24, 6, on)
        for r in (self.页键, self.买键, self.卖键, self.讯键, self.退键):
            if 框.按下 and 框.api_指针内(r) and not self.资讯 and not arg_板.api_活跃():
                self._绘.api_按下斜面(框.画布, r)
        if self.页 == 0:
            self._画报价(arg_宿, arg_世, arg_人, self.选中)
        else:
            self._画持仓(arg_宿, arg_世)
        if self.资讯 and self.选中 is not None:
            self._画资讯(arg_宿, arg_世, self.选中)

            def 关资讯() -> None:
                self.资讯 = False

            hit(arg_宿, 436, (0, 0, 640, 480), 4, 关资讯)
            return
        if self._弹文 and 框.时钟 < self._弹止:
            self._绘.api_弹框(arg_宿, self._弹文, 196)

        def 拒绝(arg_文: str) -> None:
            self._弹文, self._弹止 = arg_文, 框.时钟 + 1500

        def 换页() -> None:
            self.页 ^= 1

        def 退出() -> None:
            if self.页 == 1:
                self.页 = 0
            else:
                arg_动.关()

        hit(arg_宿, 434, (16, 0, 125, 47), 1, 换页)
        hit(arg_宿, 60, (552, 0, 640, 47), 2, 退出)
        if self.页 == 0:
            for i in range(len(arg_世.股票)):

                def 选行(arg_i: int = i) -> None:
                    if self.选中 == arg_i:
                        self.资讯 = True
                    self.选中 = arg_i

                hit(arg_宿, 400 + i, (16, 80 + 32 * i, 625, 112 + 32 * i), 1, 选行)
        if not row:
            return
        stock = self.选中
        quote, trend, current = (
            arg_世.股票[stock],
            股市_类.api_走势(arg_世, stock),
            self._价(arg_世, stock),
        )
        maximum = (
            min(quote.标志10, int(min(2147483647.0, holder.记录.银行 / current)))
            if current > 0
            else 0
        )
        holding, suspended = holder.持仓[stock].数量, bool(quote.停牌天数)

        def 买() -> None:
            if suspended or maximum <= 0:
                return
            if trend == 走势_类.涨停:
                拒绝("漲停無法買進！")
                return

            def 完成(arg_数: int) -> None:
                if arg_数 > 0 and not arg_动.买(stock, arg_数):
                    拒绝("無法買進！")

            arg_板.api_打开(maximum, 完成)

        def 卖() -> None:
            if suspended or holding <= 0:
                return
            if trend == 走势_类.跌停:
                拒绝("跌停無法賣出！")
                return

            def 完成(arg_数: int) -> None:
                if arg_数 > 0 and not arg_动.卖(stock, arg_数):
                    拒绝("無法賣出！")

            arg_板.api_打开(holding, 完成)

        def 资讯() -> None:
            self.资讯 = True

        hit(arg_宿, 430, (128, 0, 199, 47), 1, 买)
        hit(arg_宿, 431, (202, 0, 273, 47), 1, 卖)
        hit(arg_宿, 435, (276, 0, 411, 47), 1, 资讯)

    def api_卡片目标(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_人: int,
        arg_决: 决策_类 | None,
        arg_起: int,
        arg_答: Callable[[int], None],
    ) -> None:
        框, 文, hit = arg_宿.框, self._绘.api_文字, self._绘.api_命中
        原生界面_类.api_填充(框.画布, (0, 0, 640, 480), 0)
        self._绘.api_背景(框, "p", 75, 0)
        self.页 = 0
        off = 屏幕字样_类(16, 0xA0A0A0)
        for s, x in (("持有股數表", 70), ("買進", 163), ("賣出", 237), ("上市公司資訊", 343)):
            文(框, s, x, 24, 2, off)
        文(框, self._绘.api_货币(arg_世.玩家[arg_人].记录.银行), 540, 24, 6, self._绘.白字)
        self._画报价(arg_宿, arg_世, arg_人, self.选中)
        if arg_决 is None:
            return
        for index, option in enumerate(arg_决.选项):
            if option.值 < 0:
                if 框.按下 and 框.api_指针内(self.退键):
                    self._绘.api_按下斜面(框.画布, self.退键)

                def 取消(arg_i: int = index) -> None:
                    self.选中 = None
                    arg_答(arg_i)

                hit(arg_宿, arg_起 + index, (552, 0, 640, 47), 2, 取消)
                continue
            target = option.对象
            if target is None or target.种类 != 目标种类_类.股票 or target.数值 >= len(arg_世.股票):
                continue
            stock = target.数值

            def 选择(arg_股: int = stock, arg_i: int = index) -> None:
                if self.选中 == arg_股:
                    arg_答(arg_i)
                else:
                    self.选中 = arg_股

            hit(arg_宿, arg_起 + index, (16, 80 + 32 * stock, 625, 112 + 32 * stock), 1, 选择)
