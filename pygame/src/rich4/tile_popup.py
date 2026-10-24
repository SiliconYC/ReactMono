# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/tile_popup.cpp::lines/draw及hpp::Popup。
# ◑ 导入
from dataclasses import dataclass

from rich4.economy import 经济_类
from rich4.message_overlay import 消息层_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类, 文字样式_类
from rich4.tile_pick import 地图拾取_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass
class 地图弹框_类:
    """
    屏幕点击原点及原实例码。

    更新日志：
    2026.10.24 - 不自行保存世界副本，绘制读取当前世界。
    """

    x: int = 0
    y: int = 0
    编码: int = 0


class 地图提示_类(地图拾取_类):
    """
    原四向Data517地图资料，不改变收费或产权口径。

    更新日志：
    2026.10.24 - 研究所产出行沿用参考未解字段省略；完整文字/拾取另行差分。
    """

    地产等级 = ("空  地", "平  房", "店  舖", "商  場", "商業大樓", "摩天大樓")
    设施类型 = ("公  園", "旅  館", "購物中心", "加油站", "研究所")
    等级名 = ("０級", "一級", "二級", "三級", "四級", "五級")
    特殊名 = ("小偷", "強盜", "流氓", "間諜")
    物件名 = (
        "小財神",
        "大財神",
        "小福神",
        "大福神",
        "小窮神",
        "大窮神",
        "小衰神",
        "大衰神",
        "天使",
        "惡魔",
        "惡犬",
        "土地公",
        "禮物",
        "寶箱",
        "死神",
        "路障",
        "地雷",
        "定時炸彈",
    )

    @staticmethod
    def _人名(arg_w: 世界_类, arg_业主: int) -> str:
        return (
            画框_类.人名[arg_w.玩家[arg_业主 - 1].记录.角色 % 12]
            if 0 < arg_业主 <= len(arg_w.玩家)
            else ""
        )

    @classmethod
    def api_文字(cls, arg_w: 世界_类, arg_码: int) -> list[tuple[int, str]]:
        out: list[tuple[int, str]] = []
        code, price, 解码 = arg_码, arg_w.头.物价, 原生界面_类.api_繁中
        if 0 < code < 2000:
            if code < len(arg_w.节点) and arg_w.节点[code].名字:
                out.append((27, 解码(arg_w.节点[code].名字)))
        elif 2000 < code < 4000:
            if code - 2000 >= len(arg_w.地产):
                return out
            e = arg_w.地产[code - 2000].经济
            if e.业主:
                out.append((0, cls._人名(arg_w, e.业主)))
            level = min(e.等级, 5)
            out += [
                (18, "空  地" if level == 0 else "連鎖店" if e.连锁 else cls.地产等级[level]),
                (36, cls.等级名[level]),
            ]
            if e.业主:
                records = [d.经济 for d in arg_w.地产[1:]]
                money = (
                    f"${2000 * price:,}×{经济_类.api_连锁数(records, e.业主)}"
                    if e.连锁
                    else f"${经济_类.api_通行费(records, e.业主, price, e.街道名):,}"
                )
            else:
                money = f"${e.各级租金[level]:,}"
            out.append((54, money))
        elif 4000 < code < 6000:
            if code - 4000 >= len(arg_w.设施):
                return out
            f = arg_w.设施[code - 4000]
            if f.业主:
                out.append((0, cls._人名(arg_w, f.业主)))
            if not f.等级:
                return out + [(27, "空  地")]
            typ, level = f.类型, min(f.等级, 5)
            if typ > 4:
                return out
            if typ in (0, 3):
                out.append((27, cls.设施类型[typ]))
                if typ == 3:
                    out.append((54, "×1000"))
            else:
                out += [(18, cls.设施类型[typ]), (36, cls.等级名[level])]
                if typ != 4:
                    out.append((54, f"×{f.各级租金[level] * price}"))
        elif 6000 < code < 8000:
            if code - 6000 >= len(arg_w.公司):
                return out
            c = arg_w.公司[code - 6000]
            if c.业主:
                out.append((0, cls._人名(arg_w, c.业主)))
            out += [(27, 解码(c.名字)), (54, f"餘股:{c.剩余股份}")]
        elif 8000 < code < 10000:
            if code - 8000 < len(arg_w.景物) and arg_w.景物[code - 8000].名字:
                out.append((27, 解码(arg_w.景物[code - 8000].名字)))
        elif code & 0x8000:
            if code & 255:
                mask = code & 255
                slot = (mask & -mask).bit_length() - 1
                out.append((25, cls._人名(arg_w, slot + 1) if slot < 4 else cls.特殊名[slot - 4]))
            else:
                index = (code & 0x7F00) >> 8
                if 1 <= index <= len(arg_w.物件):
                    kind = arg_w.物件[index - 1].种类
                    if 1 <= kind <= len(cls.物件名):
                        out.append((25, cls.物件名[kind - 1]))
        return out

    @classmethod
    def api_绘制(cls, arg_框: 画框_类, arg_w: 世界_类, arg_弹: 地图弹框_类) -> None:
        lines = cls.api_文字(arg_w, arg_弹.编码)
        if not lines:
            return
        first = arg_框.美术.api_帧("d", 517, 0)
        w, h, x, y = first.宽, first.高, arg_弹.x, arg_弹.y
        q = int(y - 40 >= h) + 2 * int(x > 440 - w)
        # 原draw直接blit到点击锚点；Frame.picture会抵消原点，导致指针和整框错位。
        arg_框.画布.api_绘制(arg_框.美术.api_帧("d", 517, q), x, y)
        tx, base = x + (-(w // 2 + 9) if q & 2 else w // 2 + 9), y + (-96 if q & 1 else 42)
        style = 文字样式_类(
            16,
            原生界面_类.api_颜色(240, 240, 240),
            True,
            True,
            False,
            原生界面_类.api_颜色(16, 16, 16),
        )
        for dy, text in lines:
            消息层_类.api_文字(arg_框, text, tx, base + dy, 2, style)
