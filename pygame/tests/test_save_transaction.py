# SPDX-License-Identifier: GPL-3.0-or-later
# 所有世界字节来自合法自然对局；损坏样本只用于文件协议错误，不代替游戏规则。
# ◑ 导入
import hashlib
import json
import os
import selectors
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from rich4.save_transaction import 存档事务_类


# ◕ 功能
class 事务测试_类:
    """
    真实子进程I/O驾驶、强杀及字节预期；不向运行时代码添加测试开关。

    更新日志：
    2026.10.25 - 提交点前后、首次保存和二次恢复均用独立进程核对。
    """

    @staticmethod
    def api_启动(
        arg_模式: str,
        arg_路径: Path,
        arg_新档: Path,
        arg_种子: int,
    ) -> subprocess.Popen[str]:
        return subprocess.Popen(
            [
                sys.executable, str(Path(__file__).with_name("save_crash_worker.py")),
                arg_模式, str(arg_路径), str(arg_新档), str(arg_种子),
            ],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

    @staticmethod
    def api_消息(arg_进程: subprocess.Popen[str]) -> dict[str, str | bool | int]:
        with selectors.DefaultSelector() as selector:
            selector.register(arg_进程.stdout, selectors.EVENT_READ)
            assert selector.select(5), "子进程未及时到达I/O边界"
        line = arg_进程.stdout.readline()
        assert line, arg_进程.stderr.read()
        return json.loads(line)

    @staticmethod
    def _记录(
        arg_路径: Path,
        arg_模式: str,
        arg_记录: dict[str, str | bool | int],
    ) -> None:
        with (arg_路径.parent / "process-results.jsonl").open("a") as stream:
            stream.write(json.dumps({"mode": arg_模式, **arg_记录}) + "\n")

    @classmethod
    def api_驾驶(
        cls,
        arg_模式: str,
        arg_路径: Path,
        arg_新档: Path,
        arg_种子: int,
        arg_强杀点: int = -1,
        arg_预期哈希: str | None = None,
    ) -> list[dict[str, str | bool | int]]:
        process = cls.api_启动(arg_模式, arg_路径, arg_新档, arg_种子)
        trace = []
        try:
            while True:
                record = cls.api_消息(process)
                if "done" in record:
                    assert process.wait(timeout=5) == 0, process.stderr.read()
                    if arg_模式 != "write":
                        assert record["seed"] == arg_种子
                    if arg_预期哈希 is not None:
                        assert record["dat_sha256"] == arg_预期哈希
                    cls._记录(arg_路径, arg_模式, {"returncode": 0, **record})
                    return trace
                trace.append(record)
                if len(trace) - 1 == arg_强杀点:
                    process.kill()
                    assert process.wait(timeout=5) == -signal.SIGKILL
                    cls._记录(arg_路径, arg_模式, {"returncode": -signal.SIGKILL, **record})
                    return trace
                process.stdin.write("c")
                process.stdin.flush()
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()

    @classmethod
    def api_新进程读取(
        cls,
        arg_路径: Path,
        arg_新档: Path,
        arg_预期: tuple[bytes, int],
    ) -> None:
        cls.api_驾驶(
            "read", arg_路径, arg_新档, arg_预期[1],
            arg_预期哈希=hashlib.sha256(arg_预期[0]).hexdigest(),
        )

    @staticmethod
    def api_准备(
        arg_目录: Path,
        arg_旧对: tuple[bytes, int] | None,
        arg_新对: tuple[bytes, int],
    ) -> tuple[Path, Path]:
        arg_目录.mkdir()
        path, new = arg_目录 / "Save1.DAT", arg_目录 / "new.DAT"
        if arg_旧对 is not None:
            存档事务_类(path).api_写入(*arg_旧对)
        new.write_bytes(arg_新对[0])
        return path, new


@pytest.mark.assets
def test_事务保持原DAT和旁车字节且普通读取不写来源目录(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data, seed = 自然存档[0]
    path = tmp_path / "original.DAT"
    path.write_bytes(data)
    Path(str(path) + ".rng").write_text(f"RICH4-RNG-1 {seed}\n")
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}

    def 禁止写目录(
        self: Path,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        pytest.fail("普通原DAT读取不应创建事务或锁目录")

    with monkeypatch.context() as local:
        local.setattr(Path, "mkdir", 禁止写目录)
        assert 存档事务_类(path).api_读取(17) == (data, seed)
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()} == before
    target = tmp_path / "Save1.DAT"
    存档事务_类(target).api_写入(data, seed)
    assert target.read_bytes() == data
    assert Path(str(target) + ".rng").read_bytes() == f"RICH4-RNG-1 {seed}\n".encode()
    assert {p.name for p in tmp_path.iterdir() if p.is_file()} == {
        "original.DAT", "original.DAT.rng", "Save1.DAT", "Save1.DAT.rng",
    }
    assert {p.name for p in 存档事务_类(target)._目录.iterdir()} == {"lock"}


@pytest.mark.assets
@pytest.mark.parametrize("arg_已有", (False, True))
def test_真实强杀每个持久化边界后新进程只见提交前旧对或提交后新对(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
    arg_已有: bool,
) -> None:
    old, new = 自然存档
    previous = old if arg_已有 else None
    path, source = 事务测试_类.api_准备(tmp_path / "probe", previous, new)
    points = 事务测试_类.api_驾驶("write", path, source, new[1])
    assert any(not p["committed"] for p in points) and any(p["committed"] for p in points)
    assert len(points) >= 20
    for index, point in enumerate(points):
        path, source = 事务测试_类.api_准备(tmp_path / f"case-{index}", previous, new)
        trace = 事务测试_类.api_驾驶("write", path, source, new[1], index)
        assert trace == points[:index + 1]
        expected = new if point["committed"] else previous
        if expected is None:
            with pytest.raises(FileNotFoundError):
                存档事务_类(path).api_读取(17)
            assert not path.exists() and not Path(str(path) + ".rng").exists(), point
        else:
            事务测试_类.api_新进程读取(path, source, expected)
            assert 存档事务_类(path).api_读取(17) == expected, point
            assert path.read_bytes() == expected[0]
            assert Path(str(path) + ".rng").read_bytes() == f"RICH4-RNG-1 {expected[1]}\n".encode()
    (tmp_path / "crash-boundaries.json").write_text(json.dumps(points, indent=2) + "\n")


@pytest.mark.assets
def test_恢复本身在每个持久化边界再被强杀仍可恢复同一新对(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
) -> None:
    old, new = 自然存档
    path, source = 事务测试_类.api_准备(tmp_path / "probe", old, new)
    writes = 事务测试_类.api_驾驶("write", path, source, new[1])
    committed = next(i for i, p in enumerate(writes) if p["committed"])
    path, source = 事务测试_类.api_准备(tmp_path / "recovery-probe", old, new)
    事务测试_类.api_驾驶("write", path, source, new[1], committed)
    points = 事务测试_类.api_驾驶("recover", path, source, new[1])
    assert len(points) >= 14 and all(p["committed"] for p in points)
    for index, point in enumerate(points):
        path, source = 事务测试_类.api_准备(tmp_path / f"recover-{index}", old, new)
        事务测试_类.api_驾驶("write", path, source, new[1], committed)
        trace = 事务测试_类.api_驾驶("recover", path, source, new[1], index)
        assert trace == points[:index + 1]
        事务测试_类.api_新进程读取(path, source, new)
        assert 存档事务_类(path).api_读取(17) == new, point
    (tmp_path / "recovery-boundaries.json").write_text(json.dumps(points, indent=2) + "\n")


@pytest.mark.assets
def test_被杀进程释放槽锁且活进程锁等待有界(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old, new = 自然存档
    path, source = 事务测试_类.api_准备(tmp_path / "locked", old, new)
    process = 事务测试_类.api_启动("hold", path, source, new[1])
    try:
        assert 事务测试_类.api_消息(process)["point"] == "locked"
        with monkeypatch.context() as local:
            local.setattr(存档事务_类, "_锁等待秒", 0.03)
            with pytest.raises(TimeoutError):
                存档事务_类(path).api_写入(*new)
            with pytest.raises(TimeoutError):
                存档事务_类(path).api_读取(17)
        assert path.read_bytes() == old[0]
    finally:
        process.kill()
        assert process.wait(timeout=5) == -signal.SIGKILL
        事务测试_类._记录(
            path, "hold", {"returncode": -signal.SIGKILL, "point": "locked", "committed": False}
        )
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
    存档事务_类(path).api_写入(*new)
    assert 存档事务_类(path).api_读取(17) == new


@pytest.mark.assets
@pytest.mark.parametrize("arg_阶段", ("prepare", "journal", "dat", "rng"))
def test_IO错误不丢失已提交日志且下一次能恢复(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
    monkeypatch: pytest.MonkeyPatch,
    arg_阶段: str,
) -> None:
    old, new = 自然存档
    path = tmp_path / "Save1.DAT"
    transaction = 存档事务_类(path)
    transaction.api_写入(*old)
    原替换, 原同步 = os.replace, os.fsync

    def 替换(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        name = Path(dst).name
        if (
            arg_阶段 == "journal" and name == "pending.json"
            or arg_阶段 == "dat" and Path(dst) == path
            or arg_阶段 == "rng" and name == "Save1.DAT.rng"
        ):
            raise OSError("注入实际替换错误")
        原替换(src, dst)

    def 同步(fd: int) -> None:
        if arg_阶段 == "prepare":
            raise OSError("注入准备文件同步错误")
        原同步(fd)

    with monkeypatch.context() as local:
        local.setattr(os, "replace", 替换)
        local.setattr(os, "fsync", 同步)
        with pytest.raises(OSError, match="注入"):
            transaction.api_写入(*new)
    expected = old if arg_阶段 in ("prepare", "journal") else new
    assert transaction.api_读取(17) == expected


@pytest.mark.assets
@pytest.mark.parametrize("arg_已有", (False, True))
def test_首次并发写入恰好跨过无日志检查时读者不会返回混合对(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
    monkeypatch: pytest.MonkeyPatch,
    arg_已有: bool,
) -> None:
    old, new = 自然存档
    path = tmp_path / "Save1.DAT"
    if arg_已有:
        path.write_bytes(old[0])
        Path(str(path) + ".rng").write_text(f"RICH4-RNG-1 {old[1]}\n")
    original = Path.read_bytes
    fired = False

    def 读取(self: Path) -> bytes:
        nonlocal fired
        if self != path or fired:
            return original(self)
        fired = True
        try:
            data = original(self)
        except FileNotFoundError:
            存档事务_类(path).api_写入(*new)
            raise
        存档事务_类(path).api_写入(*new)
        return data

    with monkeypatch.context() as local:
        local.setattr(Path, "read_bytes", 读取)
        assert 存档事务_类(path).api_读取(17) == new


@pytest.mark.assets
@pytest.mark.parametrize(
    "arg_错误", ("json", "type", "version", "base64", "checksum", "path", "field-type")
)
def test_损坏已提交日志明确拒绝且读写都不覆盖原主文件(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
    monkeypatch: pytest.MonkeyPatch,
    arg_错误: str,
) -> None:
    old, new = 自然存档
    path = tmp_path / "Save1.DAT"
    transaction = 存档事务_类(path)
    transaction.api_写入(*old)
    original = os.replace

    def 替换(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        if Path(dst) == path:
            raise OSError("在提交后替换主文件之前中断")
        original(src, dst)

    with monkeypatch.context() as local:
        local.setattr(os, "replace", 替换)
        with pytest.raises(OSError):
            transaction.api_写入(*new)
    journal = transaction._待提交
    record = json.loads(journal.read_text())
    if arg_错误 == "json":
        journal.write_text("{")
    elif arg_错误 == "type":
        journal.write_text("[]")
    else:
        key, value = {
            "version": ("format", "unknown-version"),
            "base64": ("dat_base64", "%%%"),
            "checksum": ("rng_sha256", "0" * 64),
            "path": ("target", "../other.DAT"),
            "field-type": ("dat_base64", 42),
        }[arg_错误]
        record[key] = value
        journal.write_text(json.dumps(record))
    bad = journal.read_bytes()
    for operation in (lambda: transaction.api_读取(17), lambda: transaction.api_写入(*old)):
        with pytest.raises(ValueError):
            operation()
        assert path.read_bytes() == old[0]
        assert Path(str(path) + ".rng").read_bytes() == f"RICH4-RNG-1 {old[1]}\n".encode()
        assert journal.read_bytes() == bad


@pytest.mark.assets
@pytest.mark.parametrize("arg_旁车", (False, True))
def test_目标为符号链接在提交前拒绝且不改链接指向文件(
    tmp_path: Path,
    自然存档: tuple[tuple[bytes, int], tuple[bytes, int]],
    arg_旁车: bool,
) -> None:
    old, new = 自然存档
    path = tmp_path / "Save1.DAT"
    transaction = 存档事务_类(path)
    transaction.api_写入(*old)
    target = Path(str(path) + ".rng") if arg_旁车 else path
    real = tmp_path / "original-copy"
    real.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(real)
    before = real.read_bytes()
    with pytest.raises(ValueError, match="符号链接"):
        transaction.api_写入(*new)
    assert target.is_symlink() and real.read_bytes() == before
    assert not transaction._待提交.exists()
