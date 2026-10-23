# ◑ 导入
import struct
from pathlib import Path

import pygame

from rich4.app import 资源预览_类


# ◕ 功能
def test_预览人物以画布中心为锚点而非将人物裁到窗口外(tmp_path: Path) -> None:
    图 = (
        b"SMP\0"
        + struct.pack("<IIhhhhI", 1, 24, 2, 1, 24, 80, 4)
        + struct.pack("<2H", 0x7C00, 0x03E0)
    )
    索引 = 20 + len(图)
    文件 = tmp_path / "sample.mkf"
    文件.write_bytes(struct.pack("<I4I", 索引, len(图), len(图), 0, 0) + 图 + struct.pack("<I", 4))
    预览 = 资源预览_类(文件, 0, 0)
    画布 = 预览.api_画布()
    assert 画布.get_size() == (640, 480)
    assert 画布.get_at((319, 239)) == pygame.Color(255, 0, 0, 255)
    assert 画布.get_at((320, 239)) == pygame.Color(0, 250, 0, 255)
