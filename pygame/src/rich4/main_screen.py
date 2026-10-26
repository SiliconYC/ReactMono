# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/main_screen.cpp/.hpp；规则仅通过独立Python GameSession访问。
# ◑ 导入
import re
from collections.abc import Callable

from rich4.artwork import 美术_类
from rich4.board_models import 玩家精灵_类
from rich4.board_projection import 棋盘投影_类
from rich4.game import 游戏会话_类
from rich4.game_types import 游戏事件_类, 游戏事件种类_类, 游戏阶段_类
from rich4.graphics import 图像_类
from rich4.loan_notice import 贷款提醒_类
from rich4.main_panels import 主屏布局_类
from rich4.main_screen_types import 主屏动作_类
from rich4.native_frame import 画框_类
from rich4.screen_draw import 屏幕绘图_类
from rich4.world import 世界_类


# ◕ 功能
class 主屏幕_类(主屏布局_类):
    """
    原主屏输入、GO拖拽、显示回合门控与独立骰子/投掷动画时钟。

    更新日志：
    2026.10.24 - dice_busy用于应用暂停规则时钟，显示玩家覆盖不改变真实当前玩家。
    """

    棋盘区 = (0, 40, 440, 480)

    def __init__(self, arg_预设: str = "") -> None:
        self.视图, self.日历, self.页签 = 1, 0, [0] * 9
        self._悬停 = -1
        self.GOx, self.GOy = 180, 120
        self._拖拽: tuple[int, int] | None = None
        self._显示玩家: int | None = None
        self._待掷: Callable[[], None] | None = None
        self._按点 = (0, 0)
        self._自由中心: tuple[int, int] | None = None
        self._小图拖拽, self.全图, self._小图顶 = False, False, 280
        self._GO掩码 = b""
        self._绘图缓存 = 屏幕绘图_类()
        self._骰动画: dict[int, list[图像_类]] = {}
        self._骰面: list[int] = []
        self._骰向 = 0
        self._骰活跃, self._骰已响, self._跳过姿态 = False, False, False
        self._骰毫秒 = self._骰帧数 = self._投掷槽 = self._投掷帧数 = self._投掷毫秒 = 0
        for 项 in arg_预设.split(","):
            键, 等号, 值 = 项.partition("=")
            if not 等号:
                continue
            匹配 = re.match(r"\s*([+-]?\d+)", 值, flags=re.ASCII)
            数 = (int(匹配[1]) if 匹配 else 0) & 0xFFFFFFFF
            if 键 == "view":
                self.视图 = 数 % 3
            elif 键 == "tab":
                self.页签[:] = [数 % 4] * 9
            elif 键 == "calendar":
                self.日历 = 数 % 2
            elif 键 == "map":
                self.全图 = 数 != 0

    def api_相机中心(self, arg_跟随: tuple[int, int]) -> tuple[int, int]:
        return arg_跟随 if self._自由中心 is None else self._自由中心

    def api_跟随(self) -> None:
        self._自由中心 = None

    def api_显示玩家(self, arg_槽: int | None) -> None:
        self._显示玩家 = arg_槽

    def api_显示人类回合(self, arg_会话: 游戏会话_类) -> bool:
        return arg_会话.阶段 == 游戏阶段_类.人类待命 and self._显示玩家 is None

    def api_显示槽位(self, arg_世界: 世界_类) -> int:
        槽 = arg_世界.头.当前玩家 if self._显示玩家 is None else self._显示玩家
        return min(槽, len(arg_世界.玩家) - 1)

    def api_跳过投掷(self, arg_跳: bool) -> None:
        self._跳过姿态 = arg_跳

    def api_切视图(self) -> None:
        self.视图 = (self.视图 + 1) % 3

    def api_事件(
        self,
        arg_事件: 游戏事件_类,
        arg_会话: 游戏会话_类,
        arg_美术: 美术_类,
    ) -> None:
        if arg_事件.种类 == 游戏事件种类_类.回合开始:
            self._自由中心 = None
        if arg_事件.种类 != 游戏事件种类_类.骰子结果:
            return
        self._自由中心, self._骰面 = None, arg_会话.骰面.copy()
        if not self._骰面 or arg_事件.玩家 >= len(arg_会话.世界.玩家):
            self._骰活跃 = False
            return
        self._骰面 = self._骰面[:3]
        数 = len(self._骰面)
        if not self._骰动画.get(数):
            帧: list[图像_类] = []
            try:
                片 = arg_美术.api_动画("p", 3 + 数)
                while 片.api_下一帧():
                    帧.append(片.api_图像())
            except (ValueError, OSError, IndexError):
                # 原MainScreen在骰子FLC不可解码时循环原Panel3骰面。
                帧.clear()
            self._骰动画[数] = 帧
        self._骰帧数 = len(self._骰动画[数]) or 12
        世 = arg_会话.世界
        人 = 世.玩家[arg_事件.玩家]
        记, 状 = 人.记录, 人.状态
        self._骰向, self._骰毫秒, self._骰已响, self._骰活跃 = 记.方向, 0, False, True
        姿 = 玩家精灵_类(
            角色=记.角色,
            交通=记.交通 & 3,
            踩水=记.节点 < len(世.节点) and bool(世.节点[记.节点].标志 & 0x80000000),
            梦游=状.梦游天数 != 0,
            受伤=bool(记.控制标志 & 0x40),
            投骰=True,
        )
        self._投掷槽, self._投掷帧数 = arg_事件.玩家, 0
        if not 姿.受伤 and 姿.角色 < 12:
            try:
                self._投掷帧数 = arg_美术.api_帧数("d", 棋盘投影_类.api_角色资源(姿)) // 8
            except (ValueError, OSError, IndexError):
                self._投掷帧数 = 0
        self._投掷毫秒 = 0 if self._跳过姿态 else self._投掷帧数 * 80

    def api_骰子忙(self) -> bool:
        return self._骰活跃 and self._骰毫秒 < self._投掷毫秒 + self._骰帧数 * 28 + 500

    def api_投掷帧(self, arg_槽: int) -> int | None:
        if not self.api_骰子忙() or arg_槽 != self._投掷槽 or self._投掷帧数 == 0:
            return None
        if self._骰毫秒 >= self._投掷毫秒:
            return (self._投掷帧数 - 1) & 255
        return min(self._骰毫秒 // 80, self._投掷帧数 - 1) & 255

    def api_递进(self, arg_毫秒: int) -> None:
        if self._骰活跃:
            self._骰毫秒 = (self._骰毫秒 + arg_毫秒) & 0xFFFFFFFF

    def api_指针移动(self, arg_x: int, arg_y: int, arg_左按: bool) -> None:
        if not arg_左按:
            self._拖拽, self._小图拖拽 = None, False
            return
        if self._待掷 and abs(arg_x - self._按点[0]) + abs(arg_y - self._按点[1]) > 6:
            self._待掷 = None
        if self._拖拽 is not None and self._待掷 is None:
            self.GOx = min(max(arg_x - self._拖拽[0], 0), 568)
            self.GOy = min(max(arg_y - self._拖拽[1], 0), 413)
        if self._小图拖拽:
            self._自由中心 = (
                min(max(((arg_x - 440) * 761856) >> 16, 220), 2084),
                min(max(((arg_y - self._小图顶) * 761856) >> 16, 220), 2084),
            )

    def api_指针释放(self, arg_x: int, arg_y: int, arg_右键: bool) -> None:
        掷, self._待掷 = self._待掷, None
        if 掷 and not arg_右键:
            掷()
        self._拖拽, self._小图拖拽 = None, False
        if (
            arg_右键
            and self.视图 != 0
            and arg_x > 440
            and self._小图顶 < arg_y < self._小图顶 + 200
        ):
            self._自由中心 = None

    def _GO命中值(self, arg_框: 画框_类, arg_x: int, arg_y: int) -> int:
        if not self._GO掩码:
            self._GO掩码 = arg_框.美术.api_解码("p", 8)
        x, y = arg_x - self.GOx, arg_y - self.GOy
        if x < 0 or y < 0 or x >= 72 or y >= 67 or y * 72 + x >= len(self._GO掩码):
            return 0
        return self._GO掩码[y * 72 + x]

    def api_绘制(
        self,
        arg_框: 画框_类,
        arg_会话: 游戏会话_类,
        arg_旋转: int,
        arg_动作: 主屏动作_类,
    ) -> None:
        世 = arg_会话.世界
        self._绘骰子(arg_框, arg_会话, arg_旋转, arg_动作)
        if self.api_显示人类回合(arg_会话):
            self._绘GO(arg_框, arg_会话, arg_动作)
        else:
            self._拖拽, self._待掷 = None, None
        self._绘工具栏(arg_框, arg_会话, arg_动作)
        if self.视图 == 2:
            self._绘头部(arg_框, 世)
            self._绘小图(arg_框, 世, 80, arg_动作)
        else:
            self._绘信息(arg_框, 世, arg_动作)
            if self.视图 == 1:
                self._绘小图(arg_框, 世, 280, arg_动作)
        if self.视图 != 1:
            self._绘日历(arg_框, 世, arg_动作)
        if self.全图 and arg_会话.阶段 != 游戏阶段_类.人类待命:
            self.全图 = False
        if self.全图:
            self._绘全图(arg_框, 世)
        贷款提醒_类.api_绘常驻(arg_框, 世)

    def _绘GO(self, arg_框: 画框_类, arg_会话: 游戏会话_类, arg_动作: 主屏动作_类) -> None:
        人, gx, gy = arg_会话.世界.api_活跃玩家(), self.GOx, self.GOy
        停 = 人.状态.停留天数 != 0
        种类 = 4 if 人.状态.龟行天数 else 2 if 停 else 0
        self._锚图(arg_框, "p", 7, arg_框.时钟 // 500 % 2 + 种类, gx, gy)
        交通, 骰数 = 人.记录.交通 & 3, 人.记录.骰数
        if 交通 in (0, 3):
            self._锚图(arg_框, "p", 7, 6 if 停 else 7, gx + (8 if 停 else 7), gy + 26)
        else:
            for i in range(2 if 交通 == 1 else 3):
                y = gy + 16 + 19 * i if 交通 == 1 else gy + 9 + 16 * i
                活 = i < 骰数 and not 停
                self._锚图(arg_框, "p", 7, 2 * i + (7 if 活 else 6), gx + (7 if 活 else 8), y)

            def 设骰() -> None:
                ly = arg_框.指针y - self.GOy
                数 = min(
                    max(画框_类._零除(ly - (16 if 交通 == 1 else 9), 19 if 交通 == 1 else 16), 0),
                    1 if 交通 == 1 else 2,
                )
                arg_动作.骰数(数 + 1)

            arg_框.api_命中(101, (gx + 7, gy + 9, gx + 23, gy + 57), 设骰, not 停)

        def 掷骰() -> None:
            self._拖拽 = None
            arg_动作.掷骰()

        arg_框.api_命中(100, (gx + 30, gy + 14, gx + 65, gy + 55), 掷骰)

        def 按下() -> None:
            x, y = arg_框.指针x, arg_框.指针y
            self._拖拽, self._按点 = (x - self.GOx, y - self.GOy), (x, y)
            self._待掷 = 掷骰

        arg_框.api_命中(102, (gx, gy, gx + 72, gy + 67), 按下)

    def _绘骰子(
        self,
        arg_框: 画框_类,
        arg_会话: 游戏会话_类,
        arg_旋转: int,
        arg_动作: 主屏动作_类,
    ) -> None:
        if not self._骰活跃:
            return
        总 = self._骰帧数 * 28
        if self._骰毫秒 >= self._投掷毫秒 + 总 + 500 and arg_会话.阶段 != 游戏阶段_类.掷骰:
            self._骰活跃 = False
            return
        if self._骰毫秒 < self._投掷毫秒:
            return
        时 = self._骰毫秒 - self._投掷毫秒
        if not self._骰已响 and 时 // 28 >= min(30, self._骰帧数 - 1):
            self._骰已响 = True
            if arg_动作.声音:
                arg_动作.声音(10)
        朝 = (8 - arg_旋转 + self._骰向) & 7
        ax, ay = (
            136 + (4, 12, 8, -4, -12, -24, -20, -12)[朝],
            48 + (12, 12, 6, -6, -12, -12, -6, 6)[朝],
        )
        帧 = self._骰动画[len(self._骰面)]
        if 时 < 总:
            i = min(时 // 28, self._骰帧数 - 1)
            if 帧:
                arg_框.画布.api_绘制(帧[i], ax, ay, self.棋盘区)
                return
            for j in range(len(self._骰面)):
                arg_框.画布.api_绘制(
                    arg_框.美术.api_帧("p", 3, 6 * j + (i + j * 2) % 6),
                    ax + 85,
                    ay + 145,
                    self.棋盘区,
                )
            return
        for j, 面 in enumerate(self._骰面):
            arg_框.画布.api_绘制(
                arg_框.美术.api_帧("p", 3, 6 * j + min(max(面, 1), 6) - 1),
                ax + 85,
                ay + 145,
                self.棋盘区,
            )
