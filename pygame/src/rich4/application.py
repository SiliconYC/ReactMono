# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/native_game.cpp::Application；独立Python核心、原组件与Pygame宿主。
# ◑ 导入
import sys
from collections import Counter
from contextlib import ExitStack
from datetime import date
from pathlib import Path

from rich4.ai_settings_screen import 托管屏幕_类
from rich4.application_actions import 应用操作_类
from rich4.application_draw import 应用绘制_类
from rich4.application_input import 应用输入_类
from rich4.application_types import 应用设置_类, 应用页面_类
from rich4.artwork import 美术_类
from rich4.auction_room_screen import 拍卖室_类
from rich4.audio_types import 音乐_类
from rich4.bank_screen import 银行屏幕_类
from rich4.board_audio import 主板声音_类, 步行声音_类, 音乐导演_类
from rich4.board_models import 相机_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.device_audio import 设备音频_类
from rich4.effect_player import 电影播放_类
from rich4.endgame_screen import 结局屏幕_类
from rich4.facility_picker import 设施选择_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类, 决策种类_类, 游戏事件_类, 游戏事件种类_类, 游戏阶段_类
from rich4.graphics import 图像_类
from rich4.help_screen import 帮助屏幕_类
from rich4.intro_player import 开局演出_类
from rich4.item_screens import 物品屏幕_类
from rich4.lottery_bar_screen import 彩票告别_类, 彩票柜台_类
from rich4.main_menu import 主菜单_类
from rich4.main_screen import 主屏幕_类
from rich4.message_overlay import 消息声音_类, 消息层_类
from rich4.message_rules import 消息规则_类
from rich4.minigame_screen import 小游戏屏幕_类
from rich4.minigames import 声音请求_类
from rich4.monthly_common import 月报声音_类
from rich4.monthly_screen import 月报屏幕_类
from rich4.native_frame import 按钮_类, 画框_类
from rich4.native_ui import 字体_类
from rich4.new_game_screen import 新局屏幕_类
from rich4.new_game_types import 新局选择_类
from rich4.number_pad import 数字板_类
from rich4.open_text import 开放文字_类
from rich4.options_screen import 选项屏幕_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.player_info_screen import 玩家查询_类
from rich4.presentation_queue import 呈现宿主_类, 呈现队列_类
from rich4.primary_stock_screen import 一级股票屏幕_类
from rich4.save import 存档_类
from rich4.save_slot_screen import 存档槽屏幕_类
from rich4.save_transaction import 存档事务_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.spinner_screen import 转盘声音_类, 转盘屏幕_类
from rich4.stock_screen import 股票屏幕_类
from rich4.tile_popup import 地图弹框_类
from rich4.trading_board_screen import 交易公告栏_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类
from rich4.world_validation import 世界验证_类


