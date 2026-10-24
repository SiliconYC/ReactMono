# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿
from test_world import 合成地图

from rich4.native_ui import 字体_类
from rich4.original_text import 台词_类
from rich4.stock_screen import 股票屏幕_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类


# ◕ 功能
class 股票原文夹具_类:
    """
    明确无商业名称的股票绘图夹具，真实原文另由跨语言适配器检查。

    更新日志：
    2026.10.24 - 测试重置、关闭和原历史环语义。
    """

    def api_股票(self, arg_索引: int) -> str:
        return f"公司{arg_索引}"

    def api_配音(self, arg_号: int, arg_变体: int = 0) -> 台词_类:
        return 台词_类(arg_号, "")


def test_股市取消先关闭资讯再回价格页最后离开且每次仅一次取消声(字体: 字体_类) -> None:
    屏, 声, 关闭 = 股票屏幕_类(股票原文夹具_类()), [], []
    宿 = _宿(字体, 声)
    屏.页, 屏.资讯, 屏.选中 = 1, True, 3
    for _ in range(3):
        屏.api_取消(宿, lambda: 关闭.append(True))
    assert 关闭 == [True] and 声 == [4, 4, 4]
    assert 屏.页 == 0 and not 屏.资讯 and 屏.选中 == 3
    屏.api_重置()
    assert 屏.选中 is None and 屏.页 == 0


def test_历史环从游标非零处走满环否则从零起点遇原零位停止() -> None:
    世 = 世界_类.api_从地图(合成地图())
    世.股史[0] = [股市_类._位(i + 1.0) for i in range(144)]
    世.股史游标 = 143
    assert 股票屏幕_类._历史(世, 0) == [144.0] + list(map(float, range(1, 144)))
    世.股史[0][143] = 0
    assert 股票屏幕_类._历史(世, 0) == list(map(float, range(1, 144)))
    世.股史[0][2] = 0
    assert 股票屏幕_类._历史(世, 0) == [1.0, 2.0]


def test_报价小数精度依现价幅度而涨跌保留正负号() -> None:
    assert 股票屏幕_类._格式(14.999, 14.999) == "15.00"
    assert 股票屏幕_类._格式(15.0, 15.0) == "15.0"
    assert 股票屏幕_类._格式(150.0, 150.0) == "150"
    assert 股票屏幕_类._格式(-0.0, 10.0, True) == "-0.00"


def test_资讯在历史非空时还要画右侧历史高低报价数值(字体: 字体_类) -> None:
    世, 屏 = 世界_类.api_从地图(合成地图()), 股票屏幕_类(股票原文夹具_类())
    宿 = _宿(字体, [])
    屏._画资讯(宿, 世, 0)
    空 = 宿.框.画布.像素.copy()
    世.股史[0][0] = 股市_类._位(10.0)
    宿 = _宿(字体, [])
    屏._画资讯(宿, 世, 0)
    for top in (231, 271):
        assert any(
            空[y * 640 + x] != 宿.框.画布.像素[y * 640 + x]
            for y in range(top, top + 26)
            for x in range(542, 610)
        )


def test_涨停拒买跌停拒卖且停牌只保留原按钮声音(字体: 字体_类) -> None:
    from rich4.number_pad import 数字板_类
    from rich4.stock_screen import 股票动作_类

    世, 屏, 板, 声 = 世界_类.api_从地图(合成地图()), 股票屏幕_类(股票原文夹具_类()), 数字板_类(), []
    世.头.日期, 世.玩家[0].记录.银行, 屏.选中 = (14, 6, 2000), 10000, 0
    世.玩家[0].持仓[0].数量 = 500
    quote = 世.股票[0]
    quote.标志10, quote.浮点位[1] = 1000, 股市_类._位(10.0)
    动作 = 股票动作_类(lambda s, n: False, lambda s, n: False, lambda: None)
    for current, id, prompt in ((11.0, 430, "漲停無法買進！"), (9.0, 431, "跌停無法賣出！")):
        quote.浮点位[2] = 股市_类._位(current)
        宿 = _宿(字体, 声)
        屏.api_绘制(宿, 世, 0, 板, 动作)
        next(b for b in 宿.框.按钮 if b.编号 == id).动作()
        assert not 板.api_活跃() and 屏._弹文 == prompt
    quote.停牌天数, 屏._弹文 = 1, ""
    宿 = _宿(字体, 声)
    屏.api_绘制(宿, 世, 0, 板, 动作)
    next(b for b in 宿.框.按钮 if b.编号 == 430).动作()
    assert not 板.api_活跃() and not 屏._弹文 and 声 == [1, 1, 1]


def test_红黑卡股票目标按原第二次点击才提交原选项编号(字体: 字体_类) -> None:
    from rich4.cards import 卡片目标_类, 目标种类_类
    from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类

    世, 屏, 答 = 世界_类.api_从地图(合成地图()), 股票屏幕_类(股票原文夹具_类()), []
    决 = 决策_类(
        决策种类_类.卡片目标,
        0,
        选项=[
            决策选项_类("目标", 2, 对象=卡片目标_类(目标种类_类.股票, 2)),
            决策选项_类("取消", -1),
        ],
    )
    for _ in range(2):
        宿 = _宿(字体, [])
        屏.api_卡片目标(宿, 世, 0, 决, 210, 答.append)
        next(b for b in 宿.框.按钮 if b.编号 == 210).动作()
    assert 答 == [0] and 屏.选中 == 2
    宿 = _宿(字体, [])
    屏.api_卡片目标(宿, 世, 0, 决, 210, 答.append)
    next(b for b in 宿.框.按钮 if b.编号 == 211).动作()
    assert 答 == [0, 1] and 屏.选中 is None
