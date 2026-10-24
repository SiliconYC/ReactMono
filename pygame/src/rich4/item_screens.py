# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp库存、按住与卡图流程；真实规则只经GameSession执行。
# ◑ 导入
from collections import deque
from collections.abc import Callable

from rich4.artwork import 美术_类
from rich4.cards import 卡片_类, 卡片用法_类
from rich4.game import 游戏会话_类
from rich4.game_types import 游戏事件_类
from rich4.graphics import 图像_类
from rich4.item_choice_screens import 物品选择绘制_类
from rich4.item_paint import 物品绘图_类
from rich4.item_screen_types import 卡图等待_类, 物品宿主_类, 物品按住_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.services import 服务_类
from rich4.world import 世界_类


# ◕ 功能
class 物品屏幕_类(物品选择绘制_类):
    """
    原物品屏幕共享状态、按住放开、下一帧动作与卡图先于使用。

    更新日志：
    2026.10.24 - 先移植库存/卡图；服务和目标屏幕按独立阶段续接。
    """

    卡帮助 = (
        63,
        62,
        85,
        77,
        78,
        86,
        64,
        66,
        57,
        76,
        65,
        67,
        81,
        73,
        58,
        82,
        74,
        75,
        80,
        60,
        61,
        72,
        84,
        70,
        79,
        69,
        83,
        68,
        59,
        71,
    )
    道具帮助 = (99, 95, 88, 90, 97, 89, 91, 96, 98, 92, 94, 87, 93)

    def __init__(self) -> None:
        self.声音: Callable[[int], None] | None = None
        self.语音: Callable[[int, bool], None] | None = None
        self.时钟: int | None = None
        self.截图名 = ""
        self._弹图: deque[卡图等待_类] = deque()
        self._延迟: list[Callable[[], None]] = []
        self._按住: 物品按住_类 | None = None
        self._上卡 = self._上道具 = 0
        self._说明表: dict[tuple[bool, int], str] = {}
        self._卡图表: dict[int, 图像_类] = {}
        self._已说 = ""
        self._抢夺选择: int | None = None

    def _现在(self, arg_框: 画框_类) -> int:
        return self.时钟 if self.时钟 is not None else arg_框.时钟

    def api_卡图中(self) -> bool:
        return bool(self._弹图)

    def api_有延迟(self) -> bool:
        return bool(self._延迟)

    def api_运行延迟(self) -> None:
        actions, self._延迟 = self._延迟, []
        for action in actions:
            action()

    def api_重置(self) -> None:
        self._弹图.clear()
        self._延迟.clear()
        self._按住 = None
        self._上卡 = self._上道具 = 0
        self._已说 = ""

    def _只说一次(self, arg_键: str, arg_片: tuple[int, ...]) -> None:
        if arg_键 == self._已说:
            return
        self._已说 = arg_键
        if self.语音 and arg_键:
            for i, clip in enumerate(arg_片):
                self.语音(clip, i > 0)

    def _按住开始(
        self,
        arg_框: 画框_类,
        arg_所有者: str,
        arg_区: tuple[int, int, int, int],
        arg_动作: Callable[[], None],
        arg_物: int = 0,
    ) -> None:
        self._按住 = 物品按住_类(arg_所有者, arg_区, arg_动作, arg_物)
        if self.声音:
            self.声音(1)

    def _释放按住(self, arg_框: 画框_类, arg_所有者: str) -> None:
        if self._按住 is None:
            return
        if self._按住.所有者 != arg_所有者:
            self._按住 = None
            return
        if arg_框.按下:
            return
        press, self._按住 = self._按住, None
        if arg_框.api_指针内(press.区域):
            self._延迟.append(press.动作)

    def _说明(self, arg_美术: 美术_类, arg_卡: bool, arg_号: int) -> str:
        key = arg_卡, arg_号
        if self._说明表.get(key):
            return self._说明表[key]
        if arg_卡 and arg_号 == 15:
            text = "讓其他所有角色冬眠五天，期間無法行動。"
        else:
            try:
                help_id = (self.卡帮助 if arg_卡 else self.道具帮助)[arg_号 - 1]
                data, section = arg_美术.api_解码("h", help_id), bytearray()
                for part in data.split(b"\0"):
                    if not part and section:
                        break
                    section.extend(part)
                text = 原生界面_类.api_繁中(bytes(section)).removeprefix("功能：")
            except (ValueError, OSError, IndexError):
                text = " "
        self._说明表[key] = text
        return text

    def _卡图图像(self, arg_美术: 美术_类, arg_卡: int) -> 图像_类:
        if arg_卡 not in self._卡图表 or not self._卡图表[arg_卡].像素:
            data = arg_美术.api_解码("d", 570 + arg_卡)
            pixels = [0] * (165 * 256)
            for i in range(min(len(pixels), len(data) // 2)):
                pixels[i] = data[2 * i] | (data[2 * i + 1] << 8)
            self._卡图表[arg_卡] = 图像_类(165, 256, pixels)
        return self._卡图表[arg_卡]

    def api_观察(self, arg_事件: 游戏事件_类, arg_世: 世界_类) -> None:
        card = arg_事件.卡片
        if card is None or not 1 <= card <= 30 or not 0 <= arg_事件.玩家 < len(arg_世.玩家):
            return
        if arg_世.玩家[arg_事件.玩家].记录.控制标志 & 3 == 1 and 卡片_类.api_主动(card):
            return
        self._弹图.append(卡图等待_类(card))

    def api_画卡图(self, arg_框: 画框_类) -> None:
        if not self._弹图:
            return
        popup, now = self._弹图[0], self._现在(arg_框)
        if not popup.截止:
            popup.截止 = (now + 1500) & 0xFFFFFFFFFFFFFFFF
            if self.声音:
                self.声音(62)
        if now >= popup.截止:
            if popup.之后:
                self._延迟.append(popup.之后)
            self._弹图.popleft()
            return
        card, 绘, 界 = popup.卡片, 物品绘图_类, 原生界面_类
        self.截图名 = f"popup-{card}"
        arg_框.画布.api_绘制(self._卡图图像(arg_框.美术, card), 138, 200, arg_强制不透明=True)
        if card == 14:
            tile = (138, 200, 303, 456)
            界.api_填充(arg_框.画布, tile, 界.api_颜色(40, 64, 112))
            界.api_边框(arg_框.画布, tile, 界.api_颜色(16, 16, 16))
            for inset in (4, 7):
                界.api_边框(
                    arg_框.画布,
                    (138 + inset, 200 + inset, 303 - inset, 456 - inset),
                    界.api_颜色(232, 196, 96),
                )
            for text, y in (("停", 270), ("留", 330), ("卡", 390)):
                绘.api_中(arg_框, text, 220, y, 56, 界.api_颜色(250, 236, 180))
        绘.api_图(arg_框, "d", 517, 5, 220, 129)
        绘.api_中(
            arg_框,
            "使用" + 服务_类.卡名[card - 1],
            220,
            129,
            16,
            界.api_颜色(240, 240, 240),
            True,
            绘.暗,
            False,
        )

        def 跳过() -> None:
            if self._弹图:
                callback = self._弹图.popleft().之后
                if callback:
                    callback()

        arg_框.api_命中(360, (0, 0, 640, 480), 跳过)

    def api_画库存(
        self,
        arg_框: 画框_类,
        arg_会: 游戏会话_类,
        arg_卡: bool,
        arg_宿: 物品宿主_类,
    ) -> None:
        owner, 绘, 界 = "cards" if arg_卡 else "tools", 物品绘图_类, 原生界面_类
        self._释放按住(arg_框, owner)
        self.截图名 = owner
        player = arg_会.世界.玩家[arg_会.世界.头.当前玩家].记录
        gx, gy = 14, 130
        绘.api_图(arg_框, "p", 11, 0 if arg_卡 else 1, gx, gy, True)
        if arg_卡:
            order = 绘.api_卡网格(arg_框, player.卡片, gx, gy)
        else:
            order = 绘.api_道具网格(arg_框, player, gx, gy)
            vehicle = player.交通 & 3
            if vehicle in (1, 2):
                绘.api_图(arg_框, "p", 11, 15 if vehicle == 1 else 16, gx + 325, gy + 117, True)
                rect = 绘.api_格(gx, gy, 14)

                def 下车() -> None:
                    success = arg_会.api_下车()
                    if success:
                        arg_宿.关闭()
                    arg_宿.通知(success, "目前無法下車")

                def 按下车(arg_r: tuple[int, int, int, int] = rect) -> None:
                    self._按住开始(arg_框, "tools", arg_r, 下车)

                arg_框.api_命中(340, rect, 按下车)
        for tile, id in enumerate(order):
            rect = 绘.api_格(gx, gy, tile)

            def 按下(arg_id: int = id, arg_r: tuple[int, int, int, int] = rect) -> None:
                def 释放() -> None:
                    if not arg_卡:
                        self._上道具 = arg_id
                        success = arg_会.api_用道具(arg_id)
                        if success:
                            arg_宿.关闭()
                        elif self.声音:
                            self.声音(3)
                        arg_宿.通知(success, "目前無法使用")
                        return

                    def 卡后() -> None:
                        if not 卡片_类.api_主动(arg_id):
                            if self.声音:
                                self.声音(3)
                            arg_宿.通知(False, "這張卡會在需要時自動使用")
                            return
                        self._上卡 = arg_id
                        success = arg_会.api_用卡(卡片用法_类(arg_id))
                        if success:
                            arg_宿.关闭()
                        elif self.声音:
                            self.声音(3)
                        arg_宿.通知(success, "目前無法使用")

                    self._弹图.append(卡图等待_类(arg_id, 0, 卡后))

                self._按住开始(arg_框, owner, arg_r, 释放, arg_id)

            arg_框.api_命中(300 + id, rect, 按下)
        if self._按住 and self._按住.所有者 == owner:
            绘.api_下沉(arg_框.画布, self._按住.区域)
            self.截图名 = owner + "-pressed"
        strip = gx, 316, gx + 412, 382
        界.api_填充(arg_框.画布, strip, 界.纸色)
        界.api_边框(arg_框.画布, strip, 界.api_颜色(110, 74, 26))
        if self._按住 and self._按住.所有者 == owner and self._按住.物品:
            item = self._按住.物品
            arg_框.api_文字(
                (服务_类.卡名 if arg_卡 else 服务_类.道具名)[item - 1], gx + 8, 321, 16, 界.蓝色
            )
            arg_框.api_文字(self._说明(arg_框.美术, arg_卡, item), gx + 8, 342, 14, 界.墨色, 396)
        elif not order and (arg_卡 or not player.交通 & 3):
            arg_框.api_文字("目前沒有卡片。" if arg_卡 else "目前沒有道具。", gx + 10, 326, 16)
        else:
            arg_框.api_文字(
                "按住卡片可看說明，放開就使用。" if arg_卡 else "按住道具可看說明，放開就使用。",
                gx + 10,
                324,
                16,
            )
            arg_框.api_文字("手指滑開再放開即可取消。", gx + 10, 349, 14, 界.api_颜色(90, 80, 60))
        arg_框.api_按钮(60, (gx + 146, 392, gx + 266, 432), "返回", arg_宿.关闭)
        arg_框.api_命中(62, (gx, gy, gx + 412, gy + 180), lambda: None)
        arg_框.api_命中(61, (0, 0, 640, 480), arg_宿.关闭)
