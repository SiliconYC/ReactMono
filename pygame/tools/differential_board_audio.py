# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.audio_types import 循环通道_类, 音乐_类
from rich4.board_audio import 主板声音_类, 步行声音_类, 音乐导演_类
from rich4.game_types import 决策_类, 决策种类_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 策略请求记录_类:
    """
    只记录原策略调用，不播放音频且不会作为正式应用宿主。

    更新日志：
    2026.10.24 - 与C++请求记录汇点使用同一明确协议，声音波形另验。
    """

    def __init__(self) -> None:
        self.调用: list[tuple[int, int]] = []

    def api_推音乐(self, arg_音乐: 音乐_类) -> None:
        self.调用.append((0, int(arg_音乐)))

    def api_换音乐(self, arg_音乐: 音乐_类) -> None:
        self.调用.append((1, int(arg_音乐)))

    def api_弹音乐(self) -> None:
        self.调用.append((2, 0))

    def api_播循环(self, arg_号: int, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None:
        self.调用.append((3 + int(arg_通道), arg_号))

    def api_停循环(self, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None:
        self.调用.append((6 + int(arg_通道), 0))


class 主板音频差分_类:
    """
    直接原board_audio策略、真实八图只读、精确uint64截止点/倒退时钟。

    更新日志：
    2026.10.24 - 不编译原混音器，无音频设备/波形/听感通过含义。
    """

    def __init__(self, arg_素材: Path) -> None:
        self.美术 = 美术_类(arg_素材)
        self.宿, self.音乐, self.步行 = 策略请求记录_类(), 音乐导演_类(), 步行声音_类()

    def _操作(self, arg_行: str) -> tuple[str, bytes]:
        op, *args = arg_行.split()
        self.宿.调用.clear()
        a, b, old = -1, -1, self.世.api_导出() if op not in ("N", "V", "H") else None
        if op == "N":
            m = int(args[0])
            self.世 = 世界_类.api_从地图(
                self.美术.api_解码("m", 2 * m + 1), 新局设置_类(地图=m % 4, 阶段=m // 4)
            )
            self.音乐, self.步行 = 音乐导演_类(), 步行声音_类()
        elif op == "V":
            slot, node, traffic, bomb = map(int, args)
            if slot < 4:
                p = self.世.玩家[slot]
                p.记录.节点, p.记录.交通, p.状态.附身炸弹 = node, traffic, bomb
            else:
                self.世.特殊角色[slot - 4].节点 = node
        elif op == "P":
            slot = int(args[0])
            x, y = 主板声音_类.api_步行(self.世, slot), 主板声音_类.api_炸弹(self.世, slot)
            a, b = -1 if x is None else x, -1 if y is None else y
        elif op == "H":
            year, month, day, m, stage = map(int, args)
            self.世.头.日期, self.世.头.地图, self.世.头.阶段 = (day, month, year), m, stage
            value = 主板声音_类.api_节庆音乐(self.世)
            a = int(value) if value is not None else -1
        elif op == "Q":
            kind, hospital = map(int, args)
            value = 主板声音_类.api_决策音乐(
                决策_类(决策种类_类(kind), 0, 提示="探望住院角色" if hospital else "other")
            )
            a = int(value) if value is not None else -1
        elif op == "M":
            now, count, *values = map(int, args)
            if count != len(values):
                raise ValueError("策略需求长度不符")
            self.音乐.api_更新(self.宿, list(map(音乐_类, values)), now)
        elif op == "W":
            now, walk, bomb = map(int, args)
            self.步行.api_更新(
                self.宿, walk if walk >= 0 else None, bomb if bomb >= 0 else None, now
            )
        elif op == "F":
            self.音乐.api_忘记()
        elif op == "S":
            self.步行.api_停止(self.宿)
        elif op == "R":
            self.音乐, self.步行 = 音乐导演_类(), 步行声音_类()
        else:
            raise ValueError(op)
        dat = self.世.api_导出()
        if old is not None and dat != old:
            raise ValueError("声音策略改世界")
        out = [
            a,
            b,
            len(self.音乐._已推),
            *map(int, self.音乐._已推),
            int(self.音乐._待退),
            self.音乐._退起,
            self.步行._上走,
            len(self.宿.调用),
        ]
        for c in self.宿.调用:
            out += c
        out.append(len(dat))
        return " ".join(map(str, out)), dat

    def _命令(self) -> list[str]:
        groups = []
        for m in range(8):
            w = 世界_类.api_从地图(
                self.美术.api_解码("m", 2 * m + 1), 新局设置_类(地图=m % 4, 阶段=m // 4)
            )
            groups += [f"N {m}"]
            wet = next((n.编号 for n in w.节点 if n.标志 & 0x80000000), 0)
            dry = next(n.编号 for n in w.节点 if not n.标志 & 0x80000000)
            for slot in range(9):
                for node in (dry, wet, len(w.节点)):
                    for traffic in range(16 if slot < 4 else 1):
                        groups += [
                            f"V {slot} {node} {traffic} {255 if traffic % 2 else 0}",
                            f"P {slot}",
                        ]
            groups += ["P 9", "P 255", "P 4294967295"]
            for year in (1998, 1999, 2000, 2020, 2021, 2100, 65535):
                for month in range(1, 13):
                    last = (
                        29
                        if month == 2 and year % 4 == 0
                        else (28 if month == 2 else 30 if month in (4, 6, 9, 11) else 31)
                    )
                    for day in (1, 2, 3, 25, last):
                        groups += [f"H {year} {month} {day} {m % 4} {m // 4}"]
        for kind in range(21):
            groups += [f"Q {kind} {hospital}" for hospital in (0, 1)]
        wanted = [[], [0], [1], [2], [14, 5], [14, 6], [15, 7], [15], [14, 0, 5]]
        for epoch in (0, 1, 65535, 18446744073709551000):
            groups += ["R"]
            for i in range(400):
                values = wanted[(i * 13 + i // 7) % len(wanted)]
                now = (epoch + i * 149) & 0xFFFFFFFFFFFFFFFF
                groups += [f"M {now} {len(values)} " + " ".join(map(str, values))]
                if i % 19 == 0:
                    groups += [
                        f"W {now} 0 0",
                        f"W {(now + 149) & 0xFFFFFFFFFFFFFFFF} -1 -1",
                        f"W {(now + 150) & 0xFFFFFFFFFFFFFFFF} -1 -1",
                    ]
                if i % 23 == 0:
                    groups += ["F", "S"]
        groups += [
            "R",
            "M 100 2 14 5",
            "M 101 1 14",
            "M 400 1 14",
            "M 401 1 14",
            "W 500 44 32",
            "W 499 -1 -1",
            "M 99 0",
            "M 98 0",
            "S",
            "F",
        ]
        return groups

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_报告: Path) -> None:
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
        tool = arg_构建.resolve() / "board-audio-oracle"
        flags = shlex.split(
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
                str(Path(__file__).with_name("board_audio_oracle.cpp")),
                str(arg_构建.resolve() / "librich4_core.a"),
                *flags,
                "-liconv",
                "-o",
                str(tool),
            ],
            check=True,
        )
        own, digest, inputs = cls(arg_素材), hashlib.sha256(), hashlib.sha256()
        proc = subprocess.Popen(
            [str(tool), str(arg_素材)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        report = {
            "reference": ref,
            "status": "running",
            "commands": 0,
            "scope": (
                "original board_audio policies with request-recording sinks, real maps/World DAT; "
                "not mixer/device/waveform/listening proof"
            ),
            "runtime_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in ("board_audio.py", "audio_types.py", "holidays.py")
            },
        }
        try:
            for index, line in enumerate(own._命令()):
                report.update(last_index=index, last_command=line)
                proc.stdin.write((line + "\n").encode())
                proc.stdin.flush()
                actual = proc.stdout.readline().decode().strip()
                if not actual:
                    raise ValueError("原策略提前结束：" + proc.stderr.read().decode())
                dat = proc.stdout.read(int(actual.split()[-1]))
                expected, py_dat = own._操作(line)
                if expected != actual:
                    report.update(cpp=actual, python=expected)
                    raise ValueError(f"step={index} 策略状态/请求不同")
                if dat != py_dat:
                    raise ValueError(f"step={index} World DAT不同")
                digest.update(actual.encode())
                digest.update(dat)
                inputs.update((line + "\n").encode())
                report["commands"] = index + 1
            proc.stdin.close()
            code = proc.wait()
            error = proc.stderr.read().decode()
            if code or error:
                raise ValueError("原策略退出故障：" + error)
            report.update(
                status="passed", state_sha256=digest.hexdigest(), input_sha256=inputs.hexdigest()
            )
        except (ValueError, IndexError, AttributeError, OSError) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for key in ("source", "build", "assets", "report"):
        参数.add_argument("--" + key, type=Path, required=True)
    选项 = 参数.parse_args()
    主板音频差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
