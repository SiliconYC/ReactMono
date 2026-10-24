# SPDX-License-Identifier: GPL-3.0-or-later
# 仅构建标准音频依赖到忽略缓存；不安装系统包，不含游戏或商业音库。
# ◑ 导入
import argparse
import json
import os
import subprocess
from pathlib import Path


# ◕ 功能
class 音频依赖构建_类:
    """
    固定SDL3/FluidSynth公开提交与项目缓存安装，使用已有CMake/GLib。

    更新日志：
    2026.10.24 - 避免Homebrew在旧系统升级全局依赖；原SDK只读，日志/产物在缓存。
    """

    源 = (
        (
            "SDL-3.4.18",
            "https://github.com/libsdl-org/SDL.git",
            "release-3.4.18",
            "829a65d769d935c4852f8159e964312c0957260a",
            "sdl3",
        ),
        (
            "fluidsynth-2.6.1",
            "https://github.com/FluidSynth/fluidsynth.git",
            "v2.6.1",
            "71e85b2ca6bf48641ba7e2261d8f2640ae473773",
            "fluidsynth",
        ),
    )

    @staticmethod
    def _运行(arg_参数: list[str], arg_日志: Path) -> None:
        with arg_日志.open("w") as out:
            subprocess.run(arg_参数, stdout=out, stderr=subprocess.STDOUT, check=True)

    @classmethod
    def api_执行(cls, arg_根: Path, arg_并行: int) -> None:
        root = arg_根.resolve()
        cache, upstream = root / ".research-cache", root / ".research-upstreams"
        cache.mkdir(parents=True, exist_ok=True)
        upstream.mkdir(parents=True, exist_ok=True)
        prefix = cache / "audio-runtime"
        report = {
            "status": "running",
            "scope": "standard SDKs only; no Rich4 engine or commercial bank",
            "prefix": str(prefix),
            "sources": [],
        }
        try:
            for name, url, tag, commit, build_name in cls.源:
                src, build = upstream / name, cache / (build_name + "-build")
                if not src.exists():
                    subprocess.run(
                        ["git", "clone", "--depth", "1", "--branch", tag, url, str(src)], check=True
                    )
                actual = subprocess.check_output(
                    ["git", "-C", str(src), "rev-parse", "HEAD"], text=True
                ).strip()
                if actual != commit:
                    raise ValueError(f"依赖源提交不符：{name}")
                subprocess.run(
                    ["git", "-C", str(src), "diff", "--exit-code", "HEAD"],
                    check=True,
                    capture_output=True,
                )
                options = ["-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX=" + str(prefix)]
                if build_name == "sdl3":
                    options += [
                        "-DSDL_SHARED=ON",
                        "-DSDL_STATIC=OFF",
                        "-DSDL_TESTS=OFF",
                        "-DSDL_TEST_LIBRARY=OFF",
                    ]
                else:
                    options += [
                        "-Denable-framework=OFF",
                        "-Denable-coreaudio=OFF",
                        "-Denable-coremidi=OFF",
                        "-Denable-portaudio=OFF",
                        "-Denable-libsndfile=OFF",
                        "-Denable-readline=OFF",
                        "-Denable-aufile=OFF",
                        "-Denable-network=OFF",
                        "-Denable-openmp=OFF",
                        "-Denable-sdl3=OFF",
                        "-Denable-signalsmith=OFF",
                        "-Denable-native-dls=ON",
                    ]
                    if Path("/opt/homebrew").exists():
                        options.append("-DCMAKE_PREFIX_PATH=/opt/homebrew")
                cls._运行(
                    ["cmake", "-S", str(src), "-B", str(build), *options],
                    cache / (build_name + "-configure.log"),
                )
                command = ["cmake", "--build", str(build), "--parallel", str(arg_并行)]
                if build_name == "sdl3":
                    command += ["--target", "SDL3-shared"]
                cls._运行(command, cache / (build_name + "-build.log"))
                cls._运行(["cmake", "--install", str(build)], cache / (build_name + "-install.log"))
                report["sources"].append(
                    {"name": name, "url": url, "tag": tag, "commit": commit, "options": options}
                )
                print(f"[完成] 音频依赖{name}已构建到项目缓存。", flush=True)
            env = os.environ.copy()
            env["PKG_CONFIG_PATH"] = str(prefix / "lib/pkgconfig")
            report["versions"] = subprocess.check_output(
                ["pkg-config", "--modversion", "sdl3", "fluidsynth"], env=env, text=True
            ).splitlines()
            report["status"] = "passed"
        except (ValueError, OSError, subprocess.CalledProcessError) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            (cache / "audio-dependencies.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            )


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--workspace", type=Path, required=True)
    参数.add_argument("--jobs", type=int, default=4)
    选项 = 参数.parse_args()
    if 选项.jobs < 1:
        raise ValueError("构建并行数必须为正")
    音频依赖构建_类.api_执行(选项.workspace, 选项.jobs)
