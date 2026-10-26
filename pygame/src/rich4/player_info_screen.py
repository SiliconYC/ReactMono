# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/menus.cpp::PlayerInfo，查询不重算或写回游戏规则。
# ◑ 导入
from collections.abc import Callable

from rich4.economy import 经济_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.original_text import 原版文字_类
from rich4.player_info_types import 查询地产行_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类


# ◕ 功能
class 玩家查询_类:
    """
    原Panel9人物、神明、资产/库存、五分类地产与股票列表。

    更新日志：
    2026.10.24 - 保留源计数/估价/租金与翻页边界，不修改世界。
    """

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self._原文 = arg_原文
        self._人 = self._页 = self._分类 = self._滚动 = 0

    def api_打开(self, arg_人: int) -> None:
        self._人, self._页, self._分类, self._滚动 = arg_人, 0, 0, 0

    @staticmethod
    def _钱(arg_值: int) -> str:
        return "$" + 屏幕绘图_类.api_货币(arg_值)

    @staticmethod
    def _适配数字样式(
        arg_框: 画框_类,
        arg_文字: str,
        arg_最大宽度: int,
        arg_基础大小: int,
    ) -> 屏幕字样_类:
        for 大小 in range(arg_基础大小, 7, -1):
            样式 = 屏幕字样_类(大小, 0x101010, 0, 2)
            if 屏幕绘图_类.api_测量(arg_框, arg_文字, 样式) <= arg_最大宽度:
                return 样式
        return 屏幕字样_类(8, 0x101010, 0, 2)

    def _统计(self, arg_世: 世界_类) -> tuple[int, int, int, int, int]:
        owner = self._人 + 1
        companies = sum(bool(c.编号 and c.业主 == owner) for c in arg_世.公司)
        lands = chains = houses = 0
        for land in arg_世.地产[1:]:
            e = land.经济
            if e.业主 == owner:
                lands += 1
                chains += e.连锁 != 0
                houses += e.等级 > 0 and not e.连锁
        facilities = sum(f.业主 == owner for f in arg_世.设施[1:])
        return lands, chains, houses, facilities, companies

    def _画资产(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类) -> None:
        框, 文 = arg_宿.框, 屏幕绘图_类.api_文字
        p = arg_世.玩家[self._人]
        label, value, count = (
            屏幕字样_类(20, 0x101010, 0, 2),
            屏幕字样_类(28, 0x101010, 0, 2),
            屏幕字样_类(20, 0x101010, 0, 2),
        )
        rows, lower = (88, 136, 184, 232), (296, 344, 392, 440)
        left, right, bottom = (
            ("現  金", "存  款", "貸  款", "總資產"),
            ("股  票", "點  卷", "保險期", "企  業"),
            ("土  地", "連鎖店", "房  屋", "設  施"),
        )
        stock_value = sum(
            int(h.数量 * float(股市_类._浮点(arg_世.股票[i].浮点位[2])))
            for i, h in enumerate(p.持仓)
        )
        lands, chains, houses, facilities, companies = self._统计(arg_世)
        left_values = tuple(
            self._钱(n)
            for n in (p.记录.现金, p.记录.银行, p.记录.贷款, 股市_类.api_财富(arg_世, self._人))
        )
        right_values = (
            self._钱(stock_value),
            屏幕绘图_类.api_货币(p.记录.点券),
            f"{p.状态.保险天数}天",
            f"×{companies}",
        )
        counts = lands, chains, houses, facilities
        for i in range(4):
            文(框, left[i], 142, rows[i], 2, label)
            左值样式 = self._适配数字样式(框, left_values[i], 154, value.大小)
            文(框, left_values[i], 330, rows[i], 6, 左值样式)
            文(框, right[i], 430, rows[i], 2, label)
            右值样式 = self._适配数字样式(框, right_values[i], 132, value.大小)
            文(框, right_values[i], 602, rows[i], 6, 右值样式)
            文(框, bottom[i], 142, lower[i], 2, label)
            文(框, f"×{counts[i]}", 250, lower[i], 6, count)
        cell = 0
        for tool in range(len(服务_类.道具名)):
            if cell >= 15:
                break
            if not p.记录.道具[tool]:
                continue
            cx, cy = 300 + 72 * (cell % 5), 284 + 32 * (cell // 5)
            if tool < 13:
                框.画布.api_绘制(框.美术.api_帧("p", 74, tool), cx - 16, cy)
            文(框, f"×{p.记录.道具[tool]}", cx + 30, cy, 6, 屏幕绘图_类.白字)
            cell += 1
        for cell, card in enumerate(p.记录.卡片):
            if 1 <= card <= len(服务_类.卡名):
                cx, cy = 300 + 72 * (cell % 5), 388 + 32 * (cell // 5)
                文(框, 服务_类.卡名[card - 1], cx, cy, 2, 屏幕字样_类(14, 0xFFFFFF))

    def _地产行(self, arg_世: 世界_类) -> list[查询地产行_类]:
        owner, price_index, rows = self._人 + 1, arg_世.头.物价, []
        records = [land.经济 for land in arg_世.地产[1:]]
        for land in arg_世.地产[1:]:
            e = land.经济
            if e.业主 != owner:
                continue
            chain = bool(e.连锁)
            if (
                (self._分类 == 1 and chain)
                or self._分类 == 2
                or (self._分类 == 3 and (chain or not e.等级))
                or (self._分类 == 4 and not chain)
            ):
                continue
            toll = 经济_类.api_通行费(records, owner, price_index, None if chain else e.街道名)
            rows.append(
                查询地产行_类(
                    原生界面_类.api_繁中(e.街道名),
                    "連鎖店" if chain else f"{e.等级}層" if e.等级 else "空地",
                    (land.地价 + land.每级造价 * e.等级) * price_index,
                    toll,
                    land.到期日,
                )
            )
        if self._分类 in (0, 2):
            for f in arg_世.设施[1:]:
                if f.业主 == owner:
                    rows.append(
                        查询地产行_类(
                            原生界面_类.api_繁中(f.名字),
                            f"{f.等级}級",
                            (f.地价 + f.每级造价 * f.等级) * price_index,
                            f.各级租金[min(f.等级, 5)] * price_index,
                            f.到期日,
                        )
                    )
        return rows

    def _画地产(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类) -> None:
        框, 绘, 文 = arg_宿.框, 屏幕绘图_类, 屏幕绘图_类.api_文字
        for i, s in enumerate(("全  部", "住宅區", "商業區", "房  屋", "連鎖店")):
            if i == self._分类:
                框.api_资源图("p", 9, 11, 120 + 75 * i, 64)
            文(框, s, 157 + 75 * i, 80, 2, 屏幕字样_类(16, 0x101010, 0, 2))

            def 分类(arg_i: int = i) -> None:
                self._分类, self._滚动 = arg_i, 0

            绘.api_命中(arg_宿, 170 + i, (120 + 75 * i, 64, 195 + 75 * i, 98), 1, 分类)
        for s, x in (
            ("地  點", 168),
            ("開發狀況", 264),
            ("價  格", 356),
            ("收  費", 448),
            ("租  期", 540),
        ):
            文(框, s, x, 112, 2, 屏幕字样_类(16, 0x101010, 0, 2))
        rows = self._地产行(arg_世)
        if self._滚动 > len(rows):
            self._滚动 = 0
        cell = 屏幕字样_类(16, 0x101010, 0, 2)
        for r, row in enumerate(rows[self._滚动 : self._滚动 + 10]):
            y = 144 + 32 * r
            文(框, row.地点, 168, y, 2, cell)
            文(框, row.开发, 264, y, 2, cell)
            文(框, 绘.api_货币(row.价格), 398, y, 6, cell)
            文(框, 绘.api_货币(row.收费), 490, y, 6, cell)
            date = (
                f"{(row.到期 >> 8) & 255:02d}/{row.到期 & 255}/{row.到期 >> 16}"
                if row.到期
                else "無限期"
            )
            文(框, date, 540, y, 2, cell)
        for r, f in (((593, 369, 624, 400), 7), ((593, 417, 624, 448), 8)):
            if 框.按下 and 框.api_指针内(r):
                框.api_资源图("p", 9, f, r[0], r[1])

        def 上页() -> None:
            self._滚动 = self._滚动 - 10 if self._滚动 >= 10 else 0

        def 下页() -> None:
            if self._滚动 + 10 < len(rows):
                self._滚动 += 10

        绘.api_命中(arg_宿, 168, (586, 360, 634, 408), 1, 上页)
        绘.api_命中(arg_宿, 169, (586, 409, 634, 457), 1, 下页)

    def _画股票(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类) -> None:
        框, 文 = arg_宿.框, 屏幕绘图_类.api_文字
        header = 屏幕字样_类(16, 0x101010, 0, 2)
        for s, x in (("股票名稱", 204), ("持有張數", 332), ("總 市 價", 476)):
            文(框, s, x, 68, 2, header)
        row = 0
        offset = (arg_世.头.阶段 * 4 + arg_世.头.地图) * 12
        for i, quote in enumerate(arg_世.股票):
            amount = arg_世.玩家[self._人].持仓[i].数量
            if amount <= 0:
                continue
            y = 100 + 32 * row
            row += 1
            value = int(amount * float(股市_类._浮点(quote.浮点位[2])))
            文(框, self._原文.api_股票(offset + i), 204, y, 2, header)
            文(框, 屏幕绘图_类.api_货币(amount), 380, y, 6, header)
            文(框, 屏幕绘图_类.api_货币(value), 540, y, 6, header)
            if row >= 12:
                break

    def api_绘制(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类, arg_关: Callable[[], None]) -> None:
        框, 绘, 文 = arg_宿.框, 屏幕绘图_类, 屏幕绘图_类.api_文字
        if not 0 <= self._人 < len(arg_世.玩家):
            self._人 = 0
        原生界面_类.api_填充(框.画布, (0, 0, 640, 480), 0)
        绘.api_背景(框, "p", 9, self._页)
        p = arg_世.玩家[self._人]
        for i, player in enumerate(arg_世.玩家[:4]):
            x = 16 + 88 * i
            框.api_资源图("p", 9, 3 if i == self._人 else 4, x, 14 if i == self._人 else 15)
            文(框, 框.人名[player.记录.角色], x + 44, 30, 2, 屏幕字样_类(20, 0x101010, 0, 2))

            def 选人(arg_i: int = i) -> None:
                self._人, self._滚动 = arg_i, 0

            绘.api_命中(arg_宿, 160 + i, (x, 14, x + 88, 48), 1, 选人)
        down = 框.按下 and 框.api_指针内((492, 9, 603, 39))
        框.画布.api_绘制(框.美术.api_帧("p", 9, 6 if down else 5), 547, 23)
        框.画布.api_绘制(框.美术.api_帧("m", 27 + p.记录.角色, 0), 60, 100)
        god_info = p.状态.神明信息
        if god_info and god_info <= len(arg_世.物件):
            pictures = (0, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 0, 23)
            god = arg_世.物件[god_info - 1]
            if god.种类 < len(pictures) and pictures[god.种类]:
                框.画布.api_绘制(框.美术.api_帧("p", 9, pictures[god.种类]), 60, 188)
            文(框, f"{god.剩余天数}天", 60, 234, 2, 屏幕字样_类(16, 0x101010, 0, 0))
        for i, s in enumerate(("資產清單", "地產清單", "股票清單")):
            r = (12, 282 + 64 * i, 110, 323 + 64 * i)
            if 框.按下 and 框.api_指针内(r):
                框.api_资源图("p", 9, 12, r[0], r[1])
            文(框, s, 60, 302 + 64 * i, 2, 屏幕字样_类(20, 0xFFFFFF if i == self._页 else 0xC0C0C0))

            def 选页(arg_i: int = i) -> None:
                self._页, self._滚动 = arg_i, 0

            绘.api_命中(arg_宿, 165 + i, r, 1, 选页)
        if self._页 == 0:
            self._画资产(arg_宿, arg_世)
        elif self._页 == 1:
            self._画地产(arg_宿, arg_世)
        else:
            self._画股票(arg_宿, arg_世)
        绘.api_命中(arg_宿, 60, (492, 0, 610, 48), 2, arg_关)
