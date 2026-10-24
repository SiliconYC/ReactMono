# SPDX-License-Identifier: GPL-3.0-or-later
# 测试进程只在实际I/O前后等待父进程，不修改正式事务或游戏状态机。
# ◑ 导入
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from rich4.save_transaction import 存档事务_类


# ◕ 功能
class 中断驾驶_类:
    """
    报告真实持久化边界，由父进程选择继续或OS强杀。

    更新日志：
    2026.10.25 - 标记提交点是prepare→pending成功，不从待验文件推导预期结果。
    """

    def __init__(self, arg_已提交: bool) -> None:
        self._已提交 = arg_已提交
        self._同步数 = 0
        self._原同步, self._原替换, self._原删除 = os.fsync, os.replace, os.unlink

    def _边界(self, arg_名字: str) -> None:
        print(json.dumps({"point": arg_名字, "committed": self._已提交}), flush=True)
        if sys.stdin.buffer.read(1) != b"c":
            raise SystemExit("父测试进程已退出")

    def 同步(self, fd: int) -> None:
        self._同步数 += 1
        self._边界(f"fsync-{self._同步数}-before")
        self._原同步(fd)
        self._边界(f"fsync-{self._同步数}-after")

    def 替换(self, src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        label = f"replace-{Path(src).name}-{Path(dst).name}"
        self._边界(label + "-before")
        self._原替换(src, dst)
        if Path(dst).name == "pending.json":
            self._已提交 = True
        self._边界(label + "-after")

    def 删除(self, path: str | os.PathLike[str], *, dir_fd: int | None = None) -> None:
        label = "unlink-" + Path(path).name
        self._边界(label + "-before")
        self._原删除(path, dir_fd=dir_fd)
        self._边界(label + "-after")

    def api_接线(self) -> None:
        os.fsync, os.replace, os.unlink = self.同步, self.替换, self.删除


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("mode", choices=("write", "read", "recover", "hold"))
    参数.add_argument("path", type=Path)
    参数.add_argument("data", type=Path)
    参数.add_argument("seed", type=int)
    选项 = 参数.parse_args()
    事务 = 存档事务_类(选项.path)
    if 选项.mode == "hold":
        with 事务._锁():
            print(json.dumps({"point": "locked", "committed": False}), flush=True)
            sys.stdin.buffer.read(1)
    else:
        if 选项.mode != "read":
            驾驶 = 中断驾驶_类(选项.mode == "recover")
            驾驶.api_接线()
        if 选项.mode == "write":
            事务.api_写入(选项.data.read_bytes(), 选项.seed)
            print(json.dumps({"done": True}), flush=True)
        else:
            数据, 种子 = 事务.api_读取(17)
            print(
                json.dumps(
                    {"done": True, "seed": 种子, "dat_sha256": hashlib.sha256(数据).hexdigest()}
                ),
                flush=True,
            )
