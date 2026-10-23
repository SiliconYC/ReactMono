# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/auction.cpp；保留活动记录空位和经济/表现随机流分离。
# ◑ 导入
import struct
from dataclasses import dataclass, field
from enum import IntEnum

from rich4.calendar import 日期_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.world import 世界_类
from rich4.world_map import 地产_类, 设施_类
from rich4.world_player import 玩家状态_类


# ◕ 功能
class 拍卖行动_类(IntEnum):
    """
    原拍卖回调的七个行动编号。

    更新日志：
    2026.10.23 - 对应 AuctionAction。
    """

    放弃 = 0
    加一百 = 1
    加五百 = 2
    加一千 = 3
    加五千 = 4
    加一万 = 5
    退出 = 6


@dataclass
class 拍卖决策_类:
    """
    当前人类玩家可提交的行动和已退出槽位掩码。

    更新日志：
    2026.10.23 - 对应 AuctionDecision。
    """

    玩家: int
    价格: int
    行动: list[拍卖行动_类] = field(default_factory=list)
    已退出: int = 0


@dataclass
class 拍卖结果_类:
    """
    成交才填写赢家和价格；无人出价保留零价与原地产。

    更新日志：
    2026.10.23 - 对应 AuctionResult。
    """

    赢家: int | None = None
    价格: int = 0
    地产: int = 0


@dataclass
class 竞买记录_类:
    """
    活动玩家按原槽位压紧后保留不合资格的记录空位。

    更新日志：
    2026.10.23 - 对应 AuctionSession::Bidder。
    """

    玩家: int = 0
    上限: int = 0
    在场: bool = False
    放弃: bool = False
    人类: bool = False


