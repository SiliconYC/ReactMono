# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import random
from pathlib import Path

from differential_game_transactions import 会话事务差分_类, 会话事务探针_类

from rich4.events import 事件_类
from rich4.game_finance import 会话金融_类
from rich4.numeric import 数值范围错误_类
from rich4.world import 世界_类
from rich4.world_player import 玩家状态_类


# ◕ 功能
class 会话金融探针_类(会话金融_类, 会话事务探针_类):
    """
    金融私有入口使用实际规则；夹具避开尚未接入的神明/收容和三地产拍卖。

    更新日志：
    2026.10.24 - 不提供正式游戏的替代回调；越出范围将直接失败。
    """

    def _重置(self) -> None:
        super()._重置()
        self.胜者, self.恢复移动, self.银行后遭遇, self.剩余步 = None, False, False, 0

    def _状态(self) -> 玩家状态_类:
        return self.世界.玩家[self._当前()].状态

    def _序列(self, arg_状态: int, arg_值: list[int]) -> str:
        return (
            super()._序列(arg_状态, arg_值)
            + " "
            + " ".join(
                map(
                    str,
                    [
                        self.胜者 if self.胜者 is not None else -1,
                        int(self.恢复移动),
                        int(self.银行后遭遇),
                    ],
                )
            )
        )

    def api_动作(self, arg_行: str) -> str:
        op, *列 = arg_行.split()
        if op not in {"P", "T", "C", "H", "L", "K", "J", "N", "F"}:
            return super().api_动作(arg_行)
        n, 状态, 值 = list(map(int, 列)), 0, []
        try:
            if op == "P":
                p = 事件_类._取(self.世界.玩家, n[0]).记录
                p.现金, p.银行, p.贷款, p.特殊融资, p.控制标志 = n[1:]
            elif op == "T":
                p = 事件_类._取(self.世界.玩家, n[0]).状态
                (
                    p.银行禁贷天数,
                    p.银行拒绝天数,
                    p.贷款到期,
                    p.保险天数,
                    p.初始现金比例,
                    p.贷款比例,
                    p.累计支出,
                    p.累计收入,
                    p.冬眠总天数,
                    p.神运修正,
                    p.结盟天数,
                    p.盟友,
                ) = n[1:13]
                p.敌意[:] = n[13:17]
            elif op == "C":
                p = 事件_类._取(self.世界.公司, n[0])
                p.类型, p.业主, p.资金, p.资金变化 = n[1:]
            elif op == "H":
                self.世界.头.当前玩家, self.世界.头.物价, self.世界.头.初始资金 = n[:3]
                self.世界.头.日期, self.世界.租约模式 = (n[5], n[4], n[3]), n[6]
            elif op == "L":
                if n[0] >= 4000:
                    p = 事件_类._取(self.世界.设施, n[0] - 4000)
                    p.业主, p.等级, p.临时状态, p.到期日 = n[1:]
                else:
                    p = 事件_类._取(self.世界.地产, n[0] - 2000)
                    p.经济.业主, p.经济.等级, p.临时状态, p.到期日 = n[1:]
            elif op == "K":
                p = 事件_类._取(self.世界.玩家, n[0])
                事件_类._取(p.持仓, n[1]).数量 = n[2]
            elif op == "J":
                事件_类._取(self.世界.股票, n[0]).标志4 = n[1]
            elif op == "N":
                事件_类._取(self.世界.节点, self._玩家().节点).类型索引 = n[0]
            elif op == "F":
                k, *参 = n
                if k == 0:
                    值 = [self._付款(*参)]
                elif k == 1:
                    self._更新敌意(*参)
                elif k == 2:
                    值 = [self._财富(*参)]
                elif k == 3:
                    值 = [int(self._检查终局())]
                elif k == 4:
                    self._破产(*参)
                elif k == 5:
                    self._保险赔偿(*参)
                elif k == 6:
                    self._收银债(*参)
                elif k == 7:
                    self._收到期贷款()
                elif k == 8:
                    self._对账融资(bool(参[0]))
                elif k == 9:
                    self._设置贷款日(*参)
                elif k == 10:
                    值 = [int(self._借款(*参))]
                elif k == 11:
                    值 = [int(self._还款(参[0], bool(参[1])))]
                elif k == 12:
                    self._电脑银行贷款()
                elif k == 13:
                    值 = [int(self._拥有当前银行()), self._融资上限()]
                elif k == 14:
                    值 = [int(self._变更融资(参[0], bool(参[1])))]
                elif k == 15:
                    self._开银行(bool(参[0]))
                elif k == 16:
                    self._离银行()
                elif k == 17:
                    self._更新物价()
                elif k == 18:
                    self._派发股利()
                elif k == 19:
                    self._结月()
                elif k == 20:
                    值 = [self._租约到期()]
                elif k == 21:
                    self._地产到期()
                elif k == 22:
                    self._付租(参[0], 参[1], 参[2], None if 参[3] < 0 else 参[3], *参[4:])
                else:
                    raise RuntimeError("未知金融探针")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        return self._序列(状态, 值)


