# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_flc import 影片

from rich4.flc import 动画_类
from rich4.graphics import 图像_类
from rich4.minigame_presentation import 小游戏演出_类
from rich4.minigames import 小游戏种类_类, 小游戏阶段_类


# ◕ 功能
class 测试美术_类:
    """
    合成绘图资源仅供时钟/锚点/输入测试，真实像素另与外部素材差分。

    更新日志：
    2026.10.23 - 不向正式资源路径提供代用品。
    """

    def api_帧(self, arg_库: str, arg_条: int, arg_帧: int) -> 图像_类:
        if arg_帧 == 0 and arg_条 in (80, 91):
            return 图像_类(640, 480, [5] * (640 * 480))
        return 图像_类(2, 2, [1 + arg_帧] * 4)

    def api_帧数(self, arg_库: str, arg_条: int) -> int:
        return 25

    def api_解码(self, arg_库: str, arg_条: int) -> bytes:
        return bytes(640 * 480) if arg_条 == 81 else 影片()

    def api_动画(self, arg_库: str, arg_条: int) -> 动画_类:
        return 动画_类(self.api_解码(arg_库, arg_条))

    def api_原图(self, arg_库: str, arg_条: int, arg_宽: int, arg_高: int) -> 图像_类:
        return 图像_类(arg_宽, arg_高, [6] * (arg_宽 * arg_高))


def test_缩放锚点不随倍率变化并保留透明像素() -> None:
    画 = 图像_类(640, 480, [9] * (640 * 480))
    图 = 图像_类(2, 1, [0, 12], 1, 0, bytes([0, 1]))
    小游戏演出_类._缩放(画, 图, 10, 10, 131072)
    assert 画.像素[10 * 640 + 9 : 10 * 640 + 13] == [9, 9, 12, 12]
    assert 画.像素[11 * 640 + 9 : 11 * 640 + 13] == [9, 9, 12, 12]


def test_真实间隔上限和准备片阻塞() -> None:
    演 = 小游戏演出_类(测试美术_类(), 小游戏种类_类.企鹅, 1)
    演.api_帧(10000)
    assert 演.逻辑.倒数 == 9
    for _ in range(9):
        演.api_帧(100)
    assert 演.逻辑.阶段 == 小游戏阶段_类.准备
    assert 演.准备片 is None
    演.api_帧(0)
    assert 演.准备片 is not None and 演.逻辑.剩余帧 == 150
    for _ in range(5):
        演.api_帧(70)
    assert 演.准备片 is None and 演.逻辑.阶段 == 小游戏阶段_类.游玩
    assert 演.逻辑.剩余帧 == 150


def test_命中图外按原椭圆距离找最近格() -> None:
    演 = 小游戏演出_类(测试美术_类(), 小游戏种类_类.企鹅, 1)
    演.逻辑.阶段 = 小游戏阶段_类.游玩
    演.api_点击(320, 121)
    assert (演.逻辑.目标x >> 16, 演.逻辑.目标y >> 16) == (6, 2)
    演.api_点击(-500, -500)
    assert (演.逻辑.目标x >> 16, 演.逻辑.目标y >> 16) == (6, 2)


def test_盖章背景独立于缓存帧且完成结果只提交一次() -> None:
    演 = 小游戏演出_类(测试美术_类(), 小游戏种类_类.企鹅, 1)
    演.逻辑.洞.append((10, 10))
    演.api_帧(0)
    assert 演.背景.像素[10 * 640 + 10] == 10
    assert 演.美术.api_帧("p", 80, 0).像素[10 * 640 + 10] == 5
    演.逻辑.阶段 = 小游戏阶段_类.完成
    _, 果 = 演.api_帧(0)
    assert 果 is not None and 果.分数 == 0 and 果.随机次数 == 28
    assert 演.api_帧(0)[1] is None
