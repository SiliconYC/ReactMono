# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ include/rich4/game.hpp；顺序/缺省值供跨语言协议与重放比较。
# ◑ 导入
from dataclasses import dataclass, field
from enum import IntEnum

from rich4.cards import 卡片目标_类


# ◕ 功能
class 游戏阶段_类(IntEnum):
    """
    原GamePhase六阶段，动画与规则决策保持分离。

    更新日志：
    2026.10.24 - 保留原枚举顺序。
    """

    人类待命, 掷骰, 移动, 等待决策, 推进回合, 结束 = range(6)


class 决策种类_类(IntEnum):
    """
    原二十一种GameDecision入口。

    更新日志：
    2026.10.24 - 原类型号不重新排序。
    """

    (
        购地,
        升级地产,
        银行,
        卡片目标,
        选择卡片,
        救援,
        购买设施,
        建造设施,
        升级设施,
        轮盘,
        商店,
        魔法类别,
        魔法效果,
        拍卖,
        彩票,
        初级股票,
        地产目标,
        行动目标,
        提示,
        金额转盘,
        小游戏,
    ) = range(21)


class 游戏事件种类_类(IntEnum):
    """
    原十三种GameEventKind。

    更新日志：
    2026.10.24 - 数值与固定C++相同。
    """

    (
        回合开始,
        骰子结果,
        已移动,
        已购地,
        已升级,
        已付租,
        银行转账,
        日期改变,
        得点券,
        玩家破产,
        游戏结束,
        未支持事件,
        提示,
    ) = range(13)


class 公告种类_类(IntEnum):
    """
    原屏幕公告编号，音画呈现不替代规则。

    更新日志：
    2026.10.24 - 对应Announcement。
    """

    (
        无,
        租金,
        现金不足,
        新闻,
        命运,
        神明出现,
        点券,
        缺席状态,
        免租,
        用道具,
        股票卡,
        抢得,
        小游戏点券,
    ) = range(13)


class 语句表_类(IntEnum):
    """
    原事件、卡片和道具三套人物语句表。

    更新日志：
    2026.10.24 - 对应SpeechTable。
    """

    事件, 卡片, 道具 = range(3)


class 效果种类_类(IntEnum):
    """
    原三十三种EffectKind，保留呈现交错而不重复结算。

    更新日志：
    2026.10.24 - 对应骰子/地图电影/月报/暂停/神明离开。
    """

    (
        掷骰,
        顶楼闪光,
        免费建设,
        抛物,
        飞弹,
        核弹,
        爆炸,
        拆屋,
        怪兽,
        神明出现,
        恶魔烟,
        破产,
        金额转盘,
        轮盘,
        股利,
        彩票开奖,
        月报,
        救护车,
        警车,
        狗撞车,
        狗打架,
        飞碟,
        飞机,
        降落伞,
        新闻影片,
        抛卡,
        问号箱,
        点券,
        工程车拆屋,
        节日烟花,
        圣诞,
        暂停,
        神明离开,
    ) = range(33)


@dataclass(frozen=True)
class 决策位置_类:
    """
    决策选项在原世界的定位点。

    更新日志：
    2026.10.24 - 对应DecisionLocation。
    """

    x: int
    y: int


@dataclass
class 决策选项_类:
    """
    原标签/值与可选定位/原对象，用于真实选项UI。

    更新日志：
    2026.10.24 - 对应DecisionOption。
    """

    标签: str
    值: int
    位置: 决策位置_类 | None = None
    对象: 卡片目标_类 | None = None


@dataclass
class 转盘状态_类:
    """
    原金额转盘/爱神轮盘的表现状态，不用于二次结算。

    更新日志：
    2026.10.24 - 对应SpinnerState。
    """

    类型: int = 0
    数位: list[int] = field(default_factory=lambda: [0] * 4)
    阶段: int = 0
    游标: int = 0
    主体: int = -1
    种子: int = 0
    结果: int = 0


@dataclass
class 小游戏状态_类:
    """
    主流在小游戏落点的种子、游戏和人物。

    更新日志：
    2026.10.24 - 对应MiniGameState。
    """

    游戏: int = 0
    人物: int = 0
    种子: int = 0


@dataclass
class 决策_类:
    """
    可暂停的原真实规则决策，None与0的语义分别保留。

    更新日志：
    2026.10.24 - 对应GameDecision。
    """

    种类: 决策种类_类
    玩家: int
    地产: int = 0
    金额: int = 0
    提示: str = ""
    选项: list[决策选项_类] = field(default_factory=list)
    金额上限: int = 0
    转盘: 转盘状态_类 | None = None
    小游戏: 小游戏状态_类 | None = None
    不活跃玩家: int = 0
    被抢玩家: int | None = None


