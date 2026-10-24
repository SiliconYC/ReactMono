# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/tile_popup.cpp::instance_at；沿用参考包围盒近似，不伪称原ID缓冲。
# ◑ 导入
from rich4.board_models import 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.world import 世界_类


# ◕ 功能
class 地图拾取_类:
    """
    原参考按深度/距离拾取角色、对象、建筑，最后反投影找有名道路。

    更新日志：
    2026.10.24 - 角色和物件单独优先于建筑，不从画面反改规则坐标。
    """

    @staticmethod
    def api_拾取(
        arg_世界: 世界_类,
        arg_相机: 相机_类,
        arg_x: int,
        arg_y: int,
    ) -> int:
        左, 顶, 右, 底 = arg_相机.视口
        if not (左 <= arg_x < 右 and 顶 <= arg_y < 底):
            return 0
        best: tuple[int, int, int] | None = None

        def 纳入(
            arg_码: int,
            arg_wx: int,
            arg_wy: int,
            arg_框: tuple[int, int, int, int],
        ) -> None:
            nonlocal best
            anchor = 棋盘投影_类.api_投影((arg_wx, arg_wy), arg_相机)
            if anchor is None:
                return
            x, y = anchor
            左, 顶, 右, 底 = arg_框
            if not (x + 左 <= arg_x <= x + 右 and y + 顶 <= arg_y <= y + 底):
                return
            distance = abs(x - arg_x) + abs(y + int((顶 + 底) / 2) - arg_y)
            if best is None or y > best[1] or (y == best[1] and distance < best[2]):
                best = arg_码 & 65535, y, distance

        w = arg_世界
        for i, p in enumerate(w.玩家[:4]):
            if p.记录.x and p.记录.控制标志 and not p.状态.消失天数:
                纳入(0x8000 | (1 << i), p.记录.x, p.记录.y, (-16, -48, 16, 6))
        for i, p in enumerate(w.特殊角色[:4]):
            if p.x and not p.不活跃状态 and p.节点:
                纳入(0x8000 | (0x10 << i), p.x, p.y, (-16, -48, 16, 6))
        for i, o in enumerate(w.物件[:127]):
            if o.节点 and not o.附身玩家 and o.节点 < len(w.节点):
                n = w.节点[o.节点]
                纳入(0x8000 | ((i + 1) << 8), n.x, n.y, (-14, -34, 14, 6))
        if best is not None:
            return best[0]
        for i, d in enumerate(w.地产[1:], 1):
            纳入(2000 + i, d.x, d.y, (-22, -50, 22, 12) if d.经济.等级 else (-20, -14, 20, 12))
        for i, d in enumerate(w.设施[1:], 1):
            纳入(4000 + i, d.x, d.y, (-30, -60, 30, 16) if d.等级 else (-26, -16, 26, 16))
        for i, d in enumerate(w.公司[1:], 1):
            纳入(6000 + i, d.x, d.y, (-30, -60, 30, 16))
        for i, d in enumerate(w.景物[1:], 1):
            if d.名字:
                纳入(8000 + i, d.x, d.y, (-30, -60, 30, 16))
        if best is not None:
            return best[0]
        tile = 棋盘投影_类.api_反投影((arg_x, arg_y), arg_相机)
        if tile is not None:
            for i, n in enumerate(w.节点[1:2000], 1):
                if n.名字 and n.x >> 5 == tile[0] >> 5 and n.y >> 5 == tile[1] >> 5:
                    return i
        return 0
