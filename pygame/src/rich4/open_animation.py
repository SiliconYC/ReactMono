# SPDX-License-Identifier: GPL-3.0-or-later
# 普通PNG帧序列实现既有动画契约；不解码或合成原FLC数据。
# ◑ 导入

from rich4.flc import 动画_类
from rich4.graphics import 图像_类
from rich4.open_archive import 开放档案_类


# ◕ 功能
class PNG动画_类(动画_类):
    """
    保留已解帧/间隔/倒带和末帧语义，逐帧读取项目内PNG。

    更新日志：
    2026.10.24 - 继承仅用于统一动画公开契约；不调用旧FLC构造器或私有解码。
    """

    def __init__(self, arg_档案: 开放档案_类, arg_条: int) -> None:
        data = arg_档案.api_元数据(arg_条)
        if data["kind"] != "animation":
            raise ValueError("资源不是PNG动画序列")
        self._档案, self._条 = arg_档案, arg_条
        self.宽, self.高 = data["width"], data["height"]
        self.帧数, self.间隔毫秒 = len(data["frames"]), data["interval_ms"]
        if not 0 < self.宽 <= 4096 or not 0 < self.高 <= 4096 or self.间隔毫秒 < 0:
            raise ValueError("PNG动画尺寸或间隔越界")
        self.api_倒带()

    def api_倒带(self) -> None:
        self.已解帧 = 0
        self._当前 = 图像_类(
            self.宽, self.高, [0] * (self.宽 * self.高), 不透明=bytes(self.宽 * self.高)
        )

    def api_下一帧(self) -> bool:
        if self.已解帧 >= self.帧数:
            return False
        image = self._档案.api_帧(self._条, self.已解帧)
        if (image.宽, image.高) != (self.宽, self.高):
            raise ValueError("PNG动画帧尺寸与序列不符")
        self._当前 = image
        self.已解帧 += 1
        return True

    def api_图像(self) -> 图像_类:
        image = self._当前
        return 图像_类(
            image.宽, image.高, image.像素.copy(), image.原点x, image.原点y, image.不透明
        )
