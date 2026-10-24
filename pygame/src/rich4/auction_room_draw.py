# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定market.cpp的draw_room/announce/draw_bidders。
# ◑ 导入
from collections.abc import Callable

from rich4.native_frame import 画框_类
from rich4.screen_draw import 屏幕字样_类, 屏幕绘图_类
from rich4.world import 世界_类


# ◕ 功能
class 拍卖绘制_类:
    """
    原拍卖室/标的/竞买人姿态；保留源未区分房屋样式的图号选择。

    更新日志：
    2026.10.24 - 画面不更改卖家、标价或持有人。
    """

    式 = 屏幕字样_类(18, 0xFFFFFF)

    @classmethod
    def _画房(
        cls,
        arg_框: 画框_类,
        arg_世: 世界_类,
        arg_地: int,
        arg_价: int,
        arg_锤: bool,
    ) -> int:
        框 = arg_框
        屏幕绘图_类.api_背景(框, "p", 26, 0)
        框.api_资源图("p", 26, 17, 67, 63)
        if arg_锤:
            框.api_资源图("p", 26, 21, 124, 27)
        else:
            框.api_资源图("p", 26, 25, 123, 24)
        picture, seller = 90, -1
        if 2000 < arg_地 < 4000 and arg_地 - 2000 < len(arg_世.地产):
            land = arg_世.地产[arg_地 - 2000].经济
            seller = land.业主 - 1 if land.业主 else -1
            if land.等级:
                picture = (114 if arg_世.头.阶段 else 29) + land.等级
            elif land.业主 and land.业主 <= len(arg_世.玩家):
                picture = 91 + arg_世.玩家[land.业主 - 1].记录.角色
        elif arg_地 > 4000 and arg_地 - 4000 < len(arg_世.设施):
            owner = arg_世.设施[arg_地 - 4000].业主
            seller = owner - 1 if owner else -1
        if picture < 框.美术.api_帧数("p", 26):
            框.画布.api_绘制(框.美术.api_帧("p", 26, picture), 232, 180)
        屏幕绘图_类.api_文字(框, "標價：", 182, 242, 0, cls.式)
        屏幕绘图_类.api_文字(框, f"{arg_价}元", 272, 262, 6, cls.式)
        return seller

    @staticmethod
    def _公告(arg_框: 画框_类, arg_文: str) -> None:
        arg_框.画布.api_绘制(arg_框.美术.api_帧("p", 26, 2), 410, 60)
        屏幕绘图_类.api_文字(arg_框, arg_文, 410, 60, 4, 屏幕字样_类(16, 0x101010, 0, 2))

    @classmethod
    def _竞买人(
        cls,
        arg_框: 画框_类,
        arg_世: 世界_类,
        arg_当前: int | None,
        arg_卖家: int,
        arg_姿态: Callable[[int], tuple[int, int]],
    ) -> None:
        for k, p in enumerate(arg_世.玩家[:4]):
            if not p.记录.控制标志:
                continue
            y = 80 + 120 * k
            offset, index = arg_姿态(k)
            entry = 27 + 3 * p.记录.角色 + offset
            count = max(1, arg_框.美术.api_帧数("p", entry))
            arg_框.画布.api_绘制(arg_框.美术.api_帧("p", entry, index % count), 590, y)
            if arg_当前 == k:
                arg_框.画布.api_绘制(arg_框.美术.api_帧("p", 26, 78 + p.记录.角色), 590, y)
            if k == arg_卖家:
                屏幕绘图_类.api_文字(arg_框, "賣方", 590, y + 14, 2, cls.式)
            else:
                屏幕绘图_类.api_文字(arg_框, f"{p.记录.现金}元", 620, y + 14, 6, cls.式)
