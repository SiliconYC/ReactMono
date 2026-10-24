# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import platform
import shlex
import struct
import subprocess
import sys
from array import array
from collections.abc import Iterator
from pathlib import Path

from rich4.audio import 音频_类
from rich4.audio_types import 循环通道_类, 音乐_类


# ◕ 功能
class MIDI差分_类:
    """
    原实际MIDI控制/软件合成与PCM叠加，私有状态和全部F32位对照。

    更新日志：
    2026.10.24 - 使用同版本公共FluidSynth和外部银行，设备关闭，明确离线范围。
    """

    def __init__(
        self,
        arg_素材: Path,
        arg_音库: Path,
        arg_SDL库: Path,
        arg_Fluid库: Path,
    ) -> None:
        self.素材, self.音库 = arg_素材, arg_音库
        self.SDL库, self.Fluid库 = arg_SDL库, arg_Fluid库
        self.时 = 0
        self.播放器: 音频_类 | None = None
        self.调用: list[tuple[str, str]] = []
        self.自然歌单: list[int] = []
        self.自然上下文: list[int] = []
        self.恢复缺陷: dict[str, int] = {}

    @staticmethod
    def _位(arg_值: float) -> int:
        return struct.unpack("<I", struct.pack("<f", arg_值))[0]

    @staticmethod
    def _字节(arg_数据: bytes) -> list[int]:
        h = 14695981039346656037
        for b in arg_数据:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(arg_数据), h]

    @classmethod
    def _串(cls, arg_值: str) -> list[int]:
        return cls._字节(arg_值.encode())

    def _操作(self, arg_行: str) -> tuple[str, bytes, bool]:
        op, *args = arg_行.split()
        self.调用.clear()
        output, accepted = array("f"), True
        try:
            if op == "N":
                if self.播放器 is not None:
                    self.播放器.api_关闭()
                enabled, bank = map(int, args)
                self.时 = 0
                self.播放器 = 音频_类(
                    self.素材,
                    bool(enabled),
                    self.音库 if bank else self.素材 / "__missing_midi_bank__.sf2",
                    self.SDL库,
                    self.Fluid库,
                    lambda: self.时,
                )
                self.播放器.api_追踪(lambda a, b: self.调用.append((a, b)))
            elif op == "P":
                self.播放器.api_推音乐(音乐_类(int(args[0])))
            elif op == "C":
                self.播放器.api_换音乐(音乐_类(int(args[0])))
            elif op == "O":
                self.播放器.api_弹音乐()
            elif op == "M":
                self.播放器.api_音乐开关(bool(int(args[0])))
            elif op == "I":
                self.播放器.api_选音乐(int(args[0]))
            elif op == "S":
                self.播放器.api_播音(int(args[0]))
            elif op == "V":
                self.播放器.api_语音(int(args[0]))
            elif op == "Q":
                self.播放器.api_排语音(int(args[0]))
            elif op == "L":
                c, i = map(int, args)
                self.播放器.api_播循环(i, 循环通道_类(c))
            elif op == "T":
                self.播放器.api_停循环(循环通道_类(int(args[0])))
            elif op == "U":
                self.时 = int(args[0])
                self.播放器.api_更新()
            elif op == "B":
                for _ in range(int(args[0])):
                    output.extend(self.播放器.api_渲染块())
            else:
                raise ValueError("未知MIDI命令")
        except (ValueError, RuntimeError, OSError):
            accepted = False
        p = self.播放器
        m, core = p._音乐, p._混音
        state = [
            int(accepted),
            int(p.启用),
            int(p.api_音乐可用()),
            int(p.api_音乐启用()),
            p.api_音乐曲目(),
            -1 if m.上下文 is None else int(m.上下文),
            p.api_音乐深度(),
        ]
        state += self._串(p.api_音乐名称())
        state += [
            m.api_时刻(),
            m._合成.api_状态() if m._合成 is not None else -1,
            int(m._过期),
            m._恢复,
            int(m._合成 is not None),
            len(m._栈),
        ]
        for context, track, tick in m._栈:
            state += [-1 if context is None else int(context), track, tick]
        state += [len(m._缓存)]
        for name, data in sorted(m._缓存.items()):
            state += self._串(name) + self._字节(data)
        s = p.api_统计()
        state += [
            s.渲染帧,
            s.非零采样,
            s.效果启动,
            s.语音启动,
            s.片段完成,
            s.音乐帧,
            s.超时次数,
            s.饥饿毫秒,
            s.削波采样,
            s.限幅采样,
            self._位(s.峰值),
            s.最长更新间隔,
            s.最长渲染微秒,
        ]
        state += [self._位(core._限幅._包络), self._位(core._限幅.api_增益())]
        state += self._串(p.诊断) + self._串(p._渲染错误) + [len(core._待日志)]
        for a, b in core._待日志:
            state += self._串(a) + self._串(b)
        state += [len(self.调用)]
        for a, b in self.调用:
            state += self._串(a) + self._串(b)
        state += [len(output)]
        if sys.byteorder != "little":
            output.byteswap()
        return " ".join(map(str, state)), output.tobytes(), accepted

    def _命令(self, arg_预检: bool) -> Iterator[tuple[str, bool]]:
        yield "N 1 1", True
        yield "B 128", True
        tick = self.播放器._音乐.api_时刻()
        for line in ("M 0", "P 5", "O", "M 1", "B 4"):
            yield line, True
        self.恢复缺陷 = {
            "saved_tick": tick,
            "after_resume_four_blocks": self.播放器._音乐.api_时刻(),
        }
        for line in ("P 0", "B 16", "O", "B 16", "U 1000000000"):
            yield line, True
        if arg_预检:
            return
        for enabled, bank in ((0, 0), (1, 0), (1, 1)):
            yield f"N {enabled} {bank}", True
            for line in (
                "C 1",
                "P 5",
                "P 7",
                "M 0",
                "C 8",
                "O",
                "B 4",
                "M 1",
                "B 4",
                "O",
                "O",
                "O",
                "I 8",
                "I 0",
                "M 1",
            ):
                yield line, True
        yield "I 9", False
        for track in range(1, 9):
            for line in (f"I {track}", "S 0", "V 127", "Q 128", "B 128", "U 1000000001"):
                yield line, True
        for context in range(18):
            for line in (
                f"P {context}",
                "B 128",
                "M 0",
                "B 4",
                "M 1",
                "B 4",
                "P 5",
                "B 8",
                "C 7",
                "B 8",
                "O",
                "B 8",
                "O",
                "B 8",
            ):
                yield line, True
        for line in (
            "I 1",
            "L 0 51",
            "L 1 44",
            "L 2 32",
            "V 127",
            "Q 128",
            "B 128",
            "T 0",
            "T 1",
            "T 2",
            "B 128",
            "U 2000000000",
        ):
            yield line, True
        # 自然前进不得用seek/强制DONE；给每首最多640秒，超过即失败。
        yield "N 1 1", True
        for _ in range(8):
            track = self.播放器.api_音乐曲目()
            for _ in range(120):
                yield "B 500", True
                if self.播放器.api_音乐曲目() != track:
                    self.自然歌单.append(track)
                    break
            else:
                raise ValueError(f"原歌单曲目{track}未在640秒内自然完成")
            yield "U 3000000000", True
        for context in range(1, 18):
            yield f"P {context}", True
            previous = 0
            for _ in range(480):
                yield "B 125", True
                tick = self.播放器._音乐.api_时刻()
                if tick < previous:
                    self.自然上下文.append(context)
                    break
                previous = tick
            else:
                raise ValueError(f"上下文{context}未在640秒内自然循环")
            yield "O", True
        yield "U 4000000000", True

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_音库: Path,
        arg_SDL库: Path,
        arg_Fluid库: Path,
        arg_报告: Path,
        arg_预检: bool,
    ) -> None:
        ref = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if ref != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            capture_output=True,
            check=True,
        )
        flags = shlex.split(
            subprocess.check_output(
                ["pkg-config", "--cflags", "--libs", "sdl3", "fluidsynth"], text=True
            )
        )
        tool = arg_构建.resolve() / "midi-oracle"
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
                str(Path(__file__).with_name("midi_oracle.cpp")),
                str(arg_构建.resolve() / "librich4_core.a"),
                *flags,
                "-Wl,-rpath," + str(arg_SDL库.resolve().parent),
                "-o",
                str(tool),
            ],
            check=True,
        )
        own = cls(arg_素材, arg_音库, arg_SDL库, arg_Fluid库)
        digest, inputs = hashlib.sha256(), hashlib.sha256()
        proc = subprocess.Popen(
            [str(tool), str(arg_素材), str(arg_音库)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        report = {
            "reference": ref,
            "status": "running",
            "commands": 0,
            "samples": 0,
            "rejected": 0,
            "scope": "actual original MIDI/PCM offline; all F32 bits, stack, ticks, status, "
            "cache, stats, limiter and trace; no device or listening proof",
            "mode": "smoke" if arg_预检 else "base",
            "architecture": platform.machine(),
            "compiler": subprocess.check_output(["c++", "--version"], text=True).splitlines()[0],
            "bank_sha256": hashlib.sha256(arg_音库.read_bytes()).hexdigest(),
            "runtime_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in (
                    "audio.py",
                    "midi_player.py",
                    "fluid_synth.py",
                    "audio_player.py",
                    "audio_pcm.py",
                    "audio_limiter.py",
                    "wave_decoder.py",
                )
            },
        }
        try:
            for index, (line, expected_ok) in enumerate(own._命令(arg_预检)):
                report.update(last_index=index, last_command=line)
                proc.stdin.write((line + "\n").encode())
                proc.stdin.flush()
                actual = proc.stdout.readline().decode().strip()
                if not actual:
                    raise ValueError("原MIDI提前退出：" + proc.stderr.read().decode())
                count = int(actual.split()[-1])
                cpp = proc.stdout.read(count * 4)
                if len(cpp) != count * 4:
                    raise ValueError("原MIDI采样截断")
                expected, py, ok = own._操作(line)
                if bool(int(actual.split()[0])) != expected_ok or ok != expected_ok:
                    report.update(expected_success=expected_ok, cpp=actual, python=expected)
                    raise ValueError(f"step={index} 有效MIDI输入接受分类不符")
                if actual != expected:
                    report.update(cpp=actual, python=expected)
                    raise ValueError(f"step={index} MIDI状态不同")
                if cpp != py:
                    offset = next((i for i, (a, b) in enumerate(zip(cpp, py)) if a != b), -1)
                    report["first_sample_difference"] = offset // 4
                    raise ValueError(f"step={index} MIDI采样位不同")
                digest.update(actual.encode())
                digest.update(cpp)
                inputs.update((line + "\n").encode())
                report["commands"], report["samples"] = index + 1, report["samples"] + count
                report["rejected"] += int(not ok)
                if index % 16 == 0:
                    report.update(natural_playlist=own.自然歌单, natural_contexts=own.自然上下文)
                    arg_报告.parent.mkdir(parents=True, exist_ok=True)
                    arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
                    print(f"[信息] MIDI对照{index}命令/{report['samples']}采样。", flush=True)
            proc.stdin.close()
            code, error = proc.wait(), proc.stderr.read().decode()
            if code or any(
                message != "fluidsynth: error: Not a SoundFont file"
                for message in error.splitlines()
            ):
                raise ValueError("原MIDI退出或新诊断：" + error)
            report.update(
                status="passed",
                state_sha256=digest.hexdigest(),
                input_sha256=inputs.hexdigest(),
                natural_playlist=own.自然歌单,
                natural_contexts=own.自然上下文,
                resume_reference_defect=own.恢复缺陷,
                soundbank_probe_messages=error.splitlines(),
            )
        except (ValueError, IndexError, AttributeError, OSError) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait()
            if own.播放器 is not None:
                own.播放器.api_关闭()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for key in ("source", "build", "assets", "bank", "sdl-library", "fluid-library", "report"):
        参数.add_argument("--" + key, type=Path, required=True)
    参数.add_argument("--smoke", action="store_true")
    选项 = 参数.parse_args()
    MIDI差分_类.api_执行(
        选项.source,
        选项.build,
        选项.assets,
        选项.bank,
        选项.sdl_library,
        选项.fluid_library,
        选项.report,
        选项.smoke,
    )
