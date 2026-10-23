# SPDX-License-Identifier: GPL-3.0-or-later
# 对应固定 C++ world.hpp::PlayerStatus/WorldPlayer。
# ◑ 导入
from dataclasses import dataclass, field

from rich4.save_records import 玩家记录_类
from rich4.world_stocks import 持仓_类


# ◕ 功能
@dataclass
class 玩家状态_类:
    """
    原记录 104 字节中的全部已解读状态，未知间隙仍留在 backing。

    更新日志：
    2026.10.23 - 建立全部状态字段与持续计数器。
    """

    卡片策略: int = 0
    救援策略: int = 0
    贷款比例: int = 0
    初始现金比例: int = 50
    股票投资比例: int = 0
    保存方向: int = 0
    贷款到期: int = 0
    酒店天数: int = 0
    消失天数: int = 0
    监狱天数: int = 0
    医院天数: int = 0
    睡眠天数: int = 0
    梦游天数: int = 0
    停留天数: int = 0
    龟行天数: int = 0
    银行拒绝天数: int = 0
    银行禁贷天数: int = 0
    结盟天数: int = 0
    保险天数: int = 0
    神明信息: int = 0
    附身炸弹: int = 0
    盟友: int = 0
    冬眠总天数: int = 0
    神运修正: int = 0
    财运修正: int = 0
    其他运修正: int = 0
    设施编号: int = 0
    敌意: list[int] = field(default_factory=lambda: [0] * 4)
    累计支出: int = 0
    累计收入: int = 0
    标志100: int = 0
    标志101: int = 0
    标志102: int = 0
    标志103: int = 0


@dataclass
class 世界玩家_类:
    """
    玩家可变记录、状态与十二份股票持仓。

    更新日志：
    2026.10.23 - 对应 WorldPlayer。
    """

    记录: 玩家记录_类
    状态: 玩家状态_类 = field(default_factory=玩家状态_类)
    持仓: list[持仓_类] = field(default_factory=lambda: [持仓_类() for _ in range(12)])
