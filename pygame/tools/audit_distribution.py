# SPDX-License-Identifier: GPL-3.0-or-later
# 构建实际产物后检查白名单，防止忽略的商业资源或本机部署被源码包收集。
# ◑ 导入
import argparse
import json
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


# ◕ 功能
class 分发审计_类:
    """
    只接受Python源码与列明的项目说明/构建元数据，不展开归档到磁盘。

    更新日志：
    2026.10.25 - 实际发现本地部署被默认sdist收集后建立独立产物验收。
    """

    _说明 = {
        ".gitignore", "AGENTS.md", "LICENSE", "NOTICE.md", "README.md",
        "pyproject.toml", "uv.lock", "PKG-INFO",
    }
    _轮子元数据 = {"METADATA", "WHEEL", "entry_points.txt", "RECORD", "LICENSE", "NOTICE.md"}

    @classmethod
    def api_检查(cls, arg_目录: Path) -> dict[str, int | str]:
        wheels, sources = list(arg_目录.glob("*.whl")), list(arg_目录.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sources) != 1:
            raise ValueError("需且仅需一个wheel及一个sdist")
        with zipfile.ZipFile(wheels[0]) as archive:
            names = [n for n in archive.namelist() if not n.endswith("/")]
            for name in names:
                path = PurePosixPath(name)
                valid = (
                    path.parts[0] == "rich4" and path.suffix == ".py"
                    or path.parts[0].endswith(".dist-info") and path.name in cls._轮子元数据
                )
                if path.is_absolute() or ".." in path.parts or not valid:
                    raise ValueError(f"wheel包含非源码/元数据：{name}")
        with tarfile.open(sources[0]) as archive:
            members = [m for m in archive.getmembers() if not m.isdir()]
            for member in members:
                path = PurePosixPath(member.name)
                parts = path.parts[1:]
                valid = (
                    len(parts) == 1 and parts[0] in cls._说明
                    or len(parts) >= 2 and parts[0] in {"src", "tests", "tools"}
                    and path.suffix == ".py"
                )
                if not member.isfile() or path.is_absolute() or ".." in path.parts or not valid:
                    raise ValueError(f"sdist包含非源码/项目元数据：{member.name}")
        return {"status": "passed", "wheel_files": len(names), "sdist_files": len(members)}


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--dist", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    选项 = 参数.parse_args()
    print(json.dumps(分发审计_类.api_检查(选项.dist), ensure_ascii=False))
