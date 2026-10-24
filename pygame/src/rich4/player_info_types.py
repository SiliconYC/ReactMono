# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定menus.cpp::PlayerInfo::draw_properties中的Row。
# ◑ 导入
from dataclasses import dataclass


# ◕ 功能
@dataclass(frozen=True)
class 查询地产行_类:
    """
    仅供原玩家查询页显示的地产/设施行；不回写规则价格。

    更新日志：
    2026.10.24 - 保留原价格/收费不同计算路径与未验证日期编码。
    """

    地点: str
    开发: str
    价格: int
    收费: int
    到期: int