class 会话金融差分_类(会话事务差分_类):
    """
    实际金额、原非空月报与终局顺序对照，明确为私有入口夹具而非自然对局。

    更新日志：
    2026.10.24 - 完整DAT、RNG和事件/效果/决策序列逐命令比较。
    """

    探针 = 会话金融探针_类
    工具名 = "game-finance-oracle"
    原生参数 = ("finance",)
    增量范围 = (
        "original payment/bank/loan/financing/dividend/month-end/lease private entries; "
        "explicit field/reset probes, not natural game; "
        "no active gods/special actors or >3-property auctions"
    )

    @staticmethod
    def _设置(arg_世: 世界_类) -> None:
        会话事务差分_类._设置(arg_世)
        arg_世.头.日期 = (1, 1, 2000)
        for 人 in arg_世.玩家:
            人.状态 = 玩家状态_类(初始现金比例=50)
            人.记录.卡片[:] = [0] * 15
            人.记录.道具[:] = [0] * len(人.记录.道具)
            人.记录.交通, 人.记录.骰数 = 0, 1
            for 持 in 人.持仓:
                持.数量 = 0
        for 地 in arg_世.地产:
            地.经济.业主, 地.到期日 = 0, 0
        for 地 in arg_世.设施:
            地.业主, 地.到期日 = 0, 0
        for 公 in arg_世.公司:
            公.业主 = 0
        for 特 in arg_世.特殊角色:
            特.不活跃状态 = 1
        for 股 in arg_世.股票:
            股.标志4 = 0

    @staticmethod
    def _命令(arg_生: random.Random) -> list[str]:
        组 = []
        for 标 in range(8):
            for 金 in (-1, 0, 500, 150000, 2147483647):
                组 += ["r", f"F 0 1 0 {金} {标}"]
        for 主 in (0, 1, 2, 5):
            for 经过 in (0, 1):
                for 比 in (0, 50, 100, 255):
                    组 += [
                        "r",
                        f"P 0 0 30000 0 0 {主}",
                        f"T 0 0 0 0 0 {比} 50 0 0 0 0 0 0 0 0 0 0",
                        f"F 15 {经过}",
                    ]
        for 日 in (1, 7, 8, 25, 26, 31):
            for 模 in range(6):
                组 += ["r", f"H 0 1 10000 2000 1 {日} {模}", "F 20", "F 9 0", "F 7"]
        for 款 in (-2147483648, -1001, 0, 1001, 2147483647):
            组 += ["r", f"C 1 4 0 {款} 123", "J 0 1", "K 0 0 1", "K 1 0 2", "F 18", "F 19"]
        for _ in range(250):
            k, 人 = arg_生.randrange(23), arg_生.randrange(4)
            钱 = arg_生.choice([-2147483648, -1, 0, 100, 30000, 2147483647])
            组 += [
                "r",
                f"H {人} {arg_生.choice([1, 2, 2147483647])} 10000 2000 1 "
                f"{arg_生.choice([1, 7, 8, 25, 26, 31])} {arg_生.randrange(6)}",
            ]
            for 槽 in range(4):
                现, 银 = arg_生.choices([-100, 0, 1000, 15000, 100000, 2147483647], k=2)
                贷, 融 = arg_生.choices([0, 1000, 30000], k=2)
                旗 = 1 if 槽 == 0 else arg_生.choice([0, 2, 5])
                组.append(f"P {槽} {现} {银} {贷} {融} {旗}")
            状态 = [
                人,
                arg_生.choice([0, 128]),
                arg_生.choice([0, 1]),
                arg_生.choice([0, 0x07D00101, 0x07D00104, 0x07CF0101, 0x07D00D01]),
                arg_生.choice([0, 128]),
                arg_生.choice([0, 25, 50, 100, 255]),
                arg_生.choice([0, 30, 100, 255]),
                arg_生.randrange(4294967296),
                arg_生.randrange(4294967296),
                arg_生.randrange(256),
                arg_生.choice([-32768, -1, 0, 32767]),
                128,
                arg_生.randrange(5),
                *arg_生.choices([0, 1, 2147483647, 4294967295], k=4),
            ]
            组 += [
                "T " + " ".join(map(str, 状态)),
                f"C 1 {arg_生.choice([4, 7])} {arg_生.randrange(5)} {钱} 123",
                "N 6001",
            ]
            if k == 0:
                令 = (
                    f"F 0 {arg_生.choice([0, 1, 101])} "
                    f"{arg_生.choice([-1, 0, 1, 101])} {钱} {arg_生.randrange(8)}"
                )
            elif k == 1:
                令 = f"F 1 {人} {arg_生.randrange(4)} {钱}"
            elif k in (2, 4, 9):
                令 = f"F {k} {人}"
            elif k in (5, 6):
                令 = f"F {k} {人} {钱}"
            elif k in (8, 15):
                令 = f"F {k} {arg_生.randrange(2)}"
            elif k == 10:
                令 = f"F 10 {钱}"
            elif k in (11, 14):
                令 = f"F {k} {钱} {arg_生.randrange(2)}"
            elif k == 18:
                组 += ["J 0 1", "K 0 0 3", "K 1 0 7"]
                令 = "F 18"
            elif k == 21:
                组 += [f"L 2000 1 4 {arg_生.randrange(256)} 131072257", "L 4000 1 3 31 131072257"]
                令 = "F 21"
            elif k == 22:
                令 = f"F 22 1 {钱} 0 2 200 2001 3 2"
            else:
                令 = f"F {k}"
            组 += [令, "d"]
        return 组


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    会话金融差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
