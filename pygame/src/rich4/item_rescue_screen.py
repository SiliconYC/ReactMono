# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp::Screens::draw_rescue/rescue_voice；真实释放和扣点由会话处理。
# ◑ 导入
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类
from rich4.item_paint import 物品绘图_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_service_types import 救援屏幕状态_类
from rich4.message_overlay import 消息层_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.original_text import 原版文字_类


# ◕ 功能
class 救援屏幕_类:
    """
    原监狱/医院八槽、保释确认、点数不足与NPC感谢后回应。

    更新日志：
    2026.10.24 - 外部护士/NPC台词；保留2500毫秒感谢与下一帧回应。
    """

    _救援: 救援屏幕状态_类
    _原文: 原版文字_类 | None
    NPC名 = ("小偷", "強盜", "流氓", "間諜")
    感谢声音 = (124, 125, 123, 126)

    def _救援台词(self, arg_号: int) -> str:
        if self._原文 is None:
            raise ValueError("救援屏幕需要外部原版台词")
        return self._原文.api_配音(arg_号).文字

    def _救援语音(self, arg_医院: bool, arg_槽: int) -> None:
        if self.语音 is None:
            return
        clips = [128, 129] if arg_医院 else []
        if arg_槽 >= 4:
            clips.append(self.感谢声音[(arg_槽 - 4) & 3])
        if arg_医院:
            clips.append(130)
        for i, clip in enumerate(clips):
            self.语音(clip, i > 0)

    def api_画救援(
        self,
        arg_框: 画框_类,
        arg_会: 游戏会话_类,
        arg_决: 决策_类,
        arg_宿: 物品宿主_类,
    ) -> None:
        now, 绘, 界 = self._现在(arg_框), 物品绘图_类, 原生界面_类
        if not self._救援.活跃:
            self._救援 = 救援屏幕状态_类(活跃=True, 打开=now)
        rescue, world = self._救援, arg_会.世界
        hospital = "住院" in arg_决.提示
        points, entry = world.玩家[arg_决.玩家].记录.点券, 65 if hospital else 63
        self.截图名 = ("hospital" if hospital else "prison") + (
            "-selected" if rescue.选中 >= 0 else ""
        )
        绘.api_图(arg_框, "p", entry, 0, 0, 0, True)
        if hospital:
            绘.api_图(arg_框, "p", 65, 4, 104, 110)

        def 槽位置(arg_槽: int) -> tuple[int, int]:
            if hospital:
                return 297 if arg_槽 < 4 else 481, 1 + 120 * (arg_槽 % 4)
            return (33, 185, 336, 487)[arg_槽 % 4], 24 if arg_槽 < 4 else 183

        def 槽名(arg_槽: int) -> str:
            return (
                self.NPC名[arg_槽 - 4] if arg_槽 >= 4 else arg_框.人名[world.玩家[arg_槽].记录.角色]
            )

        def 确认(arg_槽: int, arg_i: int) -> None:
            self._救援语音(hospital, arg_槽)
            if arg_槽 < 4:
                arg_宿.回答(arg_i)
                return
            self._救援.选中, self._救援.感谢, self._救援.感谢止 = -1, arg_槽, 1

        thanking = 4 <= rescue.感谢 < 8
        for slot in range(8):
            x, y = 槽位置(slot)
            index = None if rescue.感谢 == slot else self._选项(arg_决, slot)
            if index is not None:
                character = world.玩家[slot].记录.角色 if slot < 4 else 0
                portrait = (
                    ((14 if hospital else 5) + character)
                    if slot < 4
                    else ((22 if hospital else 13) + slot)
                )
                绘.api_图(arg_框, "p", entry, portrait, x, y)
                if not hospital:
                    绘.api_图(arg_框, "p", 63, 3, x, y)
                rect = (x, y, x + 147, y + 102) if hospital else (x, y, x + 121, y + 137)
                if rescue.选中 == slot:
                    for inset in range(2):
                        界.api_边框(
                            arg_框.画布,
                            (rect[0] + inset, rect[1] + inset, rect[2] - inset, rect[3] - inset),
                            界.api_颜色(255, 255, 0),
                        )
                if not thanking:

                    def 选择(arg_槽: int = slot, arg_i: int = index) -> None:
                        if points < (30 if arg_槽 < 4 else 300):
                            self._救援.选中, self._救援.不足止 = -1, 1
                            if self.声音:
                                self.声音(3)
                        elif self._救援.选中 == arg_槽:
                            确认(arg_槽, arg_i)
                        else:
                            self._救援.选中, self._救援.不足止 = arg_槽, 0

                    arg_框.api_命中(210 + index, rect, 选择)
            elif not hospital:
                绘.api_图(arg_框, "p", 63, 4, x, y)
        绘.api_图(arg_框, "p", entry, 30 if hospital else 21, 8 if hospital else 542, 432)
        绘.api_右中(arg_框, str(points), 88 if hospital else 622, 452, 20, 绘.白)
        if thanking:
            self.截图名 = ("hospital" if hospital else "prison") + "-thanks"
            slot = rescue.感谢
            if rescue.感谢止 == 1:
                rescue.感谢止 = (now + 2500) & 0xFFFFFFFFFFFFFFFF
            绘.api_图(arg_框, "p", 64, slot - 4, 420 if hospital else 365, 450)
            bx, by = (200, 200) if hospital else (210, 150)
            绘.api_图(arg_框, "p", entry, 1, bx, by)
            绘.api_中(
                arg_框,
                self._救援台词(self.感谢声音[slot - 4]),
                bx + 92,
                by + 34,
                18,
                绘.暗,
                False,
                绘.暗,
                True,
            )
            index = self._选项(arg_决, slot)
            if index is not None:

                def 完成() -> None:
                    self._救援 = 救援屏幕状态_类()
                    arg_宿.回答(index)

                if now >= rescue.感谢止 and not rescue.感谢已安排:
                    rescue.感谢已安排 = True
                    self._延迟.append(完成)
                arg_框.api_命中(210 + index, (0, 0, 640, 480), 完成)
            return
        if hospital:
            绘.api_图(arg_框, "p", 65, 2, 8, 8)
            绘.api_中(arg_框, self._救援台词(127), 148, 56, 18, 绘.暗, False, 绘.暗, True)
            if not self._已说:
                self._只说一次("hospital", (127,))
        if rescue.不足止 == 1:
            rescue.不足止 = (now + 2000) & 0xFFFFFFFFFFFFFFFF
        if rescue.不足止 > now:
            绘.api_图(arg_框, "p", entry, 1, 230, 300)
            绘.api_中(arg_框, self._救援台词(2), 322, 334, 18, 绘.暗, False, 绘.暗, True)
            self._只说一次("poor" + str(rescue.不足止), (2,))
        leave = self._选项(arg_决, -1)
        if rescue.选中 >= 0:
            slot = rescue.选中
            x, y = 槽位置(slot)
            tx, ty = (x - 80, y) if hospital else (x + 20, y + 120)
            绘.api_图(arg_框, "p", entry, 3 if hospital else 2, tx, ty)
            text_x = tx + (41 if hospital else 57)
            for text, cy in (
                (槽名(slot), ty + 26),
                ("保釋點數", ty + 48),
                (f"{30 if slot < 4 else 300}點", ty + 70),
            ):
                绘.api_中(arg_框, text, text_x, cy, 16, 绘.暗, False, 绘.暗, True)
            index = self._选项(arg_决, slot)
            if index is not None:

                def 取消选择() -> None:
                    self._救援.选中 = -1

                消息层_类.api_确认条(
                    arg_框, 320, 240, 290, lambda: 确认(slot, index), 291, 取消选择
                )
        if leave is not None:
            rect = (150, 436, 230, 476) if hospital else (55, 436, 135, 476)
            down = arg_框.按下 and arg_框.api_指针内(rect)
            绘.api_图(arg_框, "p", 10, 36 if down else 35, rect[0], rect[1])
            arg_框.api_命中(210 + leave, rect, lambda: arg_宿.回答(leave))

        def 清选择() -> None:
            self._救援.选中 = -1

        arg_框.api_命中(63, (0, 0, 640, 480), 清选择)
