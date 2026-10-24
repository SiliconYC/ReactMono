# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from collections import Counter
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.cards import 卡片目标_类, 目标种类_类
from rich4.game_types import (
    公告种类_类,
    决策_类,
    决策种类_类,
    决策选项_类,
    游戏事件_类,
    游戏事件种类_类,
    语句表_类,
)
from rich4.message_overlay import 消息_类
from rich4.message_rules import 消息规则_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 消息规则差分_类:
    """
    直接固定原消息转换，完整值、标签、确认语句及World只读性对照。

    更新日志：
    2026.10.24 - 外部PE长文字，原源码名称/格式辅助也由原CPP直接执行。
    """

    def __init__(self, arg_素材: Path) -> None:
        self.美术 = 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        self.规 = 消息规则_类(原版文字_类(原版程序_类.api_读取(exe)))

    @staticmethod
    def _字(arg_文: str) -> str:
        return arg_文.encode().hex() or "-"

    @classmethod
    def _项(cls, arg_项: 消息_类 | None) -> list[int | str]:
        x = arg_项
        if x is None:
            return [0]
        数 = [
            1,
            int(x.种类),
            x.焦点 if x.焦点 is not None else -1,
            x.人物,
            x.情绪,
            x.图语,
            x.声音,
            x.最少毫秒,
            int(x.等待声音),
            x.框x,
            x.照片,
            cls._字(x.文字),
            cls._字(x.标题),
            len(x.行),
        ]
        for r in x.行:
            数 += [r.人物, r.头像帧, cls._字(r.文字)]
        return 数

    def _操作(self, arg_行: str) -> str:
        op, *列 = arg_行.split()
        规, 数 = self.规, [0]
        原 = self.世.api_导出() if hasattr(self, "世") else None
        if op == "N":
            图, 人 = map(int, 列)
            设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            for i in range(4):
                设.玩家[i].角色 = (人 + i * 3) % 12
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", 图 * 2 + 1), 设)
        elif op == "F":
            self.世.设施[1].类型 = int(列[0])
        elif op == "Q":
            槽, 天 = map(int, 列)
            self.世.玩家[槽].状态.消失天数 = 天
        elif op == "E":
            值 = list(map(int, 列))
            p, a, i, m, prop, s, ss, c, v, mask = 值[:10]
            cat, table, slot, mood = 值[14:]
            e = 游戏事件_类(
                游戏事件种类_类.提示,
                p,
                金额=m,
                语音类别=None if cat < 0 else cat,
                公告=公告种类_类(a),
                公告号=i,
                地产=prop,
                主体=s,
                次主体=ss,
                公司=c,
                值=v,
                玩家掩码=mask,
                玩家金额=值[10:14],
                语句表=语句表_类(table),
                语句槽=slot,
                表情=mood,
            )
            数 += self._项(规.api_从事件(e, self.世))
        elif op == "B":
            人, 类, 焦 = map(int, 列)
            数 += self._项(规.api_事件气泡(人, 类, None if 焦 < 0 else 焦))
        elif op == "T":
            人, 表, 槽, 情, 焦 = map(int, 列)
            数 += self._项(规.api_物品气泡(人, 语句表_类(表), 槽, 情, None if 焦 < 0 else 焦))
        elif op == "V":
            类, 号 = map(int, 列)
            方法 = (规.api_股名, 规.api_地名, 规._公司, 规.api_人名)[类]
            数.append(self._字(方法(self.世, 号)))
        elif op == "S":
            k, v = map(int, 列)
            数.append(self._字(规.api_对象名(self.世, 卡片目标_类(目标种类_类(k), v))))
        elif op == "D":
            k, p, 地, a, n = map(int, 列[:5])
            d = 决策_类(决策种类_类(k), p, 地产=地, 金额=a)
            for j in range(n):
                偏 = 5 + j * 4
                v, kind, sub = map(int, 列[偏 : 偏 + 3])
                label = 列[偏 + 3]
                d.选项.append(
                    决策选项_类(
                        "" if label == "-" else bytes.fromhex(label).decode(),
                        v,
                        对象=None if kind < 0 else 卡片目标_类(目标种类_类(kind), sub),
                    )
                )
            显 = 规.api_本地化(d, self.世)
            数 += [
                int(规.api_是确认(d)),
                self._字(规.api_确认问题(d, self.世)),
                self._字(显.提示),
                len(显.选项),
            ]
            for o in 显.选项:
                数 += [
                    o.值,
                    self._字(o.标签),
                    int(o.对象.种类) if o.对象 else -1,
                    o.对象.数值 if o.对象 else 0,
                ]
        else:
            raise ValueError(op)
        if op not in ("N", "Q", "F") and 原 != self.世.api_导出():
            raise ValueError("消息映射修改了规则世界")
        return " ".join(map(str, 数))

    @staticmethod
    def _命令() -> list[str]:
        组 = ["N 0 0"]
        for 人 in range(12):
            for 类 in range(27):
                组.append(f"B {人} {类} {人 % 4}")
            for 表, 宽 in ((1, 90), (2, 26)):
                for 槽 in range(宽 + 1):
                    组.append(f"T {人} {表} {槽} {槽 % 8} {人 % 4}")
        for 图 in range(8):
            组.append(f"N {图} {图 % 12}")
            for 类, 号列 in (
                (0, range(-1, 14)),
                (1, (0, 1, 2000, 2001, 2050, 3999, 4000, 4001, 4002, 5000, 65535)),
                (2, range(-1, 16)),
                (3, range(-1, 6)),
            ):
                for 号 in 号列:
                    组.append(f"V {类} {号}")
            for k, 值列 in (
                (0, range(10)),
                (1, (0, 2001, 4001, 4002, 65535)),
                (2, range(14)),
                (3, range(0, 45)),
                (4, range(32)),
                (5, range(15)),
            ):
                for v in 值列:
                    组.append(f"S {k} {v}")
            for a, 编号 in (
                (0, (0,)),
                (1, range(5)),
                (2, (0,)),
                (3, range(36)),
                (4, range(49)),
                (5, range(22)),
                (6, range(3)),
                (7, range(7)),
                (8, range(11)),
                (9, range(15)),
                (10, range(23, 27)),
                (11, range(3)),
                (12, (0,)),
            ):
                for i in 编号:
                    for prop, s, ss, value in ((2001, 1, -1, 17), (4001, 2, 3, 3)):
                        amount = (50, 30, 10)[i % 3] if a == 6 else 12345
                        组.append(
                            f"E 0 {a} {i} {amount} {prop} {s} {ss} 1 {value} "
                            "15 5 -17 1000 9999 -1 0 0 0"
                        )
            for 类型 in range(5):
                组.append(f"F {类型}")
                for i in range(11):
                    组.append(f"E 0 8 {i} 12345 4001 1 -1 -1 0 0 0 0 0 0 -1 0 0 0")
            for 金 in (-2147483648, 0, 2147483647):
                for 值 in (-1, 0, 3):
                    组.append(f"E 0 1 2 {金} 4001 1 -1 -1 {值} 0 0 0 0 0 -1 0 0 0")
            for 表, 宽 in ((1, 31), (2, 27)):
                for 槽 in range(宽):
                    组.append(f"E 0 2 0 0 0 -1 -1 -1 0 0 0 0 0 0 0 {表} {槽} 3")
            for 工具 in (0, 1):
                for 号 in range(32):
                    组.append(f"E 0 11 {工具} 0 0 2 -1 -1 {号} 0 0 0 0 0 -1 0 0 0")
            for k in range(21):
                for 选 in (
                    "0",
                    "2 1 -1 0 41 0 -1 0 42",
                    "2 17 0 1 41 -1 -1 0 42",
                    "3 1 2 0 41 0 1 4001 42 -1 4 3 43",
                ):
                    组.append(f"D {k} 0 1 12345 {选}")
            for p in (0, 3, 255):
                for cat in (-1, 0, 26, 27):
                    组.append(f"E {p} 2 0 0 0 -1 -1 -1 0 0 0 0 0 0 {cat} 0 0 0")
            组 += ["Q 0 7", "E 0 2 0 0 0 -1 -1 -1 0 0 0 0 0 0 0 0 0 0", "Q 0 0"]
        return 组

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_报告: Path) -> None:
        版 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        构 = arg_构建.resolve()
        头 = 构 / "message-rules-shim/SDL3/SDL_timer.h"
        头.parent.mkdir(parents=True, exist_ok=True)
        头.write_text(
            '#pragma once\n#include <cstdint>\nextern "C" std::uint64_t SDL_GetTicks();\n'
        )
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        工具 = 构 / "message-rules-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(头.parents[1]),
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("message_rules_oracle.cpp")),
                str(构 / "librich4_core.a"),
                *链,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
        )
        自 = cls(arg_素材)
        进 = subprocess.Popen(
            [str(工具), str(arg_素材)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        报 = {
            "reference": 版,
            "status": "running",
            "commands": 0,
            "scope": (
                "original message rules vs external PE, explicit events/decisions, "
                "not natural gameplay or GUI"
            ),
            "python_source_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in ("message_rules.py", "original_text.py")
            },
        }
        摘, 输, 计 = hashlib.sha256(), hashlib.sha256(), Counter()
        try:
            for i, 行 in enumerate(cls._命令()):
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                预 = 自._操作(行)
                if 实 != 预:
                    报["failure_command"] = 行
                    报["expected_sha256"] = hashlib.sha256(实.encode()).hexdigest()
                    报["actual_sha256"] = hashlib.sha256(预.encode()).hexdigest()
                    Path(".research-cache/message-rules-failure-private.json").write_text(
                        json.dumps({"cpp": 实, "python": 预}, indent=2)
                    )
                    raise ValueError(f"step={i} op={行[:1]} metadata differs")
                摘.update((实 + "\n").encode())
                输.update((行 + "\n").encode())
                计[行[:1]] += 1
                报["commands"] = i + 1
            进.stdin.close()
            退出 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退出 or 错:
                raise ValueError("参考消息映射故障：" + 错)
            报.update(
                status="passed",
                state_sha256=摘.hexdigest(),
                input_sha256=输.hexdigest(),
                operations=dict(计),
            )
        except (ValueError, OSError, IndexError, AttributeError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            if 进.poll() is None:
                进.terminate()
                进.wait()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(报))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    消息规则差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
