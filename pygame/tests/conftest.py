# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from rich4.native_ui import 字体_类
from rich4.save import 存档_类
from rich4.save_random import 随机旁车_类
from rich4.world import 世界_类


# ◕ 功能
@pytest.fixture
def 自然存档() -> tuple[tuple[bytes, int], tuple[bytes, int]]:
    value = os.environ.get("RICH4_TEST_NATURAL_SAVES")
    if not value:
        pytest.skip("需显式合法自然对局存档目录")
    root = Path(value)
    pairs = []
    for name in ("Save1.DAT", "Autosave.DAT"):
        data = (root / name).read_bytes()
        世界_类.api_从存档(存档_类.api_解码(data))
        seed = 随机旁车_类.api_解码((root / (name + ".rng")).read_bytes(), 0)
        pairs.append((data, seed))
    assert pairs[0][0] != pairs[1][0] and pairs[0][1] != pairs[1][1]
    return pairs[0], pairs[1]


@pytest.fixture
def 字体() -> Iterator[字体_类]:
    for 路 in (
        os.environ.get("RICH4_TEST_FONT", ""),
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if Path(路).is_file():
            字 = 字体_类(Path(路))
            yield 字
            字.api_关闭()
            return
    pytest.skip("本机没有字体夹具；像素差分可显式传入外部字体")
