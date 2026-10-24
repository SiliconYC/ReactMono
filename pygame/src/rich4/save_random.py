# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/native_game.cpp::Application::load的可选RICH4-RNG-1旁车。
# ◑ 导入
import re
from pathlib import Path


# ◕ 功能
class 随机旁车_类:
    """
    按原C++ uint32流提取数字前缀；可选旁车失败沿用启动种子。

    更新日志：
    2026.10.24 - 保留负数回绕/溢出拒绝/非UTF-8字节；DAT本体仍须严格验证。
    """

    _十进制 = re.compile(rb"([+-]?)([0-9]+)")

    @classmethod
    def api_解码(cls, arg_数据: bytes, arg_缺省: int) -> int:
        parts = arg_数据.split(None, 1)
        if len(parts) != 2 or parts[0] != b"RICH4-RNG-1":
            return arg_缺省
        match = cls._十进制.match(parts[1])
        if match is None:
            return arg_缺省
        digits = match[2].lstrip(b"0") or b"0"
        if len(digits) > 10:
            return arg_缺省
        value = int(digits)
        if value > 0xFFFFFFFF:
            return arg_缺省
        return (-value if match[1] == b"-" else value) & 0xFFFFFFFF

    @classmethod
    def api_读取(cls, arg_路径: Path, arg_缺省: int) -> int:
        try:
            data = arg_路径.read_bytes()
        except OSError:
            # 原ifstream的打开/提取失败只影响可选旁车，不会拒绝已有效的主DAT。
            return arg_缺省
        return cls.api_解码(data, arg_缺省)
