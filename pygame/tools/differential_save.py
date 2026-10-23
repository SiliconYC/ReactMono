# ◑ 导入
import argparse
import hashlib
import json
import subprocess
import tempfile
from dataclasses import astuple
from pathlib import Path

from rich4.save import 存档_类


# ◕ 功能
class 存档差分_类:
    """
    比较真实 DAT 的全部已解读字段、区域划分与每个玩家的字段编辑字节。

    更新日志：
    2026.10.23 - 只在临时目录产生副本，不改写用户原存档。
    """

    @staticmethod
    def _规范输出(arg_存档: 存档_类) -> str:
        头 = arg_存档.api_头()
        行 = [
            " ".join(
                map(
                    str,
                    [
                        头.签名,
                        *头.日期,
                        头.地图,
                        头.阶段,
                        头.人数,
                        头.人类人数,
                        头.当前玩家,
                        头.初始资金,
                        头.物价,
                    ],
                )
            )
        ]
        for 槽位 in range(头.人数):
            字段 = astuple(arg_存档.api_玩家(槽位))
            值 = list(字段[:-2]) + list(字段[-2]) + list(字段[-1])
            行.append(" ".join(map(str, 值)))
        图 = arg_存档.api_地图摘要()
        行.append(" ".join(map(str, [图.字节数, *(v for 表 in 图.表 for v in astuple(表))])))
        类别 = {"decoded": 0, "partially_decoded": 1, "raw_reserved": 2}
        行.extend(f"{r.名称} {r.偏移} {r.长度} {类别[r.类别]}" for r in arg_存档.api_区域())
        return "\n".join(行) + "\n"

    @classmethod
    def api_执行(
        cls,
        arg_源码: Path,
        arg_构建: Path,
        arg_文件: list[Path],
        arg_报告: Path,
    ) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本错误")
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
        工具 = arg_构建.resolve() / "save-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("save_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {"reference": 版本, "status": "running", "files": []}
        try:
            for 文件 in arg_文件:
                原字节 = 文件.read_bytes()
                存档 = 存档_类.api_解码(原字节)
                with tempfile.TemporaryDirectory(prefix="rich4-save-diff-") as 临时:
                    前缀 = Path(临时) / "oracle"
                    cpp = subprocess.run(
                        [str(工具), str(文件), str(前缀)],
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    if cls._规范输出(存档) != cpp.stdout:
                        raise ValueError(f"{文件.name} 已解读字段或区域划分不同")
                    if 存档.api_导出() != Path(str(前缀) + ".roundtrip.dat").read_bytes():
                        raise ValueError(f"{文件.name} 无损输出不同")
                    编辑数 = 0
                    for 槽位 in range(存档.api_头().人数):
                        for i, 金额 in enumerate([0, -1, 123456789, -2147483648, 2147483647]):
                            副本 = 存档_类.api_解码(原字节)
                            副本.api_设现金(槽位, 金额)
                            if 副本.api_导出() != Path(f"{前缀}.{槽位}.{i}.cash.dat").read_bytes():
                                raise ValueError("现金字段写入差分失败")
                            副本.api_设银行(槽位, 金额)
                            if 副本.api_导出() != Path(f"{前缀}.{槽位}.{i}.bank.dat").read_bytes():
                                raise ValueError("银行字段写入差分失败")
                            编辑数 += 2
                报告["files"].append(
                    {
                        "name": 文件.name,
                        "input_sha256": hashlib.sha256(原字节).hexdigest(),
                        "bytes": len(原字节),
                        "edited_outputs_compared": 编辑数,
                        "decoded_fields_and_regions_identical": True,
                    }
                )
            报告["status"] = "passed"
        except (ValueError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print(f"[完成] {len(arg_文件)} 份存档字段、区域、无损输出与编辑输出一致。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    参数.add_argument("files", nargs="+", type=Path)
    选项 = 参数.parse_args()
    存档差分_类.api_执行(选项.source, 选项.build, 选项.files, 选项.report)
