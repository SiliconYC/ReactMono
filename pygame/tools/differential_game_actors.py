# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import random
from pathlib import Path

from differential_game_finance import 会话金融差分_类, 会话金融探针_类

from rich4.events import 事件_类
from rich4.game_actors import 会话角色_类
from rich4.numeric import 数值范围错误_类


# ◕ 功能
class 会话角色探针_类(会话角色_类, 会话金融探针_类):
    """
    角色/防御/拍卖均走真实规则及事务重放，无替代结算回调。

    更新日志：
    2026.10.24 - 显式夹具与输入回复只用于固定源私有入口对照。
    """

    def _重置(self) -> None:
        super()._重置()
        self.动作值 = []

    def _序列(self, arg_状态: int, arg_值: list[int]) -> str:
        return (
            super()._序列(arg_状态, arg_值)
            + " "
            + " ".join(map(str, [len(self.动作值), *self.动作值]))
        )

    def _角色动作(self, arg_n: list[int]) -> None:
        k, *n = arg_n
        if k == 0:
            self._同步附身(*n)
        elif k == 1:
            self._清缺席(*n)
        elif k == 2:
            self._搬走破产者(*n)
        elif k == 3:
            self._受伤(*n)
        elif k == 4:
            self._收容(n[0], n[1], bool(n[2]))
        elif k == 5:
            self._消失(*n)
        elif k == 6:
            self.动作值 = [int(self._尝试免付卡(*n))]
        elif k == 7:
            self.动作值 = [self._尝试嫁祸卡(*n)]
        elif k == 8:
            self.动作值 = [self._尝试防御卡(*n)]
        elif k == 9:
            self.动作值 = [self._选择受害卡(*n)]
        elif k == 10:
            self._释放旅馆住客()
        elif k == 11:
            self._改建筑(n[0], bool(n[1]))
        elif k == 12:
            self._工程车拆屋()
        elif k == 13:
            self._掉头(*n)
        elif k == 14:
            结 = self._拍卖(*n)
            self.动作值 = [结.赢家 if 结.赢家 is not None else -1, 结.价格, 结.地产]
        elif k == 15:
            self.动作值 = [self._随机空节点(*n)]
        elif k == 16:
            self._放现有物件(*n)
        elif k == 17:
            self._移除物件(*n)
        elif k == 18:
            self.动作值 = list(self._选择付租者(n[0], n[1], bool(n[2]), bool(n[3])))
        else:
            raise ValueError("actor probe")

    def api_动作(self, arg_行: str) -> str:
        op, *列 = arg_行.split()
        if op not in {"U", "O", "V", "E", "R", "B"}:
            return super().api_动作(arg_行)
        n, 状态 = list(map(int, 列)), 0
        try:
            if op == "U":
                p = 事件_类._取(self.世界.玩家, n[0])
                s, t = p.记录, p.状态
                s.节点, s.上次节点, s.交通, s.骰数, s.控制标志 = n[1:6]
                (
                    t.酒店天数,
                    t.消失天数,
                    t.监狱天数,
                    t.医院天数,
                    t.睡眠天数,
                    t.梦游天数,
                    t.神明信息,
                    t.附身炸弹,
                    t.保存方向,
                    t.神运修正,
                    t.财运修正,
                    t.其他运修正,
                ) = n[6:18]
            elif op == "O":
                p = 事件_类._取(self.世界.物件, n[0])
                p.种类, p.节点, p.剩余天数, p.附身玩家, p.方向 = n[1:]
            elif op == "V":
                事件_类._取(self.世界.玩家, n[0]).记录.卡片[:] = n[1:]
            elif op == "E":
                if n[0] >= 4000:
                    p = 事件_类._取(self.世界.设施, n[0] - 4000)
                    p.业主, p.等级, p.类型, p.临时状态, p.到期日 = n[1:]
                else:
                    p = 事件_类._取(self.世界.地产, n[0] - 2000)
                    p.经济.业主, p.经济.等级, p.经济.连锁, p.临时状态, p.到期日 = n[1:]
            elif op == "R":
                p = 事件_类._取(self.世界.特殊角色, n[0])
                (
                    p.节点,
                    p.上次节点,
                    p.业主,
                    p.不活跃状态,
                    p.标志,
                    p.睡眠天数,
                    p.梦游天数,
                    p.停留天数,
                    p.龟行天数,
                ) = n[1:]
            elif op == "B":
                self.动作值.clear()
                self._执行规则(lambda: self._角色动作(n), arg_结束后=False)
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        return self._序列(状态, [])


