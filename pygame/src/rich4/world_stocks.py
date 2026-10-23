# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ world.hpp：股市、持仓与出售表的原始值模型。
# ◑ 导入
from dataclasses import dataclass, field


# ◕ 功能
@dataclass
class 持仓_类:
    """
    成本基准保留原 32 位编码，不在读取时转浮点。

    更新日志：
    2026.10.23 - 对应 StockHolding。
    """

    数量: int = 0
    成本位: int = 0


@dataclass
class 股票状态_类:
    """
    五个 binary32 字段作为位模式保存，保留 NaN payload。

    更新日志：
    2026.10.23 - 对应 StockState。
    """

    标志4: int = 0
    停牌天数: int = 0
    新闻走势: int = 0
    可购股数: int = 0
    标志10: int = 0
    浮点位: list[int] = field(default_factory=lambda: [0] * 5)
    原值32: int = 0


@dataclass
class 出售项_类:
    """
    种类编号为原出售表字节，未知值保留到规则验证阶段。

    更新日志：
    2026.10.23 - 对应 TradeOffer。
    """

    种类: int = 0
    标志: int = 0
    项目: int = 0
    价格: int = 0
    数量: int = 0
    地产类型: int = 0
    地产等级: int = 0
