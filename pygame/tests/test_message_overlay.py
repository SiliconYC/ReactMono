# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.message_overlay import 消息_类, 消息声音_类, 消息层_类, 消息种类_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类


# ◕ 功能
class 消息素材夹具_类(美术_类):
    """
    仅单元测试的原点与最高位夹具，不作为正式消息画面。

    更新日志：
    2026.10.24 - 正式像素验收另外读取真实MKF。
    """

    def __init__(self) -> None:
        super().__init__(Path("unused-test-assets"))

    def api_帧(self, arg_库: str, arg_条: int, arg_帧: int) -> 图像_类:
        return 图像_类(96, 48, [100 + arg_帧] * 4608, 2, 3)

    def api_解码(self, arg_库: str, arg_条: int) -> bytes:
        return b"\xff\xff\x00\x80\x12"


def _框(arg_字体: 字体_类) -> 画框_类:
    return 画框_类(图像_类(640, 480, [9] * 307200), 消息素材夹具_类(), arg_字体, [])


def test_气泡以声音编号去重且跳过清空及其它消息不重置最后气泡() -> None:
    层 = 消息层_类(消息声音_类(), lambda: 0)
    a = 消息_类(声音=1050, 文字="A")
    层.api_入队(a)
    a.文字 = "changed"
    层.api_入队(消息_类(声音=1050, 文字="B"))
    assert len(层._队列) == 1 and 层.api_当前().文字 == "A"
    层.api_清空()
    层.api_入队(消息_类(消息种类_类.对话框))
    层.api_跳过()
    层.api_入队(消息_类(声音=1050))
    assert not 层.api_活跃()


def test_首次绘制才开始语音且等待真实时长并在精确截止点退休(字体: 字体_类) -> None:
    时, 记录 = [100], []

    def 播(arg_号: int) -> int:
        记录.append(arg_号)
        return 2400

    层 = 消息层_类(消息声音_类(播, lambda: 记录.append(-1)), lambda: 时[0])
    层.api_入队(消息_类(声音=77, 等待声音=True))
    层.api_退休()
    assert 层.api_活跃() and not 记录
    assert 层.api_绘制(_框(字体)) and 层._截止 == 2500 and 记录 == [77]
    层.api_绘制(_框(字体))
    时[0] = 2499
    层.api_退休()
    assert 层.api_活跃() and 记录 == [77]
    时[0] = 2500
    层.api_退休()
    assert not 层.api_活跃() and 记录 == [77]


def test_未开始跳过仍停止声音但未开始清空不停止() -> None:
    记 = []
    层 = 消息层_类(消息声音_类(None, lambda: 记.append(1)), lambda: 0)
    层.api_入队(消息_类(消息种类_类.对话框))
    层.api_清空()
    assert not 记
    层.api_入队(消息_类(消息种类_类.对话框))
    层.api_跳过()
    层.api_跳过()
    assert 记 == [1]


def test_绘制清空原按钮并注册全屏跳过且即时模式必须先画一帧(字体: 字体_类) -> None:
    框 = _框(字体)
    框.api_命中(71, (0, 0, 100, 100), lambda: None)
    层 = 消息层_类(消息声音_类(), lambda: 0)
    层.api_即时(True)
    层.api_入队(消息_类(消息种类_类.对话框, 焦点=0))
    层.api_退休()
    assert 层.api_焦点() == 0
    层.api_绘制(框)
    assert [(b.编号, b.区域) for b in 框.按钮] == [(900, (0, 0, 640, 480))]
    层.api_退休()
    assert not 层.api_活跃() and 层.api_焦点() is None


def test_照片保留最高位且截断按完整双字节补零并缓存(字体: 字体_类) -> None:
    层 = 消息层_类(消息声音_类(), lambda: 0)
    图 = 层._照片(_框(字体), 441)
    assert (图.宽, 图.高) == (388, 251)
    assert 图.像素[:4] == [65535, 32768, 0, 0]
    assert 层._照片(_框(字体), 441) is 图


def test_确认条两半扩展十像素并使用原稳定编号和原点抵消(字体: 字体_类) -> None:
    框, 记 = _框(字体), []
    框.指针x, 框.指针y = 163, 286
    消息层_类.api_确认条(框, 220, 320, 71, lambda: 记.append(1), 72, lambda: 记.append(0))
    assert [(b.编号, b.区域) for b in 框.按钮] == [
        (71, (162, 286, 220, 354)),
        (72, (220, 286, 278, 354)),
    ]
    assert 框.画布.像素[296 * 640 + 172] == 101
    框.按钮[0].动作()
    assert 记 == [1]
