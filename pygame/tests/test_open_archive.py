# ◑ 导入
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from rich4.graphics import 图像_类
from rich4.open_image import 开放图像_类


# ◕ 功能
def test_开放档案直接读PNG且不伪造旧SPR字节(tmp_path: Path) -> None:
    from rich4.open_archive import 开放档案_类

    image = 图像_类(2, 1, [0x8000, 31], -1, 2, b"\0\1")
    metadata = 开放图像_类.api_保存(image, tmp_path / "a.png")
    (tmp_path / "entry.json").write_text(
        json.dumps(
            {
                "kind": "sprite",
                "indexed": True,
                "frames": [{"image": "a.png", **asdict(metadata), "team_color_ranges": [[1, 2]]}],
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
    archive = 开放档案_类(tmp_path, "d")
    assert archive.api_帧(0, 0) == image
    assert archive.api_帧数(0) == 1
    assert archive.api_换色段(0, 0) == ((1, 2),)
    with pytest.raises(ValueError, match="PNG"):
        archive.api_解码(0)


def test_资源清单路径不能逃出游戏素材目录(tmp_path: Path) -> None:
    from rich4.open_archive import 开放档案_类

    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "format": "reactmono-rich4-open-assets",
                "version": 1,
                "archives": {"d": ["../outside.json"]},
            }
        )
    )
    archive = 开放档案_类(tmp_path, "d")
    with pytest.raises(ValueError, match="目录"):
        archive.api_元数据(0)
