# ◑ 导入
from pathlib import Path

from rich4.graphics import 图像_类


# ◕ 功能
def test_PNG完整16位像素与显式掩码原点无损往返(tmp_path: Path) -> None:
    from rich4.open_image import 开放图像_类

    image = 图像_类(
        256, 256, list(range(65536)), -123, 456, bytes(i % 3 != 0 for i in range(65536))
    )
    path = tmp_path / "all-colors.png"
    metadata = 开放图像_类.api_保存(image, path)
    actual = 开放图像_类.api_读取(path, metadata)
    assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert actual == image


def test_PNG无掩码黑色与高位黑色保持原语义(tmp_path: Path) -> None:
    from rich4.open_image import 开放图像_类

    image = 图像_类(3, 1, [0, 0x8000, 0xFFFF], 2, -3)
    path = tmp_path / "no-mask.png"
    metadata = 开放图像_类.api_保存(image, path)
    assert 开放图像_类.api_读取(path, metadata) == image
