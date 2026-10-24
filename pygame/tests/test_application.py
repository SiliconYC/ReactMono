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
