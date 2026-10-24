# SPDX-License-Identifier: GPL-3.0-or-later
# 表地址及规范化依据固定tools/screens/message_strings.inc；商业原文仅从外部EXE读取。
# ◑ 导入
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from rich4.native_ui import 原生界面_类


# ◕ 功能
class 原版程序_类:
    """
    只读PE32初始化区与虚拟地址；不加载或执行原程序。

    更新日志：
    2026.10.24 - 兼容原Watcom的零VirtualSize区，所有读取限定于真实文件范围。
    """

    def __init__(self, arg_数据: bytes) -> None:
        self.数据 = arg_数据
        if len(arg_数据) < 64 or arg_数据[:2] != b"MZ":
            raise ValueError("原版程序没有有效MZ头")
        pe = self._数(60, "I")[0]
        self._范围(pe, 24)
        if arg_数据[pe : pe + 4] != b"PE\0\0":
            raise ValueError("原版程序没有有效PE头")
        机器, 区数 = self._数(pe + 4, "HH")
        选长 = self._数(pe + 20, "H")[0]
        self._范围(pe + 24, 选长)
        if 机器 != 0x14C or 选长 < 32 or self._数(pe + 24, "H")[0] != 0x10B:
            raise ValueError("需要原版x86 PE32程序")
        self.基址 = self._数(pe + 52, "I")[0]
        区表 = pe + 24 + 选长
        self._范围(区表, 区数 * 40)
        self.区: list[tuple[int, int, int]] = []
        self.具名区: dict[bytes, tuple[int, int, int]] = {}
        for i in range(区数):
            虚址, 原长, 原偏 = self._数(区表 + 40 * i + 12, "III")
            # .bss有RawSize但RawPointer为零，不可当作文件头读取。
            if not 原偏 or not 原长:
                continue
            self._范围(原偏, 原长)
            区 = self.基址 + 虚址, 原偏, 原长
            self.区.append(区)
            self.具名区[arg_数据[区表 + 40 * i : 区表 + 40 * i + 8].rstrip(b"\0")] = 区

    @classmethod
    def api_读取(cls, arg_路径: Path) -> "原版程序_类":
        return cls(arg_路径.read_bytes())

    def _范围(self, arg_偏: int, arg_长: int) -> None:
        if arg_偏 < 0 or arg_长 < 0 or arg_偏 > len(self.数据) - arg_长:
            raise ValueError("原版程序范围截断或越界")

    def _数(self, arg_偏: int, arg_式: str) -> tuple[int, ...]:
        self._范围(arg_偏, struct.calcsize("<" + arg_式))
        return struct.unpack_from("<" + arg_式, self.数据, arg_偏)

    def _所属(self, arg_地址: int, arg_长: int) -> tuple[int, int]:
        if arg_长 < 0:
            raise ValueError("读取长度不可为负")
        for 虚址, 原偏, 原长 in self.区:
            if 虚址 <= arg_地址 < 虚址 + 原长 and arg_地址 + arg_长 <= 虚址 + 原长:
                return 原偏 + arg_地址 - 虚址, 原偏 + 原长
        raise ValueError(f"原版程序未映射地址或跨区读取：{arg_地址:#x}")

    def api_定位(self, arg_地址: int, arg_长: int = 1) -> int:
        return self._所属(arg_地址, arg_长)[0]

    def api_指针表(self, arg_地址: int, arg_数: int) -> tuple[int, ...]:
        偏 = self.api_定位(arg_地址, arg_数 * 4)
        return self._数(偏, f"{arg_数}I")

    def api_原串(self, arg_地址: int) -> bytes:
        偏, 尾 = self._所属(arg_地址, 1)
        止 = self.数据.find(b"\0", 偏, min(尾, 偏 + 4096))
        if 止 < 0:
            raise ValueError("原版字符串没有区内NUL结束符或超过4096字节")
        return self.数据[偏:止]


@dataclass(frozen=True)
class 台词_类:
    """
    外部商业文字及原Speaking条目号，不包含预置台词。

    更新日志：
    2026.10.24 - 声音0是有效店员语音，缺少台词用None表达。
    """

    声音: int
    文字: str


