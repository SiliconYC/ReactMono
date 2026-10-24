# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/services.cpp；保留偏好槽位、字节回绕与回调消费顺序。
# ◑ 导入
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from rich4.inventory import 库存_类
from rich4.random import 随机数_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类
from rich4.world_player import 世界玩家_类


# ◕ 功能
@dataclass
class 商店_类:
    """
    一次访问的有限货架与营业收入，不在核心层生成界面。

    更新日志：
    2026.10.23 - 对应 services::Shop。
    """

    卡片: list[int] = field(default_factory=list)
    道具: list[int] = field(default_factory=list)
    收入: int = 0
    赠卡: int = 0
    赠道具: int = 0
    已关闭: bool = False


@dataclass(frozen=True)
class 魔法选择_类:
    """
    魔法类别与效果均沿用零基编号。

    更新日志：
    2026.10.23 - 对应 MagicChoice。
    """

    类别: int
    效果: int


@dataclass
class 魔法回调_类:
    """
    游戏会话提供真实规则处理；缺少所需能力时整次施法拒绝执行。

    更新日志：
    2026.10.23 - 对应 MagicCallbacks，不为缺失规则提供替代结果。
    """

    命运: Callable[[int], None] | None = None
    防御: Callable[[int], int] | None = None
    敌意: Callable[[int, int, int], None] | None = None
    监狱: Callable[[int, int], None] | None = None
    医院: Callable[[int, int], None] | None = None
    升级: Callable[[int], None] | None = None
    降级: Callable[[int], None] | None = None
    拍卖: Callable[[int, int], None] | None = None
    转向: Callable[[int], None] | None = None


