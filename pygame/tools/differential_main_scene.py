# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path

from differential_effect_scene import 场景差分_类

from rich4.artwork import 美术_类
from rich4.effect_player import 电影播放_类
from rich4.game import 游戏会话_类
from rich4.game_types import (
    决策_类,
    决策种类_类,
    效果_类,
    效果点_类,
    效果种类_类,
    游戏事件_类,
    游戏事件种类_类,
    移动动画_类,
)
from rich4.main_scene import 主板场景_类, 表现步_类
from rich4.main_screen import 主屏幕_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 主场景差分_类:
    """
    原draw_board板面构造源码切片与真实原辅助函数，完整场景及相机/只读性对照。

    更新日志：
    2026.10.24 - 明确切片边界及宿主夹具，不称为完整Application或像素验收。
    """

    @staticmethod
    def _期望(arg_美: 美术_类, arg_行: str) -> str:
        列 = list(map(int, arg_行.split()))
        图, v, 已过, 时 = 列[:4]
        槽 = 列[4] if len(列) > 4 else v % 9
        会 = 游戏会话_类(
            世界_类.api_从地图(
                arg_美.api_解码("m", 图 * 2 + 1), 新局设置_类(地图=图 % 4, 阶段=图 // 4)
            ),
            1,
        )
        世 = 会.世界
        场景差分_类._夹具(世, v)
        会.动画 = 移动动画_类(槽, 100 + v, 100 - v, 67 - v, 132 + v, 已过, 160)
        屏, 播 = 主屏幕_类(), 电影播放_类(arg_美)
        呈现玩家 = v % 4 if v % 5 else None
        if v % 3 == 0:
            屏._自由中心 = (400, 500)
        if v & 2:
            会.待决策 = 决策_类(决策种类_类.卡片目标, 0)
        目标 = (700, 800) if v & 4 else None
        焦 = v % 6 if v & 8 else None
        if v & 16:
            屏._骰活跃, 屏._骰帧数, 屏._骰毫秒 = True, 10, 已过
            屏._投掷槽, 屏._投掷帧数, 屏._投掷毫秒 = v % 4, 3, 240
        步 = []
        if v % 4:
            for j, k in enumerate((效果种类_类.救护车, 效果种类_类.降落伞, 效果种类_类.抛物)):
                e = 效果_类(
                    k,
                    玩家=(v + j) % 4,
                    起点=效果点_类(v * 7 + j, v * 11 + j),
                    物件种类=16 if j == 2 else 0,
                    目标=效果点_类(世.节点[1].x, 世.节点[1].y),
                )
                步.append(表现步_类(效果=e))
            世.节点[1].类型索引 = 2001 if len(世.地产) > 1 else 4001
            for k in (游戏事件种类_类.已购地, 游戏事件种类_类.已升级, 游戏事件种类_类.提示):
                步.append(
                    表现步_类(
                        事件=游戏事件_类(
                            k,
                            0,
                            节点=1,
                            消息="福神帮助房屋升级" if k == 游戏事件种类_类.提示 else "",
                        )
                    )
                )
        if v % 7 == 0:
            播.api_入队(
                [
                    效果_类(
                        效果种类_类.抛物, 物件种类=17, 目标=效果点_类(世.节点[2].x, 世.节点[2].y)
                    )
                ],
                会,
            )
        原, 随 = 世.api_导出(), 会.随机.状态
        场, 相 = 主板场景_类.api_构建(会, 屏, 播, 步, bool(v & 1), 呈现玩家, v & 7, 时, 目标, 焦)
        数 = [0, *相.中心, 相.旋转, 屏._显示玩家 if 屏._显示玩家 is not None else -1]
        数 += 场景差分_类._场景(场)
        数.append(len(播._待播人物))
        for p in 播._待播人物:
            数 += [p.槽, int(p.位置 is not None)]
            if p.位置 is not None:
                数.extend(p.位置)
            数.append(int(p.受伤))
        数 += [int(原 == 世.api_导出()), int(随 == 会.随机.状态)]
        return " ".join(map(str, 数))

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_报告: Path,
        arg_移动网格: bool = False,
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
        原 = (arg_源码 / "tools/native_game.cpp").read_text()
        起 = 原.index("    void draw_board() {")
        止 = 原.index("        native::MainScreenActions actions;", 起)
        切片 = 原[起:止]
        if "board_->render(canvas_" not in 切片 or 切片.count("void draw_board()") != 1:
            raise ValueError("参考场景边界改变")
        构 = arg_构建.resolve()
        构.mkdir(parents=True, exist_ok=True)
        (构 / "main_scene_source.inc").write_text(切片 + "    }\n")
        夹 = Path(__file__).with_name("effect_scene_oracle.cpp").read_text()
        (构 / "main_scene_fixture.inc").write_text(
            夹[夹.index("static void p(") : 夹.index("int main(")]
        )
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        工具 = 构 / "main-scene-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(构),
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("main_scene_oracle.cpp")),
                str(arg_源码 / "tools/screens/effects.cpp"),
                str(arg_源码 / "tools/screens/main_screen.cpp"),
                str(arg_源码 / "tools/screens/draw.cpp"),
                str(构 / "librich4_core.a"),
                *链,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
        )
        美 = 美术_类(arg_素材)
        进 = subprocess.Popen(
            [str(工具), str(arg_素材)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        报 = {
            "reference": 版,
            "status": "running",
            "cases": 0,
            "movement_grid": arg_移动网格,
            "scope": (
                "verbatim original draw_board scene-construction prefix with capture renderer; "
                "explicit host/world/animation fixtures; no pixel, native UI application "
                "or natural gameplay acceptance"
            ),
            "source_range": {
                "path": "tools/native_game.cpp",
                "start_line": 原[:起].count("\n") + 1,
                "end_line": 原[:止].count("\n"),
                "sha256": hashlib.sha256(切片.encode()).hexdigest(),
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/main_scene.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            for 图 in range(8):
                for v, 槽 in (
                    [(v, s) for v in range(32) for s in range(9)]
                    if arg_移动网格
                    else [(v, v % 9) for v in range(72)]
                ):
                    for 已过, 时 in zip(
                        (0, 1, 79, 80, 159, 160), (0, 119, 120, 719, 720, 2**64 - 1)
                    ):
                        行 = f"{图} {v} {已过} {时}" + (f" {槽}" if arg_移动网格 else "")
                        进.stdin.write((行 + "\n").encode())
                        进.stdin.flush()
                        实 = 进.stdout.readline().decode().strip()
                        if not 实:
                            raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                        预 = cls._期望(美, 行)
                        if 实 != 预:
                            Path(".research-cache/main-scene-private-failure.json").write_text(
                                json.dumps({"cpp": 实, "python": 预})
                            )
                            报["failure_command"] = 行
                            raise ValueError(f"case={报['cases']} scene differs")
                        摘.update((实 + "\n").encode())
                        输.update((行 + "\n").encode())
                        报["cases"] += 1
                        if 报["cases"] % 576 == 0:
                            arg_报告.parent.mkdir(parents=True, exist_ok=True)
                            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
            进.stdin.close()
            退 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退 or 错:
                raise ValueError("参考场景故障：" + 错)
            报.update(status="passed", state_sha256=摘.hexdigest(), input_sha256=输.hexdigest())
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
    参数.add_argument("--movement-grid", action="store_true")
    选项 = 参数.parse_args()
    主场景差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report, 选项.movement_grid)
