# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import struct
import subprocess
from collections import Counter, deque
from dataclasses import replace
from pathlib import Path

from differential_game_transactions import 会话事务探针_类

from rich4.assets import 资源包_类
from rich4.cards import 卡片用法_类, 卡片目标_类, 目标种类_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策种类_类, 托管设置_类, 游戏阶段_类
from rich4.numeric import 数值范围错误_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 公开会话探针_类(游戏会话_类):
    """
    正式GameSession原样执行，仅增加完整可观察状态的测试序列化。

    更新日志：
    2026.10.24 - C++进程只在本测试端提供参照，不在正式Python依赖中。
    """

    _串 = staticmethod(会话事务探针_类._串)
    _盘列 = staticmethod(会话事务探针_类._盘列)
    _基础列 = 会话事务探针_类._序列

    def __init__(self, arg_世: 世界_类, arg_种: int) -> None:
        self.成功数 = 0
        super().__init__(arg_世, arg_种)

    def _附加列(self) -> str:
        数 = [
            len(self.骰面),
            *self.骰面,
            self.剩余步,
            self.下节点,
            self.完成天数,
            self.胜者 if self.胜者 is not None else -1,
            int(self.恢复移动),
            int(self.银行后遭遇),
            self.轮盘游标,
            self.轮盘毫秒,
            self.轮盘种类,
            self.轮盘设施,
            int(self.救援医院),
            self.魔法类别,
            int(self.上次行动接受),
            int(self.未支持恢复),
            int(self.强制骰 is not None),
        ]
        if self.强制骰 is not None:
            数.append(self.强制骰)
        数 += list(
            map(
                int,
                [
                    self.地雷待处理,
                    self.卡图已示,
                    self.地产待处理,
                    self.已购地产,
                    self.地产落点,
                    self.互动小游戏,
                ],
            )
        )

        def 对象(arg_对: 卡片目标_类 | None) -> None:
            数.append(int(arg_对 is not None))
            if arg_对 is not None:
                数.extend([int(arg_对.种类), arg_对.数值])

        对象(self.选定卡目标)
        数.append(int(self.使用中卡 is not None))
        if self.使用中卡 is not None:
            数.append(self.使用中卡.卡片)
            对象(self.使用中卡.目标)
            对象(self.使用中卡.选择)
        数.append(int(self.动画 is not None))
        if self.动画 is not None:
            a = self.动画
            数 += [a.玩家, a.起x, a.起y, a.终x, a.终y, a.已过毫秒, a.时长毫秒]
        数 += [int(self.商店 is not None), self.商店地产]
        if self.商店 is not None:
            s = self.商店
            数 += [
                len(s.卡片),
                *s.卡片,
                len(s.道具),
                *s.道具,
                s.收入,
                s.赠卡,
                s.赠道具,
                int(s.已关闭),
            ]
        数 += [int(self.金钱转盘 is not None), self.转盘随机.状态, self.转盘毫秒]
        if self.金钱转盘 is not None:
            s = self.金钱转盘
            数 += [*s.数字, s.省位, s.阶段, s.帧数, s.减速周期, s.减速累计, s.上次减速位]
        for s in self.待托管:
            数.append(int(s is not None))
            if s is not None:
                数 += [int(s.自动), s.卡片策略, s.性格, s.现金比例, s.股票比例]
        数 += [int(self.世界.有初始随机状态), self.世界.初始随机状态]
        for w in self.上一回合:
            数.append(int(w is not None))
            if w is not None:
                数 += [int(w.有初始随机状态), w.初始随机状态]
        return " ".join(map(str, 数))

    def api_测试命令(self, arg_行: str) -> tuple[str, str, list[bytes]]:
        op, *列 = arg_行.split()
        n, 状, 值 = list(map(int, 列)), 0, []
        try:
            if op == "i":
                pass
            elif op == "t":
                self.api_步进(n[0])
            elif op == "a":
                值 = [int(self.api_设置托管(n[0], 托管设置_类(bool(n[1]), *n[2:])))]
            elif op == "r":
                值 = [int(self.api_掷骰())]
            elif op == "c":
                值 = [int(self.api_回答(*n))]
            elif op == "d":
                值 = [len(self.api_取事件()), len(self.api_取效果())]
            elif op == "v":
                self.api_设相机(n[0])
            elif op == "n":
                值 = [int(self.api_设骰数(n[0]))]
            elif op == "u":
                值 = [int(self.api_用道具(*n))]
            elif op == "k":
                用 = 卡片用法_类(n[0])
                if n[1] >= 0:
                    用.目标 = 卡片目标_类(目标种类_类(n[1]), n[2])
                if n[3] >= 0:
                    用.选择 = 卡片目标_类(目标种类_类(n[3]), n[4])
                值 = [int(self.api_用卡(用))]
            elif op == "b":
                值 = [int(self.api_买股票(*n))]
            elif op == "s":
                值 = [int(self.api_卖股票(*n))]
            elif op == "x":
                self.api_互动小游戏(bool(n[0]))
            elif op == "q":
                值 = [int(self.api_提交小游戏(*n))]
            elif op == "m":
                值 = [int(self.api_下车())]
            elif op == "g":
                值 = [int(self.api_可保存())]
            else:
                raise RuntimeError("unknown public probe command")
        except (IndexError, 数值范围错误_类):
            状 = 2
        except ValueError:
            状 = 1
        except RuntimeError:
            状 = 3
        return (
            self._基础列(状, 值),
            self._附加列(),
            [
                self.世界.api_导出(),
                *[w.api_导出() if w is not None else b"" for w in self.上一回合],
            ],
        )


