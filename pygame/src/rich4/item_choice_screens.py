# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp的遥控骰/抢夺/嫁祸；由完整Screens共享选择状态。
# ◑ 导入
from collections.abc import Callable

from rich4.board_models import 相机_类
from rich4.cards import 目标种类_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类
from rich4.item_paint import 物品绘图_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_targets import 地图目标绘制_类
from rich4.message_overlay import 消息层_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.services import 服务_类


# ◕ 功能
class 物品选择绘制_类:
    """
    原六面遥控骰、二次点击抢夺与嫁祸候选头像/是非条。

    更新日志：
    2026.10.24 - 只回答原决策索引，不生成任意目标或重算卡片结果。
    """

    _抢夺选择: int | None
    _上道具: int
    语音: Callable[[int, bool], None] | None
    声音: Callable[[int], None] | None
    截图名: str

    @staticmethod
    def _选项(arg_决: 决策_类, arg_值: int) -> int | None:
        return next((i for i, o in enumerate(arg_决.选项) if o.值 == arg_值), None)

    def api_画地图目标(
        self,
        arg_框: 画框_类,
        arg_决: 决策_类,
        arg_相机: 相机_类,
        arg_选: int | None,
        arg_点: Callable[[int], None],
    ) -> None:
        self.截图名 = 地图目标绘制_类.api_绘制(
            arg_框, arg_决, arg_相机, arg_选, arg_点, self._上道具, self._现在(arg_框)
        )

    def api_画遥控骰(self, arg_框: 画框_类, arg_决: 决策_类, arg_宿: 物品宿主_类) -> None:
        self.截图名 = "remote-dice"
        物品绘图_类.api_图(arg_框, "p", 72, 0, 92, 300)
        for i, o in enumerate(arg_决.选项):
            value = o.值
            if not 1 <= value <= 6:
                continue
            x = 104 + 40 * (value - 1)
            cell = (92 if value == 1 else x - 5, 300, 348 if value == 6 else x + 35, 355)
            if arg_框.按下 and arg_框.api_指针内(cell):
                物品绘图_类.api_图(arg_框, "p", 72, value, x, 314)
            arg_框.api_命中(210 + i, cell, lambda i=i: arg_宿.回答(i))
        cancel = self._选项(arg_决, 0)
        if cancel is not None:
            arg_框.api_按钮(210 + cancel, (356, 306, 436, 350), "取消", lambda: arg_宿.回答(cancel))

    def api_画抢夺(
        self,
        arg_框: 画框_类,
        arg_会: 游戏会话_类,
        arg_决: 决策_类,
        arg_宿: 物品宿主_类,
    ) -> None:
        self.截图名 = "steal"
        world, victim = arg_会.世界, arg_决.被抢玩家
        if victim is None or not 0 <= victim < len(world.玩家):
            return
        player, 绘, 界 = world.玩家[victim].记录, 物品绘图_类, 原生界面_类
        gx, card_y, tool_y = 14, 70, 270
        绘.api_图(arg_框, "p", 11, 0, gx, card_y, True)
        绘.api_图(arg_框, "p", 11, 1, gx, tool_y, True)
        cards = 绘.api_卡网格(arg_框, player.卡片, gx, card_y)
        tools = 绘.api_道具网格(arg_框, player, gx, tool_y)
        if self._抢夺选择 is not None and self._抢夺选择 >= len(arg_决.选项):
            self._抢夺选择 = None

        def 方格(arg_类: int, arg_id: int, arg_r: tuple[int, int, int, int]) -> None:
            index = self._选项(arg_决, (arg_类 << 16) | arg_id)
            if index is None:
                return
            if self._抢夺选择 == index or (arg_框.按下 and arg_框.api_指针内(arg_r)):
                绘.api_下沉(arg_框.画布, arg_r)
            if self._抢夺选择 == index:
                left, top, right, bottom = arg_r
                for inset in range(3):
                    界.api_边框(
                        arg_框.画布,
                        (left + inset, top + inset, right - inset, bottom - inset),
                        界.api_颜色(255, 255, 0),
                    )

            def 选择() -> None:
                if self._抢夺选择 == index:
                    self._抢夺选择 = None
                    if self.声音:
                        self.声音(1)
                    arg_宿.回答(index)
                else:
                    self._抢夺选择 = index
                    if self.声音:
                        self.声音(0)

            arg_框.api_命中(210 + index, arg_r, 选择)

        for tile, id in enumerate(cards):
            方格(int(目标种类_类.卡片), id, 绘.api_格(gx, card_y, tile))
        for tile, id in enumerate(tools):
            方格(int(目标种类_类.道具), id, 绘.api_格(gx, tool_y, tile))
        strip = gx, 41, gx + 412, 69
        界.api_填充(arg_框.画布, strip, 界.纸色)
        界.api_边框(arg_框.画布, strip, 界.api_颜色(110, 74, 26))
        line = "請選擇要搶的卡片或道具"
        if self._抢夺选择 is not None:
            value = arg_决.选项[self._抢夺选择].值
            tool, id = (value & 0xFFFFFFFF) >> 16 == int(目标种类_类.道具), value & 65535
            line = (服务_类.道具名 if tool else 服务_类.卡名)[id - 1] + "　再點一次就搶走"
        arg_框.api_文字(line, gx + 8, 46, 16, 界.墨色)
        cancel = self._选项(arg_决, -1)
        if cancel is not None:

            def 取消() -> None:
                self._抢夺选择 = None
                arg_宿.回答(cancel)

            arg_框.api_按钮(210 + cancel, (gx + 316, 452, gx + 412, 478), "取消", 取消)

    def api_画嫁祸(
        self,
        arg_框: 画框_类,
        arg_会: 游戏会话_类,
        arg_决: 决策_类,
        arg_宿: 物品宿主_类,
    ) -> None:
        world, 绘, 界 = arg_会.世界, 物品绘图_类, 原生界面_类
        candidates = [i for i, o in enumerate(arg_决.选项) if 0 <= o.值 < len(world.玩家)]
        keep = self._选项(arg_决, -1)

        def 角色(arg_i: int) -> int:
            return world.玩家[arg_决.选项[arg_i].值].记录.角色

        if len(candidates) == 1 and keep is not None:
            self.截图名 = "frame-up-yesno"
            yes = candidates[0]
            消息层_类.api_确认框(
                arg_框,
                "是否嫁禍給" + arg_框.人名[角色(yes)] + "？",
                210 + yes,
                lambda: arg_宿.回答(yes),
                210 + keep,
                lambda: arg_宿.回答(keep),
            )
            return
        self.截图名 = "frame-up"
        绘.api_图(arg_框, "d", 517, 5, 220, 140)
        绘.api_中(arg_框, "請選擇嫁禍對象...", 220, 140, 16, 界.api_颜色(240, 240, 240))
        strip = arg_框.美术.api_帧("d", 518, min(max(len(candidates), 2), 4) - 2)
        arg_框.画布.api_绘制(strip, 220, 320)
        left, top = 220 - strip.原点x, 320 - strip.原点y
        for k, index in enumerate(candidates[:4]):
            face = left + 12 + 80 * k, top + 12, left + 84 + 80 * k, top + 84
            arg_框.api_资源图("d", 2, 角色(index), face[0], face[1])
            if arg_框.按下 and arg_框.api_指针内(face):
                for inset in range(2):
                    界.api_边框(
                        arg_框.画布,
                        (face[0] + inset, face[1] + inset, face[2] - inset, face[3] - inset),
                        界.api_颜色(255, 255, 0),
                    )
            arg_框.api_命中(
                210 + index,
                (face[0] - 4, face[1] - 4, face[2] + 4, face[3] + 4),
                lambda index=index: arg_宿.回答(index),
            )
        if keep is not None:
            arg_框.api_按钮(
                210 + keep,
                (160, top + strip.高 + 10, 280, top + strip.高 + 52),
                "保留卡片",
                lambda: arg_宿.回答(keep),
            )
