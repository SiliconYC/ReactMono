# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿

from rich4.artwork import 美术_类
from rich4.help_screen import 帮助屏幕_类
from rich4.native_ui import 字体_类


# ◕ 功能
class 帮助正文夹具_类(美术_类):
    """
    分页边界的非商业正文夹具，正式界面另做原MKF差分。

    更新日志：
    2026.10.24 - 显式分隔与14行切页、无效资源的原空页。
    """

    def __init__(self) -> None:
        pass

    def api_解码(self, arg_库: str, arg_条: int) -> bytes:
        if arg_条 == 1:
            return b"\0".join([str(i).encode() for i in range(15)] + [b"@", b"end", b"", b""])
        if arg_条 == 58:
            return b"bad copy"
        raise ValueError("missing fixture entry")


def test_十四行及独立分隔分页保留中间空页且冬眠坏资源按原源码说明() -> None:
    s, art = 帮助屏幕_类(), 帮助正文夹具_类()
    s.api_打开(-1, -1)
    assert (s._x, s._y) == (120, 40)
    s._选择(art, 0, 0)
    assert list(map(len, s._页表)) == [14, 1, 1]
    assert s._页表[-1] == ["end"]
    s._选择(art, 6, 1)
    assert s._页表 == [["功能：讓其他所有角色", "冬眠五天，期間無法行", "動。"]]
    s._选择(art, 1, 0)
    assert s._页表 == [[]]


def test_分类滚动按八行钳制且重开保留每类起行并取消只发原声音(字体: 字体_类) -> None:
    s, sounds = 帮助屏幕_类(), []
    s.api_打开(20, 60)
    s._类别, s._话题 = 6, 2
    s._滚动(1)
    assert (s._首行[6], s._话题) == (8, 10)
    s._滚动(1)
    s._滚动(1)
    assert (s._首行[6], s._话题) == (22, 24)
    s._滚动(-1)
    assert (s._首行[6], s._话题) == (14, 16)
    s.api_取消(_宿(字体, sounds))
    s.api_打开(-1, -1)
    assert sounds == [4] and (s._类别, s._话题, s._页, s._已载) == (0, 0, 0, -1)
    assert s._首行[6] == 14
