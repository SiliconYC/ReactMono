# ◑ 导入
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from rich4.application import 游戏应用_类
from rich4.application_types import 应用设置_类, 应用页面_类
from rich4.new_game_types import 新局选择_类
from rich4.world_options import 新玩家_类


# ◕ 功能
@pytest.fixture
def 应用(tmp_path: Path) -> Iterator[游戏应用_类]:
    if not all(os.environ.get(n) for n in ("RICH4_TEST_ASSETS", "RICH4_TEST_FONT")):
        pytest.skip("需显式外部原素材/字体")
    app = 游戏应用_类(
        应用设置_类(
            Path(os.environ["RICH4_TEST_ASSETS"]),
            Path(os.environ["RICH4_TEST_FONT"]),
            tmp_path,
            种子=123,
            日期=(5, 10, 2026),
            静音=True,
        )
    )
    yield app
    app.api_关闭()


@pytest.mark.assets
def test_真实新局安装与开场阻塞不提前推进核心(应用: 游戏应用_类) -> None:
    choice = 新局选择_类(玩家=[新玩家_类(10, 1), 新玩家_类(3, 2), 新玩家_类(0, 2), 新玩家_类(6, 2)])
    assert 应用.api_新局(choice)
    assert 应用.页面 == 应用页面_类.游戏 and 应用.开场.api_活跃()
    before = 应用.会话.世界.api_导出(), 应用.会话.随机.状态
    应用.api_推进(100)
    assert (应用.会话.世界.api_导出(), 应用.会话.随机.状态) == before
    assert 应用.呈现.步骤 and 应用.人类数 == 1


@pytest.mark.assets
def test_坏存档完整保留会话板面及原DAT与RNG恢复(应用: 游戏应用_类, tmp_path: Path) -> None:
    choice = 新局选择_类(玩家=[新玩家_类(10, 1), 新玩家_类(3, 2)])
    assert 应用.api_新局(choice)
    session, board = 应用.会话, 应用.棋盘
    bad = tmp_path / "bad.DAT"
    bad.write_bytes(b"broken")
    assert not 应用.api_读取(bad)
    assert 应用.会话 is session and 应用.棋盘 is board
    path = tmp_path / "Save1.DAT"
    应用.api_写存档(path)
    assert Path(str(path) + ".rng").read_text() == f"RICH4-RNG-1 {session.随机.状态}\n"
    assert 应用.api_读取(path)
    assert 应用.会话 is not session and not 应用.开场.api_活跃()
    assert 应用.会话.世界.api_导出() == session.世界.api_导出()
    assert 应用.会话.随机.状态 == session.随机.状态


@pytest.mark.assets
def test_菜单实际原命中与开场覆盖下层按钮(应用: 游戏应用_类) -> None:
    应用.api_绘制(0)
    assert [b.编号 for b in 应用.按钮] == [1, 2, 3, 5, 4]
    assert not next(b for b in 应用.按钮 if b.编号 == 2).启用
    next(b for b in 应用.按钮 if b.编号 == 1).动作()
    应用.api_绘制(16)
    assert 应用.页面 == 应用页面_类.新局
    assert 应用.api_新局(新局选择_类(玩家=[新玩家_类(10, 1), 新玩家_类(3, 2)]))
    before = 应用.会话.世界.api_导出()
    应用.api_绘制(32)
    assert 应用.开场.api_活跃() and not 应用.按钮
    assert 应用.会话.世界.api_导出() == before


@pytest.mark.assets
def test_同批输入不会重复旧按钮且新局OK释放不跳开场(应用: 游戏应用_类) -> None:
    import pygame

    from rich4.native_frame import 按钮_类

    count = []
    应用.按钮[:] = [按钮_类(1, (0, 0, 640, 480), True, lambda: count.append(1))]
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10))
    应用.api_输入([down, down])
    assert count == [1] and not 应用.按钮
    assert 应用.api_新局(新局选择_类(玩家=[新玩家_类(10, 1), 新玩家_类(3, 2)]))
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(10, 10))
    应用.api_输入([up])
    assert 应用.开场.api_活跃()
    应用.api_输入([down, up])
    assert not 应用.开场.api_活跃()


@pytest.mark.assets
@pytest.mark.parametrize(
    "arg_旁车,arg_种子",
    ((b"RICH4-RNG-1 12\xff", 12), (b"RICH4-RNG-1 -1", 0xFFFFFFFF), (b"\xff", 123)),
)
def test_有效DAT的原流式RNG解析和坏旁车回退(
    应用: 游戏应用_类,
    tmp_path: Path,
    arg_旁车: bytes,
    arg_种子: int,
) -> None:
    assert 应用.api_新局(新局选择_类(玩家=[新玩家_类(10, 1), 新玩家_类(3, 2)]))
    path = tmp_path / "Save1.DAT"
    应用.api_写存档(path)
    Path(str(path) + ".rng").write_bytes(arg_旁车)
    assert 应用.api_读取(path)
    assert 应用.会话.随机.状态 == arg_种子


@pytest.mark.assets
def test_打开窗口失败也关闭真实应用资源(
    应用: 游戏应用_类,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pygame

    from rich4.application_window import 游戏窗口_类

    def 拒绝窗口(size: tuple[int, int], flags: int = 0) -> pygame.Surface:
        raise pygame.error("测试注入的窗口创建失败")

    monkeypatch.setattr(pygame.display, "set_mode", 拒绝窗口)
    with pytest.raises(pygame.error, match="窗口创建失败"):
        游戏窗口_类(应用).api_运行(1)
    assert 应用._已关闭 and 应用.音频._已关闭


@pytest.mark.assets
def test_音频退出报错仍释放字体与窗口(
    应用: 游戏应用_类,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pygame

    from rich4.application_window import 游戏窗口_类

    original = 应用.音频.api_关闭

    def 关闭后报错() -> None:
        original()
        raise OSError("测试注入的音频捕获写出失败")

    pygame.display.quit()
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    try:
        with monkeypatch.context() as local:
            local.setattr(应用.音频, "api_关闭", 关闭后报错)
            with pytest.raises(OSError, match="捕获写出失败"):
                游戏窗口_类(应用).api_运行(1)
        assert not pygame.display.get_init()
        assert not 应用.字体._字面 and 应用.字体._库.value is None
    finally:
        pygame.quit()