@dataclass
class 托管设置_类:
    """
    人类玩家原托管位和配置五字节。

    更新日志：
    2026.10.24 - 对应AiSettings。
    """

    自动: bool = False
    卡片策略: int = 0
    性格: int = 0
    现金比例: int = 50
    股票比例: int = 0


@dataclass
class 游戏事件_类:
    """
    原规则事件、公告/人物表情语句和音效，支持值比较与真实重放去重。

    更新日志：
    2026.10.24 - 对应GameEvent全部字段。
    """

    种类: 游戏事件种类_类
    玩家: int
    金额: int = 0
    节点: int = 0
    消息: str = ""
    语音类别: int | None = None
    公告: 公告种类_类 = 公告种类_类.无
    公告号: int = 0
    地产: int = 0
    主体: int = -1
    次主体: int = -1
    公司: int = -1
    值: int = 0
    玩家掩码: int = 0
    玩家金额: list[int] = field(default_factory=lambda: [0] * 4)
    卡片: int | None = None
    语句表: 语句表_类 = 语句表_类.事件
    语句槽: int = 0
    表情: int = 0
    音效: int | None = None


@dataclass
class 股利行_类:
    """
    股利表现取结算前收益和各槽实际派发额。

    更新日志：
    2026.10.24 - 对应DividendRow。
    """

    股票: int = 0
    盈余: int = 0
    派发: list[int] = field(default_factory=lambda: [0] * 4)


@dataclass
class 月报_类:
    """
    原月结/股利/彩票报告快照，避免显示时再次修改或重算世界。

    更新日志：
    2026.10.24 - 对应MonthlyFigures全部字段。
    """

    活跃: int = 0
    人物: list[int] = field(default_factory=lambda: [0] * 4)
    股利: list[股利行_类] = field(default_factory=list)
    票: list[int] = field(default_factory=lambda: [0] * 36)
    奖池: int = 0
    号码: int = 0
    赢家: int = -1
    现金: list[int] = field(default_factory=lambda: [0] * 4)
    存款: list[int] = field(default_factory=lambda: [0] * 4)
    利息: list[int] = field(default_factory=lambda: [0] * 4)
    余额: list[int] = field(default_factory=lambda: [0] * 4)
    总资产: list[int] = field(default_factory=lambda: [0] * 4)
    贷款: int = 0
    倒霉天: list[int] = field(default_factory=lambda: [0] * 4)
    收入: list[int] = field(default_factory=lambda: [0] * 4)
    支出: list[int] = field(default_factory=lambda: [0] * 4)
    冠军: int = -1
    悲情: int = -1


@dataclass(frozen=True)
class 效果点_类:
    """
    地图动画的原世界坐标。

    更新日志：
    2026.10.24 - 对应EffectPoint。
    """

    x: int = 0
    y: int = 0


@dataclass
class 效果_类:
    """
    原地图电影/月结/转盘/暂停以及在事件队列中的交错位置。

    更新日志：
    2026.10.24 - 对应EffectEvent全部字段。
    """

    种类: 效果种类_类
    玩家: int = 0
    节点: int = 0
    目标: 效果点_类 = field(default_factory=效果点_类)
    起点: 效果点_类 | None = None
    物件种类: int = 0
    骰子: list[int] = field(default_factory=list)
    地产: int = 0
    事件位: int = 0
    转盘: 转盘状态_类 | None = None
    月报: 月报_类 | None = None
    原等级: int = 0
    原类型: int = 0
    方向: int = 0


@dataclass
class 移动动画_类:
    """
    玩家端点动画只保存规则已决定的坐标与已过时间。

    更新日志：
    2026.10.24 - 对应MoveAnimation。
    """

    玩家: int
    起x: int
    起y: int
    终x: int
    终y: int
    已过毫秒: int
    时长毫秒: int


@dataclass
class 已展示_类:
    """
    事务各次等待选择前已送出的表现，后续重放只删除完整顺序匹配。

    更新日志：
    2026.10.24 - 对应Impl::DeliveredPresentation。
    """

    事件: list[游戏事件_类] = field(default_factory=list)
    效果: list[效果_类] = field(default_factory=list)


class 待选择异常_类(Exception):
    """
    原规则要求真实决策的控制流，不作为失败或假默认答案。

    更新日志：
    2026.10.24 - 对应NeedChoice。
    """

    def __init__(self, arg_决策: 决策_类, arg_键: int) -> None:
        super().__init__(arg_决策.提示)
        self.决策, self.键 = arg_决策, arg_键


class 未支持规则异常_类(Exception):
    """
    固定源的明确缺依赖分支，不能用于隐藏未移植规则。

    更新日志：
    2026.10.24 - 对应UnsupportedRule。
    """

    def __init__(self, arg_消息: str) -> None:
        super().__init__(arg_消息)
        self.消息 = arg_消息
