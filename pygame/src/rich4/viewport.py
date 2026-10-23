# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from dataclasses import dataclass, field


# ◕ 功能
@dataclass
class 视口_类:
    """
    640×480 逻辑画布等比留边；画布外输入保持无效。

    更新日志：
    2026.10.23 - 建立显示和输入共同使用的坐标变换。
    """

    窗宽: int
    窗高: int
    矩形: tuple[int, int, int, int] = field(init=False)

    def __post_init__(self) -> None:
        if self.窗宽 <= 0 or self.窗高 <= 0:
            raise ValueError("窗口尺寸必须为正")
        比例 = min(self.窗宽 / 640, self.窗高 / 480)
        宽 = max(1, int(640 * 比例))
        高 = max(1, int(480 * 比例))
        self.矩形 = ((self.窗宽 - 宽) // 2, (self.窗高 - 高) // 2, 宽, 高)

    def api_逻辑位置(self, arg_位置: tuple[int, int]) -> tuple[int, int] | None:
        左, 顶, 宽, 高 = self.矩形
        x, y = arg_位置
        if not 左 <= x < 左 + 宽 or not 顶 <= y < 顶 + 高:
            return None
        return ((x - 左) * 640 // 宽, (y - 顶) * 480 // 高)
