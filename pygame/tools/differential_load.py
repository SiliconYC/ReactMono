# SPDX-License-Identifier: GPL-3.0-or-later
# 仅测试：直接原Application::load/draw，改写的旁车和真实DAT都留本地临时目录。
# ◑ 导入
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from differential_application import 应用差分_类

from rich4.application import 游戏应用_类
from rich4.application_types import 应用设置_类


# ◕ 功能
class 读档差分_类:
    """
    真实DAT配不同旁车逐次加载，比较原应用完整状态/世界字节/实际画布。

    更新日志：
    2026.10.24 - 旁车缺失/目录/字节与uint32范围边界，不替换原加载器。
    """

    @staticmethod
    def api_执行(
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_字体: Path,
        arg_库: Path,
        arg_存档: Path,
        arg_报告: Path,
    ) -> None:
        ref = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if ref != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"], check=True)
        exe = 应用差分_类._编译(arg_源码, arg_构建, arg_库)
        raw = arg_存档.read_bytes()
        payloads: list[bytes | None] = [None, b"", b"\xff", b"RICH4-RNG-2 17"]
        payloads += [
            b"RICH4-RNG-1 " + s
            for s in (
                b"0",
                b"1",
                b"4294967295",
                b"4294967296",
                b"-1",
                b"-2",
                b"-4294967295",
                b"-4294967296",
                b"+17",
                b"1junk",
                b"0x10",
                b"+bad",
                b"--1",
                b"18446744073709551615",
                b"12\xff",
                b"\xff",
                b"\0",
                b"17 42",
                b"0" * 5000 + b"17",
            )
        ]
        payloads += [b" \t\v\r\nRICH4-RNG-1\f 23\n", b"directory"]
        report = {
            "reference": ref,
            "status": "running",
            "scope": "direct original Application::load/draw with real DAT; exact complete "
            "state/world/canvas for optional sidecar failures and uint32 extraction; "
            "audio disabled",
            "save_sha256": hashlib.sha256(raw).hexdigest(),
            "cases": [],
            "runtime_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(Path(__file__).parents[1].glob("src/rich4/application*.py"))
                + [Path(__file__).parents[1] / "src/rich4/save_random.py"]
            },
        }
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "SDL_AUDIODRIVER": "dummy", "SDL_VIDEODRIVER": "dummy"}
        try:
            with tempfile.TemporaryDirectory(dir=arg_报告.parent) as tmp:
                root = Path(tmp)
                with (root / "cpp.log").open("w+") as errors:
                    app = 游戏应用_类(
                        应用设置_类(
                            arg_素材, arg_字体, root / "py", 种子=999, 静音=True, 验证天数=3
                        )
                    )
                    proc = None
                    try:
                        proc = subprocess.Popen(
                            [
                                str(exe),
                                str(arg_素材),
                                str(arg_字体),
                                str(root / "cpp"),
                                "0",
                                "999",
                                "3",
                            ],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=errors,
                            env=env,
                        )
                        for i, data in enumerate(payloads):
                            save = root / f"case-{i}.DAT"
                            save.write_bytes(raw)
                            sidecar = Path(str(save) + ".rng")
                            if data == b"directory":
                                sidecar.mkdir()
                            elif data is not None:
                                sidecar.write_bytes(data)
                            if not app.api_读取(save):
                                raise ValueError(f"Python原DAT载入失败，旁车案例{i}")
                            digest = hashlib.sha256()
                            commands = [
                                "L " + json.dumps(str(save), ensure_ascii=False),
                                f"D {i * 100}",
                            ]
                            for command in commands:
                                drawing = command.startswith("D")
                                if drawing:
                                    app.api_绘制(i * 100)
                                proc.stdin.write((command + "\n").encode())
                                proc.stdin.flush()
                                actual = proc.stdout.readline().decode().strip()
                                if not actual:
                                    errors.flush()
                                    raise ValueError((root / "cpp.log").read_text())
                                n, m = map(int, actual.split()[-2:])
                                pixels, world = proc.stdout.read(n), proc.stdout.read(m)
                                own, own_pixels, own_world = 应用差分_类._状态(app, drawing)
                                if actual != own or pixels != own_pixels or world != own_world:
                                    raise ValueError(
                                        f"实际原加载/绘图不同：案例{i}，命令{command[0]}"
                                    )
                                digest.update(actual.encode() + pixels + world)
                            report["cases"].append(
                                {
                                    "case": i,
                                    "kind": "missing"
                                    if data is None
                                    else "directory"
                                    if data == b"directory"
                                    else "file",
                                    "bytes": len(data)
                                    if data is not None and data != b"directory"
                                    else None,
                                    "payload_sha256": hashlib.sha256(data).hexdigest()
                                    if data is not None and data != b"directory"
                                    else None,
                                    "state_sha256": digest.hexdigest(),
                                    "random_state": app.会话.随机.状态,
                                }
                            )
                    finally:
                        try:
                            app.api_关闭()
                        finally:
                            if proc is not None:
                                if proc.stdin is not None:
                                    proc.stdin.close()
                                    proc.stdin = None
                                try:
                                    proc.communicate(timeout=10)
                                except subprocess.TimeoutExpired:
                                    proc.kill()
                                    proc.wait()
                    if proc.returncode:
                        raise ValueError("原加载器非正常退出")
            report.update(status="passed", commands=len(payloads) * 2, canvases=len(payloads))
        except (ValueError, OSError, RuntimeError) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({k: v for k, v in report.items() if k not in ("cases", "runtime_sha256")}))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for name in ("source", "build", "assets", "font", "library", "save", "report"):
        参数.add_argument("--" + name, type=Path, required=True)
    选项 = 参数.parse_args()
    读档差分_类.api_执行(
        选项.source, 选项.build, 选项.assets, 选项.font, 选项.library, 选项.save, 选项.report
    )
