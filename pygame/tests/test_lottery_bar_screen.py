# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿
from test_world import 合成地图

from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.lottery_bar_screen import 彩票告别_类, 彩票柜台_类
from rich4.native_ui import 字体_类
from rich4.original_text import 台词_类
from rich4.world import 世界_类


# ◕ 功能
class 彩票原文夹具_类:
    """
    无商业对白的选号/告别时序夹具；真实台词另做外部PE对照。

    更新日志：
    2026.10.24 - 不把字幕夹具当作正式文本。
    """

    def api_配音(self, arg_号: int) -> 台词_类:
        return 台词_类(arg_号, "测试！文字")


def test_零号选项必须算告别并等真实片长且不改彩票规则(字体: 字体_类) -> None:
    屏, 结束, 答 = 彩票柜台_类(彩票原文夹具_类()), 彩票告别_类(), []
    世, 宿 = 世界_类.api_从地图(合成地图()), _宿(字体, [])
    决 = 决策_类(决策种类_类.彩票, 0, 选项=[决策选项_类("选号", 1), 决策选项_类("离开", 0)])
    屏.api_绘制(宿, 世, 决, 答.append, 结束, lambda picked: 3500)
    next(b for b in 宿.框.按钮 if b.编号 == 210).动作()
    assert 结束.选项 == 0 and 结束.号码 == 0 and not 答 and 世.彩票[0] == 0
    宿.框.时钟 = 3499
    宿.框.按钮.clear()
    屏.api_绘制(宿, 世, 决, 答.append, 结束, lambda picked: 3500)
    assert not 答 and [b.编号 for b in 宿.框.按钮] == [210]
    宿.框.时钟 = 3500
    宿.框.按钮.clear()
    屏.api_绘制(宿, 世, 决, 答.append, 结束, lambda picked: 3500)
    assert 答 == [0] and 结束.选项 is None


def test_没有可买选项离开不等告别而即时模式选号直接回答(字体: 字体_类) -> None:
    屏, 答, 声, 结束 = 彩票柜台_类(彩票原文夹具_类()), [], [], 彩票告别_类()
    世, 宿 = 世界_类.api_从地图(合成地图()), _宿(字体, [])
    决 = 决策_类(决策种类_类.彩票, 0, 选项=[决策选项_类("离开", 0)])
    屏.api_绘制(宿, 世, 决, 答.append, 结束, lambda picked: 声.append(picked) or 1000)
    next(b for b in 宿.框.按钮 if b.编号 == 210).动作()
    assert 答 == [0] and not 声 and 结束.选项 is None
    决.选项 = [决策选项_类("选号", 1)]
    宿.即时 = True
    宿.框.按钮.clear()
    屏.api_绘制(宿, 世, 决, 答.append, 结束, lambda picked: 声.append(picked) or 1000)
    next(b for b in 宿.框.按钮 if b.编号 == 210).动作()
    assert 答 == [0, 0] and not 声 and 结束.选项 is None
