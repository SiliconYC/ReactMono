# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿
from test_services import 服务样本

from rich4.native_ui import 字体_类
from rich4.number_pad import 数字板_类
from rich4.stocks import 股市_类
from rich4.trading import 交易_类, 可售项目_类
from rich4.trading_board_screen import 交易公告栏_类
from rich4.trading_screen_types import 交易动作_类, 交易视图_类


# ◕ 功能
class 交易原文夹具_类:
    """
    无商业公司名称的交易动作夹具，不代替真实画布差分。

    更新日志：
    2026.10.24 - 仅提供明确索引名字。
    """

    def api_股票(self, arg_索引: int) -> str:
        return f"公司{arg_索引}"


def test_取消从挑选页回公告栏但只有公告栏取消才关闭(字体: 字体_类) -> None:
    屏, 关, 声 = 交易公告栏_类(交易原文夹具_类()), [], []
    动 = 交易动作_类(
        lambda 单据: False, lambda i: False, lambda s, i: False, lambda: 关.append(True)
    )
    宿 = _宿(字体, 声)
    屏._视图 = 交易视图_类.详情
    屏.api_取消(宿, 动)
    assert 屏.api_视图() == 交易视图_类.公告栏 and not 关
    屏.api_取消(宿, 动)
    assert 关 == [True] and 声 == [4, 4]


def test_真实限价驱动价格板且取消不伪装挂牌成功(字体: 字体_类) -> None:
    世, 屏, 板, 单 = 服务样本(), 交易公告栏_类(交易原文夹具_类()), 数字板_类(), []
    世.玩家[0].记录.道具[0] = 1
    动 = 交易动作_类(
        lambda 单据: 单.append(单据) or False, lambda i: False, lambda s, i: False, lambda: None
    )
    屏._视图 = 交易视图_类.物品
    屏._问价格(世, 0, 板, 动, 可售项目_类(3, 1), 1)
    assert 板.api_活跃() and 板.api_上限() > 0 and 屏.api_建议() > 0
    宿 = _宿(字体, [])
    板.api_取消(宿)
    assert not 单 and not 屏._提示 and 屏.api_视图() == 交易视图_类.物品
    屏._问价格(世, 0, 板, 动, 可售项目_类(3, 1), 1)
    板.api_键(宿, "1")
    板.api_键(宿, "\r")
    assert len(单) == 1 and 屏._通知 == "無法刊登！" and 屏.api_视图() == 交易视图_类.物品


def test_股票选择先问股数再重入问价格与真实参考价相符(字体: 字体_类) -> None:
    世, 屏, 板, 单 = 服务样本(), 交易公告栏_类(交易原文夹具_类()), 数字板_类(), []
    世.玩家[0].持仓[0].数量 = 100
    世.股票[0].浮点位[2] = 股市_类._位(10.0)
    动 = 交易动作_类(
        lambda 单据: 单.append(单据) or True, lambda i: False, lambda s, i: False, lambda: None
    )
    屏._选择物品(世, 0, 板, 动, 可售项目_类(1, 0, 100))
    assert 板.api_上限() == 100 and 屏.api_建议() == 1
    宿 = _宿(字体, [])
    for c in "20\r":
        板.api_键(宿, c)
    assert 板.api_活跃() and 板.api_上限() == 2000 and 屏.api_建议() == 200
    for c in "300\r":
        板.api_键(宿, c)
    assert len(单) == 1 and (单[0].种类, 单[0].项目, 单[0].数量, 单[0].价格) == (1, 0, 20, 300)
    assert 屏.api_视图() == 交易视图_类.公告栏


def test_真实挂牌和购买按钮只在成交时转移现金银行与道具(字体: 字体_类) -> None:
    世, 屏, 板 = 服务样本(), 交易公告栏_类(交易原文夹具_类()), 数字板_类()
    卖, 买 = 世.玩家[0].记录, 世.玩家[1].记录
    卖.控制标志, 买.控制标志 = 1, 1
    卖.道具[0], 买.道具[0], 买.现金, 卖.银行 = 2, 0, 1000, 500
    动 = 交易动作_类(
        lambda 单据: 交易_类.api_挂牌(世, 0, 单据).已应用,
        lambda i: 交易_类.api_取消(世, 0, i),
        lambda s, i: 交易_类.api_购买(世, 1, s, i).已应用,
        lambda: None,
    )
    宿 = _宿(字体, [])
    屏._选择物品(世, 0, 板, 动, 可售项目_类(3, 1))
    for c in "100\r":
        板.api_键(宿, c)
    assert (卖.道具[0], 买.道具[0], 买.现金, 卖.银行) == (2, 0, 1000, 500)
    屏.api_绘制(宿, 世, 1, 板, 动)
    next(b for b in 宿.框.按钮 if b.编号 == 600).动作()
    宿.框.按钮.clear()
    屏.api_绘制(宿, 世, 1, 板, 动)
    next(b for b in 宿.框.按钮 if b.编号 == 456).动作()
    assert 屏.api_视图() == 交易视图_类.公告栏
    assert (卖.道具[0], 买.道具[0], 买.现金, 卖.银行) == (1, 1, 900, 600)
    assert not 交易_类.api_报价(世)