class 原版文字_类:
    """
    外部原程序角色表和带#NNNN前缀的语音文字索引。

    更新日志：
    2026.10.24 - 保留原空槽；只对参考明确指定的两条卡台词删除自造字。
    """

    # 原股票名称布局并非连续指针表；第八图包含复用地址，不能按字符串顺序猜索引。
    股票地址 = (
        0x46677D,
        0x466786,
        0x46678F,
        0x466798,
        0x4667A1,
        0x4667AA,
        0x4667B3,
        0x4667BC,
        0x4667C5,
        0x4667CE,
        0x4667D7,
        0x4667E0,
        0x4667E9,
        0x4667F2,
        0x4667FB,
        0x466806,
        0x46680F,
        0x466818,
        0x466821,
        0x46682A,
        0x466833,
        0x46683C,
        0x466845,
        0x46684E,
        0x466857,
        0x466860,
        0x466869,
        0x466872,
        0x46687B,
        0x466884,
        0x46688D,
        0x466896,
        0x46689F,
        0x4668A8,
        0x4668B1,
        0x4668B8,
        0x4668C1,
        0x4668CA,
        0x4668D5,
        0x4668DE,
        0x4668E7,
        0x4668F0,
        0x4668F7,
        0x466900,
        0x466909,
        0x466910,
        0x466919,
        0x466920,
        0x466929,
        0x466932,
        0x46693B,
        0x466944,
        0x46694D,
        0x466956,
        0x46695F,
        0x466968,
        0x466971,
        0x46697A,
        0x466985,
        0x46698E,
        0x466999,
        0x4669A2,
        0x4669AB,
        0x4669B4,
        0x4669BB,
        0x4669C2,
        0x4669C9,
        0x4669D0,
        0x4669D7,
        0x4669DE,
        0x4669E5,
        0x4669EC,
        0x4669F5,
        0x4669FE,
        0x466A07,
        0x466A10,
        0x466A19,
        0x466A24,
        0x466A2F,
        0x466A38,
        0x466A43,
        0x466A4E,
        0x466A59,
        0x466A62,
        0x466A6B,
        0x466A74,
        0x466A7D,
        0x466A88,
        0x466A93,
        0x466A9E,
        0x466AA9,
        0x466920,
        0x466AB4,
        0x466910,
        0x466919,
        0x466ABB,
    )

    表 = {"event": (0x48084A, 27), "tool": (0x480D5A, 26), "card": (0x48123A, 90)}
    神明地址 = (
        0x463250,
        0x463295,
        0x4632CC,
        0x46330E,
        0x46336C,
        0x463381,
        0x46338E,
        0x4633C0,
        0x4633F0,
        0x463419,
        0x46344E,
        0x463495,
    )

    def __init__(self, arg_程序: 原版程序_类) -> None:
        self.程序 = arg_程序
        self.配音: dict[int, 台词_类] = {}
        self._表缓存: dict[str, tuple[int, ...]] = {}
        # .reloc含偶然的#2228机器字节；只索引原Watcom静态数据区。
        虚址, 原偏, 原长 = arg_程序.具名区[b"DGROUP"]
        for 匹配 in re.finditer(rb"#([0-9]{4})", arg_程序.数据[原偏 : 原偏 + 原长]):
            行 = self._台词(arg_程序.api_原串(虚址 + 匹配.start()))
            if 行.声音 in self.配音 and self.配音[行.声音] != 行:
                raise ValueError(f"原版语音编号重复且文字不同：{行.声音}")
            self.配音[行.声音] = 行

    @staticmethod
    def _规范(arg_文: bytes, arg_声音: int | None = None) -> str:
        if arg_声音 in (752, 753):
            arg_文 = arg_文.replace(b"\x9d\xdd", b"")
        return 原生界面_类.api_繁中(arg_文).replace("∼", "～").replace("﹒", "．")

    @classmethod
    def _台词(cls, arg_文: bytes) -> 台词_类:
        if len(arg_文) < 5 or arg_文[:1] != b"#" or not arg_文[1:5].isdigit():
            raise ValueError("原版台词缺少#NNNN语音前缀")
        声 = int(arg_文[1:5])
        return 台词_类(声, cls._规范(arg_文[5:], 声))

    def api_配音(self, arg_声音: int, arg_变体: int = 0) -> 台词_类:
        行 = self.配音[arg_声音]
        if arg_变体 == 0:
            return 行
        if arg_声音 == 89 and arg_变体 == 1:
            # voices.hpp保留同一声音的原文与原生银行改写；原EXE只有前者。
            return 台词_类(89, 行.文字.replace("要\n", "預備\n", 1))
        raise ValueError("原版台词没有该参考界面变体")

    def api_神明(self, arg_索引: int) -> str:
        if not 0 <= arg_索引 < len(self.神明地址):
            raise IndexError("神明原文索引越界")
        return self._规范(self.程序.api_原串(self.神明地址[arg_索引]))

    def api_台词(self, arg_表: str, arg_人物: int, arg_槽: int) -> 台词_类 | None:
        地址, 宽 = self.表[arg_表]
        if not 0 <= arg_人物 < 12 or not 0 <= arg_槽 < 宽:
            raise IndexError("原版角色台词索引越界")
        if arg_表 not in self._表缓存:
            self._表缓存[arg_表] = self.程序.api_指针表(地址, 12 * 宽)
        指针 = self._表缓存[arg_表][arg_人物 * 宽 + arg_槽]
        return None if not 指针 else self._台词(self.程序.api_原串(指针))

    def api_原文(self, arg_地址: int) -> str:
        return self._规范(self.程序.api_原串(arg_地址))

    def api_股票(self, arg_索引: int) -> str:
        if not 0 <= arg_索引 < 96:
            raise IndexError("股票原文索引越界")
        return self.api_原文(self.股票地址[arg_索引])

    def _表原文(self, arg_地址: int, arg_数: int, arg_索引: int) -> str:
        if not 0 <= arg_索引 < arg_数:
            raise IndexError("原文指针表索引越界")
        return self.api_原文(self.程序.api_指针表(arg_地址, arg_数)[arg_索引])

    def api_费名(self, arg_索引: int) -> str:
        return self._表原文(0x47517C, 4, arg_索引)

    def api_新闻标题(self, arg_索引: int) -> str:
        return self._表原文(0x475ED8, 6, arg_索引)

    def api_歌曲(self, arg_索引: int) -> str:
        if not 0 <= arg_索引 < 8:
            raise IndexError("乐曲原文索引越界")
        return self.api_原文(0x4635C6 + 13 * arg_索引)
