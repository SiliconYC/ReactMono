# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp::Screens::draw_shop；买卖只回答真实会话选项。
# ◑ 导入
from collections.abc import Callable

from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类
from rich4.item_paint import 物品绘图_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_service_types import 商店屏幕状态_类
from rich4.native_frame import 按钮_类, 画框_类
from rich4.native_ui import 原生界面_类
from rich4.original_text import 原版文字_类
from rich4.services import 服务_类


# ◕ 功能
class 商店屏幕_类:
    """
    原点券店货架快照、滑入、重复行、二次买卖、帮助与告别等待。

    更新日志：
    2026.10.24 - 长店员台词外部PE读取，不以点击即成功代替真实库存与点券。
    """

    _店: 商店屏幕状态_类
    _原文: 原版文字_类 | None

    def api_商店待选(self) -> int | None:
        return self._店.选择值 if self._店.活跃 and self._店.选择类 >= 0 else None

    def api_商店显示选项(self, arg_值: int) -> bool:
        before = self._店.模式
        if 100 < arg_值 <= 130 or 300 < arg_值 <= 330:
            self._店.模式 = 0
        elif 200 < arg_值 <= 213 or 400 < arg_值 <= 413:
            self._店.模式 = 1
        return before != self._店.模式

    def _店台词(self, arg_模式: int, arg_行: int) -> str:
        if self._原文 is None:
            raise ValueError("商店屏幕需要外部原版台词")
        return self._原文.api_配音(((0, 1, 2, 3, 4), (5, 6, 7, 8, 10))[arg_模式][arg_行]).文字

    @staticmethod
    def _滑入(arg_经过: int) -> tuple[int, int]:
        x, gx, vx, vy = -222, 640, 40, 80
        for _ in range(arg_经过 // 50):
            if x >= 5 and gx <= 227:
                break
            x, gx = min(5, x + vx), max(227, gx - vy)
            vx, vy = max(vx - 3, 1), max(vy - 7, 1)
        return x, gx

    def api_画商店(
        self,
        arg_框: 画框_类,
        arg_会: 游戏会话_类,
        arg_决: 决策_类,
        arg_宿: 物品宿主_类,
    ) -> None:
        now, 绘, 界 = self._现在(arg_框), 物品绘图_类, 原生界面_类
        shop = self._店
        if not shop.活跃:
            self._店 = shop = 商店屏幕状态_类(活跃=True, 打开=now)
            shop.卡片 = [o.值 - 100 for o in arg_决.选项 if 100 < o.值 <= 130][:15]
            shop.道具 = [o.值 - 200 for o in arg_决.选项 if 200 < o.值 <= 213]
            shop.卡已买, shop.道具已买 = [False] * len(shop.卡片), [False] * len(shop.道具)
            shop.气泡, shop.气泡止 = self._店台词(0, 0), (now + 2000) & 0xFFFFFFFFFFFFFFFF
        mode = shop.模式

        def 说(arg_行: int) -> None:
            shop.气泡, shop.气泡止 = self._店台词(mode, arg_行), (now + 2000) & 0xFFFFFFFFFFFFFFFF

        if shop.气泡 and not shop.气泡止:
            shop.气泡止 = (now + 2000) & 0xFFFFFFFFFFFFFFFF
        if shop.离开中 and not shop.离开时:
            shop.离开时 = (now + 1500) & 0xFFFFFFFFFFFFFFFF
        if shop.气泡 and now >= shop.气泡止:
            if shop.气泡 in (self._店台词(0, 0), self._店台词(1, 0)):
                说(1)
            else:
                shop.气泡 = ""
        leave = self._选项(arg_决, 0)
        if shop.离开中 and shop.离开时 and now >= shop.离开时 and leave is not None:
            self._延迟.append(lambda: arg_宿.回答(leave))
            shop.离开时 = 0xFFFFFFFFFFFFFFFF
        player, base = arg_会.世界.玩家[arg_决.玩家].记录, 16 if mode else 0
        bought = sum(shop.卡已买) + sum(shop.道具已买)
        self.截图名 = (
            "shop-"
            + ("tool" if mode else "card")
            + ("-leaving" if shop.离开中 else "")
            + ("-bought" if bought else "")
        )
        绘.api_图(arg_框, "p", 10, base, 0, 0, True)
        绘.api_图(arg_框, "p", 10, 2 + base, 320, 240)
        blink = ((now - shop.打开) & 0xFFFFFFFFFFFFFFFF) % 3700
        if blink < 400:
            frame = ((21, 22, 21, 23) if mode else (7, 8, 7, 5))[blink // 100]
            绘.api_图(arg_框, "p", 10, frame, 417 if mode else 405, 50 if mode else 60, True)
        if shop.气泡 and now // 150 % 2:
            绘.api_图(
                arg_框, "p", 10, 26 if mode else 10, 417 if mode else 405, 89 if mode else 91, True
            )
        list_x, grid_x = self._滑入((now - shop.打开) & 0xFFFFFFFFFFFFFFFF)
        绘.api_图(arg_框, "p", 10, 1 + base, list_x, 10, True)
        dx = list_x - 5

        def 买(arg_卡: bool, arg_行: int, arg_值: int) -> Callable[[], None]:
            index = self._选项(arg_决, arg_值)

            def 执行() -> None:
                state = arg_会.世界.玩家[arg_会.待决策.玩家].记录
                item = arg_值 % 100
                price = (服务_类.卡价 if arg_卡 else 服务_类.道具价)[item - 1]

                def 抱歉(arg_行号: int) -> None:
                    self._店.气泡, self._店.气泡止 = self._店台词(0 if arg_卡 else 1, arg_行号), 0
                    if self.声音:
                        self.声音(3)

                kind = 0 if arg_卡 else 1
                if state.点券 < price:
                    抱歉(2)
                elif (
                    (sum(c != 0 for c in state.卡片) >= 15)
                    if arg_卡
                    else (state.道具[item - 1] >= 9)
                ):
                    抱歉(3)
                elif self._店.选择类 != kind or self._店.选择行 != arg_行:
                    self._店.选择类, self._店.选择行, self._店.选择值 = kind, arg_行, arg_值
                    self._店.气泡 = (服务_类.卡名 if arg_卡 else 服务_类.道具名)[
                        item - 1
                    ] + f"　{price}點\n再點一次就兌換"
                    self._店.气泡止 = 0xFFFFFFFFFFFFFFFF
                    if self.声音:
                        self.声音(1)
                elif index is not None and arg_宿.回答(index):
                    self._店.选择类, self._店.气泡 = -1, ""
                    (self._店.卡已买 if arg_卡 else self._店.道具已买)[arg_行] = True
                    if self.声音:
                        self.声音(1)
                else:
                    arg_宿.通知(False, "目前無法兌換")

            return 执行

        if mode == 0:
            for i, card in enumerate(shop.卡片):
                y, sold = i * 24, shop.卡已买[i]
                if shop.选择类 == 0 and shop.选择行 == i:
                    绘.api_选色(arg_框.画布, (14 + dx, 82 + y, 215 + dx, 104 + y))
                绘.api_中(
                    arg_框, 服务_类.卡名[card - 1], 95 + dx, 93 + y, 20, 绘.灰 if sold else 绘.白
                )
                绘.api_右上(
                    arg_框,
                    f"${服务_类.卡价[card - 1]}",
                    199 + dx,
                    85 + y,
                    20,
                    绘.灰 if sold else 绘.白,
                )
                index = self._选项(arg_决, 100 + card)
                if not sold and index is not None:
                    arg_框.api_命中(
                        210 + index, (14, 81 + y, 215, 105 + y), 买(True, i, 100 + card)
                    )
        else:
            for i, tool in enumerate(shop.道具):
                y, sold = i * 48, shop.道具已买[i]
                if shop.选择类 == 1 and shop.选择行 == i:
                    绘.api_选色(arg_框.画布, (12 + dx, 81 + y, 213 + dx, 127 + y))
                绘.api_中(
                    arg_框, 服务_类.道具名[tool - 1], 95 + dx, 102 + y, 20, 绘.灰 if sold else 绘.白
                )
                绘.api_右上(
                    arg_框,
                    f"${服务_类.道具价[tool - 1]}",
                    199 + dx,
                    94 + y,
                    20,
                    绘.灰 if sold else 绘.白,
                )
                index = self._选项(arg_决, 200 + tool)
                if not sold and index is not None:
                    arg_框.api_命中(
                        210 + index, (12, 80 + y, 213, 128 + y), 买(False, i, 200 + tool)
                    )
        绘.api_图(arg_框, "p", 11, 1 if mode else 0, grid_x, 293)
        if mode == 0:
            sell_values = [300 + id for id in 绘.api_卡网格(arg_框, player.卡片, grid_x, 293)]
        else:
            sell_values = [400 + id for id in 绘.api_道具网格(arg_框, player, grid_x, 293)]
        for tile, value in enumerate(sell_values):
            index = self._选项(arg_决, value)
            if index is None:
                continue
            c, r = tile % 5, tile // 5
            rect = 233 + 80 * c, 299 + 56 * r, 311 + 80 * c, 353 + 56 * r
            if arg_框.按下 and arg_框.api_指针内(rect):
                绘.api_下沉(arg_框.画布, rect)
            kind = 3 if mode else 2
            if shop.选择类 == kind and shop.选择行 == tile:
                for inset in range(2):
                    界.api_边框(
                        arg_框.画布,
                        (rect[0] + inset, rect[1] + inset, rect[2] - inset, rect[3] - inset),
                        界.api_颜色(255, 255, 0),
                    )
            owned = player.道具[value % 100 - 1] if mode else 1

            def 卖(
                arg_类: int = kind,
                arg_格: int = tile,
                arg_有: int = owned,
                arg_i: int = index,
                arg_值: int = value,
            ) -> None:
                if self._店.选择类 != arg_类 or self._店.选择行 != arg_格:
                    item, card = arg_值 % 100, arg_类 == 2
                    price = 服务_类.卡价[item - 1] if card else 服务_类.道具价[item - 1] * arg_有
                    self._店.选择类, self._店.选择行, self._店.选择值 = arg_类, arg_格, arg_值
                    self._店.气泡 = (
                        "賣出"
                        + (服务_类.卡名 if card else 服务_类.道具名)[item - 1]
                        + f"\n可得{price * 9 // 10}點，再點一次"
                    )
                    self._店.气泡止 = 0xFFFFFFFFFFFFFFFF
                    if self.声音:
                        self.声音(1)
                    return
                self._店.选择类, self._店.气泡 = -1, ""
                if arg_宿.回答(arg_i) and self.声音:
                    self.声音(1)

            arg_框.api_命中(210 + index, rect, 卖)
        if shop.选择类 >= 0:
            buying, card, item = shop.选择类 < 2, shop.选择类 % 2 == 0, shop.选择值 % 100
            strip = (
                (grid_x + 2, 295, grid_x + 410, 471)
                if buying
                else (list_x + 4, 236, list_x + 222, 470)
            )
            界.api_填充(arg_框.画布, strip, 界.纸色)
            界.api_边框(arg_框.画布, strip, 界.api_颜色(110, 74, 26))
            arg_框.api_文字(
                (服务_类.卡名 if card else 服务_类.道具名)[item - 1],
                strip[0] + 10,
                strip[1] + 8,
                18,
                界.蓝色,
            )
            arg_框.api_文字(
                self._说明(arg_框.美术, card, item),
                strip[0] + 10,
                strip[1] + 36,
                16,
                界.墨色,
                strip[2] - strip[0] - 20,
            )
            arg_框.api_文字("點此取消", strip[2] - 74, strip[3] - 24, 14, 界.api_颜色(90, 80, 60))

            def 清选择() -> None:
                self._店.选择类, self._店.气泡 = -1, ""

            arg_框.按钮.insert(0, 按钮_类(282, strip, True, 清选择))
        switch_rect, exit_rect = (542, 13, 627, 98), (556, 246, 636, 286)
        switch_down = arg_框.按下 and arg_框.api_指针内(switch_rect)
        绘.api_图(arg_框, "p", 10, (29 if mode else 13) + int(switch_down), 542, 13)
        exit_down = shop.离开中 or (arg_框.按下 and arg_框.api_指针内(exit_rect))
        绘.api_图(arg_框, "p", 10, 36 if exit_down else 35, 556, 246)
        绘.api_图(arg_框, "p", 10, 37, 230, 246)
        绘.api_右上(arg_框, str(player.点券), 310, 257, 20, 绘.白)
        if shop.离开中:
            绘.api_图(arg_框, "p", 10, 19 if mode else 3, 320, 240)
        voice = next((v for v in range(11) if self._原文.api_配音(v).文字 == shop.气泡), None)
        self._只说一次(
            "shop:" + shop.气泡 if shop.气泡 else "", (voice,) if voice is not None else ()
        )
        if shop.气泡:
            绘.api_图(arg_框, "p", 10, 15, 120, 10)
            绘.api_中(arg_框, shop.气泡, 235, 119, 20, 绘.暗, False, 绘.暗, True)
            if not shop.离开中:

                def 收气泡() -> None:
                    self._店.气泡, self._店.选择类 = "", -1

                arg_框.api_命中(281, (150, 30, 360, 210), 收气泡)
        if shop.离开中:
            if leave is not None:
                arg_框.api_命中(210 + leave, (0, 0, 640, 480), lambda: arg_宿.回答(leave))
            return

        def 换店() -> None:
            self._店.模式 ^= 1
            self._店.选择类 = -1
            if self._店.气泡 and self._店.气泡 not in (self._店台词(0, 0), self._店台词(1, 0)):
                self._店.气泡 = ""

        arg_框.api_命中(280, switch_rect, 换店)
        if leave is not None:

            def 离开() -> None:
                self._店.选择类, self._店.离开中, self._店.离开时 = -1, True, 0
                self._店.气泡, self._店.气泡止 = self._店台词(mode, 4), 0

            arg_框.api_命中(210 + leave, exit_rect, 离开)
