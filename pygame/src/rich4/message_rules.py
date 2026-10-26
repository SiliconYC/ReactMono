# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/messages.cpp的事件/决策映射；商业长文字仅从外部PE读取。
# ◑ 导入
import re
from copy import deepcopy

from rich4.cards import 卡片目标_类, 目标种类_类
from rich4.game_types import 公告种类_类, 决策_类, 决策种类_类, 游戏事件_类, 语句表_类
from rich4.loan_notice import 贷款提醒_类
from rich4.message_overlay import 消息_类, 消息种类_类, 消息行_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.original_text import 原版文字_类
from rich4.services import 服务_类
from rich4.world import 世界_类


# ◕ 功能
class 消息规则_类:
    """
    原公告/台词/目标名及确认决策转换，只构造值，不结算或消费随机数。

    更新日志：
    2026.10.26 - 贷款预警接入主动通知，读档重置按玩家/日期的呈现去重。
    2026.10.24 - 保存外部原文VA依据，保留空台词及消失人物的原门控。
    """

    情绪 = (0, 0, 0, 2, 2, 2, 3, 3, 3, 2, 2, 2, 3, 3, 3, 0, 0, 0, 1, 2, 2, 1, 2, 2, 3, 2, 3)
    命运照片 = (
        477,
        478,
        479,
        480,
        481,
        482,
        483,
        484,
        485,
        486,
        487,
        488,
        489,
        490,
        491,
        492,
        493,
        494,
        495,
        496,
        497,
        497,
        497,
        498,
        498,
        499,
        500,
        501,
        501,
        501,
        502,
        503,
        504,
        505,
        506,
        507,
        508,
        505,
        509,
        510,
        511,
        512,
        506,
        507,
        513,
        514,
        515,
        510,
        516,
    )
    缺席地址 = (0x4631E0, 0x4631F5, 0x46320A, 0x46321F, 0x463234)
    免租地址 = (
        0x463BB8,
        0x463BCD,
        0x463BE2,
        0x463BF5,
        0x463C08,
        0x463C1B,
        0x463C2E,
        0x463C41,
        0x463C54,
    )

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self.原文 = arg_原文
        self._贷款已提醒: dict[int, tuple[tuple[int, int, int], int]] = {}
        self._贷款人类: frozenset[int] = frozenset()

    def api_重置贷款提醒(self, arg_世: 世界_类 | None = None) -> None:
        self._贷款已提醒.clear()
        # 到期收款可能将控制标志清零，必须在安装会话时记住人类归属。
        self._贷款人类 = (
            frozenset(i for i, 人 in enumerate(arg_世.玩家) if 人.记录.控制标志 & 1)
            if arg_世 is not None
            else frozenset()
        )

    @staticmethod
    def api_格式(arg_文: str, arg_值: list[str | int]) -> str:
        迭 = iter(arg_值)
        return re.sub(r"%[sd]", lambda _: str(next(迭, "")), arg_文)

    def _格式(self, arg_地址: int, *arg_值: str | int) -> str:
        return self.api_格式(self.原文.api_原文(arg_地址), list(arg_值))

    @staticmethod
    def api_人名(arg_世: 世界_类, arg_槽: int) -> str:
        return (
            画框_类.人名[arg_世.玩家[arg_槽].记录.角色 % 12]
            if 0 <= arg_槽 < len(arg_世.玩家)
            else ""
        )

    @staticmethod
    def api_地名(arg_世: 世界_类, arg_码: int) -> str:
        原 = b""
        if 2000 < arg_码 < 4000 and arg_码 - 2000 < len(arg_世.地产):
            原 = arg_世.地产[arg_码 - 2000].经济.街道名
        elif 4000 < arg_码 and arg_码 - 4000 < len(arg_世.设施):
            原 = arg_世.设施[arg_码 - 4000].名字
        return 原生界面_类.api_繁中(原).replace(" ", "")

    def api_股名(self, arg_世: 世界_类, arg_号: int) -> str:
        偏 = (arg_世.头.阶段 * 4 + arg_世.头.地图) * 12
        if not 0 <= arg_号 < 12 or not 0 <= 偏 + arg_号 < 96:
            return ""
        return self.原文.api_股票(偏 + arg_号).replace(" ", "")

    def _公司(self, arg_世: 世界_类, arg_号: int) -> str:
        if not 0 < arg_号 < len(arg_世.公司):
            return ""
        return self.api_股名(arg_世, arg_世.公司[arg_号].股票索引)

    @staticmethod
    def _气泡(
        arg_人物: int, arg_文字: str, arg_声音: int, arg_情绪: int, arg_焦: int | None
    ) -> 消息_类:
        项 = 消息_类(人物=arg_人物, 情绪=arg_情绪, 声音=arg_声音, 等待声音=True, 焦点=arg_焦)
        if arg_文字.startswith("@"):
            匹配 = re.match(r"\s*[+-]?[0-9]+", arg_文字[1:])
            if 匹配 is None:
                raise ValueError("原图语缺少编号")
            项.图语 = int(匹配[0])
        else:
            项.文字 = arg_文字
        return 项

    def api_事件气泡(self, arg_人物: int, arg_类别: int, arg_焦: int | None) -> 消息_类:
        人 = (arg_人物 & 255) % 12
        if not 0 <= arg_类别 < 27:
            raise IndexError("原事件台词类别越界")
        行 = self.原文.api_台词("event", 人, arg_类别)
        if 行 is None:
            raise ValueError("原事件台词缺失")
        return self._气泡(人, 行.文字, 1050 + 人 * 27 + arg_类别, self.情绪[arg_类别], arg_焦)

    def api_物品气泡(
        self, arg_人物: int, arg_表: 语句表_类, arg_槽: int, arg_情绪: int, arg_焦: int | None
    ) -> 消息_类 | None:
        人 = (arg_人物 & 255) % 12
        if arg_表 == 语句表_类.卡片 and 0 <= arg_槽 < 90:
            行 = self.原文.api_台词("card", 人, arg_槽)
        elif arg_表 == 语句表_类.道具 and 0 <= arg_槽 < 26:
            行 = self.原文.api_台词("tool", 人, arg_槽)
        else:
            return None
        if 行 is None or not 行.声音:
            return None
        return self._气泡(人, 行.文字, 行.声音, (arg_情绪 & 255) % 4, arg_焦)

    @staticmethod
    def _框(arg_文: str, arg_毫秒: int = 1500) -> 消息_类:
        return 消息_类(消息种类_类.对话框, 文字=arg_文, 最少毫秒=arg_毫秒)

    def _租金(self, arg_e: 游戏事件_类, arg_世: 世界_类) -> 消息_类:
        e, 世 = arg_e, arg_世
        if e.地产 > 4000:
            if e.公告号 == 1:
                return self._框(self._格式(0x4639FF, e.值, e.金额))
            if e.公告号 == 2 and e.值 > 0:
                基 = abs(e.金额) // e.值 * (-1 if e.金额 < 0 else 1)
                return self._框(self._格式(0x463A14, 基, e.值, e.金额))
        费 = self.原文.api_费名(2 if e.地产 > 4000 and e.公告号 == 3 else 0)
        名 = self.api_地名(世, e.地产)
        if e.次主体 >= 0:
            return self._框(
                self._格式(
                    0x46399A, 名, self.api_人名(世, e.主体), self.api_人名(世, e.次主体), e.金额, 费
                )
            )
        return self._框(self._格式(0x4639B3, 名, self.api_人名(世, e.主体), e.金额, 费))

    def _新闻(self, arg_e: 游戏事件_类, arg_世: 世界_类) -> 消息_类:
        e, 世 = arg_e, arg_世
        i = e.公告号 % 36
        类 = 0 if i < 6 else 1 if i < 14 else 2 if i < 16 else 3 if i < 18 else 4 if i < 22 else 5
        项 = 消息_类(
            消息种类_类.新闻,
            照片=441 + i,
            标题=self.原文.api_新闻标题(类),
            声音=149 + i,
            最少毫秒=2400,
            等待声音=True,
        )
        if i in (1, 3):
            参 = [e.值]
        elif 8 <= i <= 10:
            参 = [self.api_人名(世, e.主体), e.值]
        elif i in (27, 28):
            参 = [self.api_股名(世, e.主体)]
        elif i == 29:
            参 = [self._公司(世, e.公司), self.api_人名(世, e.主体)]
        elif i >= 30:
            参 = [self._公司(世, e.公司)]
        else:
            参 = [self.api_地名(世, e.地产)]
        项.文字 = self.api_格式(self.原文.api_配音(149 + i).文字, 参)
        for 槽 in range(min(4, len(世.玩家))):
            if not e.玩家掩码 & (1 << 槽):
                continue
            人 = 世.玩家[槽].记录.角色 % 12
            if 11 <= i <= 13 or i == 23:
                文 = self._格式(
                    0x465727 if i == 23 else 0x465592, self.api_人名(世, 槽), e.玩家金额[槽]
                )
                项.行.append(消息行_类(人, 3, 文))
            elif i < 4 or i == 29:
                项.行.append(消息行_类(人, 4))
        return 项

    def api_从事件(self, arg_e: 游戏事件_类, arg_世: 世界_类) -> 消息_类 | None:
        e, 世 = arg_e, arg_世
        贷款 = 贷款提醒_类.api_从事件(e, 世, self._贷款人类)
        if 贷款 is not None:
            if 贷款.标题 == "贷款到期提醒":
                # 原三天事件与回合开始都可触发；读档仅有后者，同一天只展示一次。
                键 = 世.头.日期, 世.玩家[e.玩家].状态.贷款到期
                if e.玩家 in self._贷款已提醒 and self._贷款已提醒[e.玩家] == 键:
                    return None
                self._贷款已提醒[e.玩家] = 键
            return 贷款
        if e.语句表 != 语句表_类.事件 and e.玩家 < len(世.玩家):
            return self.api_物品气泡(世.玩家[e.玩家].记录.角色, e.语句表, e.语句槽, e.表情, e.玩家)
        if e.语音类别 is not None and e.玩家 < len(世.玩家) and e.语音类别 < 27:
            if 世.玩家[e.玩家].状态.消失天数:
                return None
            return self.api_事件气泡(世.玩家[e.玩家].记录.角色, e.语音类别, e.玩家)
        a, i = e.公告, e.公告号
        if a == 公告种类_类.租金:
            return self._租金(e, 世)
        if a == 公告种类_类.现金不足:
            return self._框(self.原文.api_原文(0x46398B))
        if a == 公告种类_类.新闻:
            return self._新闻(e, 世)
        if a == 公告种类_类.命运:
            i %= 49
            人 = 世.玩家[e.玩家].记录.角色 % 12 if e.玩家 < len(世.玩家) else 0
            return 消息_类(
                消息种类_类.命运,
                人物=人,
                照片=self.命运照片[i],
                声音=185 + i,
                最少毫秒=1600,
                等待声音=True,
                文字=self.api_格式(self.原文.api_配音(185 + i).文字, [e.值]),
            )
        if a == 公告种类_类.神明出现:
            号 = i - 1 if 1 <= i <= 10 else 10 if i == 12 else 11 if i == 15 else -1
            return (
                None
                if 号 < 0
                else 消息_类(
                    消息种类_类.神明字幕, 焦点=e.玩家, 文字=self.原文.api_神明(号), 最少毫秒=2400
                )
            )
        if a == 公告种类_类.缺席状态:
            return (
                None
                if e.值 <= 0 or i >= 5
                else self._框(self._格式(self.缺席地址[i], self.api_人名(世, e.玩家), e.值))
            )
        if a == 公告种类_类.股票卡:
            if not 0 <= e.主体 < len(世.股票) or i not in (24, 25):
                return None
            return self._框(self._格式(0x4653AE, self.api_股名(世, e.主体), 服务_类.卡名[i - 1]))
        if a == 公告种类_类.抢得:
            名 = 服务_类.道具名 if i == 1 else 服务_类.卡名
            return (
                None
                if not 1 <= e.值 <= len(名)
                else self._框(self._格式(0x4652F8, self.api_人名(世, e.主体), 名[e.值 - 1]))
            )
        if a == 公告种类_类.用道具:
            return (
                None if not 1 <= i <= 13 else self._框(self._格式(0x4653E5, 服务_类.道具名[i - 1]))
            )
        if a == 公告种类_类.免租:
            if i >= 9:
                return None
            类 = (
                世.设施[e.地产 - 4000].类型 if 4000 < e.地产 and e.地产 - 4000 < len(世.设施) else 0
            )
            费 = self.原文.api_原文({1: 0x4638AD, 2: 0x4638DA, 3: 0x463898}.get(类, 0x46388A))
            参 = [费] if i in (0, 2) else [self.api_人名(世, e.主体), 费]
            return self._框(self.api_格式(self.原文.api_原文(self.免租地址[i]), 参))
        if a == 公告种类_类.点券:
            return self._框(
                self.原文.api_原文(
                    0x463A81 if e.金额 == 50 else 0x463A8E if e.金额 == 30 else 0x463A9B
                ),
                1000,
            )
        if a == 公告种类_类.小游戏点券:
            return self._框(self._格式(0x463797, e.金额), 2000)
        return None

    @staticmethod
    def api_是确认(arg_决: 决策_类) -> bool:
        if arg_决.种类 == 决策种类_类.卡片目标:
            return len(arg_决.选项) == 2
        return (
            arg_决.种类
            in (决策种类_类.购地, 决策种类_类.升级地产, 决策种类_类.购买设施, 决策种类_类.升级设施)
            and len(arg_决.选项) == 2
            and {o.值 for o in arg_决.选项} == {0, 1}
        )

    def api_对象名(self, arg_世: 世界_类, arg_对象: 卡片目标_类) -> str:
        k, v = arg_对象.种类, arg_对象.数值
        if k == 目标种类_类.角色:
            return (
                self.api_人名(arg_世, v)
                if v < 4
                else ("小偷", "強盜", "流氓", "間諜")[v - 4]
                if v < 8
                else ""
            )
        if k == 目标种类_类.地产:
            return self.api_地名(arg_世, v)
        if k == 目标种类_类.股票:
            return self.api_股名(arg_世, v)
        if k == 目标种类_类.物件:
            if not 1 <= v <= len(arg_世.物件):
                return ""
            种 = arg_世.物件[v - 1].种类
            return 服务_类.道具名[种 - 15] if 15 <= 种 < 28 else ""
        if k in (目标种类_类.卡片, 目标种类_类.道具):
            名 = 服务_类.卡名 if k == 目标种类_类.卡片 else 服务_类.道具名
            return 名[v - 1] if 1 <= v <= len(名) else ""
        return ""

    def api_本地化(self, arg_决: 决策_类, arg_世: 世界_类) -> 决策_类:
        显 = deepcopy(arg_决)
        for o in 显.选项:
            if o.对象 is not None:
                名 = self.api_对象名(arg_世, o.对象)
                if 名:
                    o.标签 = "嫁禍給" + 名 if arg_决.种类 == 决策种类_类.卡片目标 else 名
        if arg_决.种类 == 决策种类_类.卡片目标 and len(arg_决.选项) == 2:
            首 = arg_决.选项[0].对象
            显.提示 = (
                self._格式(0x46534E, self.api_对象名(arg_世, 首))
                if 首 is not None
                else self._格式(0x465388, self.api_人名(arg_世, arg_决.玩家))
            )
        return 显

    def api_确认问题(self, arg_决: 决策_类, arg_世: 世界_类) -> str:
        if arg_决.种类 == 决策种类_类.卡片目标:
            return self.api_本地化(arg_决, arg_世).提示
        设施 = arg_决.种类 in (决策种类_类.购买设施, 决策种类_类.升级设施)
        升级 = arg_决.种类 in (决策种类_类.升级地产, 决策种类_类.升级设施)
        名 = self.api_地名(arg_世, ((4000 if 设施 else 2000) + arg_决.地产) & 65535)
        return self._格式(0x46396D if 升级 else 0x4639E1, 名, arg_决.金额)
