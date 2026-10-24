# ◑ 导入
import os
from pathlib import Path

import pytest

from rich4.artwork import 美术_类
from rich4.terrain import 地面_类


# ◕ 功能
@pytest.mark.assets
def test_开放美术图片动画地形与命中掩码使用真实转换素材() -> None:
    if not all(os.environ.get(n) for n in ("RICH4_TEST_ASSETS", "RICH4_TEST_OPEN_ASSETS")):
        pytest.skip("需显式原素材与开放素材")
    expected = 美术_类(Path(os.environ["RICH4_TEST_ASSETS"]))
    actual = 美术_类(Path(os.environ["RICH4_TEST_OPEN_ASSETS"]))
    for key, entry, frame in (("p", 80, 0), ("d", 413, 4), ("m", 27, 1)):
        assert actual.api_帧(key, entry, frame) == expected.api_帧(key, entry, frame)
        assert actual.api_帧数(key, entry) == expected.api_帧数(key, entry)
    for key, entry, width, height in (("d", 601, 640, 480), ("j", 0, 640, 480)):
        assert actual.api_原图(key, entry, width, height) == expected.api_原图(
            key, entry, width, height
        )
    for entry in (8, 19, 81):
        assert actual.api_解码("p", entry) == expected.api_解码("p", entry)
    for entry in range(0, 16, 2):
        assert actual.api_地面(entry) == 地面_类.api_解码(expected.api_解码("m", entry))
    for key, entry in (("p", 78), ("d", 556)):
        one, two = actual.api_动画(key, entry), expected.api_动画(key, entry)
        assert (one.帧数, one.间隔毫秒) == (two.帧数, two.间隔毫秒)
        while two.api_下一帧():
            assert one.api_下一帧() and one.api_图像() == two.api_图像()
        assert not one.api_下一帧()
