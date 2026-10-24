# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/finance.cpp::draw_primary_stock。
# ◑ 导入
from collections.abc import Callable

from rich4.game_types import 决策_类
from rich4.number_pad import 数字板_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕宿主_类, 屏幕绘图_类
from rich4.world import 世界_类


# ◕ 功能
class 一级股票屏幕_类:
    """
    原Panel73认购提示与真实数字板；公司名从外部PE读取。

    更新日志：
    2026.10.24 - 保留未打开数字板时的位置及取消等同零股。
    """

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self._原文 = arg_原文

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_决策: 决策_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
    ) -> None:
        company = ""
        if arg_决策.地产 < len(arg_世.公司):
            stock = arg_世.公司[arg_决策.地产].股票索引
            index = (arg_世.头.阶段 * 4 + arg_世.头.地图) * 12 + stock
            if stock < 12 and index < 96:
                company = self._原文.api_股票(index) + "\n"
        top = arg_板.api_提示顶() if arg_板.api_活跃() else 2 if arg_板.api_比例() > 1 else 42
        arg_宿.框.api_资源图("p", 73, 5, 227, top)
        屏幕绘图_类.api_文字(
            arg_宿.框,
            f"認購原始股\n{company}每股{arg_决策.金额}元\n最多{arg_决策.金额上限}股",
            319,
            top + 44,
            4,
            屏幕绘图_类.黑字,
        )
        if not arg_板.api_活跃():

            def 完成(arg_数: int) -> None:
                arg_答(1, arg_数) if arg_数 > 0 else arg_答(0, 0)

            arg_板.api_打开(arg_决策.金额上限, 完成)
