# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp::Screens::draw_decision；只识别原专属屏幕，其他种类交回主应用。
# ◑ 导入
from rich4.game import 游戏会话_类
from rich4.game_types import 决策种类_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_service_types import 商店屏幕状态_类, 救援屏幕状态_类, 魔法屏幕状态_类
from rich4.native_frame import 画框_类


# ◕ 功能
class 物品决策分发_类:
    """
    原商店/魔法/救援互斥访问、遥控骰形状与抢夺/嫁祸路由。

    更新日志：
    2026.10.24 - 不把任意七项决策伪装遥控骰，不扩充原提示字符串匹配。
    """

    def api_画决策(self, arg_框: 画框_类, arg_会: 游戏会话_类, arg_宿: 物品宿主_类) -> bool:
        d = arg_会.待决策
        if d is None:
            raise ValueError("原物品分发需要待决策")
        if d.种类 == 决策种类_类.商店:
            self._魔法, self._救援 = 魔法屏幕状态_类(), 救援屏幕状态_类()
            self.api_画商店(arg_框, arg_会, d, arg_宿)
            return True
        if d.种类 in (决策种类_类.魔法类别, 决策种类_类.魔法效果):
            self._店, self._救援 = 商店屏幕状态_类(), 救援屏幕状态_类()
            self.api_画魔法(arg_框, arg_会, d, arg_宿)
            return True
        if d.种类 == 决策种类_类.救援:
            self._店, self._魔法 = 商店屏幕状态_类(), 魔法屏幕状态_类()
            self.api_画救援(arg_框, arg_会, d, arg_宿)
            return True
        if d.种类 == 决策种类_类.行动目标:
            if d.被抢玩家 is not None:
                self.api_结束访问()
                self.api_画抢夺(arg_框, arg_会, d, arg_宿)
                return True
            self._抢夺选择 = None
            if len(d.选项) == 7 and all(
                o.位置 is None and o.值 == (i + 1) % 7 for i, o in enumerate(d.选项)
            ):
                self.api_结束访问()
                self.api_画遥控骰(arg_框, d, arg_宿)
                return True
        elif d.种类 == 决策种类_类.卡片目标:
            if d.提示 in ("使用嫁祸卡？", "請選擇嫁禍對象..."):
                self.api_结束访问()
                self.api_画嫁祸(arg_框, arg_会, d, arg_宿)
                return True
        self.api_结束访问()
        return False