class 服务_类:
    """
    商店交易、电脑购物和十二类魔法目标/效果。

    更新日志：
    2026.10.23 - 移植 services.cpp 全部规则，UI 名称和游戏会话另行接入。
    """

    卡名 = (
        "均富卡",
        "均貧卡",
        "購地卡",
        "換地卡",
        "換屋卡",
        "轉向卡",
        "改建卡",
        "拍賣卡",
        "天使卡",
        "惡魔卡",
        "怪獸卡",
        "拆除卡",
        "搶奪卡",
        "停留卡",
        "冬眠卡",
        "夢遊卡",
        "陷害卡",
        "復仇卡",
        "嫁禍卡",
        "免費卡",
        "免罪卡",
        "送神符",
        "請神符",
        "紅卡",
        "黑卡",
        "查稅卡",
        "漲價卡",
        "查封卡",
        "同盟卡",
        "烏龜卡",
    )
    道具名 = (
        "機器娃娃",
        "路障",
        "地雷",
        "定時炸彈",
        "機車",
        "汽車",
        "飛彈",
        "遙控骰子",
        "機器工人",
        "時光機",
        "傳送機",
        "工程車",
        "核子飛彈",
    )
    卡价 = (
        200,
        200,
        35,
        25,
        20,
        20,
        15,
        20,
        160,
        180,
        60,
        15,
        25,
        20,
        100,
        25,
        20,
        20,
        40,
        25,
        25,
        10,
        20,
        50,
        30,
        35,
        35,
        35,
        40,
        70,
    )
    道具价 = (15, 30, 25, 25, 80, 150, 100, 30, 30, 40, 95, 150, 250)
    魔法分类 = (
        "最富有的人",
        "土地最多的人",
        "房屋最多的人",
        "現金最多的人",
        "存款最多的人",
        "點數最多的人",
        "步行的人",
        "騎機車的人",
        "開汽車的人",
        "神明附身的人",
        "男性",
        "女性",
    )
    魔法效果 = (
        "出售全部卡片",
        "連抽三次命運",
        "入獄三天",
        "停留一天",
        "現金全部存入銀行",
        "腳下房屋升級",
        "獲得一張卡片",
        "掉轉方向",
        "出售全部道具",
        "腳下房屋降級",
        "住院三天",
        "拍賣腳下土地",
    )
    卡偏好 = (
        2,
        2,
        1,
        0,
        0,
        0,
        0,
        1,
        0,
        2,
        2,
        1,
        2,
        0,
        2,
        1,
        2,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        0,
        1,
        0,
        0,
    )
    道具偏好 = (0, 1, 1, 1, 0, 0, 2, 0, 1, 2, 1, 2, 2)

    @staticmethod
    def _整数(arg_值: int) -> int:
        return ((arg_值 + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    @staticmethod
    def _玩家(arg_世: 世界_类, arg_槽: int) -> 世界玩家_类:
        if not 0 <= arg_槽 < len(arg_世.玩家):
            raise IndexError("服务玩家越界")
        return arg_世.玩家[arg_槽]

    @classmethod
    def _库存(cls, arg_世: 世界_类, arg_槽: int) -> 库存_类:
        记录 = cls._玩家(arg_世, arg_槽).记录
        return 库存_类(记录.卡片, arg_世.卡供应, cls.卡价, 记录.道具, arg_世.道具供应, cls.道具价)

    @staticmethod
    def _加权(arg_供应: Sequence[int], arg_随机: 随机数_类) -> int:
        总 = sum(arg_供应)
        if 总 == 0:
            return 0
        索引 = arg_随机.api_下一个() % 总
        for i, 数 in enumerate(arg_供应):
            if 索引 < 数:
                return i + 1
            索引 -= 数
        raise RuntimeError("加权库存不变量破坏")

    @classmethod
    def api_随机卡(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int) -> int:
        编号 = cls._加权(arg_世.卡供应, arg_随机)
        if 编号:
            cls._库存(arg_世, arg_槽).api_收卡(编号)
        return 编号

    @classmethod
    def api_随机道具(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int) -> int:
        编号 = cls._加权(arg_世.道具供应, arg_随机)
        if 编号:
            cls._库存(arg_世, arg_槽).api_收道具(编号)
        return 编号

    @classmethod
    def _买卡(cls, arg_世: 世界_类, arg_店: 商店_类, arg_槽: int, arg_卡: int) -> None:
        记录 = cls._玩家(arg_世, arg_槽).记录
        cls._库存(arg_世, arg_槽).api_收卡(arg_卡)
        记录.点券 = (记录.点券 - cls.卡价[arg_卡 - 1]) & 0xFFFF
        arg_店.收入 = cls._整数(arg_店.收入 + cls.卡价[arg_卡 - 1] * 10)

    @classmethod
    def _买道具(cls, arg_世: 世界_类, arg_店: 商店_类, arg_槽: int, arg_物: int) -> None:
        记录 = cls._玩家(arg_世, arg_槽).记录
        cls._库存(arg_世, arg_槽).api_收道具(arg_物)
        记录.点券 = (记录.点券 - cls.道具价[arg_物 - 1]) & 0xFFFF
        arg_店.收入 = cls._整数(arg_店.收入 + cls.道具价[arg_物 - 1] * 10)

    @classmethod
    def api_开店(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_地产: int = 0
    ) -> 商店_类:
        店 = 商店_类()
        记录 = cls._玩家(arg_世, arg_槽).记录
        if 6000 < arg_地产 < 8000 and arg_世.公司[arg_地产 - 6000].业主 == arg_槽 + 1:
            if arg_随机.api_下一个() & 1:
                店.赠道具 = cls.api_随机道具(arg_世, arg_随机, arg_槽)
            else:
                店.赠卡 = cls.api_随机卡(arg_世, arg_随机, arg_槽)
        if 记录.控制标志 != 1:
            cls._电脑购物(arg_世, 店, arg_槽)
            return 店
        供应 = arg_世.卡供应.copy()
        数量 = arg_随机.api_下一个() % 10 + 6
        for _ in range(数量):
            编号 = cls._加权(供应, arg_随机)
            if not 编号:
                break
            店.卡片.append(编号)
            供应[编号 - 1] -= 1
        店.道具 = [i + 1 for i, 数 in enumerate(arg_世.道具供应) if 数]
        return 店

    @classmethod
    def api_买卡(cls, arg_世: 世界_类, arg_店: 商店_类, arg_槽: int, arg_卡: int) -> bool:
        记录 = cls._玩家(arg_世, arg_槽).记录
        if (
            arg_店.已关闭
            or not 1 <= arg_卡 <= 30
            or arg_卡 not in arg_店.卡片
            or 记录.点券 < cls.卡价[arg_卡 - 1]
            or cls._库存(arg_世, arg_槽).api_卡数() == 15
            or not arg_世.卡供应[arg_卡 - 1]
        ):
            return False
        cls._买卡(arg_世, arg_店, arg_槽, arg_卡)
        arg_店.卡片.remove(arg_卡)
        return True

    @classmethod
    def api_买道具(cls, arg_世: 世界_类, arg_店: 商店_类, arg_槽: int, arg_物: int) -> bool:
        记录 = cls._玩家(arg_世, arg_槽).记录
        if (
            arg_店.已关闭
            or not 1 <= arg_物 <= 8
            or arg_物 not in arg_店.道具
            or 记录.点券 < cls.道具价[arg_物 - 1]
            or 记录.道具[arg_物 - 1] >= 9
            or not arg_世.道具供应[arg_物 - 1]
        ):
            return False
        cls._买道具(arg_世, arg_店, arg_槽, arg_物)
        if not arg_世.道具供应[arg_物 - 1]:
            arg_店.道具.remove(arg_物)
        return True

    @classmethod
    def api_卖卡(cls, arg_世: 世界_类, arg_店: 商店_类, arg_槽: int, arg_卡: int) -> bool:
        记录 = cls._玩家(arg_世, arg_槽).记录
        if arg_店.已关闭 or not 1 <= arg_卡 <= 30 or not cls._库存(arg_世, arg_槽).api_用卡(arg_卡):
            return False
        记录.点券 = (记录.点券 + cls.卡价[arg_卡 - 1] * 9 // 10) & 0xFFFF
        arg_店.收入 = cls._整数(arg_店.收入 + cls.卡价[arg_卡 - 1])
        return True

    @classmethod
    def api_卖道具(
        cls, arg_世: 世界_类, arg_店: 商店_类, arg_槽: int, arg_物: int, arg_数: int = 1
    ) -> bool:
        记录 = cls._玩家(arg_世, arg_槽).记录
        if arg_店.已关闭 or not 1 <= arg_物 <= 13 or arg_数 <= 0 or arg_数 > 记录.道具[arg_物 - 1]:
            return False
        价 = cls.道具价[arg_物 - 1] * arg_数
        for _ in range(arg_数):
            cls._库存(arg_世, arg_槽).api_用道具(arg_物)
        记录.点券 = (记录.点券 + 价 * 9 // 10) & 0xFFFF
        arg_店.收入 = cls._整数(arg_店.收入 + 价)
        return True

    @classmethod
    def api_关店(cls, arg_世: 世界_类, arg_店: 商店_类, arg_地产: int = 0) -> None:
        if arg_店.已关闭:
            return
        if 6000 < arg_地产 < 8000:
            公司 = arg_世.公司[arg_地产 - 6000]
            公司.资金 = cls._整数(公司.资金 + arg_店.收入)
            公司.资金变化 = cls._整数(公司.资金变化 + arg_店.收入)
        arg_店.已关闭 = True

    @classmethod
    def _电脑购物(cls, arg_世: 世界_类, arg_店: 商店_类, arg_槽: int) -> None:
        玩家 = cls._玩家(arg_世, arg_槽)
        记录 = 玩家.记录

        def 厌恶(arg_偏好: int) -> bool:
            return arg_偏好 - 玩家.状态.救援策略 == 2

        # 原 0x42edac 按当前槽位查偏好；压紧后同一槽位须再次判断。
        i = 0
        while i < 15 and 记录.卡片[i]:
            if 厌恶(cls.卡偏好[i]):
                cls.api_卖卡(arg_世, arg_店, arg_槽, 记录.卡片[i])
            else:
                i += 1
        for i in range(13):
            if 记录.道具[i] and 厌恶(cls.道具偏好[i]):
                cls.api_卖道具(arg_世, arg_店, arg_槽, i + 1, 记录.道具[i])
        if 记录.点券 < 100:
            卡 = cls._库存(arg_世, arg_槽).api_最便宜卡()
            if 卡:
                cls.api_卖卡(arg_世, arg_店, arg_槽, 卡)
            for i in range(13):
                if 记录.道具[i] > 1:
                    cls.api_卖道具(arg_世, arg_店, arg_槽, i + 1, 记录.道具[i] - 1)
            if 记录.交通 & 3 == 1 and 记录.道具[4]:
                cls.api_卖道具(arg_世, arg_店, arg_槽, 5, 记录.道具[4])
            if 记录.交通 & 3 == 2 and 记录.道具[5]:
                cls.api_卖道具(arg_世, arg_店, arg_槽, 6, 记录.道具[5])
        卡预算 = 记录.点券 // 2
        物预算 = 记录.点券 - 卡预算
        候选 = [
            i + 1
            for i, 数 in enumerate(arg_世.卡供应)
            if cls.卡价[i] <= 卡预算 and not 厌恶(cls.卡偏好[i])
            for _ in range(数)
        ]
        候选.sort(key=lambda k: -cls.卡价[k - 1])
        for 卡 in 候选:
            if cls._库存(arg_世, arg_槽).api_卡数() == 15:
                break
            if cls.卡价[卡 - 1] <= 卡预算:
                cls._买卡(arg_世, arg_店, arg_槽, 卡)
                卡预算 -= cls.卡价[卡 - 1]
        for 物 in (5, 6):
            if (
                记录.交通 & 3 != 物 - 4
                and not 记录.道具[物 - 1]
                and cls.道具价[物 - 1] < 物预算
                and arg_世.道具供应[物 - 1]
            ):
                cls._买道具(arg_世, arg_店, arg_槽, 物)
                物预算 -= cls.道具价[物 - 1]
        for 物 in (8, 2, 7, 1, 4, 3):
            if (
                记录.道具[物 - 1] < 9
                and not 厌恶(cls.道具偏好[物 - 1])
                and cls.道具价[物 - 1] <= 物预算
                and arg_世.道具供应[物 - 1]
            ):
                cls._买道具(arg_世, arg_店, arg_槽, 物)
                物预算 -= cls.道具价[物 - 1]

    @classmethod
    def _脚下地产(cls, arg_世: 世界_类, arg_槽: int) -> int:
        玩家 = cls._玩家(arg_世, arg_槽)
        if cls._缺席(玩家):
            return 0
        编码 = arg_世.节点[玩家.记录.节点].类型索引
        return 编码 if 2000 < 编码 < 6000 else 0

    @staticmethod
    def _缺席(arg_玩家: 世界玩家_类) -> bool:
        态 = arg_玩家.状态
        return bool(态.酒店天数 or 态.消失天数 or 态.监狱天数 or 态.医院天数)

    @classmethod
    def api_魔法目标(cls, arg_世: 世界_类, arg_类别: int) -> list[int]:
        if not 0 <= arg_类别 < 12:
            raise ValueError("魔法类别超出原表")
        结果: list[int] = []
        最大 = 0
        for 槽, 玩家 in enumerate(arg_世.玩家):
            记录 = 玩家.记录
            if not 记录.控制标志:
                continue
            if arg_类别 >= 6:
                交通 = 记录.交通 & 3
                包含 = (
                    交通 == 0,
                    交通 == 1,
                    交通 == 2,
                    玩家.状态.神明信息 != 0,
                    记录.性别 != 0,
                    记录.性别 == 0,
                )[arg_类别 - 6]
                if 包含:
                    结果.append(槽)
                continue
            if arg_类别 == 0:
                值 = 股市_类.api_财富(arg_世, 槽)
            elif arg_类别 in (1, 2):
                值 = sum(
                    地.经济.业主 == 槽 + 1 and (arg_类别 == 1 or 地.经济.等级 != 0)
                    for 地 in arg_世.地产[1:]
                )
                值 += sum(
                    地.业主 == 槽 + 1 and (arg_类别 == 1 or 地.等级 != 0) for 地 in arg_世.设施[1:]
                )
            else:
                值 = (记录.现金, 记录.银行, 记录.点券)[arg_类别 - 3]
            if (arg_类别 != 0 and 值 == 0) or 值 < 最大:
                continue
            if 值 > 最大:
                最大 = 值
                结果.clear()
            结果.append(槽)
        return 结果

    @classmethod
    def api_电脑魔法(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_演员: int
    ) -> 魔法选择_类 | None:
        if not any(cls.api_魔法目标(arg_世, 类别) for 类别 in range(12)):
            return None
        while True:
            类别 = arg_随机.api_下一个() % 12
            目标 = cls.api_魔法目标(arg_世, 类别)
            if 目标:
                break
        效果 = 6
        if arg_演员 not in 目标:
            效果 = arg_随机.api_下一个() % 11
            if 效果 == 6:
                效果 = 7
        return 魔法选择_类(类别, 效果)

    @classmethod
    def api_施法(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_演员: int,
        arg_目标: Sequence[int],
        arg_效果: int,
        arg_回调: 魔法回调_类,
    ) -> bool:
        if not 0 <= arg_演员 < len(arg_世.玩家) or not 0 <= arg_效果 < 12:
            raise ValueError("无效魔法行动")
        for 槽 in arg_目标:
            cls._玩家(arg_世, 槽)
        必需 = {
            1: (arg_回调.命运,),
            2: (arg_回调.防御, arg_回调.敌意, arg_回调.监狱),
            10: (arg_回调.防御, arg_回调.敌意, arg_回调.医院),
            5: (arg_回调.升级,),
            9: (arg_回调.降级,),
            7: (arg_回调.转向,),
            11: (arg_回调.拍卖,),
        }
        if any(回调 is None for 回调 in 必需.get(arg_效果, ())):
            return False
        for 槽 in arg_目标:
            玩家 = cls._玩家(arg_世, 槽)
            记录 = 玩家.记录
            if arg_效果 == 0:
                记录.点券 = (记录.点券 + cls._库存(arg_世, 槽).api_卖卡()) & 0xFFFF
            elif arg_效果 == 1:
                for _ in range(3):
                    arg_回调.命运(槽)
            elif arg_效果 in (2, 10):
                arg_回调.敌意(槽, arg_演员, cls._整数(arg_世.头.物价 * 90))
                目标 = arg_回调.防御(槽)
                if 目标 >= 0:
                    if arg_效果 == 2:
                        arg_回调.监狱(目标, 3)
                    else:
                        arg_回调.医院(目标, 3)
            elif arg_效果 == 3:
                玩家.状态.停留天数 = (玩家.状态.停留天数 + 1) & 0x7F
            elif arg_效果 == 4:
                记录.银行 = cls._整数(记录.银行 + 记录.现金)
                记录.现金 = 0
            elif arg_效果 in (5, 9, 11):
                地产 = cls._脚下地产(arg_世, 槽)
                if 地产:
                    if arg_效果 == 5:
                        arg_回调.升级(地产)
                    elif arg_效果 == 9:
                        arg_回调.降级(地产)
                    else:
                        arg_回调.拍卖(地产, 槽)
            elif arg_效果 == 6:
                cls.api_随机卡(arg_世, arg_随机, 槽)
            elif arg_效果 == 7:
                if not cls._缺席(玩家):
                    arg_回调.转向(槽)
            elif arg_效果 == 8:
                交通 = 记录.交通 & 3
                if 交通:
                    i = 4 if 交通 == 1 else 5 if 交通 == 2 else 11
                    记录.道具[i] = (记录.道具[i] + 1) & 255
                记录.交通, 记录.骰数 = 0, 1
                记录.点券 = (记录.点券 + cls._库存(arg_世, 槽).api_卖库存道具()) & 0xFFFF
        return True
