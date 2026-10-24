# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.game import 游戏会话_类
from rich4.game_types import (
    效果_类,
    效果种类_类,
    月报_类,
    游戏事件_类,
    游戏事件种类_类,
    转盘状态_类,
)
from rich4.presentation_queue import 呈现宿主_类, 呈现队列_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 队列差分_类:
    """
    原观察排序/泵源码及原专属屏幕判定切片，捕获宿主路由，不代替真实表现屏幕。

    更新日志：
    2026.10.24 - 显式事件/效果输出夹具，参考会话仅供真实drain接口与身份。
    """

    def __init__(self, arg_素材: Path) -> None:
        self.美术 = 美术_类(arg_素材)
        self.调用 = []
        self.忙 = self.阻塞 = False

    def _记(self, arg_类型: int, arg_号: int, arg_玩家: int = 0) -> None:
        self.调用.append((arg_类型, arg_号, arg_玩家))
        if arg_类型 and self.阻塞:
            self.忙 = True

    def _操作(self, arg_行: str) -> str:
        op, *列 = arg_行.split()
        self.调用.clear()
        if op == "N":
            self.会 = 游戏会话_类(世界_类.api_从地图(self.美术.api_解码("m", 1), 新局设置_类()), 1)
            self.会.api_取事件()
            self.会.api_取效果()
            self.忙 = self.阻塞 = False
            宿 = 呈现宿主_类(
                lambda: self.忙,
                lambda e: self._记(0, int(e.种类), e.玩家),
                lambda e: self._记(1, int(e.种类), e.玩家),
                lambda e: self._记(2, int(e.种类)),
                lambda e: self._记(3, int(e.种类)),
                lambda es, owner: [self._记(4, int(e.种类)) for e in es],
            )
            self.q = 呈现队列_类(宿)
        elif op == "Q":
            值 = list(map(int, 列))
            ne, nf = 值[:2]
            偏 = 2
            self.会.事件队列 = []
            self.会.效果队列 = []
            for _ in range(ne):
                k, p = 值[偏 : 偏 + 2]
                偏 += 2
                self.会.事件队列.append(游戏事件_类(游戏事件种类_类(k), p))
            for _ in range(nf):
                k, obj, after, flags = 值[偏 : 偏 + 4]
                偏 += 4
                self.会.效果队列.append(
                    效果_类(
                        效果种类_类(k),
                        物件种类=obj,
                        事件位=after,
                        转盘=转盘状态_类() if flags & 1 else None,
                        月报=月报_类() if flags & 2 else None,
                    )
                )
        elif op == "B":
            self.忙 = bool(int(列[0]))
        elif op == "M":
            self.阻塞 = bool(int(列[0]))
        elif op == "H":
            self.q.api_消费等待(int(列[0]))
        elif op in ("P", "O"):
            auto, play = map(int, 列)
            if op == "P":
                self.q.api_泵(self.会, bool(auto), bool(play))
            else:
                self.q.api_观察会话(self.会, bool(auto), bool(play))
        else:
            raise ValueError(op)
        q = self.q
        数 = [
            0,
            q.等待毫秒,
            int(q.破产音乐),
            q.呈现玩家 if q.呈现玩家 is not None else -1,
            int(self.忙),
            int(q.api_可推进()),
            len(q.步骤),
        ]
        for 步 in q.步骤:
            数.append(int(步.事件 is not None))
            if 步.事件 is not None:
                数 += [int(步.事件.种类), 步.事件.玩家]
            数.append(int(步.效果 is not None))
            if (e := 步.效果) is not None:
                数 += [
                    int(e.种类),
                    e.物件种类,
                    e.事件位,
                    int(e.转盘 is not None),
                    int(e.月报 is not None),
                ]
        数.append(len(self.调用))
        for call in self.调用:
            数.extend(call)
        数 += [len(self.会.事件队列), len(self.会.效果队列)]
        return " ".join(map(str, 数))

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        for k in range(33):
            for flags in range(4):
                for after in range(4):
                    auto, play = int(k % 3 == 0), flags % 2
                    组 += [
                        "N",
                        f"M {k % 2}",
                        f"Q 3 3 0 0 9 1 2 2 {k} {5 + flags} {after} {flags} 17 0 3 0 23 0 2 0",
                        f"O {auto} {play}",
                    ]
                    for _ in range(8):
                        组 += ["B 0", "H 9999", f"P {auto} {play}"]
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
        原 = (arg_源码 / "tools/native_game.cpp").read_text()
        构 = arg_构建.resolve()
        切片 = {}
        起 = 原.index("    void pump_presentation() {")
        止 = 原.index("    void present(", 起)
        切片["pump"] = 原[起:止]
        (构 / "presentation_pump.inc").write_text(切片["pump"])
        起 = 原.index("    void observe() {")
        止 = 原.index("            ++event_counts_", 起)
        观察 = 原[起:止]
        尾起 = 原.index("        queue_effects_before(events.size());", 止)
        尾止 = 原.index("    void draw()", 尾起)
        尾 = 原[尾起:尾止]
        切片["observe_ordering"] = (
            观察
            + 原[原.index("            items_.observe(event, session_->world());", 止) :].split(
                "\n"
            )[0]
            + "\n        }\n"
            + 尾
        )
        (构 / "presentation_observe.inc").write_text(切片["observe_ordering"])
        起 = 原.index(
            "        if (event.kind == GameEventKind::turn_started)", 原.index("    void present(")
        )
        止 = 原.index("        main_screen_.on_event", 起)
        起2 = 原.index("        if (event.kind == GameEventKind::player_bankrupt)", 止)
        止2 = 原.index("        if (event.kind == GameEventKind::notice", 起2)
        切片["present_flags"] = 原[起:止] + 原[起2:止2]
        (构 / "presentation_present.inc").write_text(切片["present_flags"])
        hs = []
        for 名, 命名空间 in (("spinners", "spinners"), ("monthly", "monthly")):
            s = (arg_源码 / f"tools/screens/{名}.cpp").read_text()
            起 = s.index("bool handles(const EffectEvent &effect)")
            止 = s.index("\n}", 起) + 2
            切片[名 + "_handles"] = s[起:止]
            hs.append(f"namespace rich4::native::{命名空间} {{\n{s[起:止]}\n}}\n")
        (构 / "presentation_handles.inc").write_text("".join(hs))
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        工具 = 构 / "presentation-queue-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(构),
                "-I",
                str(arg_源码),
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("presentation_queue_oracle.cpp")),
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
                "verbatim ordering/pump/flag/handles source seams; "
                "explicit emitted-output fixtures and capture-only route callbacks; "
                "not actual presentation components, natural game or GUI"
            ),
            "source_slice_sha256": {
                n: hashlib.sha256(s.encode()).hexdigest() for n, s in 切片.items()
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/presentation_queue.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
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
                    报["cpp"] = 实
                    报["python"] = 预
                    raise ValueError(f"step={i} queue state differs")
                摘.update((实 + "\n").encode())
                输.update((行 + "\n").encode())
                报["commands"] = i + 1
            进.stdin.close()
            退 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退 or 错:
                raise ValueError("参考队列故障：" + 错)
            报.update(
                status="passed",
                state_sha256=摘.hexdigest(),
                input_sha256=输.hexdigest(),
                episodes=528,
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
    队列差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
