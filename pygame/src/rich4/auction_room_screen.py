# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定market.cpp::AuctionRoom；按原演出结束后才回答真实决策。
# ◑ 导入
from collections.abc import Callable

from rich4.auction_room_draw import 拍卖绘制_类
from rich4.auction_room_types import 拍卖出价_类, 拍卖成交_类
from rich4.game_types import 决策_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类


# ◕ 功能
class 拍卖室_类(拍卖绘制_类):
    """
    原五帧出价/二次点击跳过、换决策弃旧与3500毫秒成交演出。

    更新日志：
    2026.10.24 - 保留零时钟哨兵和无符号经过时间，不重算核心成交结果。
    """

    def __init__(self) -> None:
        self._出价: 拍卖出价_类 | None = None
        self._成交: 拍卖成交_类 | None = None

    def api_重置(self) -> None:
        self._出价 = self._成交 = None

    def api_成交中(self) -> bool:
        return self._成交 is not None

    def api_成交(self, arg_赢家: int, arg_价: int, arg_地: int) -> None:
        self._成交 = 拍卖成交_类(arg_赢家, arg_价, arg_地)

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_决: 决策_类,
        arg_答: Callable[[int], None],
    ) -> None:
        框, 绘 = arg_宿.框, 屏幕绘图_类
        key = f"{arg_决.地产}:{arg_决.玩家}:{arg_决.金额}"
        if self._出价 and self._出价.键 != key:
            self._出价 = None
        if self._出价 and not self._出价.开始:
            self._出价.开始 = 框.时钟
        if self._出价 and 框.时钟 >= ((self._出价.开始 + 1000) & 0xFFFFFFFFFFFFFFFF):
            index, self._出价 = self._出价.索引, None
            arg_答(index)
            return
        price = self._出价.价格 if self._出价 else arg_决.金额
        seller = self._画房(框, arg_世, arg_决.地产, price, False)
        self._公告(框, f"目前標價{arg_决.金额}元\n請意者出價。")
        bid_frame = ((框.时钟 - self._出价.开始) & 0xFFFFFFFFFFFFFFFF) // 200 if self._出价 else 0

        def 姿态(arg_k: int) -> tuple[int, int]:
            if arg_决.不活跃玩家 & (1 << arg_k):
                return 1, 0
            if self._出价 and arg_k == arg_决.玩家:
                return 0, (bid_frame + 1) % 5
            return 0, 0

        self._竞买人(框, arg_世, arg_决.玩家, seller, 姿态)
        if self._出价:
            b = self._出价
            y = 80 + 120 * arg_决.玩家
            框.画布.api_绘制(框.美术.api_帧("p", 26, 1), 480, y - 15)
            label = "ＰＡＳＳ" if b.行动 == 0 else "放棄" if b.行动 == 6 else f"{b.价格}元"
            绘.api_文字(框, label, 480, y - 15, 4, 屏幕字样_类(16, 0x101010, 0, 2))
        for i, y in enumerate((133, 181, 229, 277, 325, 373, 421)):
            rect = (363, y - 19, 450, y + 20)
            pressed = (框.按下 and 框.api_指针内(rect)) or (self._出价 and self._出价.行动 == i)
            框.画布.api_绘制(框.美术.api_帧("p", 26, 2 * i + (3 if pressed else 4)), 406, y)
            for index, option in enumerate(arg_决.选项):
                if option.值 != i or (self._出价 and self._出价.索引 != index):
                    continue
                instant, sound = arg_宿.即时, arg_宿.声音
                price = 股市_类._回绕(arg_决.金额 + (0, 100, 500, 1000, 5000, 10000, 0)[i])

                def 出价(arg_索: int = index, arg_i: int = i, arg_价: int = price) -> None:
                    if self._出价 or instant:
                        self._出价 = None
                        arg_答(arg_索)
                        return
                    self._出价 = 拍卖出价_类(key, arg_索, arg_i, arg_价, 0)
                    if sound:
                        sound(29)

                绘.api_命中(
                    arg_宿,
                    210 + index,
                    (0, 0, 640, 480) if self._出价 else rect,
                    -1 if self._出价 else 1,
                    出价,
                )

    def api_画成交(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类) -> None:
        if self._成交 is None:
            return
        框, sold = arg_宿.框, self._成交
        if not sold.开始:
            sold.开始 = max(框.时钟, 1)
        elapsed = (框.时钟 - sold.开始) & 0xFFFFFFFFFFFFFFFF
        if elapsed >= 3500 or not 0 <= sold.赢家 < len(arg_世.玩家):
            self._成交 = None
            return
        if not sold.已响:
            sold.已响 = True
            if arg_宿.声音 is None:
                raise ValueError("原拍卖锤声要求声音回调")
            arg_宿.声音(63)
        self._画房(框, arg_世, sold.地产, sold.价格, True)
        winner = sold.赢家
        buyer = 框.人名[arg_世.玩家[winner].记录.角色]
        self._公告(框, f"{sold.价格}元成交" if elapsed < 1750 else f"恭喜{buyer}\n購得此地！")
        self._竞买人(
            框, arg_世, winner, -1, lambda k: (2, elapsed // 100 % 5) if k == winner else (0, 0)
        )

        def 跳过() -> None:
            self._成交 = None

        屏幕绘图_类.api_命中(arg_宿, 1650, (0, 0, 640, 480), -1, 跳过)
