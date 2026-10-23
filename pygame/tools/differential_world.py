# ◑ 导入
import argparse
import hashlib
import json
import subprocess
import tempfile
from copy import deepcopy
from dataclasses import astuple
from pathlib import Path
from typing import TypeAlias

from rich4.assets import 资源包_类
from rich4.save import 存档_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类, 新玩家_类
from rich4.world_validation import 世界验证_类

# ◕ 功能
规范值: TypeAlias = int | bytes | list["规范值"] | tuple["规范值", ...]


class 世界差分_类:
    """
    全部已解读世界值逐项比较，另外比较无损、破产与选定编辑后的存档字节。

    更新日志：
    2026.10.23 - 原 DAT 世界恢复模型跨语言差分。
    """

    @staticmethod
    def _展平(arg_值: 规范值) -> list[int]:
        if isinstance(arg_值, int):
            return [int(arg_值)]
        if isinstance(arg_值, bytes):
            return [len(arg_值), *arg_值]
        return [项 for 值 in arg_值 for 项 in 世界差分_类._展平(值)]

    @classmethod
    def _规范(cls, arg_世: 世界_类) -> list[int]:
        return cls._展平(
            (
                astuple(arg_世.头),
                [astuple(v) for v in arg_世.玩家],
                [astuple(v) for v in arg_世.节点],
                [astuple(v) for v in arg_世.地产],
                [astuple(v) for v in arg_世.设施],
                [astuple(v) for v in arg_世.公司],
                [astuple(v) for v in arg_世.景物],
                arg_世.卡供应,
                arg_世.道具供应,
                arg_世.新闻牌堆,
                arg_世.命运牌堆,
                arg_世.新闻游标,
                arg_世.命运游标,
                arg_世.监狱名单,
                arg_世.医院名单,
                [astuple(v) for v in arg_世.特殊角色],
                [astuple(v) for v in arg_世.物件],
                arg_世.彩票,
                [astuple(v) for v in arg_世.股票],
                [[astuple(v) for v in 行] for 行 in arg_世.出售表],
                arg_世.股史,
                arg_世.股史游标,
                arg_世.股市指数,
                arg_世.股市走势位,
                arg_世.公共基金,
                arg_世.新闻影响天数,
                arg_世.租约模式,
                arg_世.相机旋转,
                arg_世.轮数,
                arg_世.月数,
                arg_世.初始随机状态,
                arg_世.有初始随机状态,
            )
        )

    @classmethod
    def _比一个(
        cls,
        arg_世: 世界_类,
        arg_工具: Path,
        arg_入参: list[str],
    ) -> dict:
        初始哈希 = hashlib.sha256(arg_世.api_导出()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="rich4-world-") as 临时:
            前缀 = Path(临时) / "world"
            cpp = subprocess.run(
                [str(arg_工具), *arg_入参, str(前缀)], text=True, capture_output=True, check=True
            )
            实际 = list(map(int, cpp.stdout.split()))
            预期 = cls._规范(arg_世)
            可玩 = True
            try:
                世界验证_类.api_验证(arg_世)
            except ValueError:
                可玩 = False
            预期.append(int(可玩))
            if 实际 != 预期:
                不同 = next(
                    (i for i, (a, b) in enumerate(zip(实际, 预期)) if a != b),
                    min(len(实际), len(预期)),
                )
                raise ValueError(f"世界字段差分失败，标量位置 {不同}，输入 {arg_入参}")
            if arg_世.api_导出() != Path(str(前缀) + ".roundtrip.dat").read_bytes():
                raise ValueError("世界无损导出不同")
            for 槽位 in range(len(arg_世.玩家)):
                副 = deepcopy(arg_世)
                副.api_清破产字段(槽位)
                if 副.api_导出() != Path(f"{前缀}.bankrupt-{槽位}.dat").read_bytes():
                    raise ValueError("破产清除与 C++ 不同")
            arg_世.玩家[0].记录.银行 = -123
            if len(arg_世.玩家) > 1:
                arg_世.玩家[1].状态.附身炸弹 = 3
            arg_世.股票[2].浮点位[3] = 0x7FC01234
            arg_世.节点[1].x = -32768
            if arg_世.api_导出() != Path(str(前缀) + ".edited.dat").read_bytes():
                raise ValueError("世界选定编辑导出不同")
        return {
            "canonical_scalar_count": len(预期) - 1,
            "playable_validation": 可玩,
            "bankruptcy_exports_compared": len(arg_世.玩家),
            "roundtrip_and_selected_edit_identical": True,
            "initial_export_sha256": 初始哈希,
        }

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_文件: list[Path],
        arg_报告: Path,
        arg_素材: Path | None = None,
    ) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++ 版本不符")
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
        工具 = arg_构建.resolve() / "world-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("world_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {"reference": 版本, "status": "running", "files": [], "new_games": []}
        try:
            for 文件 in arg_文件:
                数据 = 文件.read_bytes()
                世 = 世界_类.api_从存档(存档_类.api_解码(数据))
                行 = cls._比一个(世, 工具, [str(文件)])
                行.update(name=文件.name, input_sha256=hashlib.sha256(数据).hexdigest())
                报告["files"].append(行)
            if arg_素材 is not None:
                地图包 = 资源包_类(arg_素材)
                报告["map_archive_sha256"] = hashlib.sha256(arg_素材.read_bytes()).hexdigest()
                for 图 in range(8):
                    数据 = 地图包.api_解码(图 * 2 + 1)
                    for 种子 in [0, 1, 0xFFFFFFFF]:
                        for 变体 in range(3):
                            设置 = 新局设置_类(地图=图 % 4, 阶段=图 // 4, 随机种子=种子)
                            if 变体 == 1:
                                设置.玩家 = [新玩家_类(11, 1, 1, 1), 新玩家_类(2, 2, 2, 1)]
                                设置.租约模式 = 5
                            elif 变体 == 2:
                                设置.玩家 = [新玩家_类(8, 2)]
                                设置.初始资金 = 123456789
                            世 = 世界_类.api_从地图(数据, 设置)
                            行 = cls._比一个(
                                世, 工具, ["--new", str(arg_素材), str(图), str(种子), str(变体)]
                            )
                            行.update(map=图, seed=种子, variant=变体)
                            报告["new_games"].append(行)
                    print(f"[完成] 地图 {图} 九组完整初始世界差分一致。", flush=True)
            if not arg_文件 and arg_素材 is None:
                raise ValueError("需要原存档或 map.mkf 输入")
            报告["status"] = "passed"
        except (ValueError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print(f"[完成] {len(arg_文件)} 份原档与 {len(报告['new_games'])} 个八图新局差分一致。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    参数.add_argument("--assets", type=Path)
    参数.add_argument("files", nargs="*", type=Path)
    选项 = 参数.parse_args()
    世界差分_类.api_执行(选项.source, 选项.build, 选项.files, 选项.report, 选项.assets)
