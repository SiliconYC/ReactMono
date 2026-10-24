# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from array import array
from pathlib import Path

from replay_application import 应用重放_类

from rich4.application import 游戏应用_类


# ◕ 功能
class 应用差分_类:
    """
    直接原Application绘制/控件/真实核心与Python应用逐步对照；输入循环边界明确列出。

    更新日志：
    2026.10.24 - 同逻辑视口全部RGB555字节、世界DAT、随机/阶段与原主应用状态。
    """

    @staticmethod
    def _串(arg_值: str) -> list[int]:
        data, h = arg_值.encode(), 14695981039346656037
        for v in data:
            h = ((h ^ v) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(data), h]

    @classmethod
    def _状态(cls, arg_a: 游戏应用_类, arg_绘制: bool) -> tuple[str, bytes, bytes]:
        a = arg_a
        state = [
            int(a.页面),
            int(a.上页面),
            int(a.前页面),
            a.旋转,
            a.速度,
            int(a.运行),
            int(a.声效),
            int(a.互动小游戏),
            a.选地图,
            a.选阶段,
            a.银行金额,
            a.选股票,
            a.股票卡截止,
            a.股票卡玩家,
            a.人类数,
            a.清关掩码,
            a.清关阶段,
            a.上保存日,
        ]
        state += (
            cls._串(a.提示) + [a.提示截止] + cls._串(a.决策键) + cls._串(a.配音决策键) + [a.决策页]
        )
        state += [int(a.选目标 is not None)] + ([] if a.选目标 is None else [a.选目标])
        state += [int(a.目标中心 is not None)] + ([] if a.目标中心 is None else list(a.目标中心))
        state += [a.呈现.等待毫秒, int(a.呈现.呈现玩家 is not None)]
        if a.呈现.呈现玩家 is not None:
            state += [a.呈现.呈现玩家]
        state += [int(a.呈现.破产音乐), int(a.拍卖已开), len(a.呈现.步骤)]
        for step in a.呈现.步骤:
            state += [int(step.事件 is not None)]
            if step.事件 is not None:
                e = step.事件
                state += [int(e.种类), e.玩家, e.金额] + cls._串(e.消息)
            state += [int(step.效果 is not None)]
            if step.效果 is not None:
                e = step.效果
                state += [int(e.种类), e.玩家, e.事件位]
        state += [
            int(v)
            for v in (
                a.消息.api_活跃(),
                a.电影.api_活跃(),
                a.转盘.api_活跃(),
                a.月报.api_活跃(),
                a.开场.api_活跃(),
                a.主屏.api_骰子忙(),
                a.物品.api_卡图中(),
                a.物品.api_电脑施法中(),
                a.拍卖.api_成交中(),
                a.帮助.api_活跃(),
                a.数字板.api_活跃(),
            )
        ]
        state += [a.框.指针x, a.框.指针y, int(a.框.按下), a.框.时钟, len(a.按钮)]
        for b in a.按钮:
            state += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        state += [len(a.事件计数)]
        for k, v in sorted(a.事件计数.items()):
            state += [int(k), v]
        state += [a.新局次数, a.读取次数, a.保存次数, a.帧数, int(a.首随机 is not None)]
        if a.首随机 is not None:
            state += [a.首随机]
        state += [
            int(a.音频.api_音乐启用()),
            a.音频.api_音乐曲目(),
            -1 if a.音频.api_音乐上下文() is None else int(a.音频.api_音乐上下文()),
            a.音频.api_音乐深度(),
        ] + cls._串(a.音频.api_音乐名称())
        state += [int(a.会话 is not None)]
        world = b""
        if a.会话 is not None:
            s = a.会话
            state += [int(s.阶段), s.随机.状态, s.完成天数, int(s.待决策 is not None)]
            world = s.世界.api_导出()
            if s.待决策 is not None:
                d = s.待决策
                state += [int(d.种类), d.玩家, d.金额, d.金额上限] + cls._串(d.提示) + [len(d.选项)]
                for o in d.选项:
                    state += cls._串(o.标签) + [o.值, int(o.位置 is not None)]
                    if o.位置 is not None:
                        state += [o.位置.x, o.位置.y]
                    state += [int(o.对象 is not None)]
                    if o.对象 is not None:
                        state += [int(o.对象.种类), o.对象.数值]
        pixels = array("H", a.画布.像素) if arg_绘制 else array("H")
        if sys.byteorder != "little":
            pixels.byteswap()
        state += [len(pixels) * 2, len(world)]
        return " ".join(map(str, state)), pixels.tobytes(), world

    @staticmethod
    def _编译(arg_源码: Path, arg_构建: Path, arg_库: Path) -> Path:
        flags = shlex.split(
            subprocess.check_output(
                ["pkg-config", "--cflags", "--libs", "sdl3", "fluidsynth", "freetype2"], text=True
            )
        )
        names = (
            "main_screen",
            "effects",
            "intro",
            "messages",
            "draw",
            "finance",
            "stocks",
            "market",
            "menus",
            "items",
            "spinners",
            "facility",
            "endgame",
            "help",
            "monthly",
            "minigames",
            "tile_popup",
            "ai_settings",
        )
        stamp = {
            "clock_override": "SDL_GetTicks=rich4_application_clock (all translation units)",
            "oracle": hashlib.sha256(
                Path(__file__).with_name("application_oracle.cpp").read_bytes()
            ).hexdigest(),
            "core": hashlib.sha256(
                (arg_构建.resolve() / "librich4_core.a").read_bytes()
            ).hexdigest(),
            "library": hashlib.sha256(arg_库.read_bytes()).hexdigest(),
            "flags": flags,
            "compiler": subprocess.check_output(["c++", "--version"], text=True),
        }
        key = hashlib.sha256(json.dumps(stamp, sort_keys=True).encode()).hexdigest()[:16]
        exe = arg_构建.resolve() / ("application-oracle-" + key)
        manifest = exe.with_suffix(".build.json")
        if exe.is_file() and manifest.is_file() and json.loads(manifest.read_text()) == stamp:
            return exe
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-DSDL_GetTicks=rich4_application_clock",
                '-DRICH4_DEFAULT_ASSETS="."',
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("application_oracle.cpp")),
                str(arg_源码 / "tools/native_audio.cpp"),
                str(arg_源码 / "tools/platform_desktop.cpp"),
                *[str(arg_源码 / "tools/screens" / (n + ".cpp")) for n in names],
                str(arg_构建.resolve() / "librich4_core.a"),
                *flags,
                "-liconv",
                "-Wl,-rpath," + str(arg_库.resolve().parent),
                "-o",
                str(exe),
            ],
            check=True,
        )
        manifest.write_text(json.dumps(stamp, indent=2) + "\n")
        return exe

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_库: Path,
        arg_输出: Path,
        arg_地图: list[int],
        arg_种子: int,
        arg_天数: int,
        arg_浏览页面: bool,
        arg_正常流程: bool = False,
        arg_存读: bool = False,
        arg_帧上限: int = 10000,
        arg_读档: Path | None = None,
    ) -> None:
        ref = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if ref != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        exe = cls._编译(arg_源码, arg_构建, arg_库)
        arg_输出.mkdir(parents=True, exist_ok=True)
        report = {
            "reference": ref,
            "status": "running",
            "normal_flow": arg_正常流程,
            "exercise_save": arg_存读,
            "scope": "original Application private drawing "
            "and button actions + mirrored original post-input orchestration; Python uses "
            "Pygame event batches. All logical canvas bytes/world DAT/state; audio disabled, "
            "not original OS event loop/desktop/listening proof",
            "cases": [],
            "commands": 0,
            "canvases": 0,
            "pixels": 0,
            "runtime_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(
                    set(Path(__file__).parents[1].glob("src/rich4/application*.py"))
                    | set(Path(__file__).parents[1].glob("src/rich4/minigame*.py"))
                    | {
                        Path(__file__).parents[1] / "src/rich4/board_renderer.py",
                        Path(__file__).parents[1] / "src/rich4/ground_samples.py",
                    }
                )
            },
            "oracle_build": json.loads(exe.with_suffix(".build.json").read_text()),
            "driver_sha256": {
                n: hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
                for n in ("differential_application.py", "replay_application.py")
            },
        }
        try:
            for map_id in arg_地图:
                with tempfile.TemporaryDirectory(dir=arg_输出) as tmp:
                    root = Path(tmp)
                    env = {**os.environ, "SDL_AUDIODRIVER": "dummy", "SDL_VIDEODRIVER": "dummy"}
                    with (root / "stderr.log").open("w+") as errors:
                        proc = subprocess.Popen(
                            [
                                str(exe),
                                str(arg_素材),
                                str(arg_字体),
                                str(root / "cpp-saves"),
                                str(map_id),
                                str(arg_种子),
                                str(0 if arg_正常流程 else arg_天数),
                            ],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=errors,
                            env=env,
                        )
                        digest, inputs = hashlib.sha256(), hashlib.sha256()
                        commands = 0

                        def 观察(arg_命令: str, arg_应用: 游戏应用_类) -> None:
                            nonlocal commands
                            report.update(
                                last_map=map_id, last_command=arg_命令, last_index=commands
                            )
                            proc.stdin.write((arg_命令 + "\n").encode())
                            proc.stdin.flush()
                            actual = proc.stdout.readline().decode().strip()
                            if not actual:
                                errors.flush()
                                errors.seek(0)
                                raise ValueError("原应用提前退出：" + errors.read())
                            n, m = map(int, actual.split()[-2:])
                            cpp_pixels = proc.stdout.read(n)
                            cpp_world = proc.stdout.read(m)
                            own, pixels, world = cls._状态(arg_应用, arg_命令.startswith("D"))
                            if actual != own:
                                report.update(cpp=actual, python=own)
                                raise ValueError(f"map={map_id} step={commands} 应用状态不同")
                            if cpp_pixels != pixels:
                                first = (
                                    next(
                                        (
                                            i
                                            for i, (a, b) in enumerate(zip(cpp_pixels, pixels))
                                            if a != b
                                        ),
                                        -1,
                                    )
                                    // 2
                                )
                                report["first_pixel_difference"] = first
                                raise ValueError(
                                    f"map={map_id} step={commands} 应用画布不同，像素{first}"
                                )
                            if cpp_world != world:
                                report["first_world_difference"] = next(
                                    (i for i, (a, b) in enumerate(zip(cpp_world, world)) if a != b),
                                    -1,
                                )
                                raise ValueError(f"map={map_id} step={commands} 应用世界DAT不同")
                            commands += 1
                            report["commands"] += 1
                            if n:
                                report["canvases"] += 1
                                report["pixels"] += n // 2
                            digest.update(actual.encode())
                            digest.update(pixels)
                            digest.update(world)
                            inputs.update((arg_命令 + "\n").encode())

                        try:
                            应用重放_类.api_执行(
                                arg_素材,
                                arg_字体,
                                root / "py",
                                map_id,
                                arg_种子,
                                arg_天数,
                                arg_帧上限,
                                观察,
                                arg_浏览页面,
                                arg_正常流程,
                                arg_存读,
                                arg_读档,
                            )
                            proc.stdin.close()
                            code = proc.wait(timeout=30)
                            errors.flush()
                            errors.seek(0)
                            error = errors.read()
                            if code:
                                raise ValueError("原应用退出故障：" + error)
                            saved = {}
                            py_saves, cpp_saves = root / "py/saves", root / "cpp-saves"
                            py_names = {p.name for p in py_saves.glob("*") if p.is_file()}
                            cpp_names = {p.name for p in cpp_saves.glob("*") if p.is_file()}
                            if py_names != cpp_names:
                                raise ValueError("实际应用存档文件列表不同")
                            for name in sorted(py_names):
                                data = (py_saves / name).read_bytes()
                                if data != (cpp_saves / name).read_bytes():
                                    raise ValueError("实际应用存档字节不同：" + name)
                                saved[name] = {
                                    "bytes": len(data),
                                    "sha256": hashlib.sha256(data).hexdigest(),
                                }
                            report["cases"].append(
                                {
                                    "map": map_id,
                                    "commands": commands,
                                    "state_sha256": digest.hexdigest(),
                                    "input_sha256": inputs.hexdigest(),
                                    "reference_stderr": error.splitlines(),
                                    "save_files": saved,
                                    "replay": {
                                        k: v
                                        for k, v in json.loads(
                                            (root / "py/report.json").read_text()
                                        ).items()
                                        if k != "inputs"
                                    },
                                }
                            )
                        except (ValueError, RuntimeError, OSError) as error:
                            shutil.copytree(
                                root / "py", arg_输出 / f"failure-map-{map_id}", dirs_exist_ok=True
                            )
                            errors.flush()
                            shutil.copyfile(
                                root / "stderr.log", arg_输出 / f"failure-cpp-{map_id}.log"
                            )
                            raise error
                        finally:
                            if proc.poll() is None:
                                if proc.stdin is not None:
                                    proc.stdin.close()
                                    proc.stdin = None
                                try:
                                    proc.communicate(timeout=10)
                                except subprocess.TimeoutExpired:
                                    proc.kill()
                                    proc.wait()
                (arg_输出 / "report.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
                )
            report["status"] = "passed"
        except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            (arg_输出 / "report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            )
        print(json.dumps(report))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for name in ("source", "build", "assets", "font", "library", "output"):
        参数.add_argument("--" + name, type=Path, required=True)
    参数.add_argument("--maps", default="0")
    参数.add_argument("--seed", type=int, default=123)
    参数.add_argument("--days", type=int, default=3)
    参数.add_argument("--exercise-screens", action="store_true")
    参数.add_argument("--normal-flow", action="store_true")
    参数.add_argument("--exercise-save", action="store_true")
    参数.add_argument("--frames", type=int, default=10000)
    参数.add_argument("--load", type=Path)
    选项 = 参数.parse_args()
    应用差分_类.api_执行(
        选项.source,
        选项.build,
        选项.assets,
        选项.font,
        选项.library,
        选项.output,
        [int(v) for v in 选项.maps.split(",")],
        选项.seed,
        选项.days,
        选项.exercise_screens,
        选项.normal_flow,
        选项.exercise_save,
        选项.frames,
        选项.load,
    )
