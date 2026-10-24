# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from copy import deepcopy
from pathlib import Path

import pytest
from test_flc import 影片
from test_game import 会话样本

from rich4.artwork import 美术_类
from rich4.board_models import 场景_类, 相机_类, 绘制统计_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.effect_player import 电影播放_类
from rich4.game_types import 效果_类, 效果点_类, 效果种类_类
from rich4.graphics import 图像_类


# ◕ 功能
class 电影夹具_类(美术_类):
    """
    单元时钟测试的合成五帧FLC；真实画面另与原CPP/外部素材比较。

    更新日志：
    2026.10.24 - 只在测试中注入，正式美术路径没有替代图。
    """

    def __init__(self, arg_坏片: bool = False) -> None:
        super().__init__(Path("unused-test-assets"))
        self.坏片 = arg_坏片

    def api_解码(self, arg_库: str, arg_条: int) -> bytes:
        return b"broken" if self.坏片 else 影片()


class 场景观察_类(棋盘绘制_类):
    """
    只观察播放器传入的完整场景，不能用于像素或窗口验收。

    更新日志：
    2026.10.24 - 不替代正式棋盘渲染器。
    """

    def __init__(self) -> None:
        self.场景: list[场景_类] = []

    def api_绘制(self, arg_目标: 图像_类, arg_场景: 场景_类, arg_相机: 相机_类) -> 绘制统计_类:
        self.场景.append(deepcopy(arg_场景))
        return 绘制统计_类()


def test_效果按值入队且忽略专属屏幕类并正确查询待落地抛物() -> None:
    会, 播 = 会话样本(), 电影播放_类(美术_类(Path("unused")))
    e = 效果_类(效果种类_类.抛物, 目标=效果点_类(32, 64), 物件种类=16)
    播.api_入队([效果_类(效果种类_类.暂停), e, 效果_类(效果种类_类.轮盘)], 会)
    e.目标 = 效果点_类(999, 64)
    assert 播.api_活跃() and 播.api_抛物待落地((32, 64), 16)
    assert not 播.api_抛物待落地((999, 64), 16)
    assert len(播._队列) == 1


def test_切换所有者清空旧快照与队列而跳过标志不追溯清空已入队电影() -> None:
    a, b, 播 = 会话样本(), 会话样本(), 电影播放_类(电影夹具_类())
    播.api_记忆(a.世界, a, 0)
    播.api_入队([效果_类(效果种类_类.爆炸)], a)
    播.api_跳过(True)
    assert 播.api_活跃()
    播.api_入队([效果_类(效果种类_类.爆炸)], b)
    assert not 播.api_活跃() and 播._快照 is None


def test_首帧完整显示并逐次钳制100毫秒且声音只触发一次() -> None:
    会, 播, 板, 声 = 会话样本(), 电影播放_类(电影夹具_类()), 场景观察_类(), []
    画 = 图像_类(640, 480, [0] * 307200)
    播.api_入队([效果_类(效果种类_类.顶楼闪光)], 会)
    播.api_绘制(画, 板, 会.世界, 0, 9999, 0, 声.append)
    assert 播._当前.已过 == 0 and 播._当前.影片.已解帧 == 1
    播.api_绘制(画, 板, 会.世界, 0, 9999, 100, 声.append)
    assert 播._当前.已过 == 100 and 播._当前.影片.已解帧 == 2 and 声 == [90]
    for t in (200, 300, 400):
        播.api_绘制(画, 板, 会.世界, 0, 100, t, 声.append)
    assert not 播.api_活跃() and len(板.场景) == 4 and 声 == [90]


def test_提交帧之前保留旧房屋之后显示真实世界并释放快照() -> None:
    会, 播, 板 = 会话样本(), 电影播放_类(电影夹具_类()), 场景观察_类()
    会.世界.地产[1].经济.等级 = 2
    播.api_记忆(会.世界, 会, 0)
    会.世界.地产[1].经济.等级 = 0
    播.api_入队([效果_类(效果种类_类.爆炸)], 会)
    画 = 图像_类(640, 480, [0] * 307200)
    for t in (0, 100, 200):
        播.api_绘制(画, 板, 会.世界, 0, 100, t)
        assert 板.场景[-1].地产[0].等级 == 2
    播.api_绘制(画, 板, 会.世界, 0, 100, 300)
    assert 板.场景[-1].地产[0].等级 == 0 and 播._快照 is None


def test_神明影片结束保留末帧直到下一电影或显式丢弃() -> None:
    会, 播, 板 = 会话样本(), 电影播放_类(电影夹具_类()), 场景观察_类()
    画 = 图像_类(640, 480, [0] * 307200)
    播.api_入队([效果_类(效果种类_类.神明出现, 物件种类=1)], 会)
    for t in range(5):
        播.api_绘制(画, 板, 会.世界, 0, 100, t * 100)
    assert 播.api_保留中() and not 播.api_活跃()
    播.api_丢弃末帧()
    assert not 播.api_保留中()


def test_损坏电影仅清当前并记录明确故障而不修改规则世界(caplog: pytest.LogCaptureFixture) -> None:
    会, 播, 板 = 会话样本(), 电影播放_类(电影夹具_类(True)), 场景观察_类()
    原 = 会.世界.api_导出()
    播.api_入队([效果_类(效果种类_类.爆炸)], 会)
    播.api_绘制(图像_类(640, 480, [0] * 307200), 板, 会.世界, 0, 0, 0)
    assert not 播.api_活跃() and 会.世界.api_导出() == 原
    assert "跳过损坏效果" in caplog.text
