# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_game.cpp::draw/draw_board/draw_decision及电影/开局/月结覆盖次序。
# ◑ 导入
from rich4.application_types import 应用页面_类
from rich4.cards import 目标种类_类
from rich4.game_types import 公告种类_类, 决策_类, 决策种类_类, 游戏阶段_类
from rich4.graphics import 图像_类
from rich4.main_menu import 主菜单动作_类
from rich4.main_scene import 主板场景_类
from rich4.main_screen_types import 主屏动作_类
from rich4.message_overlay import 消息种类_类
from rich4.native_ui import 原生界面_类
from rich4.options_types import 选项动作_类, 选项状态_类
from rich4.screen_draw import 屏幕绘图_类
from rich4.tile_popup import 地图提示_类


# ◕ 功能
class 应用绘制_类:
    """
    原软件画布合成与专属决策路由；不推进游戏规则或用通用屏替代原专屏。

    更新日志：
    2026.10.24 - 保留模态覆盖清命中、原确认选项和地图二次选择；复用已差分场景构造。
    """

    def _经过(self, arg_上次: int) -> int:
        return min((self.时钟 - arg_上次) & 0xFFFFFFFFFFFFFFFF, 100) if arg_上次 else 0

    def api_绘制(self, arg_时钟: int) -> 图像_类:
        self.时钟 = arg_时钟 & 0xFFFFFFFFFFFFFFFF
        self.按钮.clear()
        self.消息.api_退休()
        self.画布 = 图像_类(640, 480, [原生界面_类.api_颜色(7, 30, 55)] * 307200)
        self.框.画布, self.框.时钟 = self.画布, self.时钟
        S = 应用页面_类
        if self.页面 != self.上页面:
            self.前页面, self.上页面 = self.上页面, self.页面
            self.数字板.api_关闭()
            if self.页面 == S.设置:
                self.选项.api_打开(
                    选项状态_类(self.速度, self.音频.api_音乐启用(), self.声效, self.互动小游戏),
                    self.会话 is not None,
                )
            if self.页面 == S.查询 and self.会话 is not None:
                self.查询.api_打开(self.会话.世界.头.当前玩家)
            if self.页面 == S.托管 and (
                self.会话 is None or not self.托管.api_打开(self.会话, self.api_呈现玩家())
            ):
                self.页面 = self.上页面 = S.游戏
        if not self.api_银行待决():
            self.银行.api_重置()
        host = self.api_宿主()
        if self.会话 is not None:
            self.电影.api_服装(tuple(self.会话.api_服装(i) for i in range(4)))
            if self.呈现.api_可推进():
                self.电影.api_记忆(self.会话.世界, self.会话, self.时钟)
            self.物品.api_运行延迟()
        self.物品.截图名 = ""
        if self.设置.验证天数:
            self.物品.时钟 = self.帧数 * 250
        menu = (
            self.页面 == S.菜单
            or self.页面 in (S.设置, S.读取)
            and self.前页面 == S.菜单
            or self.会话 is None
        )
        if menu and self.页面 != S.新局:
            if self.页面 != S.菜单:
                self.框.api_资源图("d", 1, 0, 0, 0)
        elif self.会话 is not None and self.页面 != S.新局:
            self.api_绘棋盘()
        if self.会话 is not None and self.页面 == S.游戏 and not self.物品.api_卡图中():
            self.api_绘电影()
            if not self.电影.api_活跃():
                elapsed = self._经过(self.转盘时钟)
                self.转盘时钟 = self.时钟
                self.转盘.api_绘效果(
                    self.框, self.会话.世界, 40 if self.设置.验证天数 else elapsed, 901
                )
        if (
            self.会话 is not None
            and self.页面 == S.游戏
            and self.月报.api_活跃()
            and not self.电影.api_活跃()
            and not self.转盘.api_活跃()
        ):
            elapsed = self._经过(self.月报时钟)
            self.月报时钟 = self.时钟
            self.月报.api_绘制(
                self.框, self.会话.世界, 40 if self.设置.验证天数 else elapsed * self.速度
            )
        if self.会话 is not None and self.页面 == S.游戏:
            elapsed = self._经过(self.开场时钟)
            self.开场时钟 = self.时钟
            if self.开场.api_活跃():
                self.开场.api_绘制(self.画布, elapsed, self.api_声音)
                if self.开场.api_活跃():
                    self.按钮.clear()
        if self.会话 is not None and self.页面 == S.游戏 and self.时钟 < self.股票卡截止:
            self.按钮.clear()
            self.股票.api_卡片目标(host, self.会话.世界, self.股票卡玩家, None, 210, self.api_回答)
        elif self.股票卡截止:
            self.股票卡截止, self.股票.选中 = 0, None
        if self.页面 == S.菜单:
            self.清关掩码 = 0
            self.主菜单.api_绘制(
                host,
                主菜单动作_类(
                    self.api_继续或新局,
                    self.api_开读取,
                    lambda: self.api_页面(S.设置),
                    self.api_退出,
                    lambda: self.api_开新局(1),
                    self.api_载入路径().exists()
                    or any(self.api_槽路径(i).exists() for i in range(6)),
                ),
            )
        elif self.页面 == S.新局:
            self.新局.api_绘制(host, self.api_新局, lambda: self.api_页面(S.菜单))
        elif self.页面 == S.设置:
            self.按钮.clear()
            self.选项.api_绘制(
                host,
                选项动作_类(
                    self.api_应用选项,
                    lambda: self.api_页面(self.api_返回页面()),
                    self.api_试听,
                    self.音频.api_音乐曲目() if self.音频.api_音乐启用() else 0,
                    lambda: self.api_开新局(self.选阶段),
                    self.api_回标题,
                    lambda: self.帮助.api_打开(-1, -1),
                ),
            )
        elif self.页面 in (S.读取, S.保存):
            self.按钮.clear()
            self.存档槽.api_绘制(
                host, self.api_选槽,
                lambda: self.api_页面(self.api_返回页面()),
                self.api_切换自动槽 if self.页面 == S.读取 else None,
            )
        elif self.页面 == S.查询:
            self.按钮.clear()
            self.查询.api_绘制(host, self.会话.世界, lambda: self.api_页面(S.游戏))
        elif self.页面 in (S.卡片, S.道具):
            self.按钮.clear()
            self.物品.api_画库存(self.框, self.会话, self.页面 == S.卡片, self.api_物品宿主())
        elif self.页面 == S.股票:
            self.按钮.clear()
            self.股票.api_绘制(
                host, self.会话.世界, self.会话.世界.头.当前玩家, self.数字板, self.api_股票动作()
            )
        elif self.页面 == S.交易:
            self.按钮.clear()
            self.交易.api_绘制(
                host, self.会话.世界, self.会话.世界.头.当前玩家, self.数字板, self.api_交易动作()
            )
        elif self.页面 == S.托管 and self.会话 is not None:
            self.按钮.clear()
            self.托管.api_绘制(host, self.会话.世界, self.api_托管动作())
        if self.页面 == S.游戏 and self.会话 is not None and self.消息.api_活跃():
            self.消息.api_绘制(self.框)
        if (
            self.页面 == S.游戏
            and self.会话 is not None
            and self.物品.api_电脑施法中()
            and not self.消息.api_活跃()
        ):
            self.按钮.clear()
            self.物品.api_画电脑施法(self.框)
        if (
            self.页面 == S.游戏
            and self.会话 is not None
            and self.拍卖.api_成交中()
            and not self.消息.api_活跃()
        ):
            self.按钮.clear()
            self.拍卖.api_画成交(host, self.会话.世界)
        if (
            self.物品.api_卡图中()
            and self.会话 is not None
            and self.页面 in (S.游戏, S.卡片, S.道具)
        ):
            self.按钮.clear()
            self.物品.api_画卡图(self.框)
        if self.数字板.api_活跃():
            self.按钮.clear()
            self.数字板.api_绘制(host)
        if self.帮助.api_活跃():
            self.按钮.clear()
            self.帮助.api_绘制(host)
        if self.提示 and self.时钟 < self.提示截止:
            原生界面_类.api_填充(self.画布, (210, 439, 430, 474), 原生界面_类.纸色)
            原生界面_类.api_边框(self.画布, (210, 439, 430, 474), 原生界面_类.蓝色)
            self.字体.api_绘制(self.画布, self.提示, 320 - self.字体.api_测量(self.提示) // 2, 447)
        self.转盘.api_收帧()
        self.帧数 += 1
        return self.画布

    def api_继续或新局(self) -> None:
        if self.会话 is not None and self.会话.阶段 != 游戏阶段_类.结束:
            self.页面 = 应用页面_类.游戏
        else:
            self.api_开新局(0)

    def api_退出(self) -> None:
        self.运行 = False

    def api_绘电影(self) -> None:
        elapsed = self._经过(self.电影时钟)
        self.电影时钟 = self.时钟
        if not self.电影.api_活跃():
            if self.电影.api_保留中():
                current = self.消息.api_当前()
                shown = self.消息.api_活跃() and current.种类 == 消息种类_类.神明字幕
                first = self.呈现.步骤[0] if self.呈现.步骤 else None
                next_caption = (
                    not self.消息.api_活跃()
                    and first is not None
                    and first.事件 is not None
                    and first.事件.公告 == 公告种类_类.神明出现
                )
                if shown or next_caption:
                    self.电影.api_绘留帧(self.画布, self.棋盘, self.会话.世界, self.旋转, self.时钟)
                else:
                    self.电影.api_丢弃末帧()
            return
        self.电影.api_绘制(
            self.画布, self.棋盘, self.会话.世界, self.旋转, elapsed, self.时钟, self.api_声音
        )
        if self.电影.api_活跃():
            self.按钮.clear()

    def api_绘棋盘(self) -> None:
        self.api_同步决策()
        scene, camera = 主板场景_类.api_构建(
            self.会话,
            self.主屏,
            self.电影,
            self.呈现.步骤,
            self.呈现.api_忙碌(),
            self.呈现.呈现玩家,
            self.旋转,
            self.时钟,
            self.目标中心,
            self.消息.api_焦点(),
        )
        self.当前相机 = camera
        self.棋盘.api_绘制(self.画布, scene, camera)
        S = 应用页面_类
        actions = 主屏动作_类(
            lambda: self.帮助.api_打开(20, 60),
            lambda: self.api_页面(S.设置),
            lambda: self.api_页面(S.托管),
            self.api_开读取,
            self.api_开保存,
            lambda: self.api_页面(S.查询),
            lambda: self.api_页面(S.道具),
            lambda: self.api_页面(S.卡片),
            self.api_开交易,
            lambda: self.api_页面(S.股票),
            self.api_转图,
            self.api_掷骰,
            self.api_骰数,
            self.api_声音,
            self.会话.api_可保存(),
            self.api_载入路径().exists(),
        )
        idle = (
            self.页面 == S.游戏
            and self.会话.阶段 == 游戏阶段_类.人类待命
            and self.会话.待决策 is None
            and not self.消息.api_活跃()
            and self.呈现.api_可推进()
            and not self.主屏.api_骰子忙()
        )
        if not idle:
            self.地图弹框 = None
        elif self.地图弹框 is not None:
            地图提示_类.api_绘制(self.框, self.会话.世界, self.地图弹框)
        self.主屏.api_绘制(self.框, self.会话, self.旋转, actions)
        if idle:
            self.框.api_命中(
                95, camera.视口, lambda: self.api_地图提示(self.框.指针x, self.框.指针y)
            )
            self.按钮[-1].点击声音 = False
        if self.页面 == S.游戏 and self.会话.待决策 is not None and self.呈现.api_可推进():
            self.api_绘决策()
        self.api_绘结局()

    def api_绘结局(self) -> None:
        if self.会话.阶段 != 游戏阶段_类.结束 or self.页面 != 应用页面_类.游戏:
            return
        if self.结局会话 is not self.会话:
            if not self.呈现.api_可推进():
                return
            self.结局会话 = self.会话
            self.api_开始结局()
        if self.结局.api_活跃():
            self.按钮.clear()
            self.结局.api_绘制(self.api_宿主(), self.消息.api_活跃(), self.api_结局动作())

    def api_绘决策(self) -> None:
        self.按钮.clear()
        d, K, host = self.会话.待决策, 决策种类_类, self.api_宿主()
        if self.配音决策键 != self.决策键:
            self.配音决策键 = self.决策键
            self.api_配音决策(d)
        if d.种类 == K.银行:
            self.银行.api_绘制(host, self.会话.世界, d, self.数字板, self.api_回答值)
        elif d.种类 == K.初级股票:
            self.一级股票.api_绘制(host, self.会话.世界, d, self.数字板, self.api_回答值)
        elif d.种类 == K.彩票:
            self.彩票.api_绘制(
                host, self.会话.世界, d, self.api_回答, self.彩票告别, self.api_彩票再见
            )
        elif d.种类 == K.拍卖:
            self.拍卖.api_绘制(host, self.会话.世界, d, self.api_回答)
        elif self.api_地图决策():
            self.api_绘地图决策(self.消息规则.api_本地化(d, self.会话.世界))
        elif d.种类 == K.行动目标 and any(
            o.对象 is not None and o.对象.种类 == 目标种类_类.股票 for o in d.选项
        ):
            player = d.玩家
            self.股票.api_卡片目标(
                host, self.会话.世界, player, d, 210, lambda i: self.api_股票卡回答(i, player)
            )
        elif self.物品.api_画决策(self.框, self.会话, self.api_物品宿主()):
            return
        elif self.小游戏.api_处理(d):
            result = self.小游戏.api_绘决策(self.框, d)
            if result is not None:
                self.会话.api_提交小游戏(result.分数, result.随机次数)
        elif self.转盘.api_处理决策(d):
            self.转盘.api_绘决策(self.框, self.会话.世界, d, 210, lambda: self.api_回答(0))
        elif self.设施.api_接管(d):
            self.设施.api_绘制(host, d, self.决策键, self.api_回答)
        elif self.消息规则.api_是确认(d):
            card = d.种类 == K.卡片目标
            yes, no = (0, 1) if card else (self.api_确认索引(1), self.api_确认索引(0))
            self.消息.api_确认框(
                self.框,
                self.消息规则.api_确认问题(d, self.会话.世界),
                210 + yes,
                lambda: self.api_回答(yes),
                210 + no,
                lambda: self.api_回答(no),
            )
        else:
            self.api_绘普通选择(self.消息规则.api_本地化(d, self.会话.世界))

    def api_彩票再见(self, arg_已买: bool) -> int:
        if not self.声效:
            return 0
        if arg_已买:
            self.api_声音(31)
        return self.api_语音(14 if arg_已买 else 16)

    def api_股票卡回答(self, arg_索引: int, arg_玩家: int) -> None:
        used = self.会话.待决策 is not None and self.会话.待决策.选项[arg_索引].值 >= 0
        self.api_回答(arg_索引)
        if used and not self.设置.验证天数:
            self.股票卡玩家, self.股票卡截止 = arg_玩家, self.时钟 + 1000
        else:
            self.股票.选中 = None

    def api_绘地图决策(self, arg_决策: 决策_类) -> None:
        d, U = arg_决策, 原生界面_类
        U.api_填充(self.画布, (440, 0, 640, 480), U.纸色)
        self.字体.api_绘制(self.画布, d.提示, 449, 16, 16, U.蓝色, 181)
        first = self.决策页 * 8
        self.物品.api_画地图目标(self.框, d, self.当前相机, self.选目标, self.api_地图目标点击)
        self.字体.api_绘制(
            self.画布, "點地圖上的目標，再點一次確認", 449, 66, 12, U.api_颜色(144, 38, 17)
        )
        for i, option in enumerate(d.选项):
            if first <= i < first + 8:
                y = 91 + (i - first) * 34
                label = (str(i + 1) + " " if option.位置 is not None else "") + option.标签
                self.框.api_按钮(
                    210 + i, (448, y, 633, y + 30), label, lambda i=i: self.api_目标列表点击(i)
                )
                if self.选目标 == i:
                    U.api_边框(self.画布, (450, y + 2, 631, y + 28), U.蓝色)
        self.框.api_按钮(
            203, (448, 369, 538, 398), "上一頁", lambda: self.api_翻页(-1), self.决策页 > 0
        )
        self.框.api_按钮(
            204, (543, 369, 633, 398), "下一頁", lambda: self.api_翻页(1), first + 8 < len(d.选项)
        )
        self.框.api_按钮(
            207, (449, 420, 560, 462), "確認目標", self.api_确认目标, self.选目标 is not None
        )
        cancel = next((i for i, o in enumerate(d.选项) if o.标签 == "取消"), None)
        if cancel is not None:
            self.框.api_按钮(208, (567, 420, 632, 462), "取消", lambda: self.api_回答(cancel))

    def api_地图目标点击(self, arg_索引: int) -> None:
        if self.选目标 != arg_索引:
            self.api_选目标(arg_索引)
        else:
            self.api_声音(2)
            self.api_回答(arg_索引)

    def api_目标列表点击(self, arg_索引: int) -> None:
        d = self.会话.待决策
        if d is None or arg_索引 >= len(d.选项):
            return
        if d.选项[arg_索引].位置 is not None:
            self.api_选目标(arg_索引)
        else:
            self.api_回答(arg_索引)

    def api_确认目标(self) -> None:
        if self.选目标 is not None:
            self.api_回答(self.选目标)

    def api_翻页(self, arg_增加: int) -> None:
        self.决策页 += arg_增加

    def api_绘普通选择(self, arg_决策: 决策_类) -> None:
        d, U = arg_决策, 原生界面_类
        multiple = len(d.选项) > 3
        top, bottom = (52, 438) if multiple else (115, 360)
        self.框.api_对话框((72, top, 570, bottom), "請選擇")
        self.字体.api_绘制(self.画布, d.提示, 97, top + 50, 18, U.墨色, 448)
        if d.种类 in (决策种类_类.商店, 决策种类_类.救援):
            self.字体.api_绘制(
                self.画布,
                "可用點數 " + str(self.会话.世界.玩家[d.玩家].记录.点券),
                110,
                top + 110,
                18,
                U.蓝色,
            )
        elif d.金额:
            text = (
                "轉盤 " + str(d.金额)
                if d.种类 == 决策种类_类.轮盘
                else 屏幕绘图_类.api_货币(d.金额)
            )
            self.字体.api_绘制(self.画布, text, 110, top + 110, 22, U.蓝色)
        width, first = min(160, 430 // max(1, len(d.选项))), self.决策页 * 8
        for i in range(first, min(first + 8, len(d.选项))):
            position, bank = i - first, d.种类 == 决策种类_类.银行
            x = 93 + position % 2 * 232 if multiple else 105 + position * (width + 8)
            y = (
                (200 + position // 2 * 36 if bank else 208 + position // 2 * 44)
                if multiple
                else 290
            )
            self.框.api_按钮(
                210 + i,
                (x, y, x + (220 if multiple else width), y + (32 if bank else 36)),
                d.选项[i].标签,
                lambda i=i: self.api_回答(i),
            )
        if len(d.选项) > 8:
            self.框.api_按钮(
                203, (105, 392, 290, 424), "上一頁", lambda: self.api_翻页(-1), self.决策页 > 0
            )
            self.框.api_按钮(
                204,
                (335, 392, 520, 424),
                "下一頁",
                lambda: self.api_翻页(1),
                first + 8 < len(d.选项),
            )
