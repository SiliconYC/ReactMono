# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定market.cpp::TradingBoard；界面通过真实规则回调挂牌/购买/撤件。
# ◑ 导入
from copy import deepcopy

from rich4.number_pad import 数字板_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.stocks import 股市_类
from rich4.trading import 交易_类, 可售项目_类, 报价_类, 挂单_类
from rich4.trading_screen_text import 交易图文_类
from rich4.trading_screen_types import 交易动作_类, 交易视图_类
from rich4.world import 世界_类


# ◕ 功能
class 交易公告栏_类(交易图文_类):
    """
    原Panel73公告栏、报价详情、分类挑选与数量/价格两级数字板。

    更新日志：
    2026.10.24 - 保留原按钮编号、世界只读、报价值快照及通知时钟。
    """

    字A = 屏幕字样_类()
    字B = 屏幕字样_类(16, 0xFFFFFF, 0x800000, 3)
    字C = 屏幕字样_类(20, 0x101010, 0, 2)
    字D = 屏幕字样_类(20, 0xFFFFFF, 0, 2)
    小黑 = 屏幕字样_类(12, 0x101010, 0, 0)

    def __init__(self, arg_原文: 原版文字_类) -> None:
        super().__init__(arg_原文)
        self.api_重置()

    def api_重置(self) -> None:
        self._视图 = 交易视图_类.公告栏
        self._货类 = self._分类 = self._滚动 = 0
        self._详情: 报价_类 | None = None
        self._提示 = self._通知 = ""
        self._通知止 = self._现在 = 0
        self._建议 = 1

    def api_视图(self) -> 交易视图_类:
        return self._视图

    def api_建议(self) -> int:
        return self._建议

    def _通知提示(self, arg_文: str) -> None:
        self._通知, self._通知止 = arg_文, (self._现在 + 1500) & 0xFFFFFFFFFFFFFFFF

    def api_取消(self, arg_宿: 屏幕宿主_类, arg_动: 交易动作_类) -> None:
        if arg_宿.声音:
            arg_宿.声音(4)
        if self._视图 == 交易视图_类.公告栏:
            arg_动.关闭()
        else:
            self._视图 = 交易视图_类.公告栏

    def _问价格(
        self,
        arg_世: 世界_类,
        arg_人: int,
        arg_板: 数字板_类,
        arg_动: 交易动作_类,
        arg_物: 可售项目_类,
        arg_数: int,
    ) -> None:
        limits = 交易_类.api_限价(arg_世, arg_人, arg_物.种类, arg_物.编号, arg_数)
        if limits is None or limits.最高价 <= 0:
            self._通知提示("無法出售！")
            self._视图 = 交易视图_类.公告栏
            return
        self._提示 = f"請輸入欲拍賣的價格\n\n（市價：{limits.参考价}元）"
        self._建议 = max(1, limits.参考价)

        def 完成(arg_价: int) -> None:
            self._提示 = ""
            if arg_价 <= 0:
                return
            if arg_动.挂牌(挂单_类(arg_物.种类, arg_物.编号, arg_价, arg_数)):
                self._视图 = 交易视图_类.公告栏
            else:
                self._通知提示("無法刊登！")

        arg_板.api_打开(limits.最高价, 完成)

    def _选择物品(
        self,
        arg_世: 世界_类,
        arg_人: int,
        arg_板: 数字板_类,
        arg_动: 交易动作_类,
        arg_物: 可售项目_类,
    ) -> None:
        if arg_物.种类 == 1:
            self._提示, self._建议 = "請輸入欲賣出的張數", 1

            def 数量(arg_数: int) -> None:
                self._提示 = ""
                if arg_数 > 0:
                    self._问价格(arg_世, arg_人, arg_板, arg_动, arg_物, arg_数 & 65535)

            arg_板.api_打开(arg_物.最大数量, 数量)
        else:
            self._问价格(arg_世, arg_人, arg_板, arg_动, arg_物, 1)

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_人: int,
        arg_板: 数字板_类,
        arg_动: 交易动作_类,
    ) -> None:
        self._现在 = arg_宿.框.时钟
        self._画公告栏(arg_宿, arg_世, arg_人, arg_动)
        if self._视图 == 交易视图_类.详情 and self._详情 is not None:
            self._画详情(arg_宿, arg_世, arg_人, arg_动)
        elif self._视图 != 交易视图_类.公告栏:
            self._画挑选(arg_宿, arg_世, arg_人, arg_板, arg_动)
        if arg_板.api_活跃() and self._提示:
            arg_宿.框.api_资源图("p", 73, 5, 227, arg_板.api_提示顶())
            屏幕绘图_类.api_文字(
                arg_宿.框, self._提示, 319, arg_板.api_提示顶() + 44, 4, 屏幕绘图_类.黑字
            )
        if self._通知 and self._现在 < self._通知止:
            屏幕绘图_类.api_弹框(arg_宿, self._通知, 196)

    def _画公告栏(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_人: int,
        arg_动: 交易动作_类,
    ) -> None:
        框, 绘, 文 = arg_宿.框, 屏幕绘图_类, 屏幕绘图_类.api_文字
        active = self._视图 == 交易视图_类.公告栏
        框.api_资源图("p", 73, 0, 22, 66)
        for p, player in enumerate(arg_世.玩家[:4]):
            if player.记录.控制标志:
                框.画布.api_绘制(框.美术.api_帧("m", 27 + player.记录.角色, 0), 66, 150 + 72 * p)
        quotes, columns, own = 交易_类.api_报价(arg_世), [0] * 4, 0
        for i, quote in enumerate(quotes):
            if quote.卖家 >= 4:
                continue
            own += quote.卖家 == arg_人
            column = columns[quote.卖家]
            columns[quote.卖家] += 1
            x, y = 104 + 72 * column, 114 + 72 * quote.卖家
            sex = int(bool(arg_世.玩家[quote.卖家].记录.性别))
            框.api_资源图("p", 73, 8 + quote.出售项.种类 + 4 * sex, x, y)
            文(框, 绘.api_货币(quote.出售项.价格), x + 36, y + 63, 2, self.小黑)
            cell = x, y, x + 72, y + 72
            if active and 框.按下 and 框.api_指针内(cell):
                绘.api_暗化(框.画布, cell, -12)
            if active:

                def 详情(arg_q: 报价_类 = deepcopy(quote)) -> None:
                    self._详情, self._视图 = arg_q, 交易视图_类.详情

                绘.api_命中(arg_宿, 600 + i, cell, 1, 详情)
        sale, exit = (465, 75, 536, 114), (537, 75, 608, 114)
        for rect in (sale, exit):
            if active and 框.按下 and 框.api_指针内(rect):
                绘.api_按下斜面(框.画布, rect)
        if not active:
            return

        def 出售() -> None:
            if own >= 7:
                self._通知提示("公佈欄已滿\n\n請先撤件！")
            else:
                self._视图 = 交易视图_类.菜单

        绘.api_命中(arg_宿, 480, sale, 1, 出售)
        绘.api_命中(arg_宿, 481, exit, 2, arg_动.关闭)

    def _画详情(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_人: int,
        arg_动: 交易动作_类,
    ) -> None:
        框, 绘, 文, quote = arg_宿.框, 屏幕绘图_类, 屏幕绘图_类.api_文字, self._详情
        offer = quote.出售项
        art = 7 if offer.种类 == 1 else 8 if offer.种类 == 2 else 6
        height = 224 if art == 6 else 256 if art == 7 else 288
        left, top = 224, 240 - height // 2
        框.api_资源图("p", 73, art, left, top)
        文(框, 框.人名[arg_世.玩家[quote.卖家].记录.角色], left + 57, top + 37, 2, self.字A)
        reference = 交易_类.api_限价(
            arg_世, quote.卖家, offer.种类, offer.项目, offer.数量 if offer.种类 == 1 else 0
        )
        if offer.种类 == 1:
            rows = [
                ("股票", self._物名(arg_世, offer.种类, offer.项目)),
                ("張數", 绘.api_货币(offer.数量)),
                ("市價", 绘.api_货币(reference.参考价) if reference else "-"),
                ("售價", 绘.api_货币(offer.价格)),
            ]
        elif offer.种类 == 2:
            row = self._地产行(arg_世, offer.项目)
            rows = [
                ("地點", row.地点),
                ("開發", row.开发),
                ("收費", 绘.api_货币(row.收费)),
                ("市價", 绘.api_货币(reference.参考价 if reference else row.价格)),
                ("售價", 绘.api_货币(offer.价格)),
            ]
        else:
            rows = [
                ("道具" if offer.种类 == 3 else "卡片", self._物名(arg_世, offer.种类, offer.项目)),
                ("市價", 绘.api_货币(reference.参考价) if reference else "-"),
                ("售價", 绘.api_货币(offer.价格)),
            ]
        for k, (label, val) in enumerate(rows):
            y = top + 91 + 30 * k
            文(框, label, left + 29, y, 2, 屏幕字样_类(14, 0xFFFFFF))
            文(框, val, left + 178, y, 6, self.字A)
        own = quote.卖家 == arg_人
        act, close = (
            (238, top + height - 34, 309, top + height - 11),
            (326, top + height - 34, 397, top + height - 11),
        )
        for r in (act, close):
            if 框.按下 and 框.api_指针内(r):
                绘.api_按下斜面(框.画布, r)
        文(
            框,
            "撤 件" if own else "購 買",
            (act[0] + act[2]) // 2,
            (act[1] + act[3]) // 2,
            2,
            self.字B,
        )
        文(框, "離 開", (close[0] + close[2]) // 2, (close[1] + close[3]) // 2, 2, self.字B)
        cash = arg_世.玩家[arg_人].记录.现金

        def 执行() -> None:
            if own:
                if arg_动.撤件(quote.索引):
                    self._视图 = 交易视图_类.公告栏
                return
            if arg_动.购买(quote.卖家, quote.索引):
                self._视图 = 交易视图_类.公告栏
            else:
                self._通知提示("您的現金不足！" if cash < offer.价格 else "無法購買！")

        def 关闭() -> None:
            self._视图 = 交易视图_类.公告栏

        def 手指(arg_r: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
            return arg_r[0] - 6, arg_r[1] - 9, arg_r[2] + 6, arg_r[3] + 9

        绘.api_命中(arg_宿, 456, 手指(act), 1, 执行)
        绘.api_命中(arg_宿, 457, 手指(close), 2, 关闭)
        绘.api_命中(arg_宿, 359, (left, top, left + 192, top + height), -1, lambda: None)
        绘.api_命中(arg_宿, 459, (0, 0, 640, 480), 4, 关闭)

    def _画挑选(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_人: int,
        arg_板: 数字板_类,
        arg_动: 交易动作_类,
    ) -> None:
        框, 绘, 文 = arg_宿.框, 屏幕绘图_类, 屏幕绘图_类.api_文字
        items = 交易_类.api_可售项目(arg_世, arg_人)
        if self._视图 == 交易视图_类.菜单:
            框.api_资源图("p", 73, 17, 464, 116)
            for k in range(4):
                cell = (
                    473 + 63 * (k // 2),
                    125 + 39 * (k % 2),
                    536 + 63 * (k // 2),
                    164 + 39 * (k % 2),
                )
                if 框.api_指针内(cell):
                    绘.api_暗化(框.画布, cell, -12)
                any_item = any(item.种类 == k + 1 for item in items)

                def 分类(arg_k: int = k, arg_有: bool = any_item) -> None:
                    if not arg_有:
                        self._通知提示("沒有可出售的物品！")
                        self._视图 = 交易视图_类.公告栏
                        return
                    self._货类, self._滚动 = arg_k, 0
                    self._视图 = (
                        交易视图_类.股票
                        if arg_k == 0
                        else 交易视图_类.地产
                        if arg_k == 1
                        else 交易视图_类.物品
                    )

                绘.api_命中(arg_宿, 484 + k, cell, 1, 分类)

            def 回公告() -> None:
                self._视图 = 交易视图_类.公告栏

            绘.api_命中(arg_宿, 459, (0, 0, 640, 480), 4, 回公告)
            return
        if arg_板.api_活跃():
            return

        def 选(arg_item: 可售项目_类) -> None:
            self._选择物品(arg_世, arg_人, arg_板, arg_动, arg_item)

        def 回公告() -> None:
            self._视图 = 交易视图_类.公告栏

        if self._视图 == 交易视图_类.股票:
            window = (152, 32, 488, 448)
            框.api_资源图("p", 73, 1, 152, 32)
            for s, x in (("股票名稱", 200), ("持有張數", 300), ("總 市 價", 420)):
                文(框, s, x, 48, 2, self.字D)
            row = 0
            for i, item in enumerate(items):
                if item.种类 != 1 or row >= 12:
                    continue
                y = 80 + 32 * row
                row += 1
                value = int(item.最大数量 * float(股市_类._浮点(arg_世.股票[item.编号].浮点位[2])))
                文(框, self._物名(arg_世, 1, item.编号), 200, y, 2, self.字A)
                文(框, 绘.api_货币(item.最大数量), 332, y, 6, self.字A)
                文(框, 绘.api_货币(value), 478, y, 6, self.字A)
                line = (152, y - 16, 488, y + 16)
                if 框.api_指针内(line):
                    绘.api_边框(框.画布, line, 绘.api_RGB(0xFFFFFF))
                绘.api_命中(arg_宿, 460 + i, line, 1, lambda item=deepcopy(item): 选(item))
            绘.api_命中(arg_宿, 458, (448, 26, 500, 64), 2, 回公告)
        elif self._视图 == 交易视图_类.地产:
            window = (112, 32, 528, 448)
            框.api_资源图("p", 73, 2, 112, 32)
            for i, s in enumerate(("全  部", "住宅區", "商業區", "房  屋", "連鎖店")):
                if i == self._分类:
                    框.api_资源图("p", 73, 19, 112 + 80 * i, 32)
                文(框, s, 152 + 80 * i, 47, 2, self.字C)

                def 标签(arg_i: int = i) -> None:
                    self._分类, self._滚动 = arg_i, 0

                绘.api_命中(arg_宿, 490 + i, (112 + 80 * i, 33, 192 + 80 * i, 62), 1, 标签)
            for s, x in (
                ("地  點", 147),
                ("開發狀況", 231),
                ("價  格", 293),
                ("收  費", 369),
                ("租  期", 471),
            ):
                文(框, s, x, 80, 2, self.字D)
            visible = [
                i
                for i, item in enumerate(items)
                if item.种类 == 2 and self._分类内(self._地产行(arg_世, item.编号), self._分类)
            ]
            if self._滚动 >= len(visible):
                self._滚动 = 0
            for r, index in enumerate(visible[self._滚动 : self._滚动 + 11]):
                item = items[index]
                row, y = self._地产行(arg_世, item.编号), 112 + 32 * r
                文(框, row.地点, 147, y, 2, self.字A)
                文(框, row.开发, 231, y, 2, self.字A)
                文(框, 绘.api_货币(row.价格), 319, y, 6, self.字A)
                文(框, 绘.api_货币(row.收费), 395, y, 6, self.字A)
                文(框, self._租期(row.到期), 471, y, 2, self.字A)
                line = (112, y - 16, 512, y + 16)
                if 框.api_指针内(line):
                    绘.api_边框(框.画布, line, 绘.api_RGB(0xFFFFFF))
                绘.api_命中(arg_宿, 460 + index, line, 1, lambda item=deepcopy(item): 选(item))

            def 上页() -> None:
                self._滚动 = self._滚动 - 11 if self._滚动 >= 11 else 0

            def 下页() -> None:
                if self._滚动 + 11 < len(visible):
                    self._滚动 += 11

            绘.api_命中(arg_宿, 458, (512, 26, 548, 62), 2, 回公告)
            绘.api_命中(arg_宿, 495, (512, 62, 548, 98), 1, 上页)
            绘.api_命中(arg_宿, 496, (512, 98, 548, 134), 1, 下页)
        else:
            cards = self._货类 == 3
            window = (140, 160, 500, 288)
            框.api_资源图("p", 73, 4 if cards else 3, 140, 160)
            cell = 0
            for i, item in enumerate(items):
                if cell >= 15:
                    break
                if item.种类 != (4 if cards else 3):
                    continue
                x, y = 140 + 72 * (cell % 5), 192 + 32 * (cell // 5)
                cell += 1
                if cards:
                    文(
                        框,
                        self._物名(arg_世, 4, item.编号),
                        x + 36,
                        y + 16,
                        2,
                        屏幕字样_类(14, 0xFFFFFF),
                    )
                else:
                    if 1 <= item.编号 <= 13:
                        框.画布.api_绘制(框.美术.api_帧("p", 74, item.编号 - 1), x + 20, y + 16)
                    文(框, f"×{item.最大数量}", x + 66, y + 16, 6, self.字A)
                box = (x, y, x + 72, y + 32)
                if 框.api_指针内(box):
                    绘.api_暗化(框.画布, box, -12)
                绘.api_命中(arg_宿, 460 + i, box, 1, lambda item=deepcopy(item): 选(item))
            绘.api_命中(arg_宿, 458, (429, 161, 500, 192), 2, 回公告)
        绘.api_命中(arg_宿, 359, window, -1, lambda: None)
        绘.api_命中(arg_宿, 459, (0, 0, 640, 480), 4, 回公告)
