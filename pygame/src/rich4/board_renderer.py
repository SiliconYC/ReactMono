# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/board_renderer.cpp，保留原资源编号、深度键和调色方式。
# ◑ 导入
import struct
from dataclasses import dataclass, replace
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.board_models import 地产外观_类, 场景_类, 相机_类, 绘制统计_类
from rich4.board_projection import 棋盘投影_类
from rich4.graphics import 图像_类
from rich4.projection_tables import 投影表_类
from rich4.terrain import 地形_类, 地面_类


# ◕ 功能
@dataclass
class 摆放_类:
    """
    地图只读渲染字段；与规则世界分开保留原有符号坐标读取。

    更新日志：
    2026.10.23 - 对应 Placement。
    """

    位置: tuple[int, int] = (0, 0)
    精灵: int = 0
    方向: int = 0
    业主: int = 0
    等级: int = 0
    类型: int = 0


@dataclass
class 精灵资源_类:
    """
    解码资源及各帧像素偏移，只在需要绘帧时生成RGB555图像。

    更新日志：
    2026.10.23 - 对应 SpriteResource与assets::parse_graphics布局。
    """

    数据: bytes
    索引色: bool
    帧偏移: list[int]


class 棋盘绘制_类:
    """
    八图原地面、道路与场景合成，资源/换色缓存不改变外部游戏状态。

    更新日志：
    2026.10.23 - 对应 board::Renderer/Impl，程序运行不调用C++。
    """

    @staticmethod
    def _查包(arg_目录: Path, arg_名字: str) -> Path:
        for 项 in arg_目录.iterdir():
            if 项.is_file() and 项.name.lower() == arg_名字:
                return 项
        raise ValueError(f"缺少棋盘资源：{arg_名字}")

    @staticmethod
    def _摆放(arg_数据: bytes, arg_表: int) -> list[摆放_类]:
        步长 = (40, 52, 56, 52, 28)[arg_表]
        资源包_类.api_检查范围(arg_表 * 8, 8, len(arg_数据))
        数, 偏 = struct.unpack_from("<II", arg_数据, arg_表 * 8)
        if 偏 < 40 or 偏 > len(arg_数据) or 数 > 65535 or (数 + 1) * 步长 > len(arg_数据) - 偏:
            raise ValueError("棋盘元数据表边界无效")
        结果 = [摆放_类()]
        for i in range(1, 数 + 1):
            记录 = arg_数据[偏 + i * 步长 : 偏 + (i + 1) * 步长]
            项 = 摆放_类(位置=struct.unpack_from("<hh", 记录))
            if arg_表 == 0:
                项.精灵 = struct.unpack_from("<H", 记录, 0x22)[0]
            elif arg_表 == 4:
                项.精灵 = struct.unpack_from("<H", 记录, 0x1A)[0]
                项.方向 = 记录[0x18]
            else:
                项.方向 = 记录[0x1B]
                项.业主 = 记录[0x18 if arg_表 == 3 else 0x19]
                项.等级, 项.类型 = 记录[0x1A], 记录[0x18]
                if arg_表 == 3:
                    项.精灵 = struct.unpack_from("<H", 记录, 0x20)[0]
            结果.append(项)
        return 结果

    def __init__(self, arg_目录: Path, arg_地图: int) -> None:
        if not 0 <= arg_地图 <= 7:
            raise ValueError("棋盘地图编号必须为0..7")
        self.地图 = arg_地图
        self.地图包 = 资源包_类(self._查包(arg_目录, "map.mkf"))
        self.数据包 = 资源包_类(self._查包(arg_目录, "data.mkf"))
        self.地面 = 地面_类.api_解码(self.地图包.api_解码(arg_地图 * 2))
        元数据 = self.地图包.api_解码(arg_地图 * 2 + 1)
        self.摆放 = [self._摆放(元数据, 表) for 表 in range(5)]
        self.资源缓存: dict[tuple[bool, int], 精灵资源_类] = {}
        self.帧缓存: dict[tuple[bool, int, int, int], 图像_类] = {}

    def _资源(self, arg_数据包: bool, arg_号: int) -> 精灵资源_类:
        键 = arg_数据包, arg_号
        if 键 in self.资源缓存:
            return self.资源缓存[键]
        数据 = (self.数据包 if arg_数据包 else self.地图包).api_解码(arg_号)
        资源包_类.api_检查范围(0, 12, len(数据))
        签, 数, 偏 = struct.unpack_from("<4sII", 数据)
        if 签 not in (b"SPR\0", b"SMP\0") or 数 > (len(数据) - 12) // 12 or 偏 < 12 + 数 * 12:
            raise ValueError("棋盘精灵资源头或帧表无效")
        资源包_类.api_检查范围(偏, 512 if 签 == b"SPR\0" else 0, len(数据))
        偏 += 512 if 签 == b"SPR\0" else 0
        帧 = []
        for i in range(数):
            大小 = struct.unpack_from("<I", 数据, 12 + i * 12 + 8)[0]
            资源包_类.api_检查范围(偏, 大小, len(数据))
            帧.append(偏)
            偏 += 大小
        资源 = 精灵资源_类(数据, 签 == b"SPR\0", 帧)
        self.资源缓存[键] = 资源
        return 资源

    def _帧(self, arg_数据包: bool, arg_号: int, arg_帧: int, arg_色: int = -1) -> 图像_类:
        键 = arg_数据包, arg_号, arg_帧, arg_色
        if 键 in self.帧缓存:
            return self.帧缓存[键]
        资源 = self._资源(arg_数据包, arg_号)
        if not 0 <= arg_帧 < len(资源.帧偏移):
            raise ValueError("棋盘精灵帧超出原资源")
        图 = 图像_类.api_解码(资源.数据, arg_帧)
        if arg_色 >= 0 and 资源.索引色:
            偏 = 资源.帧偏移[arg_帧]
            for i in range(len(图.像素)):
                if 资源.数据[偏 + i] == 255:
                    图.像素[i] = arg_色 & 0xFFFF
        self.帧缓存[键] = 图
        return 图

    def _设施基数(self) -> int:
        return 0x57 if self.地图 < 4 else 0x68 + (self.地图 - 4) * 17

    def _景物资源(self, arg_号: int) -> int:
        if arg_号 < 5:
            return 0x27 + self.地图 * 5 + arg_号
        if arg_号 == 5:
            return 0x4F + self.地图
        if arg_号 < 23:
            return self._设施基数() + arg_号 - 6
        return 0x19 if arg_号 == 23 else 0x26 + arg_号

    @staticmethod
    def _取框(arg_图: 图像_类, arg_相机: 相机_类) -> tuple[int, int, int, int]:
        棋盘投影_类.api_验证相机(arg_相机)
        if (
            not 0 < arg_图.宽 <= 8192
            or not 0 < arg_图.高 <= 8192
            or len(arg_图.像素) != arg_图.宽 * arg_图.高
        ):
            raise ValueError("棋盘目标画布无效")
        左, 顶, 右, 底 = arg_相机.视口
        return 左, 顶, min(右, arg_图.宽), min(底, arg_图.高)

    @staticmethod
    def _业主色(arg_主: int, arg_场景: 场景_类) -> int:
        if arg_主 == 0:
            return 0
        if arg_主 - 1 < len(arg_场景.业主):
            return arg_场景.业主[arg_主 - 1].颜色
        for 玩家 in arg_场景.玩家:
            if 玩家.槽位 == arg_主 - 1:
                return 玩家.颜色
        return (0x7C00, 0x03E0, 0x001F, 0x7FE0)[(arg_主 - 1) % 4]

    @staticmethod
    def _业主角色(arg_主: int, arg_场景: 场景_类) -> int:
        if arg_主 != 0 and arg_主 - 1 < len(arg_场景.业主):
            return arg_场景.业主[arg_主 - 1].角色
        for 玩家 in arg_场景.玩家:
            if arg_主 != 0 and 玩家.槽位 == arg_主 - 1:
                return 玩家.角色
        return 0

    @staticmethod
    def _覆盖(arg_摆放: 摆放_类, arg_号: int, arg_覆盖: list[地产外观_类]) -> 摆放_类:
        项 = replace(arg_摆放)
        for 态 in arg_覆盖:
            if 态.编号 == arg_号:
                项.业主, 项.等级, 项.类型 = 态.业主, 态.等级, 态.类型
                break
        return 项

    def api_节点位置(self, arg_号: int) -> tuple[int, int] | None:
        return self.摆放[0][arg_号].位置 if 0 < arg_号 < len(self.摆放[0]) else None

    def api_节点数(self) -> int:
        return len(self.摆放[0]) - 1

    def api_地图编号(self) -> int:
        return self.地图

    def api_绘地面(self, arg_目标: 图像_类, arg_相机: 相机_类) -> 绘制统计_类:
        框 = self._取框(arg_目标, arg_相机)
        统计 = 绘制统计_类()
        左, 顶, 右, 底 = 框
        if 右 <= 左 or 底 <= 顶:
            return 统计
        地 = self.地面
        for y in range(顶, 底):
            arg_目标.像素[y * arg_目标.宽 + 左 : y * arg_目标.宽 + 右] = [地.调色板[0]] * (右 - 左)
        中 = 棋盘投影_类.api_屏幕中心(arg_相机)
        偏 = 棋盘投影_类.api_分数偏移(arg_相机.中心, arg_相机.旋转)
        瓦x, 瓦y = arg_相机.中心[0] // 32, arg_相机.中心[1] // 32
        for x, y in 投影表_类.地面次序[arg_相机.旋转]:
            if y == -128:
                break
            点组 = [
                棋盘投影_类.api_格点(a, b, arg_相机)
                for a, b in ((x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1))
            ]
            角 = [
                (
                    ((点[1] + 中[1] + 偏[1] + 32768) & 0xFFFF) - 32768,
                    ((点[0] + 中[0] + 偏[0] + 32768) & 0xFFFF) - 32768,
                )
                for 点 in 点组
            ]
            纹理 = bytes(1024)
            if 0 <= 瓦x + x < 地.宽瓦片 and 0 <= 瓦y + y < 地.高瓦片:
                纹理 = 地.api_瓦片(地.索引[(瓦y + y) * 地.宽瓦片 + 瓦x + x])
            地形_类.api_绘瓦片(arg_目标, 纹理, 地.调色板, 角, 框)
            统计.地面 += 1
        for 项 in self.摆放[0][1:]:
            if 项.精灵 == 0:
                continue
            位置 = 棋盘投影_类.api_投影(项.位置, arg_相机)
            if 位置 is not None:
                arg_目标.api_绘制(self._帧(False, 0x18, 项.精灵 - 1), *位置, 框)
                统计.道路 += 1
        return 统计

    def api_绘制(self, arg_目标: 图像_类, arg_场景: 场景_类, arg_相机: 相机_类) -> 绘制统计_类:
        统计 = self.api_绘地面(arg_目标, arg_相机)
        框 = self._取框(arg_目标, arg_相机)
        for 表, 态组 in ((1, arg_场景.地产), (2, arg_场景.设施)):
            for 态 in 态组:
                if not 态.临时状态 or not 0 < 态.编号 < len(self.摆放[表]):
                    continue
                项 = self.摆放[表][态.编号]
                位置 = 棋盘投影_类.api_投影(项.位置, arg_相机)
                if 位置 is None:
                    continue
                方向 = (8 - ((项.方向 + arg_相机.旋转) & 7)) & 7
                掩码 = self._帧(False, 0x1A, (方向 & 1) + (2 if 表 == 2 else 0))
                色 = 0x003F if 态.临时状态 & 1 else 0x7C00
                左, 顶 = 位置[0] - 掩码.原点x, 位置[1] - 掩码.原点y
                for y in range(max(顶, 框[1]), min(顶 + 掩码.高, 框[3])):
                    for x in range(max(左, 框[0]), min(左 + 掩码.宽, 框[2])):
                        号 = (y - 顶) * 掩码.宽 + x - 左
                        if 掩码.不透明 and 掩码.不透明[号]:
                            arg_目标.像素[y * arg_目标.宽 + x] |= 色
        命令: list[tuple[tuple[int, int], int, 图像_类]] = []

        def 入队(
            arg_世界: tuple[int, int],
            arg_数据: bool,
            arg_资源: int,
            arg_帧: int,
            arg_优先: int = 0,
            arg_色: int = -1,
        ) -> None:
            位置 = 棋盘投影_类.api_投影(arg_世界, arg_相机)
            if 位置 is not None:
                命令.append((位置, arg_优先, self._帧(arg_数据, arg_资源, arg_帧, arg_色)))

        for 玩家 in arg_场景.玩家:
            if not 0 <= 玩家.角色 < 12 or not 0 <= 玩家.方向 <= 7 or not 0 <= 玩家.交通 <= 3:
                raise ValueError("棋盘玩家精灵选择无效")
            资源 = 棋盘投影_类.api_角色资源(玩家)
            每向 = len(self._资源(True, 资源).帧偏移) // 8
            if 每向 == 0:
                raise ValueError("玩家精灵不足八个方向帧")
            方向 = (玩家.方向 + 8 - arg_相机.旋转) & 7
            入队(玩家.位置, True, 资源, 方向 * 每向 + 玩家.动画帧 % 每向, 13 if 玩家.活跃 else 12)
            if 玩家.梦游:
                数 = max(1, len(self._资源(True, 0x19E).帧偏移))
                入队(玩家.位置, True, 0x19E, 玩家.动画帧 % 数, 13 if 玩家.活跃 else 12)
        for 人物 in arg_场景.特殊人物:
            if not 4 <= 人物.槽位 <= 8 or not 0 <= 人物.方向 <= 7:
                raise ValueError("棋盘特殊人物选择无效")
            姿态 = (3 if 人物.走动 else 0) if 人物.梦游 else 2 if 人物.踩水 else int(人物.走动)
            资源 = 0x209 + int(人物.走动) if 人物.槽位 == 8 else 0x16C + 人物.槽位 * 4 + 姿态
            每向 = len(self._资源(True, 资源).帧偏移) // 8
            if 每向 == 0:
                raise ValueError("特殊人物精灵不足八方向")
            方向 = (人物.方向 + 8 - arg_相机.旋转) & 7
            入队(人物.位置, True, 资源, 方向 * 每向 + 人物.动画帧 % 每向, 13 if 人物.活跃 else 12)
            if 人物.梦游 and 人物.槽位 < 8:
                数 = max(1, len(self._资源(True, 0x19E).帧偏移))
                入队(人物.位置, True, 0x19E, 人物.动画帧 % 数, 13 if 人物.活跃 else 12)
        近 = (
            (-10, -22),
            (-22, -10),
            (-22, 10),
            (-10, 22),
            (10, 22),
            (22, 10),
            (22, -10),
            (10, -22),
        )
        远 = (
            (-18, -44),
            (-44, -18),
            (-44, 18),
            (-18, 44),
            (18, 44),
            (44, 18),
            (44, -18),
            (18, -44),
        )
        for 物件 in arg_场景.物件:
            if not 1 <= 物件.种类 <= 20 or not 0 <= 物件.方向 <= 7:
                raise ValueError("棋盘物件精灵选择无效")
            资源 = 0x18C + 物件.种类 - 1
            数 = len(self._资源(True, 资源).帧偏移)
            if 数 == 0:
                raise ValueError("物件精灵无帧")
            方向 = (物件.方向 + 8 - arg_相机.旋转) & 7
            if 物件.跟随:
                位置 = 棋盘投影_类.api_投影(物件.位置, arg_相机)
                if 位置 is not None:
                    偏 = (远 if 物件.跟随 == 2 else 近)[方向]
                    命令.append(
                        (
                            (位置[0] + 偏[0], 位置[1] + 偏[1]),
                            0,
                            self._帧(True, 资源, ((方向 + 4) & 7) % 数),
                        )
                    )
                continue
            帧 = 方向 if 数 >= 8 else 物件.动画帧 % 数
            入队(物件.位置, True, 资源, 帧)
        for 表, 态组 in ((1, arg_场景.地产), (2, arg_场景.设施)):
            for i in range(1, len(self.摆放[表])):
                项 = self._覆盖(self.摆放[表][i], i, 态组)
                if 棋盘投影_类.api_投影(项.位置, arg_相机) is None:
                    continue
                方向 = (8 - ((项.方向 + arg_相机.旋转) & 7)) & 7
                if 项.等级 == 0:
                    if 项.业主 != 0:
                        入队(项.位置, False, 0x19, self._业主角色(项.业主, arg_场景))
                    continue
                if 表 == 1:
                    if 项.等级 > 5:
                        raise ValueError("地产建筑等级超过五")
                    资源 = 0x4F + self.地图 if 项.类型 else 0x27 + self.地图 * 5 + 项.等级 - 1
                else:
                    基 = self._设施基数()
                    if 项.类型 == 0:
                        资源 = 基
                    elif 项.类型 == 1:
                        资源 = 基 + 项.等级
                    elif 项.类型 == 2:
                        资源 = 基 + 5 + 项.等级
                    elif 项.类型 == 3:
                        资源 = 基 + 11
                    elif 项.类型 == 4:
                        资源 = 基 + 11 + 项.等级
                    else:
                        raise ValueError("设施类型超过四")
                    if 资源 >= 基 + 17:
                        raise ValueError("设施等级超过原精灵范围")
                入队(项.位置, False, 资源, 方向, 0, self._业主色(项.业主, arg_场景))
        for 表 in (3, 4):
            for i in range(1, len(self.摆放[表])):
                项 = self._覆盖(self.摆放[表][i], i, arg_场景.公司) if 表 == 3 else self.摆放[表][i]
                if 项.精灵 == 0:
                    continue
                方向 = (8 - ((项.方向 + arg_相机.旋转) & 7)) & 7
                入队(
                    项.位置,
                    False,
                    self._景物资源(项.精灵),
                    方向,
                    0,
                    self._业主色(项.业主, arg_场景) if 表 == 3 else -1,
                )

        def 深度(arg_命令: tuple[tuple[int, int], int, 图像_类]) -> int:
            位 = ((arg_命令[0][1] << 4) & 0xFFF0) | arg_命令[1]
            return 位 - 0x10000 if 位 >= 0x8000 else 位

        命令.sort(key=深度)
        for 位置, _, 图 in 命令:
            arg_目标.api_绘制(图, *位置, 框)
            统计.精灵 += 1
        return 统计
