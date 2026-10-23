# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/board_renderer.cpp::project/unproject/player_resource。
# ◑ 导入
from rich4.board_models import 玩家精灵_类, 相机_类
from rich4.projection_tables import 投影表_类


# ◕ 功能
class 棋盘投影_类:
    """
    原29×29离散投影查表和逐瓦片最近中心反投影，保留分别向下取整。

    更新日志：
    2026.10.23 - 对应投影辅助函数和角色资源选择，不使用浮点矩阵替代。
    """

    @staticmethod
    def api_验证相机(arg_相机: 相机_类) -> None:
        if not 0 <= arg_相机.旋转 <= 7:
            raise ValueError("棋盘旋转必须为0..7")
        左, 顶, 右, 底 = arg_相机.视口
        if 左 < 0 or 顶 < 0 or 右 <= 左 or 底 <= 顶 or 右 > 8192 or 底 > 8192:
            raise ValueError("棋盘视口必须为8192像素内的正矩形")

    @staticmethod
    def api_屏幕中心(arg_相机: 相机_类) -> tuple[int, int]:
        左, 顶, 右, 底 = arg_相机.视口
        return (左 + 右) // 2, (顶 + 底) // 2

    @staticmethod
    def api_分数偏移(arg_点: tuple[int, int], arg_旋转: int) -> tuple[int, int]:
        基 = 投影表_类.分数基底[arg_旋转]
        x, y = arg_点[0] & 31, arg_点[1] & 31
        return 基[0] * x // 32 + 基[2] * y // 32, 基[1] * x // 32 + 基[3] * y // 32

    @staticmethod
    def api_格点(arg_x: int, arg_y: int, arg_相机: 相机_类) -> tuple[int, int]:
        return 投影表_类.相机网格[arg_相机.旋转][(arg_y + 14) * 29 + arg_x + 14]

    @classmethod
    def api_投影(cls, arg_点: tuple[int, int], arg_相机: 相机_类) -> tuple[int, int] | None:
        cls.api_验证相机(arg_相机)
        x, y = arg_点[0] // 32 - arg_相机.中心[0] // 32, arg_点[1] // 32 - arg_相机.中心[1] // 32
        if not -14 <= x <= 14 or not -14 <= y <= 14:
            return None
        格 = cls.api_格点(x, y, arg_相机)
        中 = cls.api_屏幕中心(arg_相机)
        相机偏 = cls.api_分数偏移(arg_相机.中心, arg_相机.旋转)
        世界偏 = cls.api_分数偏移(arg_点, arg_相机.旋转)
        return 中[0] + 格[0] + 相机偏[0] - 世界偏[0], 中[1] + 格[1] + 相机偏[1] - 世界偏[1]

    @classmethod
    def api_反投影(cls, arg_屏幕: tuple[int, int], arg_相机: 相机_类) -> tuple[int, int] | None:
        cls.api_验证相机(arg_相机)
        左, 顶, 右, 底 = arg_相机.视口
        if not 左 <= arg_屏幕[0] < 右 or not 顶 <= arg_屏幕[1] < 底:
            return None
        x, y = arg_相机.中心[0] // 32, arg_相机.中心[1] // 32
        最佳: tuple[int, int] | None = None
        最短 = 0
        for dy in range(-14, 15):
            for dx in range(-14, 15):
                世界 = (x + dx) * 32 + 16, (y + dy) * 32 + 16
                投影 = cls.api_投影(世界, arg_相机)
                if 投影 is None:
                    continue
                距离 = (投影[0] - arg_屏幕[0]) ** 2 + (投影[1] - arg_屏幕[1]) ** 2
                if 最佳 is None or 距离 < 最短:
                    最佳, 最短 = 世界, 距离
        return 最佳

    @staticmethod
    def api_角色资源(arg_玩家: 玩家精灵_类) -> int:
        if not 0 <= arg_玩家.角色 < 12 or not 0 <= arg_玩家.交通 <= 3:
            raise ValueError("棋盘角色或交通无效")
        行动 = 2 if arg_玩家.投骰 else int(arg_玩家.走动)
        if arg_玩家.特殊姿态 and not arg_玩家.投骰:
            姿态 = arg_玩家.特殊姿态
        elif arg_玩家.受伤:
            姿态 = 18
        elif arg_玩家.梦游:
            姿态 = 2 if arg_玩家.投骰 else 16 + 行动
        elif arg_玩家.踩水:
            姿态 = 13 + 行动
        else:
            姿态 = arg_玩家.交通 * 3 + 行动
        return 0x80 + arg_玩家.角色 * 21 + 姿态