class 主会话差分_类:
    """
    原始八图、新局与公开操作，逐条流式比较状态，不注入规则字段或预定结算。

    更新日志：
    2026.10.24 - 完整世界及四个历史DAT按原字节比较，避免哈希替代比较。
    """

    @staticmethod
    def _读全(arg_流, arg_数: int) -> bytes:
        片 = []
        while arg_数:
            b = arg_流.read(arg_数)
            if not b:
                raise RuntimeError("C++ oracle truncated binary frame")
            片.append(b)
            arg_数 -= len(b)
        return b"".join(片)

    @staticmethod
    def _输入(arg_会: 公开会话探针_类) -> str:
        if arg_会.阶段 == 游戏阶段_类.人类待命:
            return "r"
        if arg_会.阶段 == 游戏阶段_类.等待决策:
            d = arg_会.待决策
            if d.种类 == 决策种类_类.金额转盘:
                return "c 0 0" if arg_会.金钱转盘.阶段 == 1 else "t 30"
            if d.种类 in (决策种类_类.银行, 决策种类_类.商店):
                i = next(i for i, o in enumerate(d.选项) if o.值 == 0)
            elif d.种类 == 决策种类_类.救援:
                i = next((i for i, o in enumerate(d.选项) if o.值 < 0), 0)
            elif d.种类 == 决策种类_类.拍卖:
                i = next(i for i, o in enumerate(d.选项) if o.值 == 0)
            else:
                i = 0
            return f"c {i} {min(10, d.金额上限) if d.金额上限 else 100}"
        return "t 160"

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_报告: Path,
        arg_图: list[int],
        arg_种: list[int],
        arg_天: int,
        arg_托管: bool,
    ) -> None:
        版 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("reference version mismatch")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        工具 = arg_构建.resolve() / ("game-session-oracle-" + arg_报告.stem)
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
                str(Path(__file__).with_name("game_session_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            capture_output=True,
            text=True,
        )
        if 编.returncode:
            raise RuntimeError(编.stderr)
        报 = {
            "reference": 版,
            "scope": (
                "public GameSession natural play; exact complete DAT and four history snapshots, "
                "RNG, phase, decisions, events, effects and internal value state; "
                "no field injection"
            ),
            "policy": (
                "autopilot human bit retained" if arg_托管
                else "automated public inputs to human-controlled player"
            ),
            "target_days": arg_天,
            "status": "running",
            "episodes": [],
            "python_source_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((Path(__file__).parent.parent / "src" / "rich4").glob("*.py"))
            },
            "oracle_source_sha256": {
                名: hashlib.sha256(Path(__file__).with_name(名).read_bytes()).hexdigest()
                for 名 in ("game_session_oracle.cpp", "game_probe_output.hpp")
            },
        }
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        包 = 资源包_类(arg_素材 / "map.mkf")
        try:
            for 图 in arg_图:
                for 种 in arg_种:
                    世 = 世界_类.api_从地图(
                        包.api_解码(图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                    )
                    会 = 公开会话探针_类(世, 种)
                    cp = subprocess.Popen(
                        [str(工具), str(arg_素材 / "map.mkf"), str(图), str(种)],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    近, 摘, 输入摘, 计, 事计, 效计 = (
                        deque(maxlen=24),
                        hashlib.sha256(),
                        hashlib.sha256(),
                        Counter(),
                        Counter(),
                        Counter(),
                    )
                    步, 待行 = 0, deque(["i"])
                    if arg_托管:
                        设 = replace(会.api_托管设置(0), 自动=True)
                        待行.append(f"a 0 1 {设.卡片策略} {设.性格} {设.现金比例} {设.股票比例}")
                    try:
                        while 步 < 200000:
                            if 待行:
                                行 = 待行.popleft()
                            elif 会.阶段 == 游戏阶段_类.结束 or 会.完成天数 >= arg_天:
                                break
                            else:
                                行 = cls._输入(会)
                                待行.append("d")
                            近.append(行)
                            if 行 == "d":
                                事计.update(str(int(e.种类)) for e in 会.事件队列)
                                效计.update(str(int(e.种类)) for e in 会.效果队列)
                            a, b, 数据 = 会.api_测试命令(行)
                            cp.stdin.write((行 + "\n").encode())
                            cp.stdin.flush()
                            for 类, 预 in (("base", a), ("extra", b)):
                                实 = cp.stdout.readline().decode().rstrip("\n")
                                if 实 != 预:
                                    x, y = shlex.split(实), shlex.split(预)
                                    首 = next(
                                        (i for i, (u, v) in enumerate(zip(x, y)) if u != v),
                                        min(len(x), len(y)),
                                    )
                                    raise ValueError(
                                        f"map={图} seed={种} step={步} cmd={行} {类} token={首} "
                                        f"cpp={x[max(0, 首 - 4) : 首 + 5]} "
                                        f"py={y[max(0, 首 - 4) : 首 + 5]}"
                                    )
                            for i, 预 in enumerate(数据):
                                长 = struct.unpack("<I", cls._读全(cp.stdout, 4))[0]
                                实 = cls._读全(cp.stdout, 长)
                                if 实 != 预:
                                    首 = next(
                                        (i for i, (u, v) in enumerate(zip(实, 预)) if u != v),
                                        min(len(实), len(预)),
                                    )
                                    raise ValueError(
                                        f"map={图} seed={种} step={步} cmd={行} DAT/history={i} "
                                        f"offset={首} cpp={实[首 : 首 + 8].hex()} "
                                        f"py={预[首 : 首 + 8].hex()}"
                                    )
                                摘.update(实)
                            摘.update((a + "\n" + b + "\n").encode())
                            输入摘.update((行 + "\n").encode())
                            计[行.split()[0]] += 1
                            if a.split()[0] != "0":
                                raise RuntimeError(
                                    f"natural command rejected or threw: {行}, "
                                    f"status={a.split()[0]}"
                                )
                            步 += 1
                        else:
                            raise RuntimeError("public game action limit reached")
                    except Exception:
                        报["failure_context"] = {
                            "map": 图,
                            "seed": 种,
                            "step": 步,
                            "recent_inputs": list(近),
                            "days": 会.完成天数,
                        }
                        raise
                    finally:
                        cp.stdin.close()
                        cp.terminate()
                        cp.wait()
                    报["episodes"].append(
                        {
                            "map": 图,
                            "seed": 种,
                            "commands": 步,
                            "operations": dict(计),
                            "days": 会.完成天数,
                            "finished": 会.阶段 == 游戏阶段_类.结束,
                            "winner": 会.胜者,
                            "active": [i for i, p in enumerate(会.世界.玩家) if p.记录.控制标志],
                            "events": dict(事计),
                            "effects": dict(效计),
                            "state_sha256": 摘.hexdigest(),
                            "input_sha256": 输入摘.hexdigest(),
                        }
                    )
                    arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
                    print(
                        f"map={图} seed={种} commands={步} days={会.完成天数} "
                        f"phase={int(会.阶段)} matched",
                        flush=True,
                    )
            报["status"] = "passed"
        except Exception as 错:
            报["status"], 报["failure"] = "failed", str(错)
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    参数.add_argument("--maps", default="0,1,2,3,4,5,6,7")
    参数.add_argument("--seeds", default="0,1,4294967295")
    参数.add_argument("--days", type=int, default=366)
    参数.add_argument("--autopilot", action="store_true")
    选项 = 参数.parse_args()
    主会话差分_类.api_执行(
        选项.source,
        选项.build,
        选项.assets,
        选项.report,
        list(map(int, 选项.maps.split(","))),
        list(map(int, 选项.seeds.split(","))),
        选项.days,
        选项.autopilot,
    )
