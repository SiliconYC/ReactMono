# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from dataclasses import astuple
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.board_models import 场景_类
from rich4.effect_scene import 待播人物_类, 演出场景_类
from rich4.effect_spec import 演出规格_类
from rich4.game import 游戏会话_类
from rich4.game_types import 效果_类, 效果点_类, 效果种类_类
from rich4.save import 存档_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 场景差分_类:
    """
    真实地图/原DAT上的显式原始字段夹具，对照原场景/演员覆盖和全部电影规格。

    更新日志：
    2026.10.24 - 所有期望来自固定原函数；夹具不是自然规则事件或窗口验收。
    """

    @staticmethod
    def _夹具(arg_世: 世界_类, arg_v: int) -> None:
        v, 世 = arg_v, arg_世
        世.头.当前玩家 = v % len(世.玩家)
        for i, 人 in enumerate(世.玩家):
            s, t = 人.记录, 人.状态
            s.x, s.y = (v * 13 + i * 61) % 2304, (v * 17 + i * 43) % 2304
            s.方向, s.交通, s.角色 = (v + i) & 7, (v + i) % 4, (v + i) % 12
            s.控制标志 = (0, 1, 2, 32, 64, 128, 33, 66)[(v + i) % 8]
            s.节点 = 1 + (v + i) % (len(世.节点) - 1)
            t.酒店天数, t.消失天数, t.监狱天数, t.医院天数 = ((v >> j) & 1 for j in range(4))
            t.梦游天数, t.神明信息 = (v + i) % 2, (v + i) % 3
            if (v + i) & 1:
                世.节点[s.节点].标志 |= 0x80000000
        for i, o in enumerate(世.物件):
            o.种类 = (16, 17, 18, 1, 2, 0)[i] if i < 6 else 0
            o.节点 = 1 + (v + i) % (len(世.节点) - 1) if i < 6 else 0
            o.附身玩家, o.方向 = (v + i) % 7 if i < 6 else 0, (v + i) & 7
        for i, a in enumerate(世.特殊角色):
            a.不活跃状态, a.节点 = (v + i) % 3, 1 + (v + i) % (len(世.节点) - 1)
            a.x, a.y = (v * 31 + i * 59) % 2304, (v * 19 + i * 41) % 2304
            a.方向, a.梦游天数 = (v + i) & 7, (v + i) % 2
        for i, a in enumerate(世.地产[1:], 1):
            a.经济.业主, a.经济.等级 = (i + v) % (len(世.玩家) + 1), (i + v) % 6
            a.经济.连锁, a.临时状态 = (i + v) % 2, (i + v * 17) & 255
        for i, a in enumerate(世.设施[1:], 1):
            a.业主, a.等级, a.临时状态 = (
                (i + v) % (len(世.玩家) + 1),
                (i + v) % 6,
                (i + v * 17) & 255,
            )
        for i, a in enumerate(世.公司):
            a.业主 = (i + v) % (len(世.玩家) + 1)

    @staticmethod
    def _扁平(arg_项: tuple) -> list[int]:
        结果 = []
        for x in arg_项:
            结果.extend(场景差分_类._扁平(x) if isinstance(x, tuple) else [int(x)])
        return 结果

    @classmethod
    def _场景(cls, arg_场: 场景_类) -> list[int]:
        数 = []
        for 组 in (
            arg_场.玩家,
            arg_场.物件,
            arg_场.地产,
            arg_场.设施,
            arg_场.公司,
            arg_场.特殊人物,
            arg_场.业主,
        ):
            数.append(len(组))
            for 项 in 组:
                数.extend(cls._扁平(astuple(项)))
        return 数

    @classmethod
    def _期望(cls, arg_美术: 美术_类, arg_行: str) -> str:
        op, *列 = arg_行.split()
        数 = [0]
        if op == "S":
            k, 物 = map(int, 列)
            规 = 演出规格_类.api_查询(效果_类(效果种类_类(k), 物件种类=物))
            值 = astuple(规)
            数 += [ord(值[0]), *map(int, 值[1:])]
        else:
            图, 种, 时, v = map(int, 列)
            if 图 < 8:
                设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种)
                世 = 游戏会话_类(
                    世界_类.api_从地图(arg_美术.api_解码("m", 图 * 2 + 1), 设), 种
                ).世界
            else:
                名 = "save0.dat" if 图 == 8 else "save1.dat"
                路 = next(p for p in arg_美术.目录.iterdir() if p.name.lower() == 名)
                世 = 世界_类.api_从存档(存档_类.api_解码(路.read_bytes()))
            cls._夹具(世, v)
            前 = 世.api_导出()
            服, 帧 = (0, 18, 19, 0), 时 // 120 % 6
            场 = 演出场景_类.api_静止快照(世, 时, 服)
            数 += cls._场景(场)
            待: list[待播人物_类] = []
            种类 = (
                效果种类_类.救护车,
                效果种类_类.警车,
                效果种类_类.狗打架,
                效果种类_类.飞碟,
                效果种类_类.飞机,
                效果种类_类.降落伞,
            )
            for j in range(3):
                演出场景_类.api_加入待播(
                    待,
                    效果_类(
                        种类[(v + j) % 6],
                        玩家=(v + j // 2) % len(世.玩家),
                        物件种类=(v + j) % 2,
                        起点=效果点_类(v * 7 + j, v * 11 + j) if (v + j) % 3 else None,
                    ),
                )
            数.append(len(待))
            for 项 in 待:
                数 += [项.槽, int(项.位置 is not None)]
                if 项.位置 is not None:
                    数.extend(项.位置)
                数.append(int(项.受伤))
            演出场景_类.api_应用待播(场.玩家, 世, 待, 帧, 服)
            场.物件 = 演出场景_类.api_物件(世, 场.玩家, 帧)
            演出场景_类.api_隐藏物件(场.物件, lambda arg_位, arg_种: arg_种 == 16)
            数 += cls._场景(场)
            数.append(int(前 == 世.api_导出()))
        return " ".join(map(str, 数))

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
        工具 = arg_构建.resolve() / "effect-scene-oracle"
        ft = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("effect_scene_oracle.cpp")),
                str(arg_源码 / "tools/screens/effects.cpp"),
                str(arg_构建 / "librich4_core.a"),
                *ft,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
        )
        组 = [f"S {k} {o}" for k in range(33) for o in range(256)]
        组 += [
            f"W {m} 1 {t} {v}"
            for m in range(10)
            for v in range(32)
            for t in (0, 119, 120, 719, 720, 18446744073709551615)
        ]
        报 = {
            "reference": 版,
            "status": "running",
            "scope": (
                "explicit scene fixtures, full data and effect specs; "
                "not natural rules or pixel playback"
            ),
            "spec_cases": 8448,
            "scene_cases": len(组) - 8448,
            "compared_commands": 0,
            "input_sha256": hashlib.sha256(("\n".join(组) + "\n").encode()).hexdigest(),
            "python_source_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in ("effect_scene.py", "effect_spec.py")
            },
        }
        美术, 摘 = 美术_类(arg_素材), hashlib.sha256()
        进 = subprocess.Popen(
            [str(工具), str(arg_素材)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            for i, 行 in enumerate(组):
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError(进.stderr.read().decode())
                预 = cls._期望(美术, 行)
                if 实 != 预:
                    a, b = 实.split(), 预.split()
                    位 = next(
                        (j for j, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b))
                    )
                    raise ValueError(
                        f"step={i} cmd={行} scalar={位} cpp_count={len(a)} py_count={len(b)}"
                    )
                摘.update((实 + "\n").encode())
                报["compared_commands"] = i + 1
            进.stdin.close()
            if 进.wait() != 0:
                raise ValueError(进.stderr.read().decode())
            报.update(status="passed", state_sha256=摘.hexdigest())
        except (ValueError, OSError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            if 进.poll() is None:
                进.terminate()
                进.wait()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": 报["status"], "commands": len(组)}))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    场景差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
