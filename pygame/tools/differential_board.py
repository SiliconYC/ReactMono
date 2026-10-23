# ◑ 导入
import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
import time
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.board_models import (
    业主外观_类,
    地产外观_类,
    场景_类,
    物件精灵_类,
    特殊人物精灵_类,
    玩家精灵_类,
    相机_类,
    绘制统计_类,
)
from rich4.board_renderer import 棋盘绘制_类
from rich4.graphics import 图像_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 棋盘差分_类:
    """
    八图八视角完整像素与掩码对照；局部模块截图不冒充图形游戏试玩。

    更新日志：
    2026.10.23 - 覆盖静态、所有权/临时效果、角色/物件/特殊人物与离图遮挡。
    """

    @staticmethod
    def _场景(arg_世: 世界_类, arg_中心: tuple[int, int], arg_型: int, arg_旋: int) -> 场景_类:
        if arg_型 == 0:
            return 场景_类()
        角色 = (10, 0, 3, 6)
        颜色 = (0x7C00, 0x03E0, 0x001F, 0x7C1F)
        场 = 场景_类(业主=[业主外观_类(色, 人) for 色, 人 in zip(颜色, 角色)])
        if arg_型 != 3:
            场.地产 = [
                地产外观_类(
                    i, i % 4 + 1, i % 6, int(i % 7 == 0), 0 if i % 3 else 0x31 if i % 2 else 0x50
                )
                for i in range(1, len(arg_世.地产))
            ]
            场.设施 = [
                地产外观_类(i, i % 4 + 1, i % 5 + 1, i % 5, 0x50 if i % 3 == 0 else 0)
                for i in range(1, len(arg_世.设施))
            ]
            场.公司 = [地产外观_类(i, i % 4 + 1) for i in range(1, len(arg_世.公司))]
        人数 = 4 if arg_型 == 1 else 12
        for i in range(人数):
            位置 = (arg_中心[0] + (i % 3 - 1) * 6, arg_中心[1] + (i % 2) * 4)
            场.玩家.append(
                玩家精灵_类(
                    位置=位置,
                    角色=角色[i] if 人数 == 4 else i,
                    方向=(arg_旋 + i * 2) & 7,
                    动画帧=i * 5 + 4,
                    交通=i % 4,
                    颜色=颜色[i % 4],
                    槽位=i % 4,
                    活跃=i == 0,
                    走动=i % 2 == 0,
                    踩水=arg_型 > 1 and i % 5 == 0,
                    梦游=arg_型 > 1 and i % 6 == 0,
                    受伤=arg_型 > 1 and i % 7 == 0,
                    投骰=arg_型 > 1 and i % 8 == 0,
                    特殊姿态=(0, 12, 19, 20)[i % 4] if arg_型 > 1 else 0,
                )
            )
        if arg_型 > 1:
            for i in range(1, 21):
                位置 = (arg_中心[0] + (i % 5 - 2) * 12, arg_中心[1] + (i // 5 - 2) * 10)
                场.物件.append(物件精灵_类(位置, i, (arg_旋 + i) & 7, i + 4, i % 3))
            for i in range(4, 9):
                位置 = (arg_中心[0] + (i - 6) * 16, arg_中心[1] + 16)
                场.特殊人物.append(
                    特殊人物精灵_类(
                        位置, i, (i + arg_旋) & 7, 5, i == 4, i % 2 == 0, i % 3 == 0, i % 4 == 0
                    )
                )
        return 场

    @staticmethod
    def _输入(arg_相机: 相机_类, arg_场: 场景_类, arg_掩码: bool, arg_地面: bool = False) -> str:
        组 = [
            arg_场.玩家,
            arg_场.物件,
            arg_场.地产,
            arg_场.设施,
            arg_场.特殊人物,
            arg_场.公司,
            arg_场.业主,
        ]
        行 = [
            ("G" if arg_地面 else "S")
            + " "
            + " ".join(
                map(
                    str,
                    [
                        *arg_相机.中心,
                        arg_相机.旋转,
                        *arg_相机.视口,
                        640,
                        480,
                        0x1234,
                        int(arg_掩码),
                        *(len(项) for 项 in 组),
                    ],
                )
            )
        ]
        for p in arg_场.玩家:
            行.append(
                " ".join(
                    map(
                        str,
                        [
                            *p.位置,
                            p.角色,
                            p.方向,
                            p.动画帧,
                            p.交通,
                            p.颜色,
                            p.槽位,
                            int(p.活跃),
                            int(p.走动),
                            int(p.踩水),
                            int(p.梦游),
                            int(p.受伤),
                            int(p.投骰),
                            p.特殊姿态,
                        ],
                    )
                )
            )
        for p in arg_场.物件:
            行.append(" ".join(map(str, [*p.位置, p.种类, p.方向, p.动画帧, p.跟随])))
        for 项组 in (arg_场.地产, arg_场.设施):
            for p in 项组:
                行.append(f"{p.编号} {p.业主} {p.等级} {p.类型} {p.临时状态}")
        for p in arg_场.特殊人物:
            行.append(
                " ".join(
                    map(
                        str,
                        [
                            *p.位置,
                            p.槽位,
                            p.方向,
                            p.动画帧,
                            int(p.活跃),
                            int(p.走动),
                            int(p.踩水),
                            int(p.梦游),
                        ],
                    )
                )
            )
        for p in arg_场.公司:
            行.append(f"{p.编号} {p.业主} {p.等级} {p.类型} {p.临时状态}")
        for p in arg_场.业主:
            行.append(f"{p.颜色} {p.角色}")
        return "\n".join(行) + "\n"

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_报告: Path) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "cmake",
                "-S",
                str(arg_源码),
                "-B",
                str(arg_构建),
                "-DRICH4_BUILD_GAME=OFF",
                "-DRICH4_BUILD_VIEWER=OFF",
                "-DBUILD_TESTING=OFF",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["cmake", "--build", str(arg_构建), "--target", "rich4_core", "--parallel", "6"],
            check=True,
            capture_output=True,
        )
        工具 = arg_构建.resolve() / "board-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("board_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "scope": "real-asset board composition; no application UI, sound or timing",
            "status": "running",
            "maps": [],
        }
        try:
            包 = 资源包_类(
                next(p for p in arg_素材.iterdir() if p.name.lower() == "map.mkf" and p.is_file())
            )
            for 地图 in range(8):
                世 = 世界_类.api_从地图(
                    包.api_解码(地图 * 2 + 1), 新局设置_类(地图=地图 % 4, 阶段=地图 // 4)
                )
                起 = time.perf_counter()
                绘制 = 棋盘绘制_类(arg_素材, 地图)
                中心 = 绘制.api_节点位置(51)
                if 中心 is None:
                    raise ValueError("真实地图缺少节点51")
                初始化 = time.perf_counter() - 起
                用例 = []
                for 旋 in range(8):
                    for 型 in range(4):
                        中 = (
                            (-4096, -4096)
                            if 型 == 3
                            else (中心[0] + (1 if 型 == 2 else 0), 中心[1] + (31 if 型 == 2 else 0))
                        )
                        相机 = 相机_类(中, 旋, (10, 20, 600, 460) if 型 == 2 else (0, 40, 440, 480))
                        场 = cls._场景(世, 中, 型, 旋)
                        用例.append((相机, 场, 型 % 2 == 0, False))
                用例.append((相机_类(中心, 0), 场景_类(), True, True))
                用例.append((相机_类(中心, 8), 场景_类(), False, False))
                输入 = "".join(cls._输入(*项) for 项 in 用例)
                摘要 = hashlib.sha256()
                绘时 = []
                拒绝数 = 0
                with tempfile.TemporaryDirectory(prefix="rich4-board-") as 临时:
                    路径 = Path(临时)
                    cpp = subprocess.run(
                        [str(工具), str(arg_素材), str(地图), str(路径)],
                        input=输入,
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    行 = cpp.stdout.splitlines()
                    if len(行) != len(用例):
                        raise ValueError("棋盘输出帧数不同")
                    for i, ((相机, 场, 掩码, 地面), cpp行) in enumerate(zip(用例, 行)):
                        图 = 图像_类(
                            640,
                            480,
                            [0x1234] * (640 * 480),
                            不透明=bytes(int(i % 3 == 0) for i in range(640 * 480))
                            if 掩码
                            else b"",
                        )
                        统计 = 绘制统计_类()
                        状态 = 0
                        起 = time.perf_counter()
                        try:
                            统计 = (
                                绘制.api_绘地面(图, 相机) if 地面 else 绘制.api_绘制(图, 场, 相机)
                            )
                        except (ValueError, IndexError):
                            状态 = 1
                        绘时.append(time.perf_counter() - 起)
                        if [状态, 统计.地面, 统计.道路, 统计.精灵] != list(map(int, cpp行.split())):
                            raise ValueError(
                                f"图{地图}/帧{i}状态/绘制计数不同：{状态}/{统计}/{cpp行}"
                            )
                        if 状态 and i != len(用例) - 1:
                            raise ValueError(
                                f"图{地图}/帧{i}本应有效的场景被拒绝，C++ stderr={cpp.stderr}"
                            )
                        输出 = struct.pack("<II", len(图.像素), len(图.不透明))
                        输出 += struct.pack(f"<{len(图.像素)}H", *图.像素) + 图.不透明
                        cpp输出 = (路径 / f"{i}.bin").read_bytes()
                        if 输出 != cpp输出:
                            首差 = next(n for n, (a, b) in enumerate(zip(输出, cpp输出)) if a != b)
                            raise ValueError(f"图{地图}/帧{i}像素或掩码不同，首差字节{首差}")
                        摘要.update(输出)
                        拒绝数 += 状态
                报告["maps"].append(
                    {
                        "map": 地图,
                        "frames": len(用例),
                        "rejected": 拒绝数,
                        "initialize_seconds": round(初始化, 4),
                        "render_seconds_min": round(min(绘时[:-1]), 4),
                        "render_seconds_max": round(max(绘时[:-1]), 4),
                        "render_seconds_total": round(sum(绘时), 4),
                        "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
                        "pixels_masks_sha256": 摘要.hexdigest(),
                    }
                )
                print(f"[完成] 地图{地图}八视角34场景全像素/掩码/计数一致。", flush=True)
            报告["status"] = "passed"
        except (ValueError, IndexError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    棋盘差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
