# SPDX-License-Identifier: GPL-3.0-or-later
# 独立于商业素材的 ESC 和整轮单份自动存档回归测试。
from pathlib import Path
from types import SimpleNamespace

import pygame
import pytest

from rich4.application import 游戏应用_类
from rich4.application_actions import 应用操作_类
from rich4.application_input import 应用输入_类
from rich4.application_types import 应用页面_类
from rich4.game_types import 游戏阶段_类
from rich4.save_transaction import 存档事务_类


class 假应用_类(应用输入_类, 应用操作_类):
    def __init__(self, page: 应用页面_类) -> None:
        self.页面 = page
        self.前页面 = 应用页面_类.菜单
        self.会话 = object()
        self.运行 = True
        self.按钮 = []
        self.开场 = SimpleNamespace(api_活跃=lambda: False)
        self.消息 = SimpleNamespace(api_活跃=lambda: False)
        self.数字板 = SimpleNamespace(api_活跃=lambda: False)
        self.帮助 = SimpleNamespace(api_活跃=lambda: False)
        self.新局 = SimpleNamespace(api_取消=lambda host, action: action())
        self.取消次数 = 0

    def api_宿主(self) -> None:
        return None

    def api_页面(self, page: 应用页面_类) -> None:
        self.页面 = page

    def api_可取消(self) -> bool:
        return self.页面 != 应用页面_类.游戏

    def api_取消(self) -> None:
        self.取消次数 += 1
        self.页面 = self.api_返回页面()


@pytest.mark.parametrize(
    "page",
    [应用页面_类.游戏, 应用页面_类.设置, 应用页面_类.新局,
     应用页面_类.读取, 应用页面_类.保存],
)
def test_escape_cannot_abandon_active_session(page: 应用页面_类) -> None:
    app = 假应用_类(page)
    before = app.会话
    events = [pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}) for _ in range(3)]
    app.api_输入(events)
    assert app.页面 == 应用页面_类.游戏
    assert app.会话 is before
    assert app.运行
    assert app.取消次数 == (0 if page == 应用页面_类.游戏 else 1)


def test_cancel_new_game_dialog_returns_to_existing_session() -> None:
    app = 假应用_类(应用页面_类.新局)
    # 这里真实调用取消分派（上一页面即使是菜单也必须返回活跃对局）。
    应用操作_类.api_取消(app)
    assert app.页面 == 应用页面_类.游戏


def test_only_window_close_requests_exit() -> None:
    app = 假应用_类(应用页面_类.游戏)
    app.api_输入([pygame.event.Event(pygame.QUIT)])
    assert not app.运行


@pytest.fixture
def 回合应用(tmp_path: Path) -> SimpleNamespace:
    state = {"ready": True, "payload": b"round-4", "warnings": []}
    world = SimpleNamespace(轮数=4, 头=SimpleNamespace(当前玩家=0))
    session = SimpleNamespace(
        世界=world,
        阶段=游戏阶段_类.人类待命,
        随机=SimpleNamespace(状态=100),
        api_可保存=lambda: state["ready"],
        api_导出存档=lambda: SimpleNamespace(api_导出=lambda: state["payload"]),
    )
    app = SimpleNamespace(
        会话=session,
        设置=SimpleNamespace(存档目录=tmp_path, 验证天数=0, 种子=99),
        上保存轮=None,
        _自动存档首存=True,
        _自动存档错误轮=None,
        api_提示=lambda *args: state["warnings"].append(args),
    )
    app.api_槽路径 = lambda slot: 游戏应用_类.api_槽路径(app, slot)
    app.api_写存档 = lambda path: 存档事务_类(path).api_写入(
        session.api_导出存档().api_导出(), session.随机.状态
    )
    app.state = state
    return app


def 读取恢复点(app: SimpleNamespace) -> tuple[bytes, int]:
    return 存档事务_类(app.api_槽路径(0)).api_读取(99)


def test_single_autosave_on_first_stable_turn_before_dice(回合应用: SimpleNamespace) -> None:
    app = 回合应用
    app.state["ready"] = False
    游戏应用_类.api_检查自动存档(app)
    assert not app.api_槽路径(0).exists()
    app.state["ready"] = True
    游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app) == (b"round-4", 100)
    assert app.上保存轮 == 4 and not app._自动存档首存


def test_players_and_ui_within_one_round_never_overwrite(回合应用: SimpleNamespace) -> None:
    app = 回合应用
    游戏应用_类.api_检查自动存档(app)
    app.state["payload"] = b"unsaved-mid-round"
    app.会话.随机.状态 = 122
    for player in (1, 2, 3, 0):
        app.会话.世界.头.当前玩家 = player
        游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app) == (b"round-4", 100)


