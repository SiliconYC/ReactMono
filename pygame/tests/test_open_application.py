# ◑ 导入
import os
from pathlib import Path

import pytest

from rich4.application import 游戏应用_类
from rich4.application_types import 应用设置_类
from rich4.new_game_types import 新局选择_类
from rich4.world_options import 新玩家_类


# ◕ 功能
@pytest.mark.assets
def test_真实主应用使用项目内PNG和文字而不需要MKF或EXE(tmp_path: Path) -> None:
    if not all(os.environ.get(n) for n in ("RICH4_TEST_ASSETS", "RICH4_TEST_OPEN_ASSETS")):
        pytest.skip("需显式原素材与开放素材")
    source = Path(os.environ["RICH4_TEST_ASSETS"])
    root = Path(os.environ["RICH4_TEST_OPEN_ASSETS"])
    font = root / "fonts/ui.ttc"
    assert not list(root.rglob("*.mkf")) and not list(root.rglob("*.exe"))
    actual = 游戏应用_类(
        应用设置_类(root, font, tmp_path / "open", 种子=123, 日期=(5, 10, 2026), 静音=True)
    )
    try:
        expected = 游戏应用_类(
            应用设置_类(
                source, font, tmp_path / "original", 种子=123, 日期=(5, 10, 2026), 静音=True
            )
        )
        try:
            assert actual.api_绘制(0) == expected.api_绘制(0)
            choice = 新局选择_类(玩家=[新玩家_类(10, 1), 新玩家_类(3, 2)])
            assert actual.api_新局(choice) and expected.api_新局(choice)
            assert actual.会话.世界.api_导出() == expected.会话.世界.api_导出()
            assert actual.api_绘制(100) == expected.api_绘制(100)
        finally:
            expected.api_关闭()
    finally:
        actual.api_关闭()


@pytest.mark.assets
def test_正式入口由开放目录自动选用项目内字体(tmp_path: Path) -> None:
    import subprocess
    import sys

    if not os.environ.get("RICH4_TEST_OPEN_ASSETS"):
        pytest.skip("需显式开放素材目录")
    root = Path(os.environ["RICH4_TEST_OPEN_ASSETS"])
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rich4.game_cli",
            "--assets",
            str(root),
            "--save-dir",
            str(tmp_path),
            "--headless",
            "--silent",
            "--frames",
            "2",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.assets
def test_项目内运行库与音库无需外部环境变量即可发声启动(tmp_path: Path) -> None:
    import subprocess
    import sys

    if not os.environ.get("RICH4_TEST_OPEN_ASSETS"):
        pytest.skip("需显式开放素材目录和本地运行库")
    root = Path(os.environ["RICH4_TEST_OPEN_ASSETS"])
    env = dict(os.environ)
    for name in ("RICH4_SDL3_LIBRARY", "RICH4_FLUIDSYNTH_LIBRARY", "RICH4_SOUNDFONT"):
        env.pop(name, None)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rich4.game_cli",
            "--assets",
            str(root),
            "--save-dir",
            str(tmp_path),
            "--headless",
            "--frames",
            "2",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[警告] 背景音乐不可用" not in result.stdout
