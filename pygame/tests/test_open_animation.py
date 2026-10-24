# ◑ 导入
import json
from dataclasses import asdict
from pathlib import Path

from rich4.graphics import 图像_类
from rich4.open_image import 开放图像_类


# ◕ 功能
def test_PNG帧序列保留间隔全部帧透明与倒带(tmp_path: Path) -> None:
    from rich4.open_animation import PNG动画_类
    from rich4.open_archive import 开放档案_类

    images = [图像_类(2, 1, [0x8000, i], 不透明=b"\0\1") for i in (1, 30, 31)]
    frames = []
    for index, image in enumerate(images):
        path = tmp_path / f"{index}.png"
        info = 开放图像_类.api_保存(image, path)
        frames.append({"image": path.name, **asdict(info)})
    (tmp_path / "entry.json").write_text(
        json.dumps(
            {
                "kind": "animation",
                "width": 2,
                "height": 1,
                "interval_ms": 73,
                "frames": frames,
            }
        )
    )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "format": "reactmono-rich4-open-assets",
                "version": 1,
                "archives": {"d": ["entry.json"]},
            }
        )
    )
    movie = PNG动画_类(开放档案_类(tmp_path, "d"), 0)
    assert (movie.帧数, movie.间隔毫秒, movie.宽, movie.高) == (3, 73, 2, 1)
    for _ in range(2):
        for index, image in enumerate(images):
            assert movie.api_下一帧()
            assert movie.已解帧 == index + 1 and movie.api_图像() == image
        assert not movie.api_下一帧()
        movie.api_倒带()
        assert movie.已解帧 == 0
