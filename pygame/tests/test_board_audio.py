# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_services import 服务样本

from rich4.audio_types import 循环通道_类, 音乐_类
from rich4.board_audio import 主板声音_类, 步行声音_类, 音乐导演_类


# ◕ 功能
class 策略音频夹具_类:
    """
    仅记录策略请求，不作为正式应用音频宿主。

    更新日志：
    2026.10.24 - 数字零是有效音乐/音效，不能作为False省略。
    """

    def __init__(self) -> None:
        self.调用: list[tuple[str, int]] = []

    def api_推音乐(self, arg_音乐: 音乐_类) -> None:
        self.调用.append(("push", int(arg_音乐)))

    def api_换音乐(self, arg_音乐: 音乐_类) -> None:
        self.调用.append(("replace", int(arg_音乐)))

    def api_弹音乐(self) -> None:
        self.调用.append(("pop", 0))

    def api_播循环(self, arg_号: int, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None:
        self.调用.append((f"play{int(arg_通道)}", arg_号))

    def api_停循环(self, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None:
        self.调用.append((f"stop{int(arg_通道)}", 0))


def test_上下文替换保留栈且仅退出等待三百毫秒恢复同需求取消等待() -> None:
    audio, d = 策略音频夹具_类(), 音乐导演_类()
    d.api_更新(audio, [音乐_类.菜单], 0)
    d.api_更新(audio, [音乐_类.新局], 1)
    d.api_更新(audio, [音乐_类.新局, 音乐_类.静音], 2)
    d.api_更新(audio, [音乐_类.新局], 100)
    d.api_更新(audio, [音乐_类.新局], 399)
    assert audio.调用 == [("push", 1), ("replace", 2), ("push", 0)]
    d.api_更新(audio, [音乐_类.新局, 音乐_类.静音], 400)
    d.api_更新(audio, [音乐_类.新局], 401)
    d.api_更新(audio, [音乐_类.新局], 701)
    assert audio.调用[-1] == ("pop", 0) and d._已推 == [音乐_类.新局]


def test_步行零号有效炸弹停止独立且无符号倒退按参考立即结束() -> None:
    audio, walk = 策略音频夹具_类(), 步行声音_类()
    walk.api_更新(audio, 0, 0, 100)
    assert audio.调用 == [("play1", 0), ("play2", 0)]
    walk.api_更新(audio, None, None, 249)
    assert len(audio.调用) == 2
    walk.api_更新(audio, None, None, 250)
    assert audio.调用[-2:] == [("stop1", 0), ("stop2", 0)]
    walk.api_更新(audio, 44, None, 500)
    walk.api_更新(audio, None, None, 499)
    assert audio.调用[-2:] == [("stop1", 0), ("stop2", 0)]


def test_水面先于交通且机器人固定声音而特殊槽无附身炸弹声音() -> None:
    w = 服务样本()
    p = w.玩家[0]
    p.记录.节点, p.记录.交通 = 1, 255
    assert 主板声音_类.api_步行(w, 0) == 53
    w.节点[1].标志 |= 0x80000000
    assert 主板声音_类.api_步行(w, 0) == 47
    assert 主板声音_类.api_步行(w, 8) == 38
    p.状态.附身炸弹 = 255
    assert 主板声音_类.api_炸弹(w, 0) == 32
    assert 主板声音_类.api_炸弹(w, 4) is None
