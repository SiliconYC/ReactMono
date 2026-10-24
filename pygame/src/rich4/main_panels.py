# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/main_screen.cpp的工具栏/信息/地图/日历。
# ◑ 导入
from functools import partial

from rich4.calendar import 日期_类
from rich4.game import 游戏会话_类
from rich4.holidays import 节日_类
from rich4.main_screen_types import 主屏动作_类
from rich4.main_text import 主屏字样_类, 主屏绘字_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.screen_draw import 屏幕绘图_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类


# ◕ 功能
class 主屏布局_类:
    """
    MainScreen布局协作类；使用同一显示状态，读取World但不结算规则。

    更新日志：
    2026.10.24 - 原日历/小地图/四页信息按固定锚点、原字体与真实资源绘制。
    """

    墨, 白, 红 = 2114, 32767, 31744
    _字体绘 = staticmethod(主屏绘字_类.api_文字)
    _框线 = staticmethod(主屏绘字_类.api_线框)
    _色章 = staticmethod(主屏绘字_类.api_色章)

    @staticmethod
    def _钱(arg_数: int) -> str:
        return "$" + 屏幕绘图_类.api_货币(arg_数)

    @staticmethod
    def _锚图(
        arg_框: 画框_类,
        arg_库: str,
        arg_条: int,
        arg_帧: int,
        arg_x: int,
        arg_y: int,
        arg_实心: bool = False,
    ) -> None:
        arg_框.画布.api_绘制(
            arg_框.美术.api_帧(arg_库, arg_条, arg_帧), arg_x, arg_y, arg_强制不透明=arg_实心
        )

    def _绘工具栏(self, arg_框: 画框_类, arg_会话: 游戏会话_类, arg_动作: 主屏动作_类) -> None:
        self._锚图(arg_框, "p", 1, 0, 0, 0, True)
        悬 = arg_框.指针x // 40 if 0 <= arg_框.指针x < 440 and 0 <= arg_框.指针y < 40 else -1
        if 悬 != self._悬停 and 0 <= 悬 < 11 and arg_动作.声音:
            arg_动作.声音(0)
        self._悬停 = 悬
        待命 = self.api_显示人类回合(arg_会话)

        def 开全图() -> None:
            self.全图 = True

        图标 = (
            (81, arg_动作.帮助, True),
            (76, arg_动作.设置, True),
            (82, arg_动作.托管, True),
            (72, arg_动作.载入, arg_动作.可载入),
            (71, arg_动作.保存, arg_动作.可保存),
            (83, 开全图, 待命),
            (75, arg_动作.查询, True),
            (78, arg_动作.道具, 待命),
            (77, arg_动作.卡片, 待命),
            (80, arg_动作.交易, 待命),
            (79, arg_动作.股票, 待命),
        )
        for i, (号, 动作, 启用) in enumerate(图标):
            self._锚图(arg_框, "p", 1, 12 + i if i == 悬 else 1 + i, 40 * i + 20, 20)
            arg_框.api_命中(号, (40 * i, 0, 40 * i + 40, 40), 动作, 启用)

    def _绘信息(self, arg_框: 画框_类, arg_世界: 世界_类, arg_动作: 主屏动作_类) -> None:
        p = self.api_显示槽位(arg_世界)
        人, 页 = arg_世界.玩家[p], self.页签[p] % 4
        记, 状 = 人.记录, 人.状态
        self._锚图(arg_框, "p", 0, 页, 440, 0, True)
        标题 = (
            ("現　金", "存　款", "總資產"),
            ("土　地", "連鎖店", "設　施"),
            ("總市值", "成　本", "經營權"),
            ("點　卷", "貸　款", "保險期"),
        )
        for 行 in range(3):
            self._字体绘(arg_框, 标题[页][行], 450, (80, 145, 208)[行], 0)
        self._字体绘(arg_框, "物價指數  " + str(arg_世界.头.物价), 450, 260, 0)

        def 切页(arg_i: int) -> None:
            if self.页签[p] != arg_i and arg_动作.声音:
                arg_动作.声音(1)
            self.页签[p] = arg_i

        for i, 名 in enumerate(("資金", "地產", "股票", "其他")):
            self._字体绘(
                arg_框,
                名,
                627,
                (35, 108, 178, 250)[i],
                3,
                主屏字样_类(18, self.墨 if i == 页 else 原生界面_类.api_颜色(64, 64, 64), 0),
            )
            arg_框.api_命中(85 + i, (616, i * 70, 640, i * 70 + 70), partial(切页, i))
        原生界面_类.api_填充(arg_框.画布, (523, 57, 609, 69), 0)
        原生界面_类.api_填充(arg_框.画布, (522, 56, 608, 68), 原生界面_类.api_玩家色(记.颜色))
        self._锚图(arg_框, "m", 27 + 记.角色, 0, 482, 40)
        if 状.盟友 and 状.盟友 <= len(arg_世界.玩家):
            self._锚图(arg_框, "m", 27 + arg_世界.玩家[状.盟友 - 1].记录.角色, 1, 524, 64)
        名 = 画框_类.人名[记.角色 % 12]
        数 = len(主屏绘字_类.api_字列(名))
        额 = min(max(画框_类._零除(86 - 数 * 22, 数 - 1), -1), 10) if 数 > 1 else 0
        self._字体绘(arg_框, 名, 564, 40, 2, 主屏字样_类(22, self.墨, 额 + 1))
        主 = p + 1
        if 页 == 0:
            值 = (self._钱(记.现金), self._钱(记.银行), self._钱(股市_类.api_财富(arg_世界, p)))
        elif 页 == 1:
            地数 = 连数 = 建数 = 0
            for 地 in arg_世界.地产[1:]:
                if 地.经济.业主 == 主:
                    地数 += 1
                    连数 += int(地.经济.连锁 != 0)
            for 地 in arg_世界.设施[1:]:
                if 地.业主 == 主:
                    地数 += 1
                    建数 += int(地.等级 != 0)
            值 = (str(地数), str(连数), str(建数))
        elif 页 == 2:
            市值 = 成本 = 0
            for k, 股 in enumerate(arg_世界.股票):
                持 = 人.持仓[k]
                # 这里原UI显式double逐项转int64，不替换为核心财富的x87算法。
                市值 = int(float(市值) + float(持.数量) * 股市_类._浮点(股.浮点位[2]))
                成本 = int(float(成本) + float(持.数量) * 股市_类._浮点(持.成本位))
            公司数 = sum(bool(商.编号 and 商.业主 == 主) for 商 in arg_世界.公司)
            值 = (self._钱(市值), self._钱(成本), str(公司数))
        else:
            值 = (str(记.点券), self._钱(记.贷款), str(状.保险天数) + "天")
            if 记.贷款 and 状.贷款到期:
                日, 月, 年 = arg_世界.头.日期
                到期 = 状.贷款到期
                天 = 日期_类(年, 月, 日).api_日期差(
                    日期_类(到期 >> 16, 到期 >> 8 & 255, 到期 & 255)
                )
                if 天:
                    self._字体绘(arg_框, str(天) + "天", 500, 146, 0)
        for 行 in range(3):
            self._字体绘(arg_框, 值[行], 600, (102, 166, 230)[行], 1, 主屏字样_类(22, self.墨, 0))

    def _绘头部(self, arg_框: 画框_类, arg_世界: 世界_类) -> None:
        人 = arg_世界.玩家[self.api_显示槽位(arg_世界)]
        记, 状 = 人.记录, 人.状态
        self._锚图(arg_框, "p", 0, 4, 440, 0, True)
        self._字体绘(arg_框, "現金", 530, 40, 0)
        self._字体绘(arg_框, "存款", 530, 62, 0)
        原生界面_类.api_填充(arg_框.画布, (529, 33, 635, 37), 0)
        原生界面_类.api_填充(arg_框.画布, (528, 32, 634, 36), 原生界面_类.api_玩家色(记.颜色))
        self._锚图(arg_框, "m", 27 + 记.角色, 0, 482, 40)
        if 状.盟友 and 状.盟友 <= len(arg_世界.玩家):
            self._锚图(arg_框, "m", 27 + arg_世界.玩家[状.盟友 - 1].记录.角色, 1, 524, 64)
        self._字体绘(arg_框, 画框_类.人名[记.角色 % 12], 582, 16, 2, 主屏字样_类(20, self.墨, 0))
        self._字体绘(arg_框, self._钱(记.现金), 634, 41, 1)
        self._字体绘(arg_框, self._钱(记.银行), 634, 63, 1)

    def _地图标记(
        self,
        arg_框: 画框_类,
        arg_世界: 世界_类,
        arg_大图: bool,
        arg_顶: int,
    ) -> None:
        左, 步, 倍 = (20, 400, 11392) if arg_大图 else (440, 200, 5696)
        区 = (左, arg_顶, 左 + 步, arg_顶 + 步)

        def 业色(arg_主: int) -> int:
            return (
                原生界面_类.api_玩家色(arg_世界.玩家[arg_主 - 1].记录.颜色)
                if arg_主 and arg_主 <= len(arg_世界.玩家)
                else self.白
            )

        def 章(arg_x: int, arg_y: int, arg_主: int, arg_号: int) -> None:
            self._色章(
                arg_框.画布,
                arg_框.美术.api_帧("d", 517, arg_号),
                左 + ((arg_x * 倍) >> 16),
                arg_顶 + ((arg_y * 倍) >> 16),
                业色(arg_主),
                区,
            )

        for 地 in arg_世界.地产[1:]:
            if 地.经济.业主:
                章(地.x, 地.y, 地.经济.业主, (26 if arg_大图 else 22) + (地.方向 & 1))
        for 地 in arg_世界.设施[1:]:
            if 地.业主:
                章(地.x, 地.y, 地.业主, (28 if arg_大图 else 24) + (地.方向 & 1))
        for 地 in arg_世界.公司:
            if 地.编号 and 地.业主:
                章(地.x, 地.y, 地.业主, (28 if arg_大图 else 24) + (地.方向 & 1))

    def _地图人物(self, arg_框: 画框_类, arg_世界: 世界_类, arg_大图: bool, arg_顶: int) -> None:
        左, 倍, 帧 = (20, 11392, 5) if arg_大图 else (440, 5696, 6)
        for 人 in arg_世界.玩家[: arg_世界.头.人数]:
            记 = 人.记录
            if 记.x and 记.控制标志 & 3:
                self._锚图(
                    arg_框,
                    "m",
                    27 + 记.角色,
                    帧,
                    左 + ((记.x * 倍) >> 16),
                    arg_顶 + ((记.y * 倍) >> 16),
                )

    def _绘小图(
        self, arg_框: 画框_类, arg_世界: 世界_类, arg_顶: int, arg_动作: 主屏动作_类
    ) -> None:
        self._小图顶 = arg_顶
        区 = (440, arg_顶, 640, arg_顶 + 200)
        self._锚图(arg_框, "m", 16 + arg_世界.头.阶段 * 4 + arg_世界.头.地图, 0, 440, arg_顶, True)
        self._地图标记(arg_框, arg_世界, False, arg_顶)
        左区, 右区 = (443, arg_顶 + 3, 468, arg_顶 + 29), (468, arg_顶 + 3, 494, arg_顶 + 29)
        左按, 右按 = (
            arg_框.按下 and arg_框.api_指针内(左区),
            arg_框.按下 and arg_框.api_指针内(右区),
        )
        self._锚图(arg_框, "d", 517, 18 if 左按 else 20, 443, arg_顶 + 3)
        self._锚图(arg_框, "d", 517, 19 if 右按 else 21, 468, arg_顶 + 3)

        def 转(arg_步: int) -> None:
            if arg_动作.声音:
                arg_动作.声音(1)
            arg_动作.旋转(arg_步)

        arg_框.api_命中(73, 左区, partial(转, 7))
        arg_框.api_命中(74, 右区, partial(转, 1))
        self._地图人物(arg_框, arg_世界, False, arg_顶)
        记 = arg_世界.玩家[self.api_显示槽位(arg_世界)].记录
        bx, by = 440 + ((记.x * 5696) >> 16), arg_顶 + ((记.y * 5696) >> 16)
        self._框线(arg_框.画布, (bx - 15, by - 15, bx + 15, by + 15), self.白, 区)
        if self._自由中心 is not None:
            x, y = (
                440 + ((self._自由中心[0] * 5696) >> 16),
                arg_顶 + ((self._自由中心[1] * 5696) >> 16),
            )
            if x != bx or y != by:
                self._框线(arg_框.画布, (x - 15, y - 15, x + 15, y + 15), self.红, 区)

        def 拖() -> None:
            self._小图拖拽 = True
            self.api_指针移动(arg_框.指针x, arg_框.指针y, True)

        arg_框.api_命中(91, 区, 拖)

    def _绘日历(self, arg_框: 画框_类, arg_世界: 世界_类, arg_动作: 主屏动作_类) -> None:
        日, 月, 年 = arg_世界.头.日期
        今日 = 日期_类(年, 月, 日)
        季 = (3, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3)[(月 + 11) % 12]
        大字 = 主屏字样_类(24, self.墨, 1, self.白, True)
        if self.日历 == 0:
            节 = self._绘图缓存.api_节日(arg_框, arg_世界)
            图 = 节 if 节 is not None else arg_框.美术.api_帧("p", 2, 季)
            arg_框.画布.api_绘制(图, 440, 280, arg_强制不透明=True)
            self._锚图(arg_框, "p", 2, 8, 462, 300)
            self._锚图(arg_框, "p", 2, 11, 492, 301)
            周 = 今日.api_星期()
            假日 = 周 == 0 or 节 is not None
            色, 边 = (self.红, self.墨) if 假日 else (self.墨, self.白)
            self._字体绘(
                arg_框,
                ("星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六")[周 % 7],
                454,
                352,
                3,
                主屏字样_类(16, 色, 1, 边, True),
            )
            self._字体绘(arg_框, str(日), 500, 376, 2, 主屏字样_类(60, 色, 1, 边, True))
        else:
            self._锚图(arg_框, "p", 2, 4 + 季, 440, 280, True)
            首, 天数 = 日期_类(年, 月, 1).api_星期(), 日期_类.api_月天数(年, 月)
            for d in range(1, 天数 + 1):
                格 = 首 + d - 1
                x, y = 470 + 23 * (格 % 7), 378 + 14 * (格 // 7)
                if d == 日:
                    self._框线(
                        arg_框.画布, (x - 10, y - 6, x + 10, y + 8), self.红, (440, 280, 640, 480)
                    )
                闭 = 节日_类.api_休市(日期_类(年, 月, d), arg_世界.头.地图, arg_世界.头.阶段)
                self._字体绘(
                    arg_框, str(d), x, y, 2, 主屏字样_类(12, self.红 if 闭 else self.墨, 1)
                )
        self._字体绘(arg_框, str(年), 580, 288, 0, 大字)
        self._字体绘(
            arg_框, str(月) + "月", 500, 328, 2, 主屏字样_类(28, self.墨, 1, self.白, True)
        )

        def 切(arg_模式: int) -> None:
            if self.日历 != arg_模式 and arg_动作.声音:
                arg_动作.声音(1)
            self.日历 = arg_模式

        arg_框.api_命中(89, (448, 288, 475, 315), partial(切, 0))
        arg_框.api_命中(90, (478, 288, 505, 315), partial(切, 1))

    def _绘全图(self, arg_框: 画框_类, arg_世界: 世界_类) -> None:
        arg_框.按钮.clear()
        self._锚图(arg_框, "m", 16 + arg_世界.头.阶段 * 4 + arg_世界.头.地图, 1, 20, 60, True)
        self._地图标记(arg_框, arg_世界, True, 60)
        self._地图人物(arg_框, arg_世界, True, 60)

        def 关() -> None:
            self.全图 = False

        arg_框.api_命中(84, (0, 0, 640, 480), 关)
