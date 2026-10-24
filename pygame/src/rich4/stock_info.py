# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/stocks.cpp：报价精度、历史环、公司资讯与图表。
# ◑ 导入
import math

from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类
from rich4.world_map import 公司_类


# ◕ 功能
class 股票图表_类:
    """
    原股价走势图和持股饼图；逐个binary32运算保留坐标截断边界。

    更新日志：
    2026.10.24 - 只读取原世界/外部公司名，不修改股价或历史。
    """

    楼图 = (
        (11, 0, 7, 5, 6, 9, 3, 0, 0, 4, 10, 0),
        (11, 0, 7, 5, 6, 9, 3, 0, 0, 4, 10, 0),
        (11, 0, 8, 5, 6, 9, 3, 0, 0, 4, 10, 0),
        (11, 0, 7, 5, 6, 9, 3, 0, 0, 4, 10, 0),
        (11, 0, 7, 12, 6, 9, 3, 0, 0, 4, 10, 0),
        (11, 23, 7, 14, 6, 9, 3, 0, 0, 4, 10, 15),
        (11, 0, 7, 13, 6, 9, 3, 0, 0, 4, 10, 0),
        (11, 24, 7, 5, 6, 9, 3, 0, 0, 4, 10, 0),
    )

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self._原文 = arg_原文
        self._绘 = 屏幕绘图_类()

    @staticmethod
    def _单(arg_值: float) -> float:
        return 股市_类._浮点(股市_类._位(arg_值))

    @staticmethod
    def _价(arg_世: 世界_类, arg_股: int, arg_位: int = 2) -> float:
        return 股市_类._浮点(arg_世.股票[arg_股].浮点位[arg_位])

    def _名(self, arg_世: 世界_类, arg_股: int) -> str:
        return self._原文.api_股票((arg_世.头.阶段 * 4 + arg_世.头.地图) * 12 + arg_股)

    @staticmethod
    def _格式(arg_值: float, arg_幅: float, arg_符: bool = False) -> str:
        precision = 2 if arg_幅 < 15 else 1 if arg_幅 < 150 else 0
        return format(arg_值, ("+" if arg_符 else "") + f".{precision}f")

    @staticmethod
    def _公司(arg_世: 世界_类, arg_股: int) -> 公司_类 | None:
        return next((c for c in arg_世.公司 if c.编号 and c.股票索引 == arg_股), None)

    @staticmethod
    def _历史(arg_世: 世界_类, arg_股: int) -> list[float]:
        ring = arg_世.股史[arg_股]
        cursor = min(max(arg_世.股史游标, 0), 143)
        start = cursor if ring[cursor] else 0
        samples = []
        for k in range(len(ring)):
            bits = ring[(start + k) % len(ring)]
            if not bits:
                break
            samples.append(股市_类._浮点(bits))
        return samples

    @staticmethod
    def _线(
        arg_画: 图像_类,
        arg_x: int,
        arg_y: int,
        arg_终x: int,
        arg_终y: int,
        arg_色: int,
    ) -> None:
        dx, dy = abs(arg_终x - arg_x), -abs(arg_终y - arg_y)
        sx, sy = (1 if arg_x < arg_终x else -1), (1 if arg_y < arg_终y else -1)
        error = dx + dy
        while True:
            if 0 <= arg_x < arg_画.宽 and 0 <= arg_y < arg_画.高:
                arg_画.像素[arg_y * arg_画.宽 + arg_x] = arg_色
            if (arg_x, arg_y) == (arg_终x, arg_终y):
                return
            twice = 2 * error
            if twice >= dy:
                error += dy
                arg_x += sx
            if twice <= dx:
                error += dx
                arg_y += sy

    def _画资讯(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类, arg_股: int) -> None:
        框, 文, 单 = arg_宿.框, self._绘.api_文字, self._单
        框.api_资源图("p", 75, 2, 26, 52)
        文(框, self._名(arg_世, arg_股), 320, 82, 2, 屏幕字样_类(20))
        company = self._公司(arg_世, arg_股) if arg_世.股票[arg_股].标志4 else None
        if company and 1 <= company.类型 <= 12:
            图 = min(max(arg_世.头.阶段 * 4 + arg_世.头.地图, 0), 7)
            框.api_资源图("p", 75, 3 + self.楼图[图][company.类型 - 1], 50, 107)
        label, small = 屏幕字样_类(), 屏幕字样_类(12, 0xF0F0F0, 0x101010, 1)
        for s, x, y in (
            ("本月盈餘", 212, 123),
            ("平均盈餘", 212, 162),
            ("經 營 者", 212, 203),
            ("成交價", 395, 123),
            ("漲  跌", 395, 162),
            ("週均價", 395, 203),
            ("交易量", 531, 123),
            ("漲跌幅", 531, 162),
            ("月均價", 531, 203),
            ("歷史高價", 531, 243),
            ("歷史低價", 531, 283),
        ):
            文(框, s, x, y, 6, label)
        文(框, "半年內股價走勢線圖", 236, 248, 2, small)
        文(框, "持股比例", 502, 318, 2, small)
        if company:
            文(框, self._绘.api_货币(company.资金), 309, 123, 6, label)
            average = (
                画框_类._零除(company.资金变化, arg_世.月数) if arg_世.月数 else company.资金变化
            )
            文(框, self._绘.api_货币(average), 309, 162, 6, label)
            if 1 <= company.业主 <= len(arg_世.玩家):
                文(框, 框.人名[arg_世.玩家[company.业主 - 1].记录.角色], 269, 203, 2, label)
        current, previous = self._价(arg_世, arg_股), self._价(arg_世, arg_股, 1)
        change = 单(current - previous)
        文(框, self._格式(current, current), 453, 123, 6, label)
        文(框, self._格式(change, current, True), 453, 162, 6, label)
        文(框, str(arg_世.股票[arg_股].标志10), 589, 123, 6, label)
        percent = 单(单(change / previous) * 100) if previous else 0.0
        文(框, f"{percent:.2f}", 589, 162, 6, label)
        samples = self._历史(arg_世, arg_股)

        def 平均(arg_数: int) -> float:
            n = min(arg_数, len(samples))
            return 单(sum(samples[-n:]) / n) if n else 0.0

        week, month = 平均(6), 平均(24)
        文(框, self._格式(week, week), 453, 203, 6, label)
        文(框, self._格式(month, month), 589, 203, 6, label)
        high, low = 0.0, 10000.0
        for v in samples:
            high, low = max(high, v), min(low, v)
        if samples:
            文(框, self._格式(high, high), 589, 243, 6, label)
            文(框, self._格式(low, low), 589, 283, 6, label)
            middle, span = 单(单(high + low) / 2), 单(high - low)
            scale = (
                单(109 / span)
                if middle > 0 and 单(span / middle) > 单(0.3)
                else 单(109 / 单(单(0.6) * middle))
                if middle > 0
                else 0.0
            )

            def 纵(arg_值: float) -> int:
                return int(单(324 - 单(单(arg_值 - middle) * scale)))

            for k in range(1, len(samples)):
                self._线(
                    框.画布,
                    92 + 2 * (k - 1),
                    纵(samples[k - 1]),
                    92 + 2 * k,
                    纵(samples[k]),
                    self._绘.api_RGB(0xFFFFFF),
                )
            文(框, self._格式(high, high), 88, 纵(high) - 8, 6, small)
            文(框, self._格式(low, low), 88, 纵(low) + 8, 6, small)
        holding = arg_世.玩家[arg_世.头.当前玩家].持仓[arg_股].数量
        fraction = min(max(holding / 10000.0, 0.0), 1.0)

        def 拥有(arg_dx: float, arg_dy: float) -> bool:
            angle = math.atan2(arg_dx, -arg_dy)
            if angle < 0:
                angle += 2 * math.pi
            return angle < 2 * math.pi * fraction

        for y in range(336, 402):
            for x in range(414, 592):
                tx, ty = (x - 502.5) / 88.5, (y - 365) / 29.0
                bx, by = tx, (y - 372) / 29.0
                top, base = tx * tx + ty * ty <= 1, bx * bx + by * by <= 1
                if top:
                    edge = tx * tx + ty * ty > 0.94
                    color = 0 if edge else 0xD00000 if 拥有(tx, ty) else 0x0000D0
                elif base or (abs(tx) <= 1 and 365 < y < 372):
                    edge = base and bx * bx + by * by > 0.94
                    color = (
                        0
                        if edge
                        else 0x900000
                        if 拥有(tx, 0.0001) and tx > 0 and fraction > 0.25
                        else 0x000090
                    )
                else:
                    continue
                框.画布.像素[y * 框.画布.宽 + x] = self._绘.api_RGB(color)
