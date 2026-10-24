# SPDX-License-Identifier: GPL-3.0-or-later
# 原Options种子是uint32；菜单、规则和结局必须共用同一归一化值。
# ◑ 导入
from pathlib import Path

import pytest

from rich4.application_types import 应用设置_类


# ◕ 功能
@pytest.mark.parametrize("arg_值,arg_预期", ((-1, 0xFFFFFFFF), (0x100000001, 1), (0, 0)))
def test_种子保留原无符号32位字段(arg_值: int, arg_预期: int) -> None:
    设置 = 应用设置_类(Path("assets"), Path("font"), Path("saves"), 种子=arg_值)
    assert 设置.种子 == arg_预期