class 拍卖会话_类:
    """
    可暂停的人类/电脑拍卖；挂起时调用方不得修改世界和随机流。

    更新日志：
    2026.10.23 - 原起价/估价、竞价、退出、结算和租期，不实现UI动画。
    """

    增量 = (0, 100, 500, 1000, 5000, 10000, 0)
    租期间隔 = (0, 0x20000, 0x10000, 0x600, 0x300, 0x100)

    @staticmethod
    def _整数(arg_值: int) -> int:
        return ((arg_值 + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    @staticmethod
    def _单精度(arg_值: float | int) -> float:
        return struct.unpack("<f", struct.pack("<f", arg_值))[0]

    @staticmethod
    def _缺席(arg_态: 玩家状态_类) -> bool:
        return bool(
            arg_态.酒店天数
            or arg_态.消失天数
            or arg_态.监狱天数
            or arg_态.医院天数
            or arg_态.睡眠天数
            or arg_态.梦游天数
        )

    def _标的(self) -> 地产_类 | 设施_类:
        if 2000 < self.地产 < 4000:
            return self.世界.地产[self.地产 - 2000]
        if 4000 < self.地产 < 6000:
            return self.世界.设施[self.地产 - 4000]
        raise ValueError("拍卖只支持原地产或设施编码")

    def __init__(
        self,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_地产: int,
        arg_卖家: int = -1,
        arg_租期: int | None = None,
    ) -> None:
        self.世界 = arg_世
        self.地产 = arg_地产
        self.卖家 = arg_卖家
        self.记录 = [竞买记录_类() for _ in range(4)]
        self.当前 = 0
        self.初始人数 = 0
        self.原记录数 = 0
        self.末次出价: int | None = None
        self.已结束 = False
        self.结果 = 拍卖结果_类(地产=arg_地产)
        if len(arg_世.玩家) > 4 or not -1 <= arg_卖家 < len(arg_世.玩家):
            raise ValueError("拍卖参与者无效")
        if arg_租期 is None:
            if not 0 <= arg_世.租约模式 < 6:
                raise ValueError("存档拍卖租期模式无效")
            arg_租期 = self.租期间隔[arg_世.租约模式]
        self.租期 = arg_租期 & 0xFFFFFFFF
        标的 = self._标的()
        等级 = 标的.经济.等级 if isinstance(标的, 地产_类) else 标的.等级
        self.起价 = self._整数(标的.地价 * (等级 + 2) // 2 * arg_世.头.物价)
        if self.起价 < 0:
            raise IndexError("拍卖起价溢出")
        self.价格 = self.起价
        for 槽, 玩家 in enumerate(arg_世.玩家):
            if 玩家.记录.控制标志 == 0:
                continue
            记录 = self.记录[self.原记录数]
            self.原记录数 += 1
            记录.玩家 = 槽
            if 玩家.记录.现金 <= self.起价 or self._缺席(玩家.状态) or 槽 == arg_卖家:
                continue
            记录.在场 = True
            记录.人类 = 玩家.记录.控制标志 == 1
            if 玩家.记录.控制标志 & 6:
                记录.上限 = self._电脑估价(arg_随机, 标的, 槽)
            self.初始人数 += 1
            self.当前 = self.原记录数 - 1
        if self.初始人数 == 0:
            self._结算()

    def _电脑估价(self, arg_随机: 随机数_类, arg_标的: 地产_类 | 设施_类, arg_槽: int) -> int:
        热情 = self._单精度(arg_随机.api_下一个() / 32767.0 * 0.3 + 0.5)
        同街 = 0
        if isinstance(arg_标的, 设施_类):
            总数 = len(self.世界.设施) - 1
            无主 = sum(地.业主 == 0 for 地 in self.世界.设施[1:])
            等级 = arg_标的.等级
        else:
            总数 = len(self.世界.地产) - 1
            无主 = sum(地.经济.业主 == 0 for 地 in self.世界.地产[1:])
            街道 = arg_标的.经济.街道名.split(b"\0", 1)[0]
            同街 = sum(
                地.经济.业主 == arg_槽 + 1 and 地.经济.街道名.split(b"\0", 1)[0] == 街道
                for 地 in self.世界.地产[1:]
            )
            等级 = arg_标的.经济.等级
        稀缺 = self._单精度(6.0 - 无主 / 总数 * 4.0)
        系数 = self._整数(self._整数((等级 // 2 + 1 + 同街) * self.起价) * self.世界.头.物价)
        E = 扩展数_类.api_从值
        期望 = (E(系数) * E(稀缺) * E(热情)).api_整数()
        基价 = self._单精度(self._整数(arg_标的.地价 * self.世界.头.物价))
        上限比 = self._单精度(3.0 + self._单精度(arg_随机.api_下一个() / 65536.0))
        积 = 基价 * 上限比
        上限 = int(积) if -2147483648 <= 积 < 2147483648 else -2147483648
        return min(期望, 上限, self.世界.玩家[arg_槽].记录.现金)

    def api_电脑上限(self, arg_槽: int) -> int | None:
        for 记录 in self.记录:
            if 记录.在场 and 记录.玩家 == arg_槽 and not 记录.人类:
                return 记录.上限
        return None

    def _合法(self, arg_行动: int) -> bool:
        if self.已结束 or not self.记录[self.当前].在场 or not 0 <= arg_行动 <= 6:
            return False
        if arg_行动 in (0, 6):
            return True
        return (
            self.价格 + self.增量[arg_行动] <= self.世界.玩家[self.记录[self.当前].玩家].记录.现金
        )

    def api_决策(self) -> 拍卖决策_类 | None:
        if self.已结束 or not self.记录[self.当前].人类:
            return None
        结果 = 拍卖决策_类(self.记录[self.当前].玩家, self.价格)
        结果.行动 = [拍卖行动_类(i) for i in range(7) if self._合法(i)]
        for 记录 in self.记录[: self.原记录数]:
            if not 记录.在场:
                结果.已退出 |= 1 << 记录.玩家
        return 结果

    def _电脑行动(self) -> int:
        记录 = self.记录[self.当前]
        选择 = 0
        if self.价格 > self.世界.玩家[记录.玩家].记录.现金:
            选择 = 6
        else:
            for 编号 in range(1, 6):
                if self.价格 + self.增量[编号] <= 记录.上限:
                    选择 = 编号
            if 选择 and self.末次出价 is not None:
                目标 = self.世界.玩家[self.记录[self.末次出价].玩家].记录.现金 + 500
                if self.价格 + self.增量[选择] > 目标:
                    差 = 目标 - self.价格
                    if 差 <= 100:
                        选择 = 1
                    elif 差 <= 500:
                        选择 = 2
                    elif 差 <= 1000:
                        选择 = 3
                    elif 差 <= 5000:
                        选择 = 4
        if self.初始人数 == 1 and 选择:
            选择 = 1
        return 选择

    def api_推进(self) -> bool:
        if self.已结束 or self.记录[self.当前].人类:
            return False
        return self.api_竞价(self._电脑行动())

    def api_竞价(self, arg_行动: int) -> bool:
        if not self._合法(arg_行动):
            return False
        记录 = self.记录[self.当前]
        if arg_行动 == 0:
            记录.放弃 = True
        elif arg_行动 == 6:
            记录.在场 = False
        else:
            self.价格 += self.增量[arg_行动]
            self.末次出价 = self.当前
            for 项 in self.记录:
                项.放弃 = False
        self._行动后()
        return True

    def _行动后(self) -> None:
        在场 = sum(项.在场 for 项 in self.记录)
        放弃 = sum(项.在场 and 项.放弃 for 项 in self.记录)
        if (
            在场 == 0
            or 在场 == 放弃
            or ((在场 == 1 or 在场 - 放弃 == 1) and self.末次出价 is not None)
        ):
            self._结算()
            return
        while True:
            self.当前 = (self.当前 + 1) % 4
            if self.记录[self.当前].在场:
                break

    def _结算(self) -> None:
        self.已结束 = True
        if self.末次出价 is None:
            return
        赢家 = self.记录[self.末次出价].玩家
        标的 = self._标的()
        经济 = 标的.经济 if isinstance(标的, 地产_类) else 标的
        if 经济.业主 != 赢家 + 1:
            if 经济.业主 == 0 and self.租期:
                日, 月, 年 = self.世界.头.日期
                标的.到期日 = 日期_类.api_打包间隔(年 << 16 | 月 << 8 | 日, self.租期)
            经济.业主 = 赢家 + 1
        买家 = self.世界.玩家[赢家]
        买家.记录.现金 = self._整数(买家.记录.现金 - self.价格)
        买家.状态.累计支出 = (买家.状态.累计支出 + self.价格) & 0xFFFFFFFF
        if self.卖家 == -1:
            self.世界.公共基金 = self._整数(self.世界.公共基金 + self.价格)
        else:
            卖家 = self.世界.玩家[self.卖家]
            卖家.记录.银行 = self._整数(卖家.记录.银行 + self.价格)
            卖家.状态.累计收入 = (卖家.状态.累计收入 + self.价格) & 0xFFFFFFFF
        self.结果.赢家 = 赢家
        self.结果.价格 = self.价格
