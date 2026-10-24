# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定market.cpp的item_name/property_row/lease/in_tab。
# ◑ 导入
from rich4.economy import 经济_类
from rich4.native_ui import 原生界面_类
from rich4.original_text import 原版文字_类
from rich4.services import 服务_类
from rich4.trading_screen_types import 交易地产行_类
from rich4.world import 世界_类


# ◕ 功能
class 交易图文_类:
    """
    原交易项目名、地产显示价与分类，不替代真实挂牌限价。

    更新日志：
    2026.10.24 - 外部股票名/地图名，只读世界。
    """

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self._原文 = arg_原文

    def _物名(self, arg_世: 世界_类, arg_类: int, arg_号: int) -> str:
        if arg_类 == 1:
            return self._原文.api_股票((arg_世.头.阶段 * 4 + arg_世.头.地图) * 12 + arg_号)
        if arg_类 == 3 and 1 <= arg_号 <= len(服务_类.道具名):
            return 服务_类.道具名[arg_号 - 1]
        if arg_类 == 4 and 1 <= arg_号 <= len(服务_类.卡名):
            return 服务_类.卡名[arg_号 - 1]
        if arg_类 == 2 and arg_号 > 4000 and arg_号 - 4000 < len(arg_世.设施):
            return 原生界面_类.api_繁中(arg_世.设施[arg_号 - 4000].名字)
        if arg_类 == 2 and arg_号 > 2000 and arg_号 - 2000 < len(arg_世.地产):
            return 原生界面_类.api_繁中(arg_世.地产[arg_号 - 2000].经济.街道名)
        return "?"

    @staticmethod
    def _地产行(arg_世: 世界_类, arg_号: int) -> 交易地产行_类:
        index = arg_世.头.物价
        if arg_号 > 4000 and arg_号 - 4000 < len(arg_世.设施):
            f = arg_世.设施[arg_号 - 4000]
            return 交易地产行_类(
                原生界面_类.api_繁中(f.名字),
                f"{f.等级}級",
                (f.地价 + f.每级造价 * f.等级) * index,
                f.各级租金[min(f.等级, 5)] * index,
                f.到期日,
                False,
                True,
                f.等级 > 0,
            )
        if arg_号 > 2000 and arg_号 - 2000 < len(arg_世.地产):
            land = arg_世.地产[arg_号 - 2000]
            e, chain = land.经济, bool(land.经济.连锁)
            records = [d.经济 for d in arg_世.地产[1:]]
            toll = 经济_类.api_通行费(records, e.业主, index, None if chain else e.街道名)
            return 交易地产行_类(
                原生界面_类.api_繁中(e.街道名),
                "連鎖店" if chain else f"{e.等级}層" if e.等级 else "空地",
                (land.地价 + land.每级造价 * e.等级) * index,
                toll,
                land.到期日,
                chain,
                False,
                e.等级 > 0,
            )
        return 交易地产行_类()

    @staticmethod
    def _租期(arg_到期: int) -> str:
        return (
            f"{arg_到期 >> 8 & 255:02d}/{arg_到期 & 255}/{arg_到期 >> 16}" if arg_到期 else "無限期"
        )

    @staticmethod
    def _分类内(arg_行: 交易地产行_类, arg_类: int) -> bool:
        if arg_类 == 1:
            return not arg_行.设施 and not arg_行.连锁
        if arg_类 == 2:
            return arg_行.设施
        if arg_类 == 3:
            return not arg_行.设施 and not arg_行.连锁 and arg_行.已建
        if arg_类 == 4:
            return arg_行.连锁
        return True
