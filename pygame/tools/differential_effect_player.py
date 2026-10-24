# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from array import array
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.effect_player import 电影播放_类
from rich4.effect_scene import 演出场景_类
from rich4.effect_spec import 演出规格_类, 演员模式_类
from rich4.game import 游戏会话_类
from rich4.game_types import 效果_类, 效果点_类, 效果种类_类
from rich4.graphics import 图像_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 电影差分_类:
    """
    直接固定原EffectPlayer，真实电影/板面像素和时钟/声音对照；显式表现夹具不是自然事件。

    更新日志：
    2026.10.24 - 逐电影独立旧世界快照/提交/运输/精灵投掷/保留末帧，不发布商业像素。
    """

    def __init__(self, arg_素材: Path) -> None:
        self.美术 = 美术_类(arg_素材)
        self.时钟 = 0
        self.声音: list[int] = []

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.声音.clear()
        画 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
        if op == "I":
            图, 人物, 交通 = map(int, 列)
            设 = 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            设.玩家[0].角色, 设.玩家[0].交通 = 人物, 交通
            self.会 = 游戏会话_类(世界_类.api_从地图(self.美术.api_解码("m", 图 * 2 + 1), 设), 1)
            self.世界 = self.会.世界
            self.板, self.播, self.时钟 = 棋盘绘制_类(self.美术.目录, 图), 电影播放_类(self.美术), 0
            世 = self.世界
            s, 地 = 世.玩家[0].记录, 世.地产[1] if len(世.地产) > 1 else 世.设施[1]
            s.x, s.y, s.控制标志, s.节点 = max(0, 地.x - 64), max(0, 地.y - 32), 1, 1
            if len(世.地产) > 1:
                地.经济.业主, 地.经济.等级 = 2, 3
            else:
                地.业主, 地.等级, 地.类型 = 2, 3, 0
            self.播.api_服装((0, 18, 19, 0))
            self.播.api_记忆(世, self.会, 0)
        elif op == "E":
            种, 物, 向 = map(int, 列)
            世 = self.世界
            地, s = (世.地产[1] if len(世.地产) > 1 else 世.设施[1]), 世.玩家[0].记录
            e = 效果_类(
                效果种类_类(种),
                玩家=0,
                节点=1,
                地产=2001 if len(世.地产) > 1 else 4001,
                目标=效果点_类(地.x, 地.y),
                起点=效果点_类(s.x, s.y),
                物件种类=物,
                方向=向,
                原等级=3,
                原类型=0,
            )
            if len(世.地产) > 1:
                地.经济.业主, 地.经济.等级 = 1, 0
            else:
                地.业主, 地.等级 = 1, 0
            规 = 演出规格_类.api_查询(e)
            if 规.演员 in (演员模式_类.离开, 演员模式_类.停留):
                世.玩家[0].状态.医院天数 = 3
            if 规.演员 == 演员模式_类.到达:
                世.玩家[0].状态.医院天数 = 0
            if e.种类 == 效果种类_类.工程车拆屋:
                世.玩家[0].记录.交通 = 3
            if e.种类 == 效果种类_类.抛物:
                o = 世.物件[-1]
                o.种类, o.节点, o.附身玩家, o.方向 = 物, 1, 0, 向
            self.播.api_入队([e], self.会)
        elif op in ("D", "L"):
            dt, 转 = map(int, 列)
            self.时钟 += dt
            if op == "D":
                self.播.api_绘制(画, self.板, self.世界, 转, dt, self.时钟, self.声音.append)
            else:
                self.播.api_绘留帧(画, self.板, self.世界, 转, self.时钟)
        elif op == "P":
            槽, 种 = map(int, 列)
            待 = []
            演出场景_类.api_加入待播(
                待,
                效果_类(
                    效果种类_类(种),
                    玩家=槽,
                    起点=效果点_类(self.世界.玩家[0].记录.x, self.世界.玩家[0].记录.y),
                ),
            )
            self.播.api_设置待播(待)
        elif op == "S":
            self.播.api_跳过(bool(int(列[0])))
        elif op == "M":
            self.播.api_记忆(self.世界, self.会, self.时钟)
        elif op == "N":
            self.会 = 游戏会话_类(self.世界, 1)
        elif op == "X":
            self.播.api_丢弃末帧()
        elif op == "C":
            self.播.api_清空()
        else:
            raise ValueError(op)
        播 = self.播
        数 = [
            0,
            self.时钟,
            int(播.api_活跃()),
            int(播.api_保留中()),
            int(播._跳过),
            int(播._快照 is not None),
            len(播._队列),
        ]
        for e in 播._队列:
            数 += [int(e.种类), e.物件种类, e.方向]
        数.append(int(播._当前 is not None))
        if (x := 播._当前) is not None:
            数 += [int(x.效果.种类), x.已过, x.间隔, int(x.已响), int(x.影片 is not None)]
            if x.影片 is not None:
                数 += [x.影片.已解帧, x.影片.帧数]
            数 += [x.帧图.宽, x.帧图.高, len(x.路径)]
            for 点 in x.路径:
                数.extend(点)
        数.append(int(播._留帧 is not None))
        if (x := 播._留帧) is not None:
            数 += [
                int(x.效果.种类),
                x.已过,
                int(x.已响),
                x.影片.已解帧 if x.影片 else 0,
                x.帧图.宽,
                x.帧图.高,
            ]
        数 += [len(self.声音), *self.声音]
        像 = array("H", 画.像素)
        if byteorder != "little":
            像.byteswap()
        return " ".join(map(str, 数)), 像.tobytes()

    @staticmethod
    def _情形() -> list[tuple[int, int, int, int]]:
        组 = []
        for k in range(33):
            物 = {3: 16, 9: 1, 23: 0, 24: 4, 28: 3, 32: 1}.get(k, 0)
            组.append((0, 0, k, 物))
        组 += [(0, 0, 9, i) for i in (*range(2, 11), 12, 15)]
        组 += [(0, 0, 24, i) for i in (5, 15, 20, 21)]
        组 += [(0, 0, 23, i) for i in range(1, 12)]
        组 += [(0, 0, k, 1) for k in (21, 22)]
        组 += [(0, 0, 3, i) for i in (17, 18)]
        组 += [(0, 0, 32, i) for i in (3, 15)]
        组 += [(m, m, k, o) for m in range(1, 8) for k, o in ((3, 16), (4, 0), (28, 7), (32, 5))]
        return 组

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_报告: Path,
        arg_上限: int = 0,
        arg_队列: bool = False,
    ) -> None:
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
        工具 = arg_构建.resolve() / "effect-player-oracle"
        ft = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("effect_player_oracle.cpp")),
                str(arg_源码 / "tools/screens/effects.cpp"),
                str(arg_构建 / "librich4_core.a"),
                *ft,
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
            "sequence_mode": arg_队列,
            "scope": (
                "direct fixed EffectPlayer with real sprites/FLC/board, explicit fixtures; "
                "no natural or desktop acceptance"
            ),
            "episodes": [],
            "compared_commands": 0,
            "python_source_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in (
                    "effect_player.py",
                    "effect_scene.py",
                    "effect_spec.py",
                    "board_renderer.py",
                )
            },
        }
        计, 摘, 输入 = 0, hashlib.sha256(), hashlib.sha256()

        def 操作(arg_行: str) -> None:
            nonlocal 计
            进.stdin.write((arg_行 + "\n").encode())
            进.stdin.flush()
            实 = 进.stdout.readline().decode().strip()
            if not 实:
                raise ValueError("C++提前结束：" + 进.stderr.read().decode())
            cpp = 进.stdout.read(614400)
            预, 像 = 自._操作(arg_行, 计)
            if 实 != 预:
                raise ValueError(f"step={计} cmd={arg_行} metadata cpp={实} py={预}")
            if cpp != 像:
                位 = next(i for i, (a, b) in enumerate(zip(cpp, 像)) if a != b)
                raise ValueError(f"step={计} cmd={arg_行} pixel={位 // 2 % 640},{位 // 2 // 640}")
            摘.update(cpp)
            摘.update(实.encode())
            输入.update((arg_行 + "\n").encode())
            计 += 1
            报["compared_commands"] = 计

        try:
            情形 = (
                cls._情形()
                if not arg_队列
                else [(0, 0, 1, 0), (0, 3, 3, 16), (7, 7, 28, 7), (1, 2, 9, 1)]
            )
            if arg_上限:
                情形 = 情形[:arg_上限]
            for n, (图, 转, k, 物) in enumerate(情形):
                起计 = 计
                操作(f"I {图} {n % 12} {n % 3}")
                操作(f"E {k} {物} {(n + 3) & 7}")
                if arg_队列:
                    操作("M")
                    操作("P 1 21")
                    for 后, 参 in ((17, 0), (23, n % 12), (32, 5), (9, 12)):
                        操作(f"E {后} {参} 3")
                    if n == 3:
                        操作("S 1")
                        操作("N")
                        操作("E 4 0 0")
                        操作("S 0")
                        操作("M")
                        操作("E 9 1 0")
                操作(f"D 9999 {转}")
                原 = 自.世界.api_导出()
                for _ in range(2048):
                    if not 自.播.api_活跃():
                        break
                    x = 自.播._当前
                    dt = (
                        80
                        if x and x.效果.种类 == 效果种类_类.工程车拆屋
                        else min(100, x.间隔)
                        if x and x.影片
                        else 24
                    )
                    操作(f"D {dt} {转}")
                else:
                    raise ValueError(f"效果未结束：{n}")
                if 自.播.api_保留中():
                    操作(f"L 40 {转}")
                    操作("X")
                操作(f"D 40 {转}")
                if 原 != 自.世界.api_导出():
                    raise ValueError("播放器修改了规则世界")
                报["episodes"].append(
                    {"map": 图, "rotation": 转, "kind": k, "object": 物, "commands": 计 - 起计}
                )
                arg_报告.parent.mkdir(parents=True, exist_ok=True)
                arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
            进.stdin.close()
            退出 = 进.wait()
            错误输出 = 进.stderr.read().decode()
            if 退出 != 0 or 错误输出:
                raise ValueError("参考播放器产生故障：" + 错误输出)
            报.update(
                status="passed",
                state_sha256=摘.hexdigest(),
                input_sha256=输入.hexdigest(),
                complete_canvas_pixels=计 * 307200,
            )
        except (ValueError, OSError, IndexError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            if 进.poll() is None:
                进.terminate()
                进.wait()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": 报["status"], "episodes": len(报["episodes"]), "commands": 计}))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    参数.add_argument("--limit", type=int, default=0)
    参数.add_argument("--sequences", action="store_true")
    选项 = 参数.parse_args()
    电影差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.report, 选项.limit, 选项.sequences
    )
