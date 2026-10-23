# ◑ 导入
from rich4.viewport import 视口_类


# ◕ 功能
def test_等比留边及输入反变换() -> None:
    视口 = 视口_类(1000, 480)
    assert 视口.矩形 == (180, 0, 640, 480)
    assert 视口.api_逻辑位置((180, 0)) == (0, 0)
    assert 视口.api_逻辑位置((819, 479)) == (639, 479)
    assert 视口.api_逻辑位置((179, 0)) is None
    assert 视口.api_逻辑位置((820, 0)) is None


def test_缩小窗口映射右下边界() -> None:
    视口 = 视口_类(320, 300)
    assert 视口.矩形 == (0, 30, 320, 240)
    assert 视口.api_逻辑位置((319, 269)) == (638, 478)
    assert 视口.api_逻辑位置((0, 270)) is None
