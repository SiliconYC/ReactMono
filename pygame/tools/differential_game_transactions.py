# ◑ 导入
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.cards import 电脑卡片记忆_类
from rich4.events import 事件_类
from rich4.game_presentation import 会话表现_类
from rich4.game_transactions import 会话事务_类
from rich4.game_types import (
    决策_类,
    决策种类_类,
    决策选项_类,
    待选择异常_类,
    效果点_类,
    效果种类_类,
    未支持规则异常_类,
    游戏事件种类_类,
    游戏阶段_类,
    语句表_类,
)
from rich4.numeric import 数值范围错误_类
from rich4.random import 随机数_类
from rich4.save import 存档_类
from rich4.save_records import 玩家记录_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 会话事务探针_类(会话表现_类, 会话事务_类):
    """
    为固定私有方法提供真实世界/状态的测试适配器，不作为GameSession替代品。

    更新日志：
    2026.10.24 - 显式回调只测试事务，不声称自然游戏事件。
    """

    def __init__(self, arg_原: bytes, arg_种: int) -> None:
        self.原, self.种 = arg_原, arg_种
        self._重置()

    def _重置(self) -> None:
        self.世界 = 世界_类.api_从存档(存档_类.api_解码(self.原))
        self.随机 = 随机数_类(self.种)
        self.阶段, self.阶段毫秒 = 游戏阶段_类.移动, 99
        self.事件队列, self.效果队列, self.事件选择, self.选择随机状态 = [], [], {}, {}
        self.卡片电脑记忆 = 电脑卡片记忆_类(5, 6, 7)
        self.待续, self.待选择键, self.待决策, self.选择序列 = None, 0, None, 99
        self.地产待处理 = self.已购地产 = self.地产落点 = False
        self.服装, self.服装键 = [0] * 4, [0] * 4
        self.选定卡目标 = self.使用中卡 = self.动画 = None
        self.卡图已示, self.成功数 = False, 0

    def _当前(self) -> int:
        return self.世界.头.当前玩家

    def _玩家(self) -> 玩家记录_类:
        return self.世界.玩家[self._当前()].记录

    def _人类(self) -> bool:
        return self._玩家().控制标志 == 1

    def _成功(self) -> None:
        self.成功数 += 1

    @staticmethod
    def _串(arg_文: str) -> str:
        return json.dumps(arg_文, ensure_ascii=False)

    @staticmethod
    def _盘列(arg_盘) -> list[int]:
        return [
            arg_盘.类型,
            *arg_盘.数位,
            arg_盘.阶段,
            arg_盘.游标,
            arg_盘.主体,
            arg_盘.种子,
            arg_盘.结果,
        ]

    def _序列(self, arg_状态: int, arg_值: list[int]) -> str:
        数 = [
            arg_状态,
            self.随机.状态,
            int(self.阶段),
            self.阶段毫秒,
            self.待选择键,
            self.选择序列,
            self.成功数,
            int(self.待续 is not None),
            self.卡片电脑记忆.参数0,
            self.卡片电脑记忆.参数1,
            self.卡片电脑记忆.参数2,
            *self.服装,
            *self.服装键,
        ]
        for 表 in (self.事件选择, self.选择随机状态):
            数 += [len(表)] + [v for 对 in sorted(表.items()) for v in 对]
        数.append(len(self.事件队列))
        for e in self.事件队列:
            数 += [
                int(e.种类),
                e.玩家,
                e.金额,
                e.节点,
                self._串(e.消息),
                int(e.语音类别 is not None),
            ]
            if e.语音类别 is not None:
                数.append(e.语音类别)
            数 += [
                int(e.公告),
                e.公告号,
                e.地产,
                e.主体,
                e.次主体,
                e.公司,
                e.值,
                e.玩家掩码,
                *e.玩家金额,
                int(e.卡片 is not None),
            ]
            if e.卡片 is not None:
                数.append(e.卡片)
            数 += [int(e.语句表), e.语句槽, e.表情, int(e.音效 is not None)]
            if e.音效 is not None:
                数.append(e.音效)
        数.append(len(self.效果队列))
        for e in self.效果队列:
            数 += [int(e.种类), e.玩家, e.节点, e.目标.x, e.目标.y, int(e.起点 is not None)]
            if e.起点 is not None:
                数 += [e.起点.x, e.起点.y]
            数 += [
                e.物件种类,
                len(e.骰子),
                *e.骰子,
                e.地产,
                e.事件位,
                int(e.转盘 is not None),
                int(e.月报 is not None),
                e.原等级,
                e.原类型,
                e.方向,
            ]
            if e.转盘 is not None:
                数 += self._盘列(e.转盘)
            if e.月报 is not None:
                m = e.月报
                数 += [m.活跃, *m.人物, len(m.股利)]
                for 行 in m.股利:
                    数 += [行.股票, 行.盈余, *行.派发]
                数 += [
                    *m.票,
                    m.奖池,
                    m.号码,
                    m.赢家,
                    *m.现金,
                    *m.存款,
                    *m.利息,
                    *m.余额,
                    *m.总资产,
                    m.贷款,
                    *m.倒霉天,
                    *m.收入,
                    *m.支出,
                    m.冠军,
                    m.悲情,
                ]
        d = self.待决策
        数.append(int(d is not None))
        if d:
            数 += [int(d.种类), d.玩家, d.地产, d.金额, self._串(d.提示), len(d.选项)]
            for o in d.选项:
                数 += [self._串(o.标签), o.值, int(o.位置 is not None), int(o.对象 is not None)]
                if o.位置 is not None:
                    数 += [o.位置.x, o.位置.y]
                if o.对象 is not None:
                    数 += [int(o.对象.种类), o.对象.数值]
            数 += [
                d.金额上限,
                int(d.转盘 is not None),
                int(d.小游戏 is not None),
                d.不活跃玩家,
                int(d.被抢玩家 is not None),
            ]
            if d.转盘 is not None:
                数 += self._盘列(d.转盘)
            if d.小游戏 is not None:
                数 += [d.小游戏.游戏, d.小游戏.人物, d.小游戏.种子]
            if d.被抢玩家 is not None:
                数.append(d.被抢玩家)
        数 += [len(arg_值), *arg_值]
        return " ".join(map(str, 数))

    def api_动作(self, arg_行: str) -> str:
        op, *列 = arg_行.split()
        n = list(map(int, 列))
        状态, 值 = 0, []
        try:
            if op == "r":
                self._重置()
            elif op == "s":
                self.随机.状态 = n[0]
            elif op == "q":
                价, 深, 型, 结束, 首次 = n
                引用 = self.世界

                def 动作() -> None:
                    for i in range(1, 深 + 1):
                        p = 引用.玩家[self._当前()].记录 if 型 == 5 else self._玩家()
                        p.现金 = 股市_类._回绕(p.现金 - 股市_类._回绕(价 + i))
                        self.随机.api_下一个()
                        self.卡片电脑记忆.参数0 = (self.卡片电脑记忆.参数0 + 1) & 0xFFFFFFFF
                        self._发事件(游戏事件种类_类.提示, f"stage{i}", i)
                        self._效果(
                            效果种类_类.怪兽 if i % 2 else 效果种类_类.爆炸,
                            self._当前(),
                            效果点_类(i, i * 2),
                        )
                        self.选择随机状态[i] = self.随机.状态
                        if 型 == 1 and i == 深:
                            raise 未支持规则异常_类("explicit dependency")
                        if 型 == 2:
                            raise ValueError("test boundary")
                        if i not in self.事件选择:
                            raise 待选择异常_类(
                                决策_类(
                                    决策种类_类.选择卡片,
                                    self._当前(),
                                    金额=i,
                                    提示="choose",
                                    选项=[决策选项_类("yes", 1), 决策选项_类("no", 0)],
                                ),
                                i,
                            )
                        p.银行 = 股市_类._回绕(p.银行 + self.事件选择[i])
                    if 型 == 3:
                        self._置阶段(游戏阶段_类.掷骰)
                    if 型 == 4:
                        self._置阶段(游戏阶段_类.结束)

                self._执行规则(动作, bool(首次), bool(结束), self._成功)
            elif op == "a":
                self.事件选择[self.待选择键] = n[0]
                续 = self.待续
                if 续:
                    续()
            elif op == "e":
                self._发事件(游戏事件种类_类(n[0]), "explicit", n[1])
            elif op == "f":
                self._效果(效果种类_类(n[0]), n[1], 效果点_类(n[2], n[3]), n[4])
            elif op == "v":
                self._金额语音(*n)
            elif op == "h":
                self._缺席语音(*n)
            elif op == "b":
                self._语句(n[0], 语句表_类(n[1]), n[2], n[3])
            elif op == "c":
                self._音效(*n)
            elif op == "p":
                self.地产落点 = bool(n[0])
                self._结束回合()
            elif op == "u":
                self._不支持("explicit dependency", 游戏阶段_类(n[0]))
            elif op == "g":
                self.阶段, self.阶段毫秒 = 游戏阶段_类(n[0]), n[1]
            elif op == "t":
                p = 事件_类._取(self.世界.玩家, n[0])
                (
                    p.记录.控制标志,
                    p.记录.交通,
                    p.状态.睡眠天数,
                    p.状态.梦游天数,
                    p.状态.消失天数,
                    p.状态.酒店天数,
                    p.状态.监狱天数,
                    p.状态.医院天数,
                    p.记录.x,
                    p.记录.y,
                ) = n[1:]
            elif op == "i":
                self.世界.头.物价 = n[0]
            elif op == "k":
                事件_类._取(self.服装, n[0])
                self.服装[n[0]], self.服装键[n[0]] = n[1:]
            elif op == "o":
                事件_类._取(self.世界.玩家, n[0])
                值 = [int(self._在场(n[0])), self._服装键(n[0])]
            elif op == "w":
                self._刷新服装()
            elif op == "S":
                p = 事件_类._取(self.世界.玩家, n[0])
                旧 = p.状态
                旧.累计支出, 旧.敌意[:], 旧.初始现金比例 = 123, [1, 2, 3, 4], 73
                数组 = 旧.敌意
                self.世界.api_清破产字段(n[0])
                值 = [
                    int(旧 is p.状态),
                    int(数组 is p.状态.敌意),
                    旧.累计支出,
                    旧.初始现金比例,
                    *数组,
                ]
            elif op == "d":
                self.事件队列.clear()
                self.效果队列.clear()
            else:
                raise RuntimeError("未知事务探针命令")
        except (IndexError, 数值范围错误_类):
            状态 = 2
        except ValueError:
            状态 = 1
        return self._序列(状态, 值)