def test_round_boundary_written_once_before_new_roll(回合应用: SimpleNamespace) -> None:
    app = 回合应用
    游戏应用_类.api_检查自动存档(app)
    # 核心规则已完成全体玩家及跨轮日期结算，轮数真实递增。
    app.会话.世界.轮数 += 1
    app.会话.世界.头.当前玩家 = 0
    app.state["ready"] = False
    app.state["payload"] = b"unsettled"
    游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app) == (b"round-4", 100)
    app.state["ready"] = True
    app.state["payload"] = b"round-5-pre-dice"
    app.会话.随机.状态 = 130
    游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app) == (b"round-5-pre-dice", 130)
    app.state["payload"] = b"after-roll"
    游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app) == (b"round-5-pre-dice", 130)


def test_eliminated_or_skipped_first_player_does_not_block_new_round(
    回合应用: SimpleNamespace,
) -> None:
    app = 回合应用
    游戏应用_类.api_检查自动存档(app)
    # 玩家 0 已淘汰/跳过；核心在玩家 2 开启新轮，不能要求当前玩家为零。
    app.会话.世界.轮数 = 5
    app.会话.世界.头.当前玩家 = 2
    app.state["payload"] = b"round-5-first-active-player-2"
    游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app)[0] == b"round-5-first-active-player-2"
    app.会话.世界.头.当前玩家 = 3
    app.state["payload"] = b"same-round"
    游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app)[0] == b"round-5-first-active-player-2"


def test_failed_autosave_keeps_old_checkpoint_and_retries(
    回合应用: SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = 回合应用
    游戏应用_类.api_检查自动存档(app)
    app.会话.世界.轮数 = 5
    app.state["payload"] = b"new-round"
    original = 存档事务_类.api_写入

    def reject(self: 存档事务_类, data: bytes, seed: int) -> None:
        if data == b"new-round":
            raise OSError("injected save failure")
        original(self, data, seed)

    with monkeypatch.context() as patch:
        patch.setattr(存档事务_类, "api_写入", reject)
        游戏应用_类.api_检查自动存档(app)
        游戏应用_类.api_检查自动存档(app)
    assert len(app.state["warnings"]) == 1
    assert app.上保存轮 == 4
    assert 读取恢复点(app) == (b"round-4", 100)
    游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app) == (b"new-round", 100)
    assert app.上保存轮 == 5


def test_unconnected_old_three_generation_files_are_not_touched(
    回合应用: SimpleNamespace,
) -> None:
    app = 回合应用
    for name in ("Autosave.Start.DAT", "Autosave.Previous.DAT"):
        path = app.设置.存档目录 / name
        path.write_bytes(b"user-existing-data")
    游戏应用_类.api_检查自动存档(app)
    app.会话.世界.轮数 += 1
    游戏应用_类.api_检查自动存档(app)
    for name in ("Autosave.Start.DAT", "Autosave.Previous.DAT"):
        assert (app.设置.存档目录 / name).read_bytes() == b"user-existing-data"
    assert len(list(app.设置.存档目录.glob("Autosave*.DAT"))) == 3


def test_save_slot_paths_are_unchanged_except_retired_extra_slots(
    回合应用: SimpleNamespace,
) -> None:
    app = 回合应用
    assert app.api_槽路径(0).name == "Autosave.DAT"
    assert [app.api_槽路径(i).name for i in range(1, 6)] == [
        f"Save{i}.DAT" for i in range(1, 6)
    ]
    with pytest.raises(ValueError):
        app.api_槽路径(6)


def test_disabled_validation_mode_does_not_write(回合应用: SimpleNamespace) -> None:
    app = 回合应用
    app.设置.验证天数 = 10
    游戏应用_类.api_检查自动存档(app)
    assert not app.api_槽路径(0).exists()


def test_game_over_or_intermediate_stage_never_overwrites_round_autosave(
    回合应用: SimpleNamespace,
) -> None:
    app = 回合应用
    游戏应用_类.api_检查自动存档(app)
    app.会话.世界.轮数 = 5
    app.state["payload"] = b"not-pre-roll"
    for stage in (游戏阶段_类.结束, 游戏阶段_类.推进回合):
        app.会话.阶段 = stage
        游戏应用_类.api_检查自动存档(app)
    assert 读取恢复点(app)[0] == b"round-4"
