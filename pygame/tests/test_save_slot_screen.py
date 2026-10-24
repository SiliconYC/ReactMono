# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿

from rich4.native_ui import 字体_类
from rich4.save_slot_screen import 存档槽_类, 存档槽屏幕_类


# ◕ 功能
def test_读取槽禁用空档仍悬选并存档模式跳过自动档(字体: 字体_类) -> None:
    屏, 声, 答 = 存档槽屏幕_类(), [], []
    slots = [存档槽_类() for _ in range(6)]
    slots[2].有效 = True
    屏.api_打开(False, slots)
    宿 = _宿(字体, 声)
    宿.框.指针x, 宿.框.指针y = 150, 25
    屏.api_绘制(宿, 答.append, lambda: None)
    assert 声 == [0] and not next(b for b in 宿.框.按钮 if b.编号 == 520).启用
    assert next(b for b in 宿.框.按钮 if b.编号 == 522).启用
    屏.api_打开(True, slots)
    宿.框.按钮.clear()
    屏.api_绘制(宿, 答.append, lambda: None)
    assert [b.编号 for b in 宿.框.按钮[:5]] == [531, 532, 533, 534, 535]
    assert all(b.启用 for b in 宿.框.按钮[:5])


def test_打开复制六槽而窗口内空白吞点击外部才取消(字体: 字体_类) -> None:
    屏, 答, 取消 = 存档槽屏幕_类(), [], []
    slots = [存档槽_类() for _ in range(6)]
    屏.api_打开(False, slots)
    slots[0].有效 = True
    assert not 屏.api_槽()[0].有效
    宿 = _宿(字体, [])
    屏.api_绘制(宿, 答.append, lambda: 取消.append(True))
    next(b for b in 宿.框.按钮 if b.编号 == 429).动作()
    assert not 答 and not 取消
    next(b for b in 宿.框.按钮 if b.编号 == 529).动作()
    assert 取消 == [True]