class 会话事务差分_类:
    """
    显式动作回调、回复和私有表现方法，逐命令完整世界/输出对照。

    更新日志：
    2026.10.24 - 测试适配器不进入正式Python运行依赖。
    """

    探针 = 会话事务探针_类
    工具名 = "game-transactions-oracle"
    原生参数: tuple[str, ...] = ()
    增量范围: str | None = None

    @staticmethod
    def _设置(arg_世: 世界_类) -> None:
        for i, 人 in enumerate(arg_世.玩家):
            人.记录.控制标志, 人.记录.现金, 人.记录.银行 = 1 if i == 0 else 2, 100000, 50000
            人.状态.睡眠天数 = 人.状态.梦游天数 = 人.状态.消失天数 = 0
            人.状态.酒店天数 = 人.状态.监狱天数 = 人.状态.医院天数 = 0
        arg_世.头.当前玩家, arg_世.头.物价 = 0, 1

    @staticmethod
    def _命令(arg_生: random.Random) -> list[str]:
        组 = []
        for 深 in range(5):
            for 型 in range(5):
                for 末 in range(2):
                    组 += ["r", f"q 100 {深} {型} {末} 1"] + ["a 25"] * 深
        for 额 in (0, 1999, 2000, 4999, 5000, 8999, 9000, 2147483647):
            组 += [f"v 0 {额} 6", f"v 1 {额} 8"]
        组 += [f"h 0 {天}" for 天 in range(-1, 10)]
        for _ in range(550):
            op = arg_生.choice(
                [
                    "q",
                    "q",
                    "a",
                    "a",
                    "e",
                    "f",
                    "v",
                    "h",
                    "b",
                    "c",
                    "p",
                    "u",
                    "g",
                    "t",
                    "i",
                    "k",
                    "o",
                    "w",
                    "d",
                    "r",
                    "s",
                ]
            )
            槽 = arg_生.randrange(5)
            if op == "q":
                行 = (
                    f"q {arg_生.choice([-2147483648, -100, 0, 100, 2147483647])} "
                    f"{arg_生.randrange(5)} {arg_生.randrange(5)} "
                    f"{arg_生.randrange(2)} {arg_生.randrange(2)}"
                )
            elif op == "a":
                行 = f"a {arg_生.choice([-2147483648, -1, 0, 25, 2147483647])}"
            elif op == "e":
                行 = f"e {arg_生.randrange(13)} {arg_生.choice([-100, 0, 100])}"
            elif op == "f":
                行 = (
                    f"f {arg_生.randrange(33)} {槽} {arg_生.randrange(-100, 100)} "
                    f"{arg_生.randrange(-100, 100)} {arg_生.randrange(6000)}"
                )
            elif op == "v":
                行 = (
                    f"v {槽} {arg_生.choice([-1, 0, 5000, 9000, 2147483647])} "
                    f"{arg_生.choice([0, 3, 6, 8, 255])}"
                )
            elif op == "h":
                行 = f"h {槽} {arg_生.randrange(-1, 128)}"
            elif op == "b":
                行 = (
                    f"b {槽} {arg_生.randrange(3)} {arg_生.randrange(1024)} {arg_生.randrange(256)}"
                )
            elif op == "c":
                行 = f"c {槽} {arg_生.randrange(256)}"
            elif op in ("p", "u"):
                行 = f"{op} {arg_生.randrange(2) if op == 'p' else arg_生.randrange(6)}"
            elif op == "g":
                行 = f"g {arg_生.randrange(6)} {arg_生.randrange(1000)}"
            elif op == "t":
                列 = [
                    槽,
                    arg_生.choice([0, 1, 2, 0x21]),
                    arg_生.choice([0, 1, 128, 255]),
                    *arg_生.choices([0, 0, 1, 128, 255], k=6),
                    arg_生.choice([0, 1, 65535]),
                    arg_生.choice([0, 1, 65535]),
                ]
                行 = "t " + " ".join(map(str, 列))
            elif op == "i":
                行 = f"i {arg_生.choice([1, 2, 100, 2147483647])}"
            elif op == "k":
                行 = (
                    f"k {槽} {arg_生.choice([0, 19, 20])} "
                    f"{arg_生.choice([0, 1, 255, 256, 512, 1023])}"
                )
            elif op == "o":
                行 = f"o {槽}"
            elif op == "s":
                行 = f"s {arg_生.randrange(4294967296)}"
            else:
                行 = op
            组.append(行)
        return 组

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_报告: Path,
        arg_仅引用: bool = False,
    ) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "cmake",
                "-S",
                str(arg_源码),
                "-B",
                str(arg_构建),
                "-DRICH4_BUILD_GAME=OFF",
                "-DRICH4_BUILD_VIEWER=OFF",
                "-DBUILD_TESTING=OFF",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["cmake", "--build", str(arg_构建), "--target", "rich4_core", "--parallel", "6"],
            check=True,
            capture_output=True,
        )
        工具 = arg_构建.resolve() / cls.工具名
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "src"),
                str(Path(__file__).with_name("game_transactions_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            text=True,
            capture_output=True,
        )
        if 编.returncode:
            raise RuntimeError(编.stderr)
        报告 = {
            "reference": 版本,
            "generator_seed": 2026102401,
            "scope": (
                "original transaction replay and scoped presentation probes; "
                "explicit field/reset/RNG test commands, not game long play"
            ),
            "status": "running",
            "episodes": [],
        }
        报告["identity_only"] = arg_仅引用
        if cls.增量范围:
            报告["scope"] = cls.增量范围
        if arg_仅引用:
            报告["scope"] = (
                "escaped World/PlayerStatus/embedded-array references through original assignment; "
                "explicit private probes, not game turns"
            )
        生 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_素材 / "map.mkf")
            for 图 in range(8):
                for 种 in (0, 1, 0xFFFFFFFF):
                    世 = 世界_类.api_从地图(
                        包.api_解码(图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                    )
                    cls._设置(世)
                    原 = 世.api_导出()
                    会 = cls.探针(原, 种)
                    命令 = (
                        ["r", "q 100 1 5 0 1", "a 25", "r", "S 0", "S 1"]
                        if arg_仅引用
                        else cls._命令(生)
                    )
                    预期, 字节 = [], []
                    for 行 in 命令:
                        返回 = 会.api_动作(行)
                        预期.append(返回)
                        字节.append(会.世界.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-tool-ai-") as 临:
                        路 = Path(临)
                        (路 / "input.dat").write_bytes(原)
                        cp = subprocess.run(
                            [
                                str(工具),
                                str(路 / "input.dat"),
                                str(路 / "out"),
                                str(种),
                                *cls.原生参数,
                            ],
                            input="\n".join(命令) + "\n",
                            text=True,
                            capture_output=True,
                            check=True,
                        )
                        行组 = cp.stdout.splitlines()
                        if len(行组) != len(命令):
                            raise ValueError("会话事务oracle行数不同")
                        摘 = hashlib.sha256()
                        for i, (令, c, p, 存) in enumerate(zip(命令, 行组, 预期, 字节)):
                            if c != p:
                                raise ValueError(f"图{图}/种{种}/步{i}/{令} 返回/RNG不同：{c}/{p}")
                            实 = (路 / "out" / f"{i}.dat").read_bytes()
                            if 存 != 实:
                                首 = next(j for j, (a, b) in enumerate(zip(存, 实)) if a != b)
                                raise ValueError(f"图{图}/种{种}/步{i}/{令} DAT不同offset={首}")
                            摘.update(存)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种,
                            "commands": len(命令),
                            "operations": dict(Counter(行.split()[0] for 行 in 命令)),
                            "statuses": dict(Counter(行.split()[0] for 行 in 预期)),
                            "state_sha256": 摘.hexdigest(),
                            "input_sha256": hashlib.sha256("\n".join(命令).encode()).hexdigest(),
                        }
                    )
                    print(f"map={图} seed={种} commands={len(命令)} matched", flush=True)
            报告["status"] = "passed"
        except Exception as 错:
            报告["status"], 报告["failure"] = "failed", str(错)
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "status": 报告["status"],
                    "episodes": len(报告["episodes"]),
                    "commands": sum(组["commands"] for 组 in 报告["episodes"]),
                }
            )
        )


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    参数.add_argument("--identity-only", action="store_true")
    选项 = 参数.parse_args()
    会话事务差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report, 选项.identity_only)
