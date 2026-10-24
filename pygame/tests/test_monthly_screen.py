# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_message_overlay import 消息素材夹具_类
from test_original_text import _程序

from rich4.game_types import 效果_类, 效果种类_类, 月报_类
from rich4.graphics import 图像_类
from rich4.monthly_screen import 月报声音_类, 月报屏幕_类
from rich4.monthly_types import 月播_类, 月泡_类, 月片_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
def _屏(arg_调用: list) -> 月报屏幕_类:
    文 = 原版文字_类(原版程序_类(_程序(b"#0017A\0#0092B\0#0018C\0")))
    return 月报屏幕_类(
        月报声音_类(
            lambda n: arg_调用.append(("play", n)), lambda n: arg_调用.append(("voice", n)) or 3500
        ),
        文,
    )


def _框(arg_字体: 字体_类) -> 画框_类:
    return 画框_类(图像_类(640, 480, [9] * 307200), 消息素材夹具_类(), arg_字体, [])


def test_只接收三个带月结数据效果且跳过策略不丢弃新入队() -> None:
    屏 = _屏([])
    屏.api_跳过(True)
    e = 效果_类(效果种类_类.股利, 月报=月报_类(活跃=3))
    屏.api_入队(e)
    e.月报.活跃 = 15
    屏.api_入队(效果_类(效果种类_类.月报))
    屏.api_入队(效果_类(效果种类_类.爆炸, 月报=月报_类()))
    assert len(屏._队列) == 1 and 屏._队列[0].月报.活跃 == 3
    屏.api_清空()
    assert not 屏.api_活跃() and 屏._跳过


def test_月结玩家掩码仅列出四槽且角色按十二取余() -> None:
    f = 月报_类(活跃=0xF5, 人物=[255, 1, 14, 3])
    assert 月报屏幕_类._槽(f) == [0, 2]
    assert 月报屏幕_类._角色(f, 0) == 3
    assert 月报屏幕_类._角色(f, 2) == 2


def test_对白至少两秒并等待实际语音且显示参数按值保存() -> None:
    调 = []
    屏 = _屏(调)
    p = 月播_类(效果_类(效果种类_类.彩票开奖, 月报=月报_类()))
    屏._说(p, 22, 300, 47, -10, 0, 17)
    assert (p.泡.条帧, p.泡.文字, p.泡.剩余毫秒, p.泡.显示) == (22, "A", 3500, True)
    assert 调 == [("voice", 17)]
    屏.声音.语音 = None
    屏._说(p, 1, 190, 10, 0, -30, 92, "")
    assert p.泡.文字 == "" and p.泡.剩余毫秒 == 2000


def test_开屏选择独立种子与原语音及股利音() -> None:
    for k, 语音 in ((效果种类_类.彩票开奖, 17), (效果种类_类.月报, 92)):
        调 = []
        屏 = _屏(调)
        p = 月播_类(效果_类(k, 月报=月报_类(号码=7)))
        屏._开始(p)
        assert p.种子 == (0x2545F491 ^ 7 ^ (int(k) << 8))
        assert p.状态 == 1 and 调 == [("voice", 语音)]
    调 = []
    屏 = _屏(调)
    p = 月播_类(效果_类(效果种类_类.股利, 月报=月报_类()))
    屏._开始(p)
    assert p.节拍 == 1000 and 调 == [("play", 61)]


def test_股利显示三秒关闭且真实世界不被再次结算(字体: 字体_类) -> None:
    屏, 框 = _屏([]), _框(字体)
    世 = 会话样本().世界
    原 = 世.api_导出()
    屏.api_入队(效果_类(效果种类_类.股利, 月报=月报_类(活跃=3)))
    屏.api_绘制(框, 世, 2999)
    assert 屏.api_活跃() and 屏._当前.计数 == 2
    屏.api_绘制(框, 世, 1)
    assert not 屏.api_活跃() and 世.api_导出() == 原
    assert 框.按钮[-1].编号 == 911


def test_开发跳过每屏仍需绘制一帧再退出(字体: 字体_类) -> None:
    屏, 框 = _屏([]), _框(字体)
    屏.api_跳过(True)
    屏.api_入队(效果_类(效果种类_类.股利, 月报=月报_类()))
    屏.api_绘制(框, 会话样本().世界, 0)
    assert 屏.api_活跃()
    框.画布.像素[:] = [9] * 307200
    屏.api_绘制(框, 会话样本().世界, 0)
    assert not 屏.api_活跃() and set(框.画布.像素) == {9}


def test_开奖点击只把对白时间清零并在下一计时节拍替换对白(字体: 字体_类) -> None:
    屏, 框 = _屏([]), _框(字体)
    p = 月播_类(效果_类(效果种类_类.彩票开奖, 月报=月报_类()))
    屏._开始(p)
    p.点过 = True
    屏._画开奖(框, p, 0)
    assert p.泡.显示 and p.泡.剩余毫秒 == 0 and p.状态 == 1
    p.点过 = False
    屏._画开奖(框, p, 49)
    assert p.状态 == 1
    屏._画开奖(框, p, 1)
    assert p.状态 == 2 and p.泡.显示 and p.泡.文字 == "C"


def test_月报点击同时消除对白与反应影片并标记下次等待跳过(字体: 字体_类) -> None:
    屏, 框 = _屏([]), _框(字体)
    p = 月播_类(效果_类(效果种类_类.月报, 月报=月报_类()))
    p.数据 = 月报_类(活跃=3, 冠军=1)
    p.泡 = 月泡_类(显示=True, 剩余毫秒=2000)
    p.片 = 月片_类(运行=True)
    p.点过 = True
    屏._画月报(框, p, 0)
    assert not p.泡.显示 and not p.片.运行 and p.片.解码 is None and p.略等待


def test_反应启动同帧使用新影片而不继续画被替换的旧末帧(字体: 字体_类) -> None:
    屏, 框 = _屏([]), _框(字体)
    p = 月播_类(效果_类(效果种类_类.月报, 月报=月报_类()))
    p.数据 = 月报_类(活跃=3, 冠军=1, 悲情=0)
    p.状态 = 7
    p.片 = 月片_类(静帧=图像_类(1, 1, [0x7C00]))
    屏._画月报(框, p, 100)
    assert p.状态 == 8 and not p.片.静帧.像素
    assert 框.画布.像素[0] == 100
