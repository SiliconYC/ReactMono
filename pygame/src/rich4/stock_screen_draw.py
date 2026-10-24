# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/stocks.cpp::draw_prices/draw_holdings。
# ◑ 导入
from rich4.native_ui import 原生界面_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类
from rich4.stock_info import 股票图表_类
from rich4.stocks import 股市_类, 走势_类
from rich4.world import 世界_类


# ◕ 功能
class 股票绘制_类(股票图表_类):
    """
    原12行报价与四人持仓页；色块、平均成本与管理者着色保持原坐标。

    更新日志：
    2026.10.24 - 名称只从外部PE读取，涨跌差先按binary32舍入。
    """

    def _画报价(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_人: int,
        arg_选: int | None,
    ) -> None:
        框, 文, 白 = arg_宿.框, self._绘.api_文字, self._绘.白字
        holder = arg_世.玩家[arg_人]
        for s, x in (
            ("股票名稱", 76),
            ("成交價", 188),
            ("漲跌", 280),
            ("交易量", 368),
            ("持有股數", 468),
            ("平均成本", 572),
        ):
            文(框, s, x, 64, 2, 白)
        for i, quote in enumerate(arg_世.股票):
            y = 96 + 32 * i
            文(
                框,
                self._名(arg_世, i),
                76,
                y,
                2,
                屏幕字样_类(16, 0x00F0F0 if quote.标志4 else 0xF0F0F0),
            )
            current = self._价(arg_世, i)
            change = self._单(current - self._价(arg_世, i, 1))
            style, change_style = 白, 白
            trend = 股市_类.api_走势(arg_世, i)
            if trend in (走势_类.上涨, 走势_类.下跌):
                style = change_style = 屏幕字样_类(
                    16, 0xFF0000 if trend == 走势_类.上涨 else 0x00FF00
                )
            elif trend in (走势_类.涨停, 走势_类.跌停):
                up = trend == 走势_类.涨停
                原生界面_类.api_填充(
                    框.画布,
                    (144, y - 10, 233, y + 10),
                    self._绘.api_RGB(0xD00000 if up else 0x00D000),
                )
                style = 屏幕字样_类(16, 0xF0F0F0 if up else 0x101010, 0, 2)
                change_style = 屏幕字样_类(16, 0xFF0000 if up else 0x00FF00)
            文(框, self._格式(current, current), 225, y, 6, style)
            文(框, self._格式(change, current, True), 305, y, 6, change_style)
            if quote.停牌天数:
                文(框, "暫停交易", 368, y, 2, 白)
            else:
                文(框, str(quote.标志10), 401, y, 6, 白)
            holding = holder.持仓[i]
            if holding.数量 > 0:
                文(框, self._绘.api_货币(holding.数量), 504, y, 6, 白)
                文(框, f"{股市_类._浮点(holding.成本位):.2f}", 609, y, 6, 白)
        if arg_选 is not None:
            self._绘.api_边框(
                框.画布, (15, 80 + 32 * arg_选, 625, 112 + 32 * arg_选), self._绘.api_RGB(0xFFFFFF)
            )

    def _画持仓(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类) -> None:
        框, 文, 白 = arg_宿.框, self._绘.api_文字, self._绘.白字
        文(框, "股票名稱", 71, 64, 2, 白)
        for p, player in enumerate(arg_世.玩家[:4]):
            文(框, 框.人名[player.记录.角色], 168 + 80 * p, 64, 2, 白)
        文(框, "保留股份", 492, 64, 2, 白)
        文(框, "累積盈餘", 580, 64, 2, 白)
        for i, quote in enumerate(arg_世.股票):
            y, listed, company = 96 + 32 * i, bool(quote.标志4), self._公司(arg_世, i)
            文(框, self._名(arg_世, i), 71, y, 2, 白)
            for p, player in enumerate(arg_世.玩家[:4]):
                x, amount = 192 + 80 * p, player.持仓[i].数量
                manager = listed and company is not None and company.业主 == p + 1
                if manager:
                    原生界面_类.api_填充(
                        框.画布, (x - 56, y - 10, x + 8, y + 10), self._绘.api_RGB(0x0000FF)
                    )
                    文(框, self._绘.api_货币(amount), x, y, 6, 屏幕字样_类(16, 0xF0F000))
                elif amount:
                    文(框, self._绘.api_货币(amount), x, y, 6, 白)
            if listed and company is not None:
                文(框, self._绘.api_货币(company.剩余股份), 520, y, 6, 白)
                文(框, self._绘.api_货币(company.资金), 609, y, 6, 白)
