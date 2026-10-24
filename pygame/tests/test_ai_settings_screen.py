# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本
from test_number_pad import _宿

from rich4.ai_settings_screen import 托管动作_类, 托管屏幕_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_打开只列人类并分别拷贝编辑与原值防止确认漏提交() -> None:
    会, 屏 = 会话样本(), 托管屏幕_类()
    会.世界.玩家[1].记录.控制标志 = 2
    assert 屏.api_打开(会, 2) and 屏._选中 == 2
    assert 屏.api_编辑(1) is None
    e = 屏.api_编辑(2)
    e.自动 = True
    assert not 屏.api_编辑(2).自动
    屏._编辑[2].自动 = True
    assert not 屏._原值[2].自动 and not 会.api_托管设置(2).自动


def test_切换人类标签不托管再次点击才切换且取消不写真实会话(字体: 字体_类) -> None:
    会, 屏, 提交, 关 = 会话样本(), 托管屏幕_类(), [], []
    屏.api_打开(会, 0)
    动作 = 托管动作_类(lambda i, e: 提交.append(i), lambda: 关.append(True))
    for _ in range(2):
        宿 = _宿(字体, [])
        屏.api_绘制(宿, 会.世界, 动作)
        next(b for b in 宿.框.按钮 if b.编号 == 1602).动作()
    assert 屏.api_编辑(2).自动 and not 会.api_托管设置(2).自动
    屏.api_取消(宿, 动作)
    assert not 提交 and 关 == [True]


def test_确认只按槽位提交有变化的设置然后关闭且拖比例不自动补到一百(字体: 字体_类) -> None:
    会, 屏, 调用 = 会话样本(), 托管屏幕_类(), []
    屏.api_打开(会, 2)
    动作 = 托管动作_类(lambda i, e: 调用.append((i, e.现金比例)), lambda: 调用.append((-1, 0)))
    宿 = _宿(字体, [])
    宿.框.指针x, 宿.框.指针y, 宿.框.按下 = 389, 340, True
    屏.api_绘制(宿, 会.世界, 动作)
    assert 屏.api_编辑(2).现金比例 == 90
    next(b for b in 宿.框.按钮 if b.编号 == 1630).动作()
    assert 调用 == [(2, 90), (-1, 0)]
