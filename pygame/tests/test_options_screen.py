# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿

from rich4.native_ui import 字体_类
from rich4.options_screen import 选项屏幕_类
from rich4.options_types import 选项动作_类, 选项状态_类


# ◕ 功能
class 乐曲原文夹具_类:
    """
    无商业歌曲名称的选项测试；真实文字另用外部PE与原CPP差分。

    更新日志：
    2026.10.24 - 提供八个明确索引的文字。
    """

    def api_歌曲(self, arg_号: int) -> str:
        return f"歌曲{arg_号}"


def test_打开复制参数取消不提交而确认按顺序提交关闭(字体: 字体_类) -> None:
    屏, 原, 调用 = 选项屏幕_类(乐曲原文夹具_类()), 选项状态_类(), []
    屏.api_打开(原, False)
    原.音乐 = False
    assert 屏._状态.音乐
    动 = 选项动作_类(lambda s: 调用.append(s.速度), lambda: 调用.append(-1))
    宿 = _宿(字体, [])
    屏.api_绘制(宿, 动)
    next(b for b in 宿.框.按钮 if b.编号 == 52).动作()
    assert 调用 == [-1]
    next(b for b in 宿.框.按钮 if b.编号 == 55).动作()
    assert 调用 == [-1, 1, -1]


def test_重开须经过原确认是而确认否只回设置(字体: 字体_类) -> None:
    屏, 调用 = 选项屏幕_类(乐曲原文夹具_类()), []
    屏.api_打开(选项状态_类(), True)
    动 = 选项动作_类(lambda s: None, lambda: 调用.append(0), 重开=lambda: 调用.append(1))
    宿 = _宿(字体, [])
    屏.api_绘制(宿, 动)
    next(b for b in 宿.框.按钮 if b.编号 == 57).动作()
    assert 屏._确认 == 0 and not 调用
    宿.框.按钮.clear()
    屏.api_绘制(宿, 动)
    assert [b.编号 for b in 宿.框.按钮] == [58, 59]
    next(b for b in 宿.框.按钮 if b.编号 == 59).动作()
    assert 屏._确认 == -1 and not 调用
    屏._确认 = 0
    宿.框.按钮.clear()
    屏.api_绘制(宿, 动)
    next(b for b in 宿.框.按钮 if b.编号 == 58).动作()
    assert 调用 == [1] and 屏._确认 == -1


def test_未实现的大按钮与窗口设置保留灰态且歌词试曲回调依指针选行(字体: 字体_类) -> None:
    屏, 调用 = 选项屏幕_类(乐曲原文夹具_类()), []
    动 = 选项动作_类(lambda s: None, lambda: None, 试曲=调用.append)
    宿 = _宿(字体, [])
    屏.api_绘制(宿, 动)
    assert not any(b.启用 for b in 宿.框.按钮 if b.编号 in (57, 61, 62))
    宿.框.指针y = 59 + 226 + 15 * 7
    next(b for b in 宿.框.按钮 if b.编号 == 56).动作()
    assert 调用 == [8]
