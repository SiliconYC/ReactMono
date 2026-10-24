# SPDX-License-Identifier: GPL-3.0-or-later
# 原Application的DAT/RNG字节不变；日志只补两文件写入中断恢复，不保存任意运行阶段。
# ◑ 导入
import base64
import errno
import hashlib
import json
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from rich4.save_random import 随机旁车_类


# ◕ 功能
class 存档事务_类:
    """
    同槽排他锁、提交前保旧、提交后按JSON日志滚动完成原DAT/RNG两文件。

    更新日志：
    2026.10.25 - 主格式及规则不变；无日志目录的外部读档不创建任何文件。
    """

    _格式 = "RICH4-SAVE-TRANSACTION-1"
    _锁等待秒 = 3.0

    def __init__(self, arg_路径: Path) -> None:
        self._主文件 = arg_路径.absolute()
        self._旁车 = Path(str(self._主文件) + ".rng")
        self._目录 = self._主文件.parent / ("." + self._主文件.name + ".rich4-save")
        self._待提交 = self._目录 / "pending.json"

    @staticmethod
    def _拒绝链接(arg_路径: Path) -> None:
        if arg_路径.is_symlink():
            raise ValueError("存档事务不覆盖符号链接：" + str(arg_路径))

    @classmethod
    def _检查目标(cls, arg_路径: Path) -> None:
        cls._拒绝链接(arg_路径)
        if arg_路径.exists() and not arg_路径.is_file():
            raise ValueError("存档目标不是普通文件：" + str(arg_路径))

    @staticmethod
    def _同步目录(arg_目录: Path) -> None:
        if os.name == "nt":
            # Windows标准库没有目录fsync；这里不宣称断电持久性或跨平台验收。
            return
        fd = os.open(arg_目录, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @contextmanager
    def _锁(self) -> Iterator[None]:
        self._拒绝链接(self._目录)
        self._目录.mkdir(exist_ok=True)
        path = self._目录 / "lock"
        self._拒绝链接(path)
        mode = "rb" if path.exists() and os.name != "nt" else "a+b"
        with path.open(mode) as lock:
            if os.name == "nt":
                import msvcrt

                if not path.stat().st_size:
                    lock.write(b"\0")
                    lock.flush()
            else:
                import fcntl
            until = time.monotonic() + self._锁等待秒
            while True:
                try:
                    if os.name == "nt":
                        lock.seek(0)
                        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as error:
                    if error.errno not in (errno.EACCES, errno.EAGAIN):
                        raise
                    if time.monotonic() >= until:
                        raise TimeoutError(
                            "存档槽正由其它进程使用：" + str(self._主文件)
                        ) from error
                    time.sleep(0.01)
            try:
                yield
            finally:
                if os.name == "nt":
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    @classmethod
    def _持久写(cls, arg_路径: Path, arg_数据: bytes) -> None:
        cls._拒绝链接(arg_路径)
        with arg_路径.open("wb") as stream:
            stream.write(arg_数据)
            stream.flush()
            os.fsync(stream.fileno())

    def _替换主文件(
        self,
        arg_目标: Path,
        arg_临时名: str,
        arg_数据: bytes,
    ) -> None:
        self._拒绝链接(arg_目标)
        staged = self._目录 / arg_临时名
        self._持久写(staged, arg_数据)
        os.replace(staged, arg_目标)
        self._同步目录(arg_目标.parent)

    def _恢复(self) -> None:
        self._拒绝链接(self._待提交)
        if not self._待提交.exists():
            return
        record = json.loads(self._待提交.read_text(encoding="utf-8"))
        fields = {"format", "dat_base64", "rng_base64", "dat_sha256", "rng_sha256"}
        if (
            not isinstance(record, dict)
            or set(record) != fields
            or not all(isinstance(v, str) for v in record.values())
            or record["format"] != self._格式
        ):
            raise ValueError("存档提交日志格式无效：" + str(self._待提交))
        dat = base64.b64decode(record["dat_base64"], validate=True)
        rng = base64.b64decode(record["rng_base64"], validate=True)
        if (
            hashlib.sha256(dat).hexdigest() != record["dat_sha256"]
            or hashlib.sha256(rng).hexdigest() != record["rng_sha256"]
        ):
            raise ValueError("存档提交日志校验失败：" + str(self._待提交))
        self._检查目标(self._主文件)
        self._检查目标(self._旁车)
        # 日志必须保留到两份主文件都替换完成，恢复过程再次被杀仍可重复执行。
        self._替换主文件(self._主文件, "dat.next", dat)
        self._替换主文件(self._旁车, "rng.next", rng)
        self._待提交.unlink()
        self._同步目录(self._目录)

    def api_写入(self, arg_数据: bytes, arg_随机: int) -> None:
        self._主文件.parent.mkdir(parents=True, exist_ok=True)
        with self._锁():
            self._恢复()
            self._检查目标(self._主文件)
            self._检查目标(self._旁车)
            rng = f"RICH4-RNG-1 {arg_随机 & 0xFFFFFFFF}\n".encode("ascii")
            record = {
                "format": self._格式,
                "dat_base64": base64.b64encode(arg_数据).decode("ascii"),
                "rng_base64": base64.b64encode(rng).decode("ascii"),
                "dat_sha256": hashlib.sha256(arg_数据).hexdigest(),
                "rng_sha256": hashlib.sha256(rng).hexdigest(),
            }
            staged = self._目录 / "prepare.json"
            self._持久写(staged, (json.dumps(record, sort_keys=True) + "\n").encode("ascii"))
            self._拒绝链接(self._待提交)
            os.replace(staged, self._待提交)
            self._同步目录(self._目录)
            self._恢复()

    def _读主文件(self, arg_缺省: int) -> tuple[bytes, int]:
        return self._主文件.read_bytes(), 随机旁车_类.api_读取(self._旁车, arg_缺省)

    def _锁内读取(self, arg_缺省: int) -> tuple[bytes, int]:
        with self._锁():
            self._恢复()
            return self._读主文件(arg_缺省)

    def api_读取(self, arg_缺省: int) -> tuple[bytes, int]:
        if self._目录.exists() or self._目录.is_symlink():
            return self._锁内读取(arg_缺省)
        try:
            result = self._读主文件(arg_缺省)
        except OSError:
            if self._目录.exists():
                return self._锁内读取(arg_缺省)
            raise
        # 首次写入可在无目录检查之后开始；保留锁目录使二次检查不会发生ABA。
        if self._目录.exists():
            return self._锁内读取(arg_缺省)
        return result
