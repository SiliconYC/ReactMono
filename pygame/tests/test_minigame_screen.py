# ◑ 导入
from test_minigame_presentation import 测试美术_类

from rich4.game_types import 决策_类, 决策种类_类, 小游戏状态_类
from rich4.graphics import 图像_类
from rich4.minigame_screen import 小游戏屏幕_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_同种子不因人物改变而重启且种子改变重启() -> None:
    art = 测试美术_类()
    # 此测试只走时序/原资源命中，MiniGames不调用字体；真实画面另做外部素材差分。
    font = 字体_类.__new__(字体_类)
    frame = 画框_类(图像_类(640, 480, [0] * 307200), art, font, [])
    screen = 小游戏屏幕_类(art)
    decision = 决策_类(决策种类_类.小游戏, 0, 小游戏=小游戏状态_类(1, 0, 123))
    frame.时钟 = 100
    assert screen.api_绘决策(frame, decision) is None
    first = screen._演出
    assert first.逻辑.倒数 == 5
    frame.时钟 += 100
    decision.小游戏.人物 = 11
    screen.api_绘决策(frame, decision)
    assert screen._演出 is first and first.逻辑.倒数 == 4
    assert [b.编号 for b in frame.按钮] == [902]
    decision.小游戏.种子 = 456
    screen.api_绘决策(frame, decision)
    assert screen._演出 is not first and screen._演出.逻辑.倒数 == 5
    screen.api_清空()
    assert not screen.api_活跃()


def test_倒退时钟按uint64封顶且结果在绘决策后清除() -> None:
    from rich4.minigames import 小游戏阶段_类

    art = 测试美术_类()
    frame = 画框_类(图像_类(640, 480, [0] * 307200), art, 字体_类.__new__(字体_类), [])
    screen = 小游戏屏幕_类(art)
    decision = 决策_类(决策种类_类.小游戏, 0, 小游戏=小游戏状态_类(0, 0, 1))
    frame.时钟 = 100
    screen.api_绘决策(frame, decision)
    frame.时钟 = 0
    screen.api_绘决策(frame, decision)
    assert screen._演出.逻辑.倒数 == 9
    screen._演出.逻辑.阶段 = 小游戏阶段_类.完成
    result = screen.api_绘决策(frame, decision)
    assert result is not None and not screen.api_活跃()
