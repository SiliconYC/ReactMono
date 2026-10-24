# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_flc import 影片
from test_message_overlay import 消息素材夹具_类

from rich4.graphics import 图像_类
from rich4.intro_player import 开局演出_类


# ◕ 功能
class 开局素材夹具_类(消息素材夹具_类):
    """
    合成开场时间线夹具，不提供正式替代素材。

    更新日志：
    2026.10.24 - 五帧70毫秒影片验证首帧完整显示与跨镜头超时传递。
    """

    def api_解码(self, arg_库: str, arg_条: int) -> bytes:
        return 影片() if arg_库 == "j" and arg_条 >= 46 else bytes(640 * 480 * 2)


def test_首帧不消耗时间随后钳制一百毫秒且余量传给真实下一影片() -> None:
    s, sounds = 开局演出_类(开局素材夹具_类()), []
    c = 图像_类(640, 480, [9] * 307200)
    s.api_开始([0])
    s.api_绘制(c, 9999, sounds.append)
    assert s._索引 == 0 and s._已过 == 0
    for _ in range(4):
        s.api_绘制(c, 9999, sounds.append)
    assert s._索引 == 1 and s._已过 == 0 and sounds == [25]
    for _ in range(4):
        s.api_绘制(c, 100, sounds.append)
    assert s._索引 == 2 and s._已过 == 50 and s._电影.已解帧 == 1
    s.api_跳过()
    s.api_绘制(c, 100, sounds.append)
    assert not s.api_活跃() and s._电影 is None and sounds == [25]


def test_开始重置镜头但保留原旧帧直到开始下一镜且等待者原图不被暗化() -> None:
    art = 开局素材夹具_类()
    s = 开局演出_类(art)
    s.api_开始([0, 1, 2, 255])
    assert len(s._镜头) == 10
    assert [shot.影片 for shot in s._镜头] == [-1, 46, 47, 48, 49, 50, 59, 60, 61, 62]
    assert art.api_帧("j", 45, 4).像素[0] == 104
    s.api_开始([])
    assert len(s._镜头) == 2 and not s._已开始
