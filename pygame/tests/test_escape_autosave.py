# SPDX-License-Identifier: GPL-3.0-or-later
# 独立于原始商业素材的 ESC 与三代自动恢复点回归测试。
from pathlib import Path
from types import SimpleNamespace

import pygame
import pytest

from rich4.application_actions import 应用操作_类
from rich4.application_input import 应用输入_类
from rich4.application_types import 应用页面_类
from rich4.autosave import 回合自动存档_类
from rich4.save import 存档_类
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
    del app.api_取消  # type: ignore[attr-defined]
    应用操作_类.api_取消(app)
    assert app.页面 == 应用页面_类.游戏


def test_only_window_close_requests_exit() -> None:
    app = 假应用_类(应用页面_类.游戏)
    app.api_输入([pygame.event.Event(pygame.QUIT)])
    assert not app.运行


@pytest.fixture
def manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> 回合自动存档_类:
    def decode(cls: type[存档_类], data: bytes) -> SimpleNamespace:
        if data == b"corrupt":
            raise ValueError("invalid save")
        return SimpleNamespace(api_头=lambda: SimpleNamespace(签名=0x26))

    monkeypatch.setattr(存档_类, "api_解码", classmethod(decode))
    return 回合自动存档_类(tmp_path)


def snapshot(path: Path) -> tuple[bytes, int]:
    return 存档事务_类(path).api_读取(999)


def test_three_autosave_generations_rotate_without_changing_start(manager: 回合自动存档_类) -> None:
    manager.api_初始化(b"start", 11)
    assert [snapshot(p) for p in (manager.开局, manager.上一, manager.当前)] == [
        (b"start", 11)] * 3
    manager.api_轮转(b"turn1", 12, 999)
    assert snapshot(manager.开局) == (b"start", 11)
    assert snapshot(manager.上一) == (b"start", 11)
    assert snapshot(manager.当前) == (b"turn1", 12)
    manager.api_轮转(b"turn2", 13, 999)
    assert snapshot(manager.开局) == (b"start", 11)
    assert snapshot(manager.上一) == (b"turn1", 12)
    assert snapshot(manager.当前) == (b"turn2", 13)
    manager.api_轮转(b"turn3", 14, 999)
    assert snapshot(manager.开局) == (b"start", 11)
    assert snapshot(manager.上一) == (b"turn2", 13)
    assert snapshot(manager.当前) == (b"turn3", 14)


def test_autosave_failed_latest_commit_keeps_valid_history(
    manager: 回合自动存档_类, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager.api_初始化(b"start", 11)
    manager.api_轮转(b"turn1", 12, 999)
    original = 存档事务_类.api_写入

    def interrupted(self: 存档事务_类, data: bytes, seed: int) -> None:
        if self._主文件 == manager.当前 and data == b"turn2":
            raise OSError("simulated write failure")
        original(self, data, seed)

    with monkeypatch.context() as patch:
        patch.setattr(存档事务_类, "api_写入", interrupted)
        with pytest.raises(OSError, match="simulated"):
            manager.api_轮转(b"turn2", 13, 999)
    assert snapshot(manager.开局) == (b"start", 11)
    assert snapshot(manager.当前) == (b"turn1", 12)
    manager.api_轮转(b"turn2", 13, 999)
    assert snapshot(manager.上一) == (b"turn1", 12)
    assert snapshot(manager.当前) == (b"turn2", 13)


def test_corrupt_latest_does_not_poison_previous(
    manager: 回合自动存档_类,
) -> None:
    manager.api_初始化(b"start", 11)
    manager.api_轮转(b"turn1", 12, 999)
    manager.当前.write_bytes(b"corrupt")
    manager.api_轮转(b"turn2", 13, 999)
    assert snapshot(manager.开局) == (b"start", 11)
    assert snapshot(manager.上一) == (b"start", 11)
    assert snapshot(manager.当前) == (b"turn2", 13)


def test_rewind_preserves_game_start(manager: 回合自动存档_类) -> None:
    manager.api_初始化(b"start", 11)
    manager.api_轮转(b"turn1", 12, 999)
    manager.api_回退(b"start", 11)
    assert snapshot(manager.开局) == (b"start", 11)
    assert snapshot(manager.上一) == (b"start", 11)
    assert snapshot(manager.当前) == (b"start", 11)