# ◕ 功能
class 游戏应用_类(应用操作_类, 应用绘制_类, 应用输入_类):
    """
    原主应用的会话/表现生命周期；各专属屏幕只发出真实核心操作。

    更新日志：
    2026.10.24 - 正式入口已接通；补齐原旁车字节提取及异常退出的资源释放。
    """

    def __init__(self, arg_设置: 应用设置_类) -> None:
        with ExitStack() as cleanup:
            self.设置, self.时钟 = arg_设置, 0
            self.美术, self.字体 = 美术_类(arg_设置.素材), 字体_类(arg_设置.字体)
            cleanup.callback(self.字体.api_关闭)
            if self.美术.开放:
                self.原文 = 开放文字_类(arg_设置.素材 / "text/original.json")
            else:
                exe = next(p for p in arg_设置.素材.iterdir() if p.name.lower() == "rich4.exe")
                self.原文 = 原版文字_类(原版程序_类.api_读取(exe))
            self.消息规则 = 消息规则_类(self.原文)
            self.按钮: list[按钮_类] = []
            self.画布 = 图像_类(640, 480, [0] * 307200)
            self.框 = 画框_类(self.画布, self.美术, self.字体, self.按钮)
            self.声效, self.互动小游戏, self.速度 = not arg_设置.静音, True, 1
            self.音频 = 设备音频_类(arg_设置.素材, not arg_设置.静音)
            cleanup.callback(self.音频.api_关闭)
            self.会话: 游戏会话_类 | None = None
            self.棋盘: 棋盘绘制_类 | None = None
            self.电影, self.开场 = 电影播放_类(self.美术), 开局演出_类(self.美术)
            self.转盘 = 转盘屏幕_类(
                转盘声音_类(self.api_声音, self.api_循环, self.音频.api_停循环), self.原文
            )
            self.月报 = 月报屏幕_类(月报声音_类(self.api_声音, self.api_语音), self.原文)
            self.小游戏 = 小游戏屏幕_类(self.美术, self._小游戏声音)
            self.消息 = 消息层_类(
                消息声音_类(self.api_语音, self.音频.api_停语音), lambda: self.时钟
            )
            self.主屏, self.主菜单, self.新局 = (
                主屏幕_类(arg_设置.界面预设),
                主菜单_类(),
                新局屏幕_类(),
            )
            self.数字板, self.银行 = 数字板_类(), 银行屏幕_类(self.原文)
            self.一级股票, self.股票 = 一级股票屏幕_类(self.原文), 股票屏幕_类(self.原文)
            self.彩票, self.彩票告别 = 彩票柜台_类(self.原文), 彩票告别_类()
            self.交易, self.拍卖, self.托管 = 交易公告栏_类(self.原文), 拍卖室_类(), 托管屏幕_类()
            self.存档槽, self.选项 = 存档槽屏幕_类(), 选项屏幕_类(self.原文)
            self.查询, self.结局, self.帮助 = 玩家查询_类(self.原文), 结局屏幕_类(), 帮助屏幕_类()
            self.物品, self.设施 = 物品屏幕_类(self.原文), 设施选择_类()
            self.物品.声音, self.物品.语音 = self.api_声音, self.api_说话
            self.呈现 = 呈现队列_类(
                呈现宿主_类(
                    self.api_呈现中,
                    self._观察事件,
                    self._呈现事件,
                    self.转盘.api_入队,
                    self.月报.api_入队,
                    self.电影.api_入队,
                )
            )
            self.步声, self.音乐导演 = 步行声音_类(), 音乐导演_类()
            self.页面 = self.上页面 = self.前页面 = 应用页面_类.菜单
            self.选地图, self.选阶段, self.旋转 = arg_设置.地图 % 4, arg_设置.地图 // 4, 0
            self.运行, self.开场按下, self.拍卖已开 = True, False, False
            self.开场时钟 = self.电影时钟 = self.转盘时钟 = self.月报时钟 = 0
            self.股票卡截止 = self.股票卡玩家 = self.清关掩码 = self.清关阶段 = 0
            self.人类数 = 1
            self.结局会话: 游戏会话_类 | None = None
            self.当前相机, self.目标中心, self.选目标 = 相机_类((0, 0)), None, None
            self.地图弹框: 地图弹框_类 | None = None
            self.决策键, self.配音决策键 = "", ""
            self.决策页, self.银行金额, self.选股票 = 0, 1000, 0
            self.上保存轮: int | None = None
            self._自动存档首存 = False
            self._自动存档错误轮: int | None = None
            self.提示, self.提示截止, self.帧数 = "", 0, 0
            self.事件计数, self.最近 = Counter(), []
            self.新局次数 = self.读取次数 = self.保存次数 = 0
            self.买股票次数 = self.卖股票次数 = self.骰数次数 = 0
            self.挂牌次数 = self.撤单次数 = self.买报价次数 = 0
            self.首随机: int | None = None
            fast = bool(arg_设置.验证天数)
            skip = fast and not arg_设置.播放效果
            self.电影.api_跳过(skip)
            self.转盘.api_跳过(skip)
            self.月报.api_跳过(skip)
            self.主屏.api_跳过投掷(skip)
            self.消息.api_即时(fast)
            self.数字板.api_缩放(2 if arg_设置.触摸 else 1)
            cleanup.pop_all()
        self._已关闭 = False

    def api_声音(self, arg_编号: int) -> None:
        if self.声效 and arg_编号 >= 0:
            self.音频.api_播音(arg_编号)

    def api_循环(self, arg_编号: int) -> None:
        if self.声效:
            self.音频.api_播循环(arg_编号)

    def api_语音(self, arg_编号: int) -> int:
        return self.音频.api_语音(arg_编号) if self.声效 else 0

    def api_说话(self, arg_编号: int, arg_排队: bool) -> None:
        if self.声效:
            if arg_排队:
                self.音频.api_排语音(arg_编号)
            else:
                self.音频.api_语音(arg_编号)

    def _小游戏声音(self, arg_声音: 声音请求_类) -> None:
        if arg_声音.操作 == 0:
            self.api_声音(arg_声音.音效)
        elif arg_声音.操作 == 1:
            self.api_循环(arg_声音.音效)
        else:
            self.音频.api_停循环()

    def api_提示(self, arg_文字: str, arg_毫秒: int = 2200) -> None:
        self.提示, self.提示截止 = arg_文字, self.时钟 + arg_毫秒

    def api_宿主(self) -> 屏幕宿主_类:
        return 屏幕宿主_类(
            self.框, self.api_声音, self.api_提示, bool(self.设置.验证天数), self.api_语音
        )

    def api_页面(self, arg_页面: 应用页面_类) -> None:
        self.页面 = arg_页面

    def api_呈现中(self) -> bool:
        return (
            self.时钟 < self.股票卡截止
            or self.开场.api_活跃()
            or self.主屏.api_骰子忙()
            or self.电影.api_活跃()
            or self.消息.api_活跃()
            or self.转盘.api_活跃()
            or self.月报.api_活跃()
            or self.拍卖.api_成交中()
            or self.物品.api_电脑施法中()
        )

    def _观察事件(self, arg_事件: 游戏事件_类) -> None:
        self.事件计数[arg_事件.种类] += 1
        self.物品.api_观察(arg_事件, self.会话.世界)
        if arg_事件.种类 != 游戏事件种类_类.已移动 and arg_事件.消息:
            self.最近.append(arg_事件.消息)
            self.最近[:] = self.最近[-5:]

    def _呈现事件(self, arg_事件: 游戏事件_类) -> None:
        self.主屏.api_事件(arg_事件, self.会话, self.美术)
        message = self.消息规则.api_从事件(arg_事件, self.会话.世界)
        if message is not None:
            self.消息.api_入队(message)
        if arg_事件.消息 in ("拍卖成交", "地产拍卖流拍"):
            self.拍卖已开 = False
        skip = self.设置.验证天数 and not self.设置.播放效果
        if arg_事件.种类 == 游戏事件种类_类.提示 and not skip:
            if arg_事件.消息 == "拍卖成交" and arg_事件.主体 >= 0:
                self.拍卖.api_成交(arg_事件.主体, arg_事件.金额, arg_事件.地产)
            if arg_事件.消息 == "魔法屋施法":
                self.物品.api_开始电脑施法(arg_事件.次主体, arg_事件.值)
        if not self.声效:
            return
        if arg_事件.音效 is not None:
            self.api_声音(arg_事件.音效)
        if arg_事件.消息 == "拍卖成交":
            self.api_声音(63)
            self.api_说话(135, False)
            if 0 <= arg_事件.主体 < len(self.会话.世界.玩家):
                self.api_说话(136 + self.会话.世界.玩家[arg_事件.主体].记录.角色, True)
        elif arg_事件.消息 == "地产拍卖流拍":
            self.api_说话(148, False)
        sound = {游戏事件种类_类.已购地: 49, 游戏事件种类_类.已升级: 50, 游戏事件种类_类.已付租: 55}
        if arg_事件.种类 in sound:
            self.api_声音(sound[arg_事件.种类])

    def api_观察(self) -> None:
        if self.会话 is not None:
            self.呈现.api_观察会话(self.会话, bool(self.设置.验证天数), self.设置.播放效果)

    def api_推进(self, arg_毫秒: int) -> None:
        if (
            self.会话 is not None
            and self.页面 == 应用页面_类.游戏
            and not self.物品.api_卡图中()
            and not self.帮助.api_活跃()
        ):
            self.api_观察()
            self.呈现.api_消费等待(arg_毫秒)
            if not (self.电影.api_活跃() or self.消息.api_活跃() or self.开场.api_活跃()):
                self.主屏.api_递进(arg_毫秒)
            self.呈现.api_泵(self.会话, bool(self.设置.验证天数), self.设置.播放效果)
            if self.呈现.api_可推进():
                self.电影.api_记忆(self.会话.世界, self.会话, self.时钟)
                self.会话.api_步进(arg_毫秒)
            self.api_观察()
            self.api_检查自动存档()
        self.api_更新音频()
        self.音频.api_更新()

    def api_安装会话(self, arg_世界: 世界_类, arg_种子: int, arg_开场: bool = False) -> None:
        世界验证_类.api_验证(arg_世界)
        candidate = 游戏会话_类(arg_世界, arg_种子)
        board = 棋盘绘制_类(self.设置.素材, arg_世界.头.阶段 * 4 + arg_世界.头.地图)
        self.会话, self.棋盘 = candidate, board
        if self.首随机 is None:
            self.首随机 = candidate.随机.状态
        self.旋转, self.页面 = candidate.世界.相机旋转 % 8, 应用页面_类.游戏
        self.结局.api_关闭()
        self.结局会话 = None
        self.人类数 = sum(bool(p.记录.控制标志 & 1) for p in candidate.世界.玩家)
        # 载入现有存档只恢复当前会话，不立即覆盖旧的自动恢复点。
        self.上保存轮 = candidate.世界.轮数
        self._自动存档首存 = False
        self._自动存档错误轮 = None
        self.数字板.api_关闭()
        self.消息.api_清空()
        self.转盘.api_清空()
        self.月报.api_清空()
        self.小游戏.api_清空()
        candidate.api_互动小游戏(self.互动小游戏 and not self.设置.验证天数)
        self.步声.api_停止(self.音频)
        self.拍卖已开 = False
        self.呈现.步骤.clear()
        self.呈现.等待毫秒, self.呈现.呈现玩家, self.呈现.破产音乐 = 0, None, False
        self.物品.api_重置()
        self.拍卖.api_重置()
        self.开场.api_跳过()
        if arg_开场 and not (self.设置.验证天数 and not self.设置.播放效果):
            self.开场.api_开始([p.记录.角色 for p in candidate.世界.玩家 if p.记录.控制标志])
            self.开场时钟, self.开场按下 = 0, False
        self.api_观察()

    def api_新局(self, arg_选择: 新局选择_类) -> bool:
        self.设置.载入 = None
        today = date.today()
        day = self.设置.日期 or (
            (5, 10, 2026) if self.设置.验证天数 else (today.day, today.month, today.year)
        )
        self.选地图, self.选阶段 = arg_选择.地图, arg_选择.阶段
        self.音频.api_选音乐(1)
        self.音乐导演.api_忘记()
        config = 新局设置_类(
            day,
            arg_选择.地图,
            arg_选择.阶段,
            arg_选择.资金,
            arg_选择.租期,
            self.设置.种子,
            arg_选择.玩家,
        )
        try:
            world = 世界_类.api_从地图(
                self.美术.api_解码("m", (arg_选择.阶段 * 4 + arg_选择.地图) * 2 + 1), config
            )
            self.api_安装会话(world, self.设置.种子, True)
        except (ValueError, OSError, RuntimeError) as error:
            print("[错误] 无法开始新局：" + str(error), file=sys.stderr)
            self.api_提示("無法開始新遊戲", 3500)
            self.页面 = 应用页面_类.菜单
            return False
        # 新局建立首个自动恢复点；已进入首位玩家的可保存状态才会写入。
        self._自动存档首存 = True
        self.api_检查自动存档()
        self.新局次数 += 1
        return True

    def api_槽路径(self, arg_槽: int) -> Path:
        if arg_槽 == 0:
            return self.设置.存档目录 / "Autosave.DAT"
        if 1 <= arg_槽 <= 5:
            return self.设置.存档目录 / f"Save{arg_槽}.DAT"
        raise ValueError("无效存档槽位")

    def api_检查自动存档(self) -> None:
        session = self.会话
        if (
            session is None
            or self.设置.验证天数
            or session.阶段 != 游戏阶段_类.人类待命
            or not session.api_可保存()
        ):
            return
        # 世界轮数仅在全部有效玩家完成、跨轮日期结算后才递增。
        # 不能以“换到下一名玩家”作为自动保存条件。
        round_number = session.世界.轮数
        if not self._自动存档首存 and self.上保存轮 == round_number:
            return
        try:
            self.api_写存档(self.api_槽路径(0))
        except (OSError, ValueError, RuntimeError) as error:
            if self._自动存档错误轮 != round_number:
                print("[错误] 自动存档失败：" + str(error), file=sys.stderr)
                self.api_提示("自動存檔失敗，請手動保存", 3500)
                self._自动存档错误轮 = round_number
            return
        self.上保存轮 = round_number
        self._自动存档首存 = False
        self._自动存档错误轮 = None

    def api_写存档(self, arg_路径: Path) -> None:
        if self.会话 is None:
            raise ValueError("没有当前会话可保存")
        存档事务_类(arg_路径).api_写入(self.会话.api_导出存档().api_导出(), self.会话.随机.状态)

    def api_读取(self, arg_路径: Path) -> bool:
        try:
            data, seed = 存档事务_类(arg_路径).api_读取(self.设置.种子)
            self.api_安装会话(世界_类.api_从存档(存档_类.api_解码(data)), seed)
            # 安装会话已记录载入时的轮数；无论来自自动还是人工存档，
            # 都要等待下一整轮结束才能再次覆盖 Autosave.DAT。
            self.音频.api_选音乐(0)
            self.音乐导演.api_忘记()
            self.读取次数 += 1
            self.api_提示("讀取完成")
            return True
        except (OSError, ValueError, RuntimeError) as error:
            self.api_提示("無法讀取此存檔", 3500)
            print("[错误] 读档失败：" + str(error), file=sys.stderr)
            return False

    def api_更新音频(self) -> None:
        walk = bomb = None
        if (
            self.会话 is not None
            and self.页面 == 应用页面_类.游戏
            and self.声效
            and not self.开场.api_活跃()
            and self.会话.动画 is not None
        ):
            player = self.会话.动画.玩家
            walk = 主板声音_类.api_步行(self.会话.世界, player)
            bomb = 主板声音_类.api_炸弹(self.会话.世界, player)
        self.步声.api_更新(self.音频, walk, bomb, self.时钟)
        if self.会话 is None or self.会话.待决策 is None:
            self.配音决策键 = ""
        if self.呈现.破产音乐 and self.呈现.api_可推进():
            self.呈现.破产音乐 = False
        wanted = []
        page, S = self.页面, 应用页面_类
        from_menu = page in (S.设置, S.读取) and self.前页面 == S.菜单
        if page == S.菜单 or from_menu or (self.会话 is None and page != S.新局):
            wanted = [音乐_类.菜单]
        elif page == S.新局:
            wanted = [音乐_类.新局]
        elif self.会话 is not None:
            holiday = 主板声音_类.api_节庆音乐(self.会话.世界)
            if holiday is not None:
                wanted.append(holiday)
            decision = self.会话.待决策
            monthly = self.月报.api_画面名()
            if self.开场.api_活跃() and page == S.游戏:
                wanted = [音乐_类.静音]
            elif self.会话.阶段 == 游戏阶段_类.结束:
                wanted.append(音乐_类.商店)
            elif self.呈现.破产音乐:
                wanted.append(音乐_类.破产)
            elif monthly in ("lottery", "report"):
                wanted.append(音乐_类.开奖 if monthly == "lottery" else 音乐_类.月报)
            elif decision is not None and decision.小游戏 is not None and self.小游戏.api_活跃():
                wanted.append(
                    (音乐_类.企鹅, 音乐_类.气球, 音乐_类.礼物)[min(decision.小游戏.游戏, 2)]
                )
            elif decision is not None and not self.呈现.步骤 and not self.电影.api_活跃():
                music = 主板声音_类.api_决策音乐(decision)
                if music is not None:
                    wanted.append(music)
        self.音乐导演.api_更新(self.音频, wanted, self.时钟)

    def api_配音决策(self, arg_决策: 决策_类) -> None:
        if arg_决策.种类 == 决策种类_类.彩票:
            if any(o.值 > 0 for o in arg_决策.选项):
                self.api_说话(11, False)
                self.api_说话(12, True)
                self.api_说话(13, True)
            else:
                self.api_说话(15, False)
        elif arg_决策.种类 == 决策种类_类.拍卖 and not self.拍卖已开:
            self.拍卖已开 = True
            self.api_说话(131, False)
            self.api_说话(132, True)

    def api_关闭(self) -> None:
        if not self._已关闭:
            self._已关闭 = True
            try:
                self.音频.api_关闭()
            finally:
                self.字体.api_关闭()