class 会话角色差分_类(会话金融差分_类):
    """
    收容、防御、建筑、拍卖与物件引用在事务中逐命令完整状态比较。

    更新日志：
    2026.10.24 - 没有把显式准备或回复计为自然游戏事件。
    """

    探针 = 会话角色探针_类
    工具名 = "game-actors-oracle"
    原生参数 = ("actors",)
    增量范围 = (
        "original actor/confinement/passive-card/building/auction/object private entries "
        "inside original run_rule; explicit field preparation and answers, not natural turns"
    )

    @staticmethod
    def _命令(arg_生: random.Random) -> list[str]:
        def 手牌(arg_槽: int, arg_卡: list[int]) -> str:
            return "V " + " ".join(map(str, [arg_槽, *arg_卡, *([0] * (15 - len(arg_卡)))]))

        组 = []
        for 主 in (1, 2, 5):
            for k in range(19):
                for 模 in (0, 1, 128):
                    组 += [
                        "r",
                        f"U 0 1 2 3 1 {主} 0 0 0 0 0 0 0 0 2 32767 -32768 30000",
                        手牌(0, [19, 20, 21]),
                        手牌(1, [3, 1, 3]),
                    ]
                    组 += [f"E 2001 2 {arg_生.randrange(6)} {arg_生.randrange(2)} 31 0"]
                    if k in (0, 1, 2, 3, 8, 13):
                        令 = f"B {k} 0"
                    elif k == 4:
                        令 = f"B 4 {arg_生.choice([0, 4, 5, 6, 7])} {模} {arg_生.randrange(2)}"
                    elif k == 5:
                        令 = f"B 5 0 {模} {arg_生.randrange(3)}"
                    elif k == 6:
                        令 = f"B 6 0 1 {arg_生.choice([0, 2000, 4000, 150001])}"
                    elif k == 7:
                        令 = f"B 7 0 {arg_生.randrange(3)} 5000"
                    elif k == 9:
                        令 = "B 9 0 1"
                    elif k in (10, 12):
                        if k == 12:
                            组.append("N 2001")
                        令 = f"B {k}"
                    elif k == 11:
                        令 = f"B 11 {arg_生.choice([2001, 4000])} {arg_生.randrange(2)}"
                    elif k == 14:
                        令 = "B 14 2001 -1"
                    elif k == 15:
                        令 = "B 15 1"
                    elif k == 16:
                        组.append("O 0 1 0 0 0 0")
                        令 = "B 16 0 1"
                    elif k == 17:
                        组 += [
                            "O 0 1 1 3 1 2",
                            f"U 0 1 2 0 1 {主} 0 0 0 0 0 0 1 0 2 32767 -32768 30000",
                        ]
                        令 = "B 17 1"
                    else:
                        令 = (
                            f"B 18 {arg_生.choice([0, 2000, 5000, 200000])} "
                            f"1 {arg_生.randrange(2)} 1"
                        )
                    组 += [令, "a 0", "a 0", "a 0", "a 0", "d"]
        for _ in range(180):
            k = arg_生.choice([1, 3, 4, 5, 6, 7, 11, 13, 17, 18])
            旗 = arg_生.choice([0, 1, 2, 5, 0x21, 0x41])
            天 = arg_生.choice([0, 1, 3, 127, 128, 255])
            缺 = arg_生.choices([0, 0, 1, 128], k=6)
            组 += [
                "r",
                "U "
                + " ".join(
                    map(
                        str,
                        [
                            0,
                            1,
                            2,
                            arg_生.choice([0, 1, 2, 3, 128, 255]),
                            3,
                            旗,
                            *缺,
                            0,
                            0,
                            2,
                            -32768,
                            32767,
                            30000,
                        ],
                    )
                ),
                手牌(0, arg_生.sample([19, 20, 21], arg_生.randrange(4))),
            ]
            if k in (1, 3, 13):
                令 = f"B {k} 0"
            elif k == 4:
                令 = f"B 4 {arg_生.randrange(8)} {天} {arg_生.randrange(2)}"
            elif k == 5:
                令 = f"B 5 0 {天} {arg_生.randrange(3)}"
            elif k == 6:
                令 = f"B 6 0 1 {arg_生.choice([0, 3000, 6000, 200000])}"
            elif k == 7:
                令 = f"B 7 0 {arg_生.randrange(3)} {arg_生.randrange(200000)}"
            elif k == 11:
                组.append(
                    f"E 4000 {arg_生.randrange(5)} {arg_生.randrange(6)} {arg_生.randrange(5)} 0 0"
                )
                令 = f"B 11 4000 {arg_生.randrange(2)}"
            elif k == 17:
                号 = arg_生.choice([1, 2, 5, 9, 13, 14, 16, 17, 18, 19])
                类 = 号 if 号 < 16 else 号 - 1
                组.append(f"O {号 - 1} {类} 1 3 {arg_生.randrange(5)} 2")
                令 = f"B 17 {号}"
            else:
                令 = (
                    f"B 18 {arg_生.randrange(200000)} -1 "
                    f"{arg_生.randrange(2)} {arg_生.randrange(2)}"
                )
            组 += [令, "a 1", "a 1", "a 1", "d"]
        return 组


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    会话角色差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
