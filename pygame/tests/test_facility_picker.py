# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿

from rich4.facility_picker import 设施选择_类
from rich4.game_types import 决策_类, 决策位置_类, 决策种类_类, 决策选项_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_设施路由只认原建造种类或无位置的零至四改建选项() -> None:
    决 = 决策_类(决策种类_类.建造设施, 0)
    assert 设施选择_类.api_接管(决)
    决.种类, 决.提示 = 决策种类_类.行动目标, "請選擇設施類別"
    决.选项 = [决策选项_类("研究", 4), 决策选项_类("取消", -1)]
    assert 设施选择_类.api_接管(决) and 设施选择_类.api_可取消(决)
    决.选项[0].位置 = 决策位置_类(0, 0)
    assert not 设施选择_类.api_接管(决)
    决.选项[0].位置, 决.选项[0].值 = None, 5
    assert not 设施选择_类.api_接管(决)


def test_原不可取消建造不回调而改建返回首个取消选项(字体: 字体_类) -> None:
    选择, 声, 答 = 设施选择_类(), [], []
    宿 = _宿(字体, 声)
    决 = 决策_类(决策种类_类.建造设施, 0, 选项=[决策选项_类("取消", -1)])
    选择.api_取消(宿, 决, 答.append)
    assert not 声 and not 答
    决.种类 = 决策种类_类.行动目标
    选择.api_取消(宿, 决, 答.append)
    assert 声 == [4] and 答 == [0]


def test_同键保留选择新键重置且第二次点击或确认才提交(字体: 字体_类) -> None:
    选择, 答 = 设施选择_类(), []
    决 = 决策_类(决策种类_类.建造设施, 0, 选项=[决策选项_类("研究", 4)])
    宿 = _宿(字体, [])
    选择.api_绘制(宿, 决, "one", 答.append)
    next(b for b in 宿.框.按钮 if b.编号 == 210).动作()
    assert 选择._选中 == 4 and not 答
    宿.框.按钮.clear()
    选择.api_绘制(宿, 决, "one", 答.append)
    next(b for b in 宿.框.按钮 if b.编号 == 207).动作()
    assert 答 == [0]
    宿.框.按钮.clear()
    选择.api_绘制(宿, 决, "two", 答.append)
    assert 选择._选中 is None and not next(b for b in 宿.框.按钮 if b.编号 == 207).启用
