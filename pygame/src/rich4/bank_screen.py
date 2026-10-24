# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/finance.cpp::BankScreen；界面回调不替代银行规则。
# ◑ 导入
from collections.abc import Callable

from rich4.calendar import 日期_类
from rich4.game_types import 决策_类
from rich4.number_pad import 数字板_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类


# ◕ 功能
class 银行屏幕_类:
    """
    原ATM、贷款柜台与董事室，数额确认和离开顺序交给真实GameSession。

    更新日志：
    2026.10.24 - 保留面板时钟、台词声序号、原数额上限及一次还款重试。
    """

    ATM框 = (
        (57, 49, 137, 90),
        (139, 49, 219, 90),
        (221, 49, 264, 90),
        (53, 137, 268, 166),
        (58, 211, 91, 228),
        (97, 211, 130, 228),
        (136, 211, 169, 228),
        (58, 230, 91, 247),
        (97, 230, 130, 247),
        (136, 230, 169, 247),
        (58, 249, 91, 266),
        (97, 249, 130, 266),
        (136, 249, 169, 266),
        (58, 268, 91, 285),
        (97, 268, 130, 285),
        (136, 268, 169, 285),
        (183, 233, 232, 258),
        (175, 260, 232, 285),
    )

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self._原文 = arg_原文
        self._绘 = 屏幕绘图_类()
        self.api_重置()

    def api_重置(self) -> None:
        self._阶段 = self._模式 = 0
        self._开始 = self._拖 = self._侧栏 = False
        self._ATM文 = "0"
        self._行: list[str] = []
        self._行起 = self._侧起 = self._弹止 = 0
        self._弹文 = ""
        self._说号 = self._已声号 = self._声行 = 0

    def api_ATM(self) -> bool:
        return self._阶段 == 0

    def api_柜台(self) -> bool:
        return self._阶段 == 1

    def api_董事室(self) -> bool:
        return self._阶段 == 2

    def api_ATM模式(self) -> int:
        return self._模式

    def api_ATM数字(self) -> str:
        return self._ATM文

    @staticmethod
    def api_ATM数字号(arg_数: int) -> int:
        return (
            934
            if arg_数 == 0
            else 917 + arg_数
            if arg_数 >= 7
            else 923 + arg_数
            if arg_数 >= 4
            else 929 + arg_数
        )

    @staticmethod
    def _有(arg_决策: 决策_类, arg_值: int) -> bool:
        return any(o.值 == arg_值 for o in arg_决策.选项)

    def _说(self, arg_宿: 屏幕宿主_类, *arg_号: int) -> None:
        self._行 = [self._原文.api_配音(i, int(i == 89)).文字 for i in arg_号]
        self._行起 = arg_宿.框.时钟
        self._说号 += 1

    def _离ATM(
        self, arg_宿: 屏幕宿主_类, arg_决策: 决策_类, arg_答: Callable[[int, int], bool]
    ) -> None:
        if any(self._有(arg_决策, v) for v in (3, 4, 5, 6)):
            self._阶段 = 1
            self._说(arg_宿, 75, 76)
        else:
            arg_答(0, 0)

    def api_取消(
        self, arg_宿: 屏幕宿主_类, arg_决策: 决策_类, arg_答: Callable[[int, int], bool]
    ) -> None:
        if arg_宿.声音:
            arg_宿.声音(4)
        if self._阶段 == 0:
            self._离ATM(arg_宿, arg_决策, arg_答)
        elif self._阶段 == 2:
            self._阶段 = 1
            self._说(arg_宿, 91)
        else:
            arg_答(0, 0)

    def _上限(self, arg_世: 世界_类, arg_槽: int) -> int:
        p = arg_世.玩家[arg_槽].记录
        return max(0, p.银行 if self._模式 == 0 else p.现金)

    @staticmethod
    def _拥有(arg_世: 世界_类, arg_槽: int) -> bool:
        n = arg_世.玩家[arg_槽].记录.节点
        if n >= len(arg_世.节点):
            return False
        code = arg_世.节点[n].类型索引
        return (
            6000 < code < 8000
            and code - 6000 < len(arg_世.公司)
            and arg_世.公司[code - 6000].业主 == arg_槽 + 1
        )

    @staticmethod
    def _别人存款(arg_世: 世界_类, arg_槽: int) -> int:
        return min(
            max(sum(p.记录.银行 for i, p in enumerate(arg_世.玩家) if i != arg_槽), -2147483648),
            2147483647,
        )

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_决策: 决策_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
    ) -> None:
        框 = arg_宿.框
        if not self._开始:
            self._开始 = True
            self._模式 = 0 if self._有(arg_决策, 2) else 1
            self._ATM文 = "0"
            days = arg_世.玩家[arg_决策.玩家].状态.银行禁贷天数
            if days and not arg_宿.即时:
                self._弹文 = self._原文.api_原文(0x464AD5) % (days & 127)
                self._弹止 = 框.时钟 + 1500
        if self._阶段 == 0:
            self._画ATM(arg_宿, arg_世, arg_决策, arg_板, arg_答)
        elif self._阶段 == 1:
            self._画柜台(arg_宿, arg_世, arg_决策, arg_板, arg_答)
        else:
            self._画董事室(arg_宿, arg_世, arg_决策, arg_板, arg_答)
        if arg_板.api_活跃() and arg_板.api_比例() > 1 and self._行:
            i = min(((框.时钟 - self._行起) & 0xFFFFFFFFFFFFFFFF) // 2000, len(self._行) - 1)
            self._绘.api_弹框(arg_宿, self._行[i], arg_板.api_提示顶())
        if self._弹文:
            if 框.时钟 < self._弹止:
                self._绘.api_弹框(arg_宿, self._弹文, 196)
            else:
                self._弹文 = ""
        if self._行 and arg_宿.语音:
            i = min(((框.时钟 - self._行起) & 0xFFFFFFFFFFFFFFFF) // 2000, len(self._行) - 1)
            if self._说号 != self._已声号 or i != self._声行:
                self._已声号, self._声行 = self._说号, i
                for v in range(75, 92):
                    if self._行[i] == self._原文.api_配音(v, int(v == 89)).文字:
                        arg_宿.语音(v)
                        break

    def _ATM键(
        self,
        arg_宿: 屏幕宿主_类,
        arg_号: int,
        arg_世: 世界_类,
        arg_决策: 决策_类,
        arg_答: Callable[[int, int], bool],
    ) -> None:
        maximum = self._上限(arg_世, arg_决策.玩家)
        if arg_号 in (0, 1):
            if arg_号 == 0 and not self._有(arg_决策, 2):
                return
            self._模式, self._ATM文 = arg_号, "0"
        elif arg_号 == 2:
            self._离ATM(arg_宿, arg_决策, arg_答)
        elif arg_号 == 16:
            self._ATM文 = str(maximum)
        elif arg_号 == 17:
            amount = min(数字板_类._解析(self._ATM文), maximum)
            if amount <= 0:
                self._离ATM(arg_宿, arg_决策, arg_答)
            elif arg_答(2 if self._模式 == 0 else 1, amount):
                self._ATM文 = "0"
                self._离ATM(arg_宿, arg_决策, arg_答)
            elif arg_宿.声音:
                arg_宿.声音(3)
        else:
            c = "????789456123C0B"[arg_号] if 0 <= arg_号 < 16 else "?"
            if c == "C":
                self._ATM文 = "0"
            elif c == "B":
                self._ATM文 = self._ATM文[:-1] or "0"
            elif "0" <= c <= "9":
                s = "" if self._ATM文 == "0" else self._ATM文
                s = (s + c if len(s) < 10 else s) or "0"
                self._ATM文 = str(maximum) if 数字板_类._解析(s) > maximum else s

    def _画ATM(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_决策: 决策_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
    ) -> None:
        框, maximum = arg_宿.框, self._上限(arg_世, arg_决策.玩家)
        if 数字板_类._解析(self._ATM文) > maximum:
            self._ATM文 = str(maximum)
        if self._拖:
            if 框.按下:
                x = 框.指针x - 118
                self._ATM文 = str(
                    0
                    if x < 0
                    else maximum
                    if x >= 204
                    else min(maximum, (x // 6 + 1) * (maximum // 34 + 1))
                )
            else:
                self._拖 = False
        框.api_资源图("p", 24, 0, 60, 71)
        框.api_资源图("p", 24, 1 + self._模式, 117 if self._模式 == 0 else 199, 120)
        if arg_世.玩家[arg_决策.玩家].状态.银行禁贷天数:
            框.画布.api_绘制(框.美术.api_帧("p", 24, 29), 157, 141)
        for k, c in enumerate(reversed(self._ATM文[-10:])):
            框.api_资源图("p", 24, 19 + ord(c) - 48, 304 - 20 * k, 172)
        if maximum > 0:
            lit = min(max(int(数字板_类._解析(self._ATM文) / maximum * 34), 0), 34) * 6
            self._绘.api_局部(框.画布, 框.美术.api_帧("p", 24, 4), (0, 0, lit, 26), 118, 210)
        回宿 = 屏幕宿主_类(框, arg_宿.声音)
        if arg_板.api_比例() > 1:

            def 打开() -> None:
                def 完成(arg_数: int) -> None:
                    self._ATM文 = str(arg_数)
                    if arg_数 > 0:
                        self._ATM键(回宿, 17, arg_世, arg_决策, arg_答)

                arg_板.api_打开(maximum, 完成)

            self._绘.api_命中(arg_宿, 938, (113, 165, 330, 362), 7, 打开)
        for i, r in enumerate(self.ATM框):
            a, b, c, d = r
            rect = (a + 60, b + 71, c + 61, d + 72)
            if 4 <= i <= 15:
                rect = rect[0] - 3, rect[1] - 1, rect[2] + 3, rect[3] + 1
            if i >= 2 and i != 3 and 框.按下 and 框.api_指针内(rect):
                框.api_资源图("p", 24, i + 1, a + 60, b + 71)
            effect = 1 if i <= 1 else 2 if i == 2 else 9 if i == 3 else 7
            if i == 3:

                def 拖动() -> None:
                    self._拖 = True

                self._绘.api_命中(arg_宿, 923, rect, effect, 拖动)
            else:
                self._绘.api_命中(
                    arg_宿,
                    920 + i,
                    rect,
                    effect,
                    lambda i=i: self._ATM键(回宿, i, arg_世, arg_决策, arg_答),
                    i != 0 or self._有(arg_决策, 2),
                )

    def _侧板(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类, arg_槽: int) -> None:
        框, p = arg_宿.框, arg_世.玩家[arg_槽]
        elapsed = (框.时钟 - self._侧起) & 0xFFFFFFFFFFFFFFFF
        x = 440 if arg_宿.即时 else max(440, 640 - int(elapsed // 50) * 40)
        框.api_资源图("p", 23, 15, x, 0)
        框.画布.api_绘制(框.美术.api_帧("m", 27 + p.记录.角色, 0), x + 42, 40)
        文 = self._绘.api_文字
        label, money = 屏幕字样_类(12, 0xFFFFFF, 0x101010, 4), 屏幕字样_类(18, 0x101010, 0, 2)
        for y, s in ((80, "現  金"), (145, "存  款"), (208, "貸  款")):
            文(框, s, x + 10, y, 0, label)
        文(框, 框.人名[p.记录.角色], x + 82, 28, 5, 屏幕字样_类(22, 0xFFFFFF, 0x101010, 6))
        for y, n in ((100, p.记录.现金), (164, p.记录.银行), (228, p.记录.贷款)):
            文(框, "$" + self._绘.api_货币(n), x + 180, y, 6, money)
        日, 月, 年 = arg_世.头.日期
        festival = self._绘.api_节日(框, arg_世)
        if festival:
            框.画布.api_绘制(festival, x, 280, arg_强制不透明=True)
        else:
            季 = (3, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3)[min(max(月, 1), 12) - 1]
            框.api_资源图("p", 2, 季, x, 280)
        式 = 屏幕字样_类(60, 0x101010, 0xFFFFFF, 6)
        文(框, str(日), x + 60, 376, 2, 式)
        try:
            today = 日期_类(年, 月, 日)
        except ValueError:
            # 原侧板遇到损坏日期仍画数字，省略无效星期与贷款日期。
            today = None
        if today:
            文(
                框,
                ("星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六")[
                    today.api_星期()
                ],
                x + 14,
                352,
                3,
                屏幕字样_类(16, 0x101010, 0xFFFFFF, 6),
            )
            due = p.状态.贷款到期
            if p.记录.贷款 > 0 and due:
                try:
                    date = 日期_类(due >> 16, (due >> 8) & 255, due & 255)
                except ValueError:
                    date = None
                if date:
                    文(
                        框,
                        f"距還款日{today.api_日期差(date)}天",
                        x + 20,
                        456,
                        5,
                        屏幕字样_类(20, 0x101010, 0xFFFFFF, 6),
                    )
        文(框, str(年), x + 140, 288, 0, 屏幕字样_类(24, 0x101010, 0xFFFFFF, 6))
        文(框, f"{月}月", x + 60, 328, 2, 屏幕字样_类(28, 0x101010, 0xFFFFFF, 6))

    def _借贷(
        self,
        arg_宿: 屏幕宿主_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
        arg_财富: int,
        arg_贷款: int,
    ) -> None:
        if arg_贷款 >= arg_财富:
            self._说(arg_宿, 81)
            return
        self._说(arg_宿, 78)
        self._侧栏, self._侧起 = True, arg_宿.框.时钟

        def 完成(arg_数: int) -> None:
            if arg_数 <= 0:
                self._行.clear()
                self._侧栏 = False
            elif arg_答(3, arg_数):
                self._说(arg_宿, 79, 80)
            else:
                self._说(arg_宿, 81)

        arg_板.api_打开(股市_类._回绕(arg_财富 - arg_贷款), 完成)

    def _还贷(
        self,
        arg_宿: 屏幕宿主_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
        arg_贷款: int,
        arg_可用: int,
    ) -> None:
        self._说(arg_宿, 82)
        self._侧栏 = True
        if not arg_板.api_活跃():
            self._侧起 = arg_宿.框.时钟

        def 完成(arg_数: int) -> None:
            if arg_数 <= 0:
                self._行.clear()
                self._侧栏 = False
            elif arg_数 > arg_可用:
                self._说(arg_宿, 83)

                def 重试(arg_数: int) -> None:
                    if 0 < arg_数 <= arg_可用 and arg_答(4, arg_数):
                        self._说(arg_宿, 84)
                    else:
                        self._行.clear()
                        self._侧栏 = False

                arg_板.api_打开(arg_贷款, 重试)
            elif arg_答(4, arg_数):
                self._说(arg_宿, 84)

        arg_板.api_打开(arg_贷款, 完成)

    def _画柜台(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_决策: 决策_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
    ) -> None:
        框, slot = arg_宿.框, arg_决策.玩家
        p, director = arg_世.玩家[slot], self._拥有(arg_世, slot)
        self._绘.api_背景(框, "p", 23, 0)
        文 = self._绘.api_文字
        if not director:
            框.画布.api_绘制(框.美术.api_帧("p", 23, 1), 320, 240)
        else:
            文(框, "特別融資", 492, 245, 2, 屏幕字样_类(14, 0x808080, 0, 2))
        line = ""
        if self._行:
            i = ((框.时钟 - self._行起) & 0xFFFFFFFFFFFFFFFF) // 2000
            if arg_板.api_活跃():
                i = min(i, len(self._行) - 1)
            if i < len(self._行):
                line = self._行[i]
            else:
                self._行.clear()
                if not arg_板.api_活跃():
                    self._侧栏 = False
        blink = 框.时钟 // 100 % 40
        if blink < 4:
            框.api_资源图("p", 23, (7, 6, 7, 5)[blink], 140, 114)
        if line:
            框.api_资源图("p", 23, 9 if 框.时钟 // 150 % 2 else 10, 140, 152)
        式 = 屏幕字样_类(26, 0x101010, 0, 2)
        文(框, "申請貸款", 345, 345, 2, 式)
        文(框, "償還貸款", 530, 345, 2, 式)
        if p.状态.银行禁贷天数:
            框.画布.api_绘制(框.美术.api_帧("p", 23, 23), 345, 345)
        if 框.按下 and 框.api_指针内((548, 431, 629, 472)):
            框.api_资源图("p", 23, 19, 548, 431)
        if line:
            框.api_资源图("p", 23, 21, 240, 80)
            文(框, line, 357, 151, 4, 屏幕字样_类(20, 0x101010, 0, 2))
        if self._侧栏 or arg_板.api_活跃():
            self._侧板(arg_宿, arg_世, slot)
        wealth, loan = 股市_类.api_财富(arg_世, slot), p.记录.贷款
        available = p.记录.现金 + p.记录.银行
        回宿 = 屏幕宿主_类(框, arg_宿.声音)
        self._绘.api_命中(arg_宿, 940, (548, 431, 629, 472), 2, lambda: arg_答(0, 0))
        self._绘.api_命中(
            arg_宿,
            941,
            (282, 324, 409, 367),
            1,
            lambda: self._借贷(回宿, arg_板, arg_答, wealth, loan),
            self._有(arg_决策, 3),
        )
        self._绘.api_命中(
            arg_宿,
            942,
            (470, 326, 591, 367),
            1,
            lambda: self._还贷(回宿, arg_板, arg_答, loan, available),
            loan > 0 and self._有(arg_决策, 4),
        )
        if director:

            def 董事室() -> None:
                self._阶段 = 2
                self._说(回宿, 86)

            self._绘.api_命中(arg_宿, 943, (268, 51, 592, 274), 1, 董事室)

    def _融资(
        self,
        arg_宿: 屏幕宿主_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
        arg_总: int,
        arg_已有: int,
    ) -> None:
        if arg_已有 >= arg_总:
            self._说(arg_宿, 88)
            return
        self._说(arg_宿, 87)

        def 完成(arg_数: int) -> None:
            if arg_数 > 0 and arg_答(5, arg_数):
                self._阶段 = 1
                arg_答(0, 0)
            else:
                self._行.clear()

        arg_板.api_打开(股市_类._回绕(arg_总 - arg_已有), 完成)

    def _还融资(
        self,
        arg_宿: 屏幕宿主_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
        arg_已有: int,
        arg_可用: int,
    ) -> None:
        if arg_已有 == 0:
            self._说(arg_宿, 90)
            return
        self._说(arg_宿, 89)

        def 完成(arg_数: int) -> None:
            if arg_数 <= 0:
                self._行.clear()
            elif arg_数 > arg_可用:
                self._说(arg_宿, 90)
            elif arg_答(6, arg_数):
                self._阶段 = 1
                arg_答(0, 0)

        arg_板.api_打开(arg_已有, 完成)

    def _画董事室(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_决策: 决策_类,
        arg_板: 数字板_类,
        arg_答: Callable[[int, int], bool],
    ) -> None:
        框, slot = arg_宿.框, arg_决策.玩家
        p, total = arg_世.玩家[slot], self._别人存款(arg_世, slot)
        special = p.记录.特殊融资
        self._绘.api_背景(框, "p", 23, 2)
        框.api_资源图("p", 23, 20, 10, 125)
        rects = ((11, 305, 126, 346), (11, 362, 126, 403), (11, 419, 92, 460))
        for i, r in enumerate(rects):
            lit = 框.api_指针内(r)
            框.api_资源图(
                "p", 23, (17 if lit else 16) if i < 2 else (19 if lit else 18), r[0], r[1]
            )
        文, 式 = self._绘.api_文字, 屏幕字样_类(20, 0xF0F0F0, 0x101010, 2)
        文(框, "週轉現金", 67, 324, 2, 式)
        文(框, "歸還款項", 67, 382, 2, 式)
        if p.状态.银行禁贷天数:
            框.画布.api_绘制(框.美术.api_帧("p", 23, 23), 67, 324)
        式 = 屏幕字样_类(16, 0x202020, 0, 2)
        for y, s in ((147, "客戶存款總額"), (195, "目前融資金額"), (243, "尚可融資金額")):
            文(框, s, 78, y, 2, 式)
        for y, n in ((163, total), (211, special), (259, total - special)):
            文(框, self._绘.api_货币(n), 128, y, 6, 式)
        if self._行:
            i = ((框.时钟 - self._行起) & 0xFFFFFFFFFFFFFFFF) // 2000
            if arg_板.api_活跃():
                i = min(i, len(self._行) - 1)
            if i < len(self._行):
                框.api_资源图("p", 23, 22, 214, 50)
                文(框, self._行[i], 339, 95, 4, 屏幕字样_类(20, 0x101010, 0, 2))
            else:
                self._行.clear()
        回宿 = 屏幕宿主_类(框, arg_宿.声音)
        self._绘.api_命中(
            arg_宿,
            944,
            rects[0],
            1,
            lambda: self._融资(回宿, arg_板, arg_答, total, special),
            not p.状态.银行禁贷天数 and self._有(arg_决策, 5),
        )
        available = p.记录.现金 + p.记录.银行
        self._绘.api_命中(
            arg_宿, 945, rects[1], 1, lambda: self._还融资(回宿, arg_板, arg_答, special, available)
        )

        def 退出() -> None:
            self._阶段 = 1
            self._说(回宿, 91)

        self._绘.api_命中(arg_宿, 946, rects[2], 2, 退出)
