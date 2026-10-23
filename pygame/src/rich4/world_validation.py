# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/world_validation.cpp；归档解码与可玩状态验证保持分离。
# ◑ 导入
import math
import struct

from rich4.calendar import 日期_类
from rich4.world import 世界_类
from rich4.world_map import (
    公司_类,
    地产_类,
    景物_类,
    节点_类,
    设施_类,
)


# ◕ 功能
class 世界验证_类:
    """
    验证玩法与渲染读取的完整世界，不规范化、修复或回写状态。

    更新日志：
    2026.10.23 - 对应 validate_playable_world。
    """

    @staticmethod
    def _检查(
        arg_条件: bool,
        arg_字段: str,
        arg_原因: str,
    ) -> None:
        if not arg_条件:
            raise ValueError(f"无效可玩世界：{arg_字段} {arg_原因}")

    @classmethod
    def _表(
        cls,
        arg_表: list[节点_类] | list[地产_类] | list[设施_类] | list[公司_类] | list[景物_类],
        arg_名: str,
    ) -> None:
        cls._检查(bool(arg_表), arg_名, "必须包含零号记录")
        for i, 记录 in enumerate(arg_表[1:], 1):
            cls._检查(记录.编号 == i, f"{arg_名}[{i}].id", "必须等于表索引")

    @classmethod
    def _牌堆(
        cls,
        arg_牌: list[int],
        arg_游标: int,
        arg_名: str,
        arg_游标名: str,
    ) -> None:
        cls._检查(0 <= arg_游标 < len(arg_牌), arg_游标名, "超出牌堆")
        已见: set[int] = set()
        for i, 值 in enumerate(arg_牌):
            cls._检查(0 <= 值 < len(arg_牌), f"{arg_名}[{i}]", "未知事件编号")
            cls._检查(值 not in 已见, f"{arg_名}[{i}]", "原牌堆必须为排列")
            已见.add(值)

    @classmethod
    def _浮点(cls, arg_位: int, arg_字段: str) -> float:
        值 = struct.unpack("<f", struct.pack("<I", arg_位 & 0xFFFFFFFF))[0]
        cls._检查(math.isfinite(值), arg_字段, "必须为有限 binary32")
        return 值

    @classmethod
    def _地产引用(
        cls,
        arg_世: 世界_类,
        arg_码: int,
        arg_字段: str,
        arg_必须地产: bool = False,
    ) -> None:
        if 2000 < arg_码 < 4000:
            cls._检查(arg_码 - 2000 < len(arg_世.地产), arg_字段, "引用不存在的地产")
        elif 4000 < arg_码 < 6000:
            cls._检查(arg_码 - 4000 < len(arg_世.设施), arg_字段, "引用不存在的设施")
        elif not arg_必须地产 and 6000 < arg_码 < 8000:
            cls._检查(arg_码 - 6000 < len(arg_世.公司), arg_字段, "引用不存在的公司")
        elif arg_必须地产:
            cls._检查(False, arg_字段, "必须是地产或设施")

    @classmethod
    def api_验证(cls, arg_世: 世界_类) -> None:
        人数 = len(arg_世.玩家)
        cls._检查(1 <= 人数 <= 4, "players", "必须有一至四名普通玩家")
        cls._检查(arg_世.头.人数 == 人数, "header.player_count", "与玩家列表不一致")
        cls._检查(0 <= arg_世.头.人类人数 <= 人数, "header.human_player_count", "超出玩家数")
        cls._检查(0 <= arg_世.头.当前玩家 < 人数, "header.current_player", "玩家不存在")
        cls._检查(0 <= arg_世.头.地图 < 4, "header.map_id", "必须为 0..3")
        cls._检查(0 <= arg_世.头.阶段 < 2, "header.stage_id", "必须为 0..1")
        日, 月, 年 = arg_世.头.日期
        有效日 = 1998 <= 年 <= 65535 and 1 <= 月 <= 12 and 1 <= 日 <= 日期_类.api_月天数(年, 月)
        cls._检查(有效日, "header.date", "超出原日期域")
        cls._检查(arg_世.头.物价 > 0, "header.price_index", "必须为正")
        cls._检查(0 <= arg_世.租约模式 < 6, "lease_mode", "必须为 0..5")
        cls._检查(0 <= arg_世.相机旋转 < 8, "camera_rotation", "必须为 0..7")
        for 表, 名 in [
            (arg_世.节点, "nodes"),
            (arg_世.地产, "lands"),
            (arg_世.设施, "facilities"),
            (arg_世.公司, "commercials"),
            (arg_世.景物, "landscapes"),
        ]:
            cls._表(表, 名)
        cls._检查(1 < len(arg_世.节点) <= 65536, "nodes", "必须包含可寻址的真实节点")
        # C++ std::array 的尺寸约束在 Python list 中需显式恢复，否则损坏状态会漏检。
        for 长度, 预期, 名 in [
            (len(arg_世.卡供应), 30, "card_supply"),
            (len(arg_世.道具供应), 8, "tool_supply"),
            (len(arg_世.新闻牌堆), 36, "news_deck"),
            (len(arg_世.命运牌堆), 37, "fortune_deck"),
            (len(arg_世.监狱名单), 8, "prison_roster"),
            (len(arg_世.医院名单), 8, "hospital_roster"),
            (len(arg_世.特殊角色), 5, "special_actors"),
            (len(arg_世.物件), 46, "objects"),
            (len(arg_世.彩票), 36, "lottery_tickets"),
            (len(arg_世.股票), 12, "stocks"),
            (len(arg_世.出售表), 4, "offers"),
            (len(arg_世.股史), 12, "stock_history_bits"),
        ]:
            cls._检查(长度 == 预期, 名, "原固定数组大小不能改变")
        for i, 玩家 in enumerate(arg_世.玩家):
            for 长度, 预期, 名 in [
                (len(玩家.记录.卡片), 15, "state.cards"),
                (len(玩家.记录.道具), 15, "state.tool_amounts"),
                (len(玩家.持仓), 12, "stocks"),
                (len(玩家.状态.敌意), 4, "status.hostility"),
            ]:
                cls._检查(长度 == 预期, f"players[{i}].{名}", "原固定数组大小不能改变")
        for 列, 预期, 名 in [
            (arg_世.股史, 144, "stock_history_bits"),
            (arg_世.出售表, 7, "offers"),
        ]:
            for i, 行 in enumerate(列):
                cls._检查(len(行) == 预期, f"{名}[{i}]", "原固定数组大小不能改变")
        for 股 in arg_世.股票:
            cls._检查(len(股.浮点位) == 5, "stocks.float_bits", "原固定数组大小不能改变")
        for 物件 in arg_世.物件:
            cls._检查(len(物件.运动位) == 4, "objects.motion_bits", "原固定数组大小不能改变")
        for 节点 in arg_世.节点:
            cls._检查(len(节点.邻居) == 4, "nodes.neighbors", "原固定数组大小不能改变")
        for 地 in arg_世.地产:
            cls._检查(len(地.经济.各级租金) == 6, "lands.toll_by_level", "原固定数组大小不能改变")
        for 设施 in arg_世.设施:
            cls._检查(len(设施.各级租金) == 6, "facilities.toll_by_level", "原固定数组大小不能改变")
        for 公司 in arg_世.公司:
            cls._检查(
                len(公司.股东排名) == 4, "commercials.shareholder_order", "原固定数组大小不能改变"
            )
        已引用 = [False] * 46

        def 节点引用(arg_编号: int, arg_字段: str) -> None:
            cls._检查(0 <= arg_编号 < len(arg_世.节点), arg_字段, "引用不存在的节点")

        def 业主引用(arg_业主: int, arg_字段: str) -> None:
            cls._检查(0 <= arg_业主 <= 人数, arg_字段, "引用不存在的普通玩家")

        def 物件引用(arg_编号: int, arg_字段: str) -> None:
            cls._检查(0 <= arg_编号 <= len(arg_世.物件), arg_字段, "引用不存在的物件")
            if arg_编号:
                已引用[arg_编号 - 1] = True

        for i, 节点 in enumerate(arg_世.节点[1:], 1):
            路径 = f"nodes[{i}]"
            for j, 邻居 in enumerate(节点.邻居):
                节点引用(邻居, f"{路径}.neighbors[{j}]")
            cls._地产引用(arg_世, 节点.类型索引, 路径 + ".type_and_index")
            物件引用((节点.标志 >> 16) & 255, 路径 + ".flags.object_id")
        for i, 玩家 in enumerate(arg_世.玩家):
            s = 玩家.记录
            路径 = f"players[{i}]"
            cls._检查(s.槽位 == i, 路径 + ".state.slot", "必须等于玩家索引")
            cls._检查(0 <= s.角色 < 12, 路径 + ".state.character", "必须为 0..11")
            cls._检查(0 <= s.方向 < 8, 路径 + ".state.direction", "必须为 0..7")
            节点引用(s.节点, 路径 + ".state.node_id")
            节点引用(s.上次节点, 路径 + ".state.last_node_id")
            cls._检查(
                0 <= s.骰数 <= 3 and (s.骰数 != 0 or s.控制标志 == 0),
                路径 + ".state.dice_count",
                "参与玩家必须为 1..3",
            )
            for j, 卡 in enumerate(s.卡片):
                cls._检查(0 <= 卡 <= 30, f"{路径}.state.cards[{j}]", "未知卡编号")
            物件引用(玩家.状态.神明信息, 路径 + ".status.god_info")
            物件引用(玩家.状态.附身炸弹, 路径 + ".status.attached_bomb")
            业主引用(玩家.状态.盟友, 路径 + ".status.allied_player")
            for j, 持仓 in enumerate(玩家.持仓):
                字段 = f"{路径}.stocks[{j}]"
                cls._检查(持仓.数量 >= 0, 字段 + ".amount", "必须非负")
                cls._检查(
                    cls._浮点(持仓.成本位, 字段 + ".raw_cost_basis") >= 0,
                    字段 + ".raw_cost_basis",
                    "必须非负",
                )
        for i, 角色 in enumerate(arg_世.特殊角色):
            if 角色.不活跃状态:
                continue
            路径 = f"special_actors[{i}]"
            cls._检查(0 <= 角色.方向 < 8, 路径 + ".direction", "活跃角色必须为 0..7")
            cls._检查(0 <= 角色.业主 < 人数, 路径 + ".owner", "引用不存在的玩家")
            节点引用(角色.节点, 路径 + ".node_id")
            节点引用(角色.上次节点, 路径 + ".last_node_id")
        for i, 物件 in enumerate(arg_世.物件):
            if not 已引用[i] and 物件.节点 == 0 and 物件.附身玩家 == 0:
                continue
            路径 = f"objects[{i}]"
            cls._检查(1 <= 物件.种类 <= 20, 路径 + ".kind", "活跃物件必须为 1..20")
            cls._检查(0 <= 物件.方向 < 8, 路径 + ".direction", "活跃物件必须为 0..7")
            节点引用(物件.节点, 路径 + ".node_id")
            业主引用(物件.附身玩家, 路径 + ".attached_player")
        for i, 地 in enumerate(arg_世.地产[1:], 1):
            业主引用(地.经济.业主, f"lands[{i}].economy.owner_code")
            cls._检查(0 <= 地.经济.等级 <= 5, f"lands[{i}].economy.level", "必须为 0..5")
        for i, 设施 in enumerate(arg_世.设施[1:], 1):
            业主引用(设施.业主, f"facilities[{i}].owner_code")
            cls._检查(0 <= 设施.等级 <= 5, f"facilities[{i}].level", "必须为 0..5")
            if 设施.等级:
                cls._检查(
                    0 <= 设施.类型 <= 4, f"facilities[{i}].facility_type", "已建设施必须为 0..4"
                )
        for i, 公司 in enumerate(arg_世.公司[1:], 1):
            业主引用(公司.业主, f"commercials[{i}].owner_code")
            for j, 业主 in enumerate(公司.股东排名):
                业主引用(业主, f"commercials[{i}].shareholder_order[{j}]")
        cls._牌堆(arg_世.新闻牌堆, arg_世.新闻游标, "news_deck", "news_cursor")
        cls._牌堆(arg_世.命运牌堆, arg_世.命运游标, "fortune_deck", "fortune_cursor")
        for i, 业主 in enumerate(arg_世.彩票):
            业主引用(业主, f"lottery_tickets[{i}]")
        cls._检查(0 <= arg_世.股史游标 < 144, "stock_history_cursor", "必须为 0..143")
        cls._浮点(arg_世.股市走势位, "stock_market_movement_bits")
        for i, 股 in enumerate(arg_世.股票):
            路径 = f"stocks[{i}]"
            cls._检查(0 <= 股.标志4 < len(arg_世.公司), 路径 + ".flags_4", "引用不存在的公司")
            for j, 位 in enumerate(股.浮点位):
                值 = cls._浮点(位, f"{路径}.float_bits[{j}]")
                if j <= 2:
                    cls._检查(0 <= 值 <= 10000, f"{路径}.float_bits[{j}]", "超出原股价域")
            for j, 位 in enumerate(arg_世.股史[i]):
                cls._浮点(位, f"stock_history_bits[{i}][{j}]")
        for i in range(人数):
            for j, 项 in enumerate(arg_世.出售表[i]):
                路径 = f"offers[{i}][{j}]"
                if 项.种类 == 0:
                    continue
                if 项.种类 == 1:
                    cls._检查(0 <= 项.项目 < len(arg_世.股票), 路径 + ".item", "引用不存在的股票")
                elif 项.种类 == 2:
                    cls._地产引用(arg_世, 项.项目, 路径 + ".item", True)
                elif 项.种类 == 3:
                    cls._检查(1 <= 项.项目 <= 13, 路径 + ".item", "道具必须为 1..13")
                elif 项.种类 == 4:
                    cls._检查(1 <= 项.项目 <= 30, 路径 + ".item", "卡片必须为 1..30")
                else:
                    cls._检查(False, 路径 + ".kind", "未知出售种类")
