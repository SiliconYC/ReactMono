# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from collections.abc import Iterator
from pathlib import Path

import pytest

from rich4.native_ui import 字体_类


# ◕ 功能
@pytest.fixture
def 字体() -> Iterator[字体_类]:
    for 路 in (
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
