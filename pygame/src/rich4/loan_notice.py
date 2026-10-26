# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ src/game.cpp:3097-3110 / tools/screens/main_screen.cpp 的只读呈现扩展。
# ◑ 导入
from dataclasses import dataclass

from rich4.calendar import 日期_类
from rich4.game_types import 游戏事件_类, 游戏事件种类_类
from rich4.message_overlay import 消息_类, 消息种类_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类, 文字样式_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass(frozen=True)
class 贷款提醒_类:
    """
    贷款展示快照，不写规则世界、存档或随机数。

    更新日志：
    2026.10.26 - 补充两周/一周提醒、原三天预警、收款反馈与人类贷款常驻摘要。
    """

    人名: str
    金额: int
    现金: int
    存款: int
    到期日: str
    剩余: int | None

    @classmethod
    def api_读取(cls, arg_世: 世界_类, arg_槽: int) -> "贷款提醒_类 | None":
        if not 0 <= arg_槽 < len(arg_世.玩家):
            return None
        人 = arg_世.玩家[arg_槽]
        if not 人.记录.控制标志 & 1 or 人.记录.贷款 <= 0:
            return None
        到 = 人.状态.贷款到期
        日, 月, 年 = arg_世.头.日期
        try:
            期 = 日期_类(到 >> 16, 到 >> 8 & 255, 到 & 255)
            剩 = 日期_类(年, 月, 日).api_日期差(期)
            日期 = f"{期.年:04d}/{期.月:02d}/{期.日:02d}"
        except ValueError:
            # 原存档允许保留无效日期；显示异常而不替规则补收或改写日期。
            日期, 剩 = "到期日异常", None
        return cls(
            画框_类.人名[人.记录.角色 % 12],
            人.记录.贷款,
            人.记录.现金,
            人.记录.银行,
            日期,
            剩,
        )

    def api_缺口(self) -> int:
        return max(0, self.金额 - (self.现金 + self.存款))

    def api_风险(self) -> bool:
        return self.剩余 is not None and 0 <= self.剩余 <= 7 and self.api_缺口() > 0

    def api_天数(self) -> str:
        if self.剩余 is None:
            return "到期日异常"
        if self.剩余 < 0:
            return f"已过期 {-self.剩余} 天"
        return "今天到期" if self.剩余 == 0 else f"剩余 {self.剩余} 天"

    @classmethod
    def api_从事件(
        cls,
        arg_事: 游戏事件_类,
        arg_世: 世界_类,
        arg_人类槽: frozenset[int] = frozenset(),
    ) -> 消息_类 | None:
        事 = arg_事
        if not 0 <= 事.玩家 < len(arg_世.玩家):
            return None
        if (
            事.种类 == 游戏事件种类_类.银行转账
            and 事.消息 == "贷款到期，银行收回贷款"
            and 事.金额 > 0
        ):
            人 = arg_世.玩家[事.玩家].记录
            if not 人.控制标志 & 1 and 事.玩家 not in arg_人类槽:
                return None
            名 = 画框_类.人名[人.角色 % 12]
            收款 = "银行已收回贷款" if 人.控制标志 else "到期应还贷款"
            文 = (
                f"{名}，贷款今天到期\n{收款} ${事.金额:,}\n"
                f"当前现金 ${人.现金:,}\n当前存款 ${人.银行:,}\n"
                + ("资金不足，已破产。" if not 人.控制标志 else "本笔贷款已结清。")
            )
            return 消息_类(
                消息种类_类.对话框, 文字=文, 标题="贷款到期结算", 需确认=True
            )
        项 = cls.api_读取(arg_世, 事.玩家)
        if 项 is None:
            return None
        早提醒 = 事.种类 == 游戏事件种类_类.回合开始 and 项.剩余 in (15, 7, 3, 2, 1)
        原预警 = (
            事.种类 == 游戏事件种类_类.提示
            and 项.剩余 in (1, 2, 3)
            and 事.消息 == f"贷款将在{项.剩余}天后到期"
        )
        if not (早提醒 or 原预警):
            return None
        状 = arg_世.玩家[事.玩家].状态
        缺席 = next(
            (名 for 天, 名 in (
                (状.医院天数, "住院中"),
                (状.监狱天数, "入狱中"),
                (状.酒店天数, "住酒店中"),
                (状.消失天数, "消失中"),
                (状.睡眠天数, "睡眠中"),
            ) if 天),
            "",
        )
        文 = f"{项.人名}，贷款{项.api_天数()}\n"
        if 缺席:
            文 += f"当前{缺席}，仍会按期收款\n"
        文 += (
            f"应还金额 ${项.金额:,}\n到期日期 {项.到期日}\n"
            f"现金 ${项.现金:,} / 存款 ${项.存款:,}\n"
            f"可用资金 ${项.现金 + 项.存款:,}\n"
        )
        文 += (
            f"资金缺口 ${项.api_缺口():,}\n破产风险：到期资金不足将破产。"
            if 项.api_风险()
            else "到期银行将先扣存款，再扣现金。"
        )
        return 消息_类(消息种类_类.对话框, 文字=文, 标题="贷款到期提醒", 需确认=True)

    @classmethod
    def api_绘常驻(cls, arg_框: 画框_类, arg_世: 世界_类) -> None:
        顶 = 46
        for 槽 in range(len(arg_世.玩家)):
            项 = cls.api_读取(arg_世, 槽)
            if 项 is None:
                continue
            危 = 项.api_风险()
            色 = 原生界面_类.api_颜色(255, 165, 140) if 危 else 32767
            高 = 44 if 危 else 25
            原生界面_类.api_填充(arg_框.画布, (6, 顶, 434, 顶 + 高), 2114)
            原生界面_类.api_填充(arg_框.画布, (6, 顶, 9, 顶 + 高), 色)
            文 = f"{项.人名}  贷款 ${项.金额:,}  |  {项.api_天数()}"
            arg_框.字体.api_绘块(
                arg_框.画布, 文, 15, 顶 + 4, 文字样式_类(16, 色)
            )
            if 危:
                arg_框.字体.api_绘块(
                    arg_框.画布,
                    f"资金缺口 ${项.api_缺口():,}，到期可能破产",
                    15,
                    顶 + 24,
                    文字样式_类(14, 色),
                )
            顶 += 高 + 3
