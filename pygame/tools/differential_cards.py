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
from rich4.cards import 卡片_类, 卡片回调_类, 卡片用法_类, 卡片目标_类, 卡片结果_类, 目标种类_类
from rich4.events import 事件_类
from rich4.random import 随机数_类
from rich4.save import 存档_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 卡片待选_类(RuntimeError):
    """
    测试选择回调中断，正式游戏会话的重放机制另行实现。

    更新日志：
    2026.10.23 - 对应测试适配器Pending。
    """


class 卡片差分_类:
    """
    逐目标序列/主动卡/被动嵌套/表现次序比较，测试牌和扫描不进入正式规则。

    更新日志：
    2026.10.23 - 八图、完整世界/RNG/结果与观察或注入回调。
    """

    @staticmethod
    def _动作(
        arg_世: 世界_类, arg_随机: 随机数_类, arg_行: str, arg_原: bytes
    ) -> tuple[str, 世界_类]:
        op, *列 = arg_行.split()
        槽, 卡, 目类, 目值, 选类, 选值, 掩, 挑, 休, 免, 嫁, 防, 拍, 设, 扫, 改, 价 = map(int, 列)
        调用: list[int] = []

        def 记(arg_类: int, *arg_值: int) -> None:
            调用.extend([arg_类, len(arg_值), *arg_值])

        def 监狱(arg_a: int, arg_b: int) -> None:
            记(3, arg_a, arg_b)
            if 改:
                if arg_a < len(arg_世.玩家):
                    事件_类._取(arg_世.玩家, arg_a).状态.监狱天数 = arg_b
                else:
                    事件_类._取(arg_世.特殊角色, arg_a - 4).不活跃状态 = 1

        def 防御(arg_a: int) -> int:
            记(4, arg_a, 防)
            if 防 == -2:
                raise 卡片待选_类("choice")
            return 防

        def 股票(arg_a: int) -> None:
            记(5, arg_a)
            if 改:
                事件_类._取(arg_世.股票, arg_a - 1).浮点位[2] = 价

        def 拍卖(arg_a: int, arg_b: int) -> bool:
            记(10, arg_a, arg_b, 拍)
            if 拍 == -2:
                raise 卡片待选_类("choice")
            return bool(拍)

        def 挑目标(arg_卡: int, arg_项: list[卡片目标_类]) -> 卡片目标_类 | None:
            记(11, arg_卡, len(arg_项), *(n for 项 in arg_项 for n in (int(项.种类), 项.数值)))
            if 挑 == -2:
                raise 卡片待选_类("choice")
            if not 挑:
                return None
            return (
                arg_项[0]
                if 挑 == 1
                else arg_项[-1]
                if 挑 == 2
                else 卡片目标_类(目标种类_类.角色, 65535)
            )

        def 库存(arg_a: int, arg_b: int) -> 卡片目标_类 | None:
            记(12, arg_a, arg_b, 挑)
            if 挑 == -2:
                raise 卡片待选_类("choice")
            if not 挑:
                return None
            人 = 事件_类._取(arg_世.玩家, arg_b)
            if 挑 == 1:
                return 卡片目标_类(目标种类_类.卡片, 人.记录.卡片[0])
            if 挑 == 2:
                return next(
                    (
                        卡片目标_类(目标种类_类.道具, i + 1)
                        for i, 量 in enumerate(人.记录.道具[:13])
                        if 量
                    ),
                    None,
                )
            return 卡片目标_类(目标种类_类.道具, 65535)

        def 设施(arg_a: int) -> int | None:
            记(14, arg_a, 设)
            if 设 == -2:
                raise 卡片待选_类("choice")
            return None if 设 == -1 else 设 & 255

        def 移除(arg_a: int) -> None:
            记(17, arg_a)
            if 改:
                物 = 事件_类._取(arg_世.物件, arg_a - 1)
                物.节点 = 物.附身玩家 = 0

        def 神明(arg_类: int, arg_a: int, arg_b: int = 0) -> None:
            记(arg_类, arg_a, *([arg_b] if arg_类 == 19 else []))
            if 改:
                事件_类._取(arg_世.玩家, arg_a).状态.神明信息 = arg_b

        def 扫描(arg_a: int) -> list[int]:
            记(21, arg_a, 扫)
            if 扫 == 3:
                return []
            值 = [0x8000 | (1 << i) for i in range(8)]
            值 += [2000 + i for i in range(1, len(arg_世.地产))]
            值 += [4000 + i for i in range(1, len(arg_世.设施))]
            值 += [0x8000 | (i << 8) for i in range(1, len(arg_世.物件) + 1)]
            if 扫 == 2:
                值.reverse()
            if 扫 == 4:
                值 = [0x8001, 0x8200, 2002]
            if 扫 == 5:
                值 = [65535, 0x8000, 0]
            return 值

        钩 = 卡片回调_类(
            语音=(lambda *a: 记(1, *a)) if 掩 & 1 else None,
            付款=(lambda *a: 记(2, *a)) if 掩 & 2 else None,
            监狱=监狱 if 掩 & 4 else None,
            防御=防御 if 掩 & 8 else None,
            更新股票=股票 if 掩 & 16 else None,
            敌意=(lambda *a: 记(6, *a)) if 掩 & 32 else None,
            转身=(lambda a: 记(7, a)) if 掩 & 64 else None,
            改建筑=(lambda a, b: 记(8, a, int(b))) if 掩 & 128 else None,
            释放酒店=(lambda a: 记(9, a)) if 掩 & 256 else None,
            拍卖地产=拍卖 if 掩 & 512 else None,
            选择目标=挑目标 if 掩 & 1024 else None,
            选择库存=库存 if 掩 & 2048 else None,
            抢得=(lambda a, b, t, p: 记(13, a, b, int(t.种类), t.数值, int(p)))
            if 掩 & 4096
            else None,
            选择设施=设施 if 掩 & 8192 else None,
            免付=(lambda a, b, c: 记(15, a, b, c, 免) or bool(免)) if 掩 & 16384 else None,
            嫁祸=(lambda a, b: 记(16, a, b, 嫁) or 嫁) if 掩 & 32768 else None,
            移除物件=移除 if 掩 & 65536 else None,
            神明脱离=(lambda a: 神明(18, a)) if 掩 & 131072 else None,
            神明附身=(lambda a, b: 神明(19, a, b)) if 掩 & 262144 else None,
            休市=(lambda: 记(20, 休) or bool(休)) if 掩 & 524288 else None,
            附近实例=扫描 if 掩 & 1048576 else None,
            卡片语音=(lambda *a: 记(22, *a)) if 掩 & 2097152 else None,
            被动卡=(lambda *a: 记(23, *a)) if 掩 & 4194304 else None,
        )
        状态, 返回, 结果, 值 = 0, 0, 卡片结果_类(), []
        try:
            if op == "u":
                用 = 卡片用法_类(
                    卡,
                    None if 目类 < 0 else 卡片目标_类(目类, 目值),
                    None if 选类 < 0 else 卡片目标_类(选类, 选值),
                )
                结果 = 卡片_类.api_使用(arg_世, arg_随机, 槽, 用, 钩)
            elif op == "l":
                值 = 卡片_类.api_合法目标(arg_世, 槽, 卡, 钩)
            elif op == "v":
                返回 = int(卡片_类.api_主动(卡))
            elif op == "r":
                arg_世 = 世界_类.api_从存档(存档_类.api_解码(arg_原))
            elif op == "h":
                事件_类._取(arg_世.玩家, 槽).记录.卡片[0] = 卡
            else:
                raise RuntimeError("未知卡片差分动作")
        except 卡片待选_类:
            状态 = 3
        except IndexError:
            状态 = 2
        except ValueError:
            状态 = 1
        数 = [
            状态,
            arg_随机.状态,
            int(结果.状态),
            返回,
            len(值),
            *(n for 项 in 值 for n in (int(项.种类), 项.数值)),
            len(调用),
            *调用,
        ]
        return " ".join(map(str, 数)) + "|" + 结果.消息, arg_世

    @staticmethod
    def _设置(arg_世: 世界_类, arg_条件: int) -> None:
        arg_世.头.物价 = [1, 2147483647, 3][arg_条件]
        arg_世.头.日期 = (31, 1, 2000)
        arg_世.租约模式 = [0, 5, 7][arg_条件]
        脚 = 2001 if len(arg_世.地产) > 1 else 4001
        for i, 人 in enumerate(arg_世.玩家):
            人.记录.控制标志 = 1 if i == 0 or (i == 1 and arg_条件 == 1) else 2
            人.记录.x, 人.记录.y, 人.记录.节点 = 100 + i, 100, i + 1
            人.记录.现金 = [1000000 * (i + 1), [2147483647, -2147483648, -1, 0][i], 10000][arg_条件]
            人.记录.交通, 人.记录.骰数 = [0, 1, 2, 128][i], i + 1
            人.记录.卡片[:] = [18, 19, 20, 21, *range(1, 12)]
            人.记录.道具[:13] = [9 if i == 0 else 1] * 13
            人.记录.道具[4] = 人.记录.道具[5] = 255
            人.状态.冬眠总天数 = 250
            人.状态.神明信息 = [5, 12, 10, 0][i]
            人.状态.附身炸弹 = 37 if i == 0 else 0
            人.状态.盟友, 人.状态.结盟天数 = [2, 1, 4, 3][i], 7
            人.状态.敌意[:] = [0, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
            for j, 持 in enumerate(人.持仓):
                持.数量 = 0 if arg_条件 == 2 else [0, 1, 2147483647, -1][(i + j) % 4]
            arg_世.节点[i + 1].类型索引 = 脚
        for i, 地 in enumerate(arg_世.地产[1:], 1):
            地.经济.业主, 地.经济.等级, 地.经济.连锁 = i % 4 + 1, i % 6, i % 2
            地.经济.街道名 = b"test-street" if i % 3 else b"other"
            地.地价, 地.每级造价, 地.到期日 = 1000, 500, 0x7D0011F
        for i, 地 in enumerate(arg_世.设施[1:], 1):
            地.业主, 地.等级, 地.类型 = i % 4 + 1, i % 6, i % 5
            地.地价, 地.每级造价, 地.到期日 = 1000, 500, 0x7D0011F
            地.标志30 = 1
        for i, 物 in enumerate(arg_世.物件):
            物.种类 = i + 1 if i < 14 else 15 if i < 16 else 16 + (i - 16) // 10
            物.节点, 物.附身玩家 = 2, 0
        arg_世.物件[4].附身玩家 = 1
        arg_世.物件[36].附身玩家 = 1
        for 人 in arg_世.特殊角色[:4]:
            人.不活跃状态, 人.x, 人.y = 0, 100, 100
        arg_世.卡供应[:] = [255] * 30
        arg_世.道具供应[:] = [255] * 8
        for 股 in arg_世.股票:
            股.浮点位[2] = 0x7F800000 if arg_条件 == 2 else 0x41200000

    @staticmethod
    def _命令(arg_世: 世界_类, arg_生: random.Random) -> list[str]:
        def 行(
            arg_op: str,
            arg_槽: int,
            arg_卡: int,
            arg_目: 卡片目标_类 | None = None,
            arg_选: 卡片目标_类 | None = None,
            arg_掩: int = 0x7FFFFF,
            arg_挑: int = 1,
            arg_休: int = 0,
            arg_免: int = 0,
            arg_嫁: int = -1,
            arg_防: int = 1,
            arg_拍: int = 0,
            arg_设: int = 0,
            arg_扫: int = 1,
            arg_改: int = 1,
            arg_价: int = 0x40E00000,
        ) -> str:
            值 = [
                arg_op,
                arg_槽,
                arg_卡,
                -1 if arg_目 is None else int(arg_目.种类),
                0 if arg_目 is None else arg_目.数值,
                -1 if arg_选 is None else int(arg_选.种类),
                0 if arg_选 is None else arg_选.数值,
                arg_掩,
                arg_挑,
                arg_休,
                arg_免,
                arg_嫁,
                arg_防,
                arg_拍,
                arg_设,
                arg_扫,
                arg_改,
                arg_价,
            ]
            return " ".join(map(str, 值))

        组 = []
        for 卡 in range(33):
            组.append(行("v", 0, 卡))
            for 槽 in range(5):
                组.append(行("l", 槽, 卡))
        for 槽 in range(4):
            for 卡 in range(1, 31):
                选项 = 卡片_类.api_合法目标(arg_世, 槽, 卡, 卡片回调_类())
                目 = 选项[0] if 选项 else None
                选 = 卡片目标_类(目标种类_类.道具, 1) if 卡 == 13 and 槽 % 2 == 0 else None
                组 += [
                    行("r", 0, 0),
                    行("h", 槽, 卡),
                    行(
                        "u",
                        槽,
                        卡,
                        目,
                        选,
                        arg_掩=0x7FFFFF if 槽 % 2 == 0 else 0x7FFFFF & ~32,
                        arg_防=目.数值 if 目 is not None and 目.种类 == 目标种类_类.角色 else 1,
                    ),
                ]
        for _ in range(300):
            op = arg_生.choice(["u", "u", "u", "l", "v", "r"])
            槽, 卡 = arg_生.randrange(5), arg_生.randrange(33)
            可 = 卡片_类.api_合法目标(arg_世, 槽, 卡, 卡片回调_类())
            目 = arg_生.choice([None, *(可[:3]), 卡片目标_类(目标种类_类.角色, 65535)])
            选 = arg_生.choice(
                [
                    None,
                    卡片目标_类(目标种类_类.卡片, 18),
                    卡片目标_类(目标种类_类.道具, 1),
                    卡片目标_类(目标种类_类.道具, 0),
                ]
            )
            if op == "u" and 0 <= 槽 < 4 and 1 <= 卡 <= 30:
                组.append(行("h", 槽, 卡))
            组.append(
                行(
                    op,
                    槽,
                    卡,
                    目,
                    选,
                    arg_掩=arg_生.choice([0x7FFFFF, 0x7FFFFF & ~32, 0, arg_生.randrange(0x800000)]),
                    arg_挑=arg_生.choice([-2, 0, 1, 2, 3]),
                    arg_休=arg_生.randrange(2),
                    arg_免=arg_生.randrange(2),
                    arg_嫁=arg_生.choice([-2, -1, 0, 1, 2, 3, 255]),
                    arg_防=arg_生.choice([-2, -1, 0, 1, 2, 3, 255]),
                    arg_拍=arg_生.choice([-2, 0, 1]),
                    arg_设=arg_生.choice([-2, -1, 0, 1, 2, 3, 4, 5, 256]),
                    arg_扫=arg_生.randrange(1, 6),
                    arg_改=arg_生.randrange(2),
                    arg_价=arg_生.choice([0x40E00000, 0x7F800000, 0x7FC01234, 0x80000000]),
                )
            )
        return 组

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_报告: Path) -> None:
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
        工具 = arg_构建.resolve() / "cards-oracle"
        编 = subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("cards_oracle.cpp")),
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
            "generator_seed": 2026102311,
            "scope": (
                "card module with explicit test hands, visibility lists "
                "and observing/injecting hooks; not game play or AI"
            ),
            "status": "running",
            "episodes": [],
        }
        生 = random.Random(报告["generator_seed"])
        try:
            包 = 资源包_类(arg_素材 / "map.mkf")
            for 图 in range(8):
                for 条件, 种 in enumerate((0, 1, 0xFFFFFFFF)):
                    世 = 世界_类.api_从地图(
                        包.api_解码(图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                    )
                    cls._设置(世, 条件)
                    原, 随机 = 世.api_导出(), 随机数_类(种)
                    命令, 预期, 字节 = cls._命令(世, 生), [], []
                    for 行 in 命令:
                        返回, 世 = cls._动作(世, 随机, 行, 原)
                        预期.append(返回)
                        字节.append(世.api_导出())
                    with tempfile.TemporaryDirectory(prefix="rich4-cards-") as 临:
                        路 = Path(临)
                        (路 / "input.dat").write_bytes(原)
                        cp = subprocess.run(
                            [str(工具), str(路 / "input.dat"), str(路 / "out"), str(种)],
                            input="\n".join(命令) + "\n",
                            text=True,
                            capture_output=True,
                            check=True,
                        )
                        行组 = cp.stdout.splitlines()
                        if len(行组) != len(命令):
                            raise ValueError("卡片oracle行数不同")
                        摘 = hashlib.sha256()
                        for i, (令, c, p, 存) in enumerate(zip(命令, 行组, 预期, 字节)):
                            if c != p:
                                raise ValueError(
                                    f"图{图}/种{种}/步{i}/{令} 返回/RNG/钩子不同：{c}/{p}"
                                )
                            实 = (路 / "out" / f"{i}.dat").read_bytes()
                            if 存 != 实:
                                首 = next(j for j, (a, b) in enumerate(zip(存, 实)) if a != b)
                                raise ValueError(
                                    f"图{图}/种{种}/步{i}/{令} DAT不同offset={首} "
                                    f"Python={存[首]} C++={实[首]}"
                                )
                            摘.update(存)
                    报告["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种,
                            "commands": len(命令),
                            "operations": dict(Counter(行.split()[0] for 行 in 命令)),
                            "exceptions": dict(Counter(行.split()[0] for 行 in 预期)),
                            "card_results": dict(
                                Counter(
                                    行.split()[2]
                                    for 令, 行 in zip(命令, 预期)
                                    if 令[0] == "u" and 行.split()[0] == "0"
                                )
                            ),
                            "used_cards": dict(
                                Counter(
                                    令.split()[2]
                                    for 令, 行 in zip(命令, 预期)
                                    if 令[0] == "u"
                                    and 行.split()[0] == "0"
                                    and 行.split()[2] == "0"
                                )
                            ),
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
    选项 = 参数.parse_args()
    卡片差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
