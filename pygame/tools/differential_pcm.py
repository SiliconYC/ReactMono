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
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.audio_player import PCM播放器_类
from rich4.audio_types import 循环通道_类


# ◕ 功能
class PCM差分_类:
    """
    实际原PCM控制/离线混音块与真实WAV、私有片段/统计/排队请求对照。

    更新日志：
    2026.10.24 - 不创建设备或MIDI；显式数字PCM夹具与商业素材输入分开。
    """

    def __init__(self, arg_素材: Path, arg_库: Path) -> None:
        self.素材, self.库, self.时 = arg_素材, arg_库, 0
        self.美术 = 美术_类(arg_素材)
        self.调用: list[tuple[str, str]] = []

    @staticmethod
    def _位(arg_值: float) -> int:
        return struct.unpack("<I", struct.pack("<f", arg_值))[0]

    @staticmethod
    def _串(arg_值: str) -> list[int]:
        data, h = arg_值.encode(), 14695981039346656037
        for b in data:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(data), h]

    @staticmethod
    def _样本(arg_数据: bytes) -> array:
        samples = array("f")
        samples.frombytes(arg_数据)
        if sys.byteorder != "little":
            samples.byteswap()
        return samples

    def _来源(self, arg_样本: array) -> tuple[bool, int]:
        return next(key for key, pcm in self.播放器._样本.items() if pcm is arg_样本)

    def _操作(self, arg_行: str, arg_数据: bytes) -> tuple[str, bytes, bool]:
        op, *args = arg_行.split()
        self.调用.clear()
        output, accepted, result = array("f"), True, -1
        try:
            if op == "N":
                self.时 = 0
                self.播放器 = PCM播放器_类(self.素材, bool(int(args[0])), self.库, lambda: self.时)
                self.播放器.api_追踪(lambda a, b: self.调用.append((a, b)))
            elif op == "S":
                self.播放器.api_播音(int(args[0]))
            elif op == "V":
                result = self.播放器.api_语音(int(args[0]))
            elif op == "Q":
                self.播放器.api_排语音(int(args[0]))
            elif op == "R":
                self.播放器.api_角色声音(*map(int, args))
            elif op == "L":
                channel, index = map(int, args)
                self.播放器.api_播循环(index, 循环通道_类(channel))
            elif op == "T":
                self.播放器.api_停循环(循环通道_类(int(args[0])))
            elif op == "A":
                self.播放器.api_停全部循环()
            elif op == "X":
                self.播放器.api_停语音()
            elif op == "U":
                self.时 = int(args[0])
                self.播放器.api_更新()
            elif op == "B":
                for _ in range(int(args[0])):
                    output.extend(self.播放器.api_渲染块())
            elif op == "D":
                voice, index, n = map(int, args)
                key = bool(voice), index
                if key in self.播放器._样本:
                    raise ValueError("PCM夹具只能插入新的缓存项")
                if len(arg_数据) != n * 4:
                    raise ValueError("PCM夹具长度不符")
                self.播放器._样本[key] = self._样本(arg_数据)
            else:
                raise ValueError(op)
        except (ValueError, IndexError, RuntimeError, OSError):
            accepted = False
        p = self.播放器
        m, s = p._混音, p.api_统计()
        values = [int(accepted), result, int(p.启用), int(p.api_有语音())]
        for loop in p._循环:
            values.append(int(loop is not None))
            if loop is not None:
                values.append(loop)
        values.append(len(m._片段))
        for c in m._片段:
            voice, index = self._来源(c.样本)
            values += [
                int(voice),
                index,
                len(c.样本),
                c.位置,
                int(c.语音),
                int(c.循环),
                int(c.通道),
            ]
        values.append(len(m._语音队列))
        for index, pcm in m._语音队列:
            voice, key = self._来源(pcm)
            values += [index, int(voice), key]
        values.append(len(p._样本))
        for (voice, index), pcm in sorted(p._样本.items()):
            values += [int(voice), index, len(pcm)]
        values += [
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
        lim = m._限幅
        values += [
            self._位(lim._上限),
            self._位(lim._释放),
            self._位(lim._包络),
            self._位(lim.api_增益()),
            p._上更新,
            int(p._已报错),
            *self._串(p.诊断),
            *self._串(p._渲染错误),
        ]
        for logs in (m._待日志, self.调用):
            values.append(len(logs))
            for a, b in logs:
                values += [*self._串(a), *self._串(b)]
        values.append(len(output))
        if sys.byteorder != "little":
            output.byteswap()
        return " ".join(map(str, values)), output.tobytes(), accepted

    def _命令(self, arg_预检: bool) -> list[tuple[str, bytes, bool]]:
        commands: list[tuple[str, bytes, bool]] = []

        def 添加(arg_行: str, arg_数据: bytes = b"", arg_成功: bool = True) -> None:
            commands.append((arg_行, arg_数据, arg_成功))

        添加("N 1")
        raw = struct.pack("<16f", *[(-1) ** i * (i + 1) * 0.01234567 for i in range(16)])
        添加("D 0 20000 16", raw)
        添加("S 20000")
        添加("L 1 20000")
        添加("V 127")
        添加("Q 128")
        添加("B 1")
        添加("U 1")
        添加("T 1")
        添加("X")
        添加("B 1")
        if arg_预检:
            return commands
        添加("N 0")
        for line in ("S 0", "V 0", "Q 0", "R 0 0", "L 1 0", "L 2 0", "L 1 0", "U 1", "A", "X"):
            添加(line)
        effects = [
            i
            for i in range(len(self.美术.api_包("e").条目))
            if self.美术.api_解码("e", i).startswith(b"RIFF")
        ]
        for start in range(0, len(effects), 32):
            添加("N 1")
            for i in effects[start : start + 32]:
                添加(f"S {i}")
                添加("B 1")
                添加(f"U {(i + 1) * 1000000}")
            添加("B 16")
        for start in range(0, 1374, 96):
            添加("N 1")
            for i in range(start, min(start + 96, 1374)):
                添加(f"V {i}")
                添加("B 1")
            添加("Q 127")
            添加("Q 128")
            添加("B 128")
            添加("U 1000000000")
            添加("X")
        for ch in range(12):
            添加("N 1")
            for category in range(27):
                添加(f"R {ch} {category}")
                添加("B 1")
        添加("N 1")
        for i in range(3):
            添加(f"L {i} {(51, 44, 32)[i]}")
        添加("V 127")
        for i in (128, 129, 130, 124):
            添加(f"Q {i}")
        添加("B 500")
        添加("U 100")
        添加("U 999999999")
        添加("U 0")
        添加("U 18446744073709551615")
        添加("A")
        添加("X")
        for i in range(20):
            添加(f"S {effects[i]}")
        添加("B 10")
        添加("N 1")
        for voice, index, data in (
            (0, 20000, b""),
            (1, 20000, raw),
            (0, 20001, struct.pack("<5I", 0x7F800001, 0x7F800000, 0xFF800000, 1, 0x80000000)),
        ):
            添加(f"D {voice} {index} {len(data) // 4}", data)
        添加("L 0 20000")
        添加("S 20001")
        添加("V 20000")
        添加("Q 127")
        添加("B 3")
        添加("U 1000000000")
        添加("S 115", arg_成功=False)
        添加("V 1374", arg_成功=False)
        添加("R 12 0", arg_成功=False)
        添加("R 0 27", arg_成功=False)
        添加("L 2 115", arg_成功=False)
        添加("L 2 115")
        添加("A")
        添加("B 1")
        添加("U 1000000001")
        return commands

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_库: Path,
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
            check=True,
            capture_output=True,
        )
        flags = shlex.split(
            subprocess.check_output(
                ["pkg-config", "--cflags", "--libs", "sdl3", "fluidsynth"], text=True
            )
        )
        tool = arg_构建.resolve() / "pcm-oracle"
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
                str(Path(__file__).with_name("pcm_oracle.cpp")),
                str(arg_构建.resolve() / "librich4_core.a"),
                *flags,
                "-Wl,-rpath," + str(arg_库.resolve().parent),
                "-o",
                str(tool),
            ],
            check=True,
        )
        own, digest, inputs = cls(arg_素材, arg_库), hashlib.sha256(), hashlib.sha256()
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
            "samples": 0,
            "rejected": 0,
            "scope": (
                "original public PCM controls and actual render_block_locked offline vs Python; "
                "real WAVs plus explicit numeric fixtures, private state/trace and exact F32; "
                "no audio device, MIDI, asynchronous loader or listening proof"
            ),
            "mode": "smoke" if arg_预检 else "base",
            "architecture": platform.machine(),
            "compiler": subprocess.check_output(["c++", "--version"], text=True).splitlines()[0],
            "runtime_sha256": {
                n: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                ).hexdigest()
                for n in (
                    "audio_player.py",
                    "audio_pcm.py",
                    "audio_pcm_types.py",
                    "audio_limiter.py",
                    "wave_decoder.py",
                )
            },
        }
        try:
            for index, (line, raw, expected_ok) in enumerate(own._命令(arg_预检)):
                report.update(last_index=index, last_command=line)
                proc.stdin.write((line + "\n").encode() + raw)
                proc.stdin.flush()
                actual = proc.stdout.readline().decode().strip()
                if not actual:
                    raise ValueError("原PCM提前结束：" + proc.stderr.read().decode())
                count = int(actual.split()[-1])
                cpp = proc.stdout.read(count * 4)
                if len(cpp) != count * 4:
                    raise ValueError("原PCM采样输出截断")
                expected, py, ok = own._操作(line, raw)
                if bool(int(actual.split()[0])) != expected_ok or ok != expected_ok:
                    report.update(expected_success=expected_ok, cpp=actual, python=expected)
                    raise ValueError(f"step={index} PCM输入接受分类不符")
                if actual != expected:
                    report.update(cpp=actual, python=expected)
                    raise ValueError(f"step={index} PCM私有状态/请求不同")
                if cpp != py:
                    offset = next((i for i, (a, b) in enumerate(zip(cpp, py)) if a != b), -1)
                    report["first_sample_difference"] = offset // 4
                    raise ValueError(f"step={index} PCM输出位不同")
                digest.update(actual.encode())
                digest.update(cpp)
                inputs.update((line + "\n").encode() + raw)
                report["commands"], report["samples"] = index + 1, report["samples"] + count
                report["rejected"] += int(not ok)
                if index % 128 == 0:
                    arg_报告.parent.mkdir(parents=True, exist_ok=True)
                    arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            proc.stdin.close()
            code, error = proc.wait(), proc.stderr.read().decode()
            if code or error:
                raise ValueError("原PCM退出故障：" + error)
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
    for key in ("source", "build", "assets", "library", "report"):
        参数.add_argument("--" + key, type=Path, required=True)
    参数.add_argument("--smoke", action="store_true")
    选项 = 参数.parse_args()
    PCM差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.library, 选项.report, 选项.smoke)
