# ◑ 导入
import json
import os
from pathlib import Path

import pytest

from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
@pytest.mark.assets
def test_开放UTF8文字与真实EXE全部导出查询一致() -> None:
    from rich4.open_text import 开放文字_类

    if not all(os.environ.get(n) for n in ("RICH4_TEST_ASSETS", "RICH4_TEST_OPEN_ASSETS")):
        pytest.skip("需显式原素材与开放素材目录")
    source = Path(os.environ["RICH4_TEST_ASSETS"])
    root = Path(os.environ["RICH4_TEST_OPEN_ASSETS"])
    exe = next(p for p in source.iterdir() if p.name.lower() == "rich4.exe")
    expected = 原版文字_类(原版程序_类.api_读取(exe))
    actual = 开放文字_类(root / "text/original.json")
    assert actual.配音 == expected.配音
    assert actual.api_配音(89, 1) == expected.api_配音(89, 1)
    for name, (_, width) in expected.表.items():
        for person in range(12):
            for slot in range(width):
                assert actual.api_台词(name, person, slot) == expected.api_台词(name, person, slot)
    for i in range(len(expected.神明地址)):
        assert actual.api_神明(i) == expected.api_神明(i)
    for i in range(len(expected.股票地址)):
        assert actual.api_股票(i) == expected.api_股票(i)
    for api, count in (("api_费名", 4), ("api_新闻标题", 6), ("api_歌曲", 8)):
        for i in range(count):
            assert getattr(actual, api)(i) == getattr(expected, api)(i)
    metadata = json.loads((root / "text/original.json").read_text())
    for address in metadata["strings"]:
        assert actual.api_原文(int(address)) == expected.api_原文(int(address))
    for address, values in metadata["pointer_tables"].items():
        assert actual.程序.api_指针表(int(address), len(values)) == expected.程序.api_指针表(
            int(address), len(values)
        )
