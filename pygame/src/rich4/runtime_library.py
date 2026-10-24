# SPDX-License-Identifier: GPL-3.0-or-later
# 仅定位公开SDL/FluidSynth依赖；不定位或装载C++参考引擎。
# ◑ 导入
import ctypes.util
import os
import sys
from pathlib import Path


# ◕ 功能
class 本地运行库_类:
    """
    显式配置优先，随后使用游戏自身.local/lib，最后查询系统安装。

    更新日志：
    2026.10.24 - 项目私有部署无需依赖研究缓存路径或进程外素材配置。
    """

    @staticmethod
    def api_选择(
        arg_名字: str,
        arg_环境: str,
        arg_显式: Path | None = None,
    ) -> str | None:
        if arg_显式 is not None:
            return str(arg_显式)
        configured = os.environ.get(arg_环境)
        if configured is not None:
            return configured
        filename = (
            f"{arg_名字}.dll"
            if sys.platform == "win32"
            else f"lib{arg_名字}.dylib"
            if sys.platform == "darwin"
            else f"lib{arg_名字}.so"
        )
        local = Path(__file__).resolve().parents[2] / ".local/lib" / filename
        if local.is_file():
            return str(local)
        return ctypes.util.find_library(arg_名字)
