# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_game.cpp的菜单/存档槽/交易/决策与结局宿主动作。
# ◑ 导入
from pathlib import Path

from rich4.ai_settings_screen import 托管动作_类
from rich4.application_types import 应用页面_类
from rich4.endgame_types import 结局动作_类, 过关资料_类
from rich4.game_types import 决策种类_类, 托管设置_类, 游戏阶段_类
from rich4.item_screen_types import 物品宿主_类
from rich4.options_types import 选项状态_类
from rich4.save import 存档_类
from rich4.save_slot_screen import 存档槽_类
from rich4.save_transaction import 存档事务_类
from rich4.stock_screen import 股票动作_类
from rich4.tile_pick import 地图拾取_类
from rich4.tile_popup import 地图弹框_类, 地图提示_类
from rich4.trading import 挂单_类
from rich4.trading_screen_types import 交易动作_类


# ◕ 功能
class 应用操作_类:
    """
    原应用按钮只调用真实GameSession，取消、保存槽及模态交易保留原顺序。

    更新日志：
    2026.10.24 - 与应用状态共用同一会话，不在UI复制经济或制造默认成功。
    """

    def api_返回页面(self) -> 应用页面_类:
        return (
            应用页面_类.游戏
            if self.会话 is not None
            and self.会话.阶段 != 游戏阶段_类.结束
            and self.前页面 != 应用页面_类.菜单
            else 应用页面_类.菜单
        )

    def api_银行待决(self) -> bool:
        return (
            self.会话 is not None
            and self.会话.待决策 is not None
            and self.会话.待决策.种类 == 决策种类_类.银行
        )

    def api_设施可取消(self) -> bool:
        return (
            self.会话 is not None
            and self.会话.待决策 is not None
            and self.设施.api_接管(self.会话.待决策)
            and self.设施.api_可取消(self.会话.待决策)
        )

    def api_可取消(self) -> bool:
        S = 应用页面_类
        return (
            self.帮助.api_活跃()
            or self.数字板.api_活跃()
            or self.页面 in (S.新局, S.设置, S.查询, S.股票, S.读取, S.交易, S.托管, S.保存)
            or self.页面 == S.游戏
            and (self.api_银行待决() or self.api_设施可取消())
        )

    def api_取消(self) -> None:
        host, S = self.api_宿主(), 应用页面_类
        if self.帮助.api_活跃():
            self.帮助.api_取消(host)
        elif self.数字板.api_活跃():
            self.数字板.api_取消(host)
        elif self.页面 == S.股票:
            self.股票.api_取消(host, self.api_关股票)
        elif self.页面 == S.交易:
            self.交易.api_取消(host, self.api_交易动作())
        elif self.页面 == S.托管:
            self.托管.api_取消(host, self.api_托管动作())
        elif self.页面 == S.新局:
            self.新局.api_取消(host, lambda: self.api_页面(S.菜单))
        elif self.页面 in (S.设置, S.读取, S.保存, S.查询):
            self.api_声音(4)
            self.页面 = self.api_返回页面()
        elif self.页面 == S.游戏:
            if self.api_银行待决():
                self.银行.api_取消(host, self.会话.待决策, self.api_回答值)
            elif self.api_设施可取消():
                self.设施.api_取消(host, self.会话.待决策, self.api_回答)

    def api_通知(self, arg_成功: bool, arg_失败: str = "目前無法使用") -> None:
        if not arg_成功:
            self.api_提示(arg_失败)
        self.api_观察()

    def api_回答值(self, arg_值: int, arg_金额: int) -> bool:
        decision = self.会话.待决策
        if decision is None:
            return False
        for i, option in enumerate(decision.选项):
            if option.值 == arg_值:
                self.银行金额 = arg_金额
                success = self.会话.api_回答(i, arg_金额)
                self.api_观察()
                return success
        return False

    def api_回答(self, arg_索引: int) -> bool:
        decision = self.会话.待决策
        if decision is None or self.小游戏.api_处理(decision):
            return False
        amount = self.银行金额 if decision.种类 in (决策种类_类.银行, 决策种类_类.初级股票) else 0
        kind = decision.种类
        value = decision.选项[arg_索引].值 if 0 <= arg_索引 < len(decision.选项) else 0
        if not self.会话.api_回答(arg_索引, amount):
            self.api_提示("金額、點數或持有數量不足")
            return False
        if kind == 决策种类_类.拍卖 and 1 <= value <= 5:
            self.api_声音(29)
        return True

    def api_同步决策(self) -> None:
        decision = self.会话.待决策
        if decision is None:
            self.物品.api_结束访问()
            self.决策键, self.选目标, self.目标中心 = "", None, None
            return
        key = decision.提示 + ":" + str(int(decision.种类))
        key += "".join(":" + str(o.值) for o in decision.选项)
        if self.决策键 == key:
            return
        self.数字板.api_关闭()
        self.决策键, self.决策页, self.选目标, self.目标中心 = key, 0, None, None
        if decision.种类 == 决策种类_类.初级股票:
            self.银行金额 = min(100, decision.金额上限)

    def api_地图决策(self) -> bool:
        return self.会话.待决策 is not None and any(
            o.位置 is not None for o in self.会话.待决策.选项
        )

    def api_选目标(self, arg_索引: int) -> None:
        if (
            self.会话 is None
            or self.会话.待决策 is None
            or not 0 <= arg_索引 < len(self.会话.待决策.选项)
        ):
            return
        self.选目标 = arg_索引
        location = self.会话.待决策.选项[arg_索引].位置
        if location is not None:
            self.目标中心 = location.x, location.y

    def api_确认索引(self, arg_值: int) -> int:
        return next((i for i, o in enumerate(self.会话.待决策.选项) if o.值 == arg_值), 0)

    def api_开新局(self, arg_阶段: int) -> None:
        self.新局.api_打开(arg_阶段, self.选地图 if arg_阶段 == self.选阶段 else 0, self.设置.种子)
        self.页面 = 应用页面_类.新局

    def api_转图(self, arg_增加: int) -> None:
        self.旋转 = (self.旋转 + arg_增加) % 8
        if self.会话 is not None:
            self.会话.api_设相机(self.旋转)

    def api_掷骰(self) -> None:
        if self.呈现.api_可推进():
            self.会话.api_掷骰()

    def api_骰数(self, arg_数量: int) -> None:
        success = self.会话.api_设骰数(arg_数量)
        self.骰数次数 += int(success)
        self.api_通知(success)

    def api_应用选项(self, arg_状态: 选项状态_类) -> None:
        self.速度, self.声效, self.互动小游戏 = arg_状态.速度, arg_状态.音效, arg_状态.动画
        if self.音频.api_音乐启用() != arg_状态.音乐:
            self.音频.api_音乐开关(arg_状态.音乐)
        if self.会话 is not None:
            self.会话.api_互动小游戏(arg_状态.动画 and not self.设置.验证天数)

    def api_试听(self, arg_曲目: int) -> None:
        if not self.音频.api_音乐启用():
            self.音频.api_音乐开关(True)
        self.音频.api_选音乐(arg_曲目)
        self.音乐导演.api_忘记()

    def api_回标题(self) -> None:
        if self.会话 is not None and self.会话.api_可保存() and not self.设置.验证天数:
            self.api_写存档(self.api_槽路径(0))
        self.消息.api_清空()
        self.转盘.api_清空()
        self.月报.api_清空()
        self.小游戏.api_清空()
        self.电影.api_清空()
        self.呈现.步骤.clear()
        self.呈现.等待毫秒, self.呈现.呈现玩家 = 0, None
        self.物品.api_重置()
        self.拍卖.api_重置()
        self.步声.api_停止(self.音频)
        self.地图弹框 = None
        self.会话 = None
        self.页面 = self.前页面 = 应用页面_类.菜单

    def api_读槽(self) -> list[存档槽_类]:
        slots = [存档槽_类() for _ in range(6)]
        for i in range(6):
            path = self.api_槽路径(i)
            try:
                data, _ = 存档事务_类(path).api_读取(self.设置.种子)
                save = 存档_类.api_解码(data)
                header = save.api_头()
                if header.签名 != 0x26:
                    continue
                slots[i] = 存档槽_类(
                    True,
                    header.日期,
                    header.地图,
                    header.阶段,
                    [save.api_玩家(j).角色 for j in range(min(header.人数, 4))],
                )
            except (OSError, ValueError, RuntimeError):
                # 原选择窗的坏槽不可用；真正点击读档的错误由读取入口报告且保留当前局。
                continue
        return slots

    def api_载入路径(self) -> Path:
        if self.设置.载入 is not None:
            return self.设置.载入
        # 首次保存若在提交点后被杀，尚无DAT也须先完成日志，才能参与最近槽选择。
        self.api_读槽()
        newest = self.api_槽路径(1)
        for i in range(6):
            path = self.api_槽路径(i)
            if path.exists() and (
                not newest.exists() or path.stat().st_mtime_ns > newest.stat().st_mtime_ns
            ):
                newest = path
        return newest

    def api_开读取(self) -> None:
        if self.设置.载入 is not None:
            self.api_读取(self.设置.载入)
            return
        slots = self.api_读槽()
        if not any(s.有效 for s in slots):
            self.api_提示("沒有存檔")
            return
        self.存档槽.api_打开(False, slots)
        self.页面 = 应用页面_类.读取

    def api_开保存(self) -> None:
        if self.会话 is not None and self.会话.api_可保存():
            self.存档槽.api_打开(True, self.api_读槽())
            self.页面 = 应用页面_类.保存

    def api_选槽(self, arg_槽: int) -> None:
        if self.存档槽.api_保存中():
            self.api_写存档(self.api_槽路径(arg_槽))
            self.设置.载入 = None
            self.保存次数 += 1
            self.api_提示("存檔完成")
            self.页面 = 应用页面_类.游戏
        else:
            previous = self.api_返回页面()
            if not self.api_读取(self.api_槽路径(arg_槽)):
                self.页面 = previous

    def api_保存(self) -> None:
        if self.会话 is not None and self.会话.api_可保存():
            self.api_写存档(self.api_槽路径(1))
            self.设置.载入 = None
            self.保存次数 += 1
            self.api_提示("存檔完成")

    def api_开交易(self) -> None:
        if self.会话.api_开交易():
            self.页面 = 应用页面_类.交易
            self.交易.api_重置()

    def api_关股票(self) -> None:
        self.数字板.api_关闭()
        self.股票.api_重置()
        self.页面 = 应用页面_类.游戏
        self.api_通知(self.会话.api_关股市(), "目前無法完成股市結算")

    def api_股票买卖(self, arg_买: bool, arg_股: int, arg_数量: int) -> bool:
        self.选股票 = arg_股
        success = (
            self.会话.api_买股票(arg_股, arg_数量)
            if arg_买
            else self.会话.api_卖股票(arg_股, arg_数量)
        )
        if success:
            if arg_买:
                self.买股票次数 += 1
            else:
                self.卖股票次数 += 1
        self.api_通知(success, "休市、限價或可交易數量不足")
        return success

    def api_股票动作(self) -> 股票动作_类:
        return 股票动作_类(
            lambda i, n: self.api_股票买卖(True, i, n),
            lambda i, n: self.api_股票买卖(False, i, n),
            self.api_关股票,
        )

    def api_关交易(self) -> None:
        self.数字板.api_关闭()
        self.交易.api_重置()
        self.页面 = 应用页面_类.游戏
        self.api_通知(self.会话.api_关交易(), "目前無法完成買賣結算")

    def api_挂牌(self, arg_挂单: 挂单_类) -> bool:
        success = self.会话.api_挂牌(arg_挂单)
        self.挂牌次数 += int(success)
        self.api_通知(True)
        return success

    def api_撤件(self, arg_索引: int) -> bool:
        success = self.会话.api_撤单(arg_索引)
        self.撤单次数 += int(success)
        self.api_通知(True)
        return success

    def api_购买报价(self, arg_卖家: int, arg_索引: int) -> bool:
        success = self.会话.api_买报价(arg_卖家, arg_索引)
        self.买报价次数 += int(success)
        self.api_通知(True)
        return success

    def api_交易动作(self) -> 交易动作_类:
        return 交易动作_类(self.api_挂牌, self.api_撤件, self.api_购买报价, self.api_关交易)

    def api_呈现玩家(self) -> int:
        if self.呈现.呈现玩家 is not None:
            return self.呈现.呈现玩家
        return self.会话.世界.头.当前玩家 if self.会话 is not None else 0

    def api_托管应用(self, arg_槽: int, arg_设置: 托管设置_类) -> None:
        waits = self.会话.阶段 not in (游戏阶段_类.人类待命, 游戏阶段_类.结束)
        if arg_设置.自动 and self.会话.api_可保存():
            self.api_写存档(self.api_槽路径(0))
        if self.会话.api_设置托管(arg_槽, arg_设置) and waits:
            self.api_通知(False, "設定將於本回合結束後生效")
        self.api_观察()

    def api_托管动作(self) -> 托管动作_类:
        return 托管动作_类(self.api_托管应用, lambda: self.api_页面(应用页面_类.游戏))

    def api_物品宿主(self) -> 物品宿主_类:
        return 物品宿主_类(lambda: self.api_页面(应用页面_类.游戏), self.api_通知, self.api_回答)

    def api_地图提示(self, arg_x: int, arg_y: int) -> None:
        if self.地图弹框 is not None:
            self.地图弹框 = None
            return
        code = 地图拾取_类.api_拾取(self.会话.世界, self.当前相机, arg_x, arg_y)
        if code and 地图提示_类.api_文字(self.会话.世界, code):
            self.地图弹框 = 地图弹框_类(arg_x, arg_y, code)
            self.api_声音(1)

    def api_开始结局(self) -> None:
        world = self.会话.世界
        stage, map_id = world.头.阶段 % 2, world.头.地图 % 4
        if self.会话.胜者 is not None:
            character = world.玩家[self.会话.胜者].记录.角色
            self.消息.api_入队(self.消息规则.api_事件气泡(character, 24, None))
            if self.清关阶段 != stage:
                self.清关掩码 = 0
            self.清关阶段, self.清关掩码 = stage, self.清关掩码 | (1 << map_id)
            self.结局.api_过关(
                过关资料_类(
                    stage,
                    map_id,
                    character,
                    self.清关掩码,
                    self.人类数 <= 1,
                    self.设置.种子 ^ (self.会话.完成天数 & 0xFFFFFFFF),
                )
            )
        elif self.人类数 <= 1:
            self.结局.api_再玩()
        else:
            self.页面 = 应用页面_类.菜单

    def api_同意再玩(self) -> None:
        world = self.会话.世界
        character = world.玩家[world.头.当前玩家 % len(world.玩家)].记录.角色
        self.消息.api_入队(self.消息规则.api_事件气泡(character, 26, None))

    def api_再玩完成(self, arg_读取: bool) -> None:
        self.页面 = 应用页面_类.菜单
        if arg_读取:
            self.api_开读取()

    def api_下一图(self, arg_地图: int) -> None:
        self.选阶段, self.选地图 = self.清关阶段, arg_地图
        self.api_开新局(self.清关阶段)

    def api_结局动作(self) -> 结局动作_类:
        return 结局动作_类(
            self.api_同意再玩,
            self.api_再玩完成,
            self.api_下一图,
            lambda: self.api_页面(应用页面_类.菜单),
        )
