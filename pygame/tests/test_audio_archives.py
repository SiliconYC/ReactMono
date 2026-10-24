# ◑ 导入
from pathlib import Path

import pytest

from rich4.audio_archives import 音频档案_类


# ◕ 功能
def test_缺资源延后到首次使用且每次重新报同一错误(tmp_path: Path) -> None:
    loader = 音频档案_类(tmp_path)
    try:
        messages = []
        for voice in (False, True, False):
            with pytest.raises(ValueError) as error:
                loader.api_包(voice)
            messages.append(str(error.value))
        assert messages[0] == messages[1] == messages[2]
        assert "effect.mkf" in messages[0].lower()
    finally:
        loader.api_关闭()


def test_关闭仍等待自有加载线程(tmp_path: Path) -> None:
    loader = 音频档案_类(tmp_path)
    future = loader._任务
    loader.api_关闭()
    loader.api_关闭()
    assert future.done()
