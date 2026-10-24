# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import shlex
import subprocess
from array import array
from pathlib import Path
from sys import byteorder

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.message_overlay import 消息_类, 消息声音_类, 消息层_类, 消息种类_类, 消息行_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类, 文字样式_类
from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
class 消息差分_类:
    """
    固定原消息层的完整画布、模态按钮、队列、语音请求及真实时钟边界对照。

    更新日志：
    2026.10.24 - 原CPP仅在研究适配器运行，商业文字和像素不写入公开报告。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.美术, self.字体 = 美术_类(arg_素材), 字体_类(arg_字体)
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.时, self.调用 = 0, []
        self.层 = 消息层_类(消息声音_类(self._说, lambda: self.调用.append(-1)), lambda: self.时)

    def _说(self, arg_号: int) -> int:
        self.调用.append(arg_号)
        return arg_号 * 37 % 3200

    @staticmethod
    def _字(arg_文: str) -> str:
        return arg_文.encode().hex() or "-"

    @staticmethod
    def _解(arg_文: str) -> str:
        return "" if arg_文 == "-" else bytes.fromhex(arg_文).decode()

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        框, 层, 解 = self.框, self.层, self._解
        self.调用.clear()
        框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
        结果 = -1
        if op == "P":
            种, 人, 情, 图, 声, 最少, 等待, 焦, x, 照 = map(int, 列[:10])
            项 = 消息_类(
                消息种类_类(种),
                None if 焦 < 0 else 焦,
                人,
                情,
                解(列[10]),
                图,
                声,
                最少,
                bool(等待),
                x,
                照,
                解(列[11]),
            )
            for i in range(int(列[12])):
                偏 = 13 + i * 3
                项.行.append(消息行_类(int(列[偏]), int(列[偏 + 1]), 解(列[偏 + 2])))
            层.api_入队(项)
        elif op == "A":
            self.时 = int(列[0])
        elif op == "B":
            框.时钟 = self.时
            结果 = int(层.api_绘制(框))
        elif op == "R":
            层.api_退休()
        elif op == "C":
            层.api_清空()
        elif op == "K":
            层.api_跳过()
        elif op == "S":
            层.api_即时(bool(int(列[0])))
        elif op == "H":
            for b in 框.按钮:
                if b.编号 == int(列[0]):
                    动作 = b.动作
                    框.按钮.clear()
                    动作()
                    break
        elif op == "Y":
            模式, x, y, 框.指针x, 框.指针y = map(int, 列[:5])
            框.按钮.clear()
            是, 否 = lambda: self.调用.append(71), lambda: self.调用.append(72)
            if 模式:
                层.api_确认框(框, 解(列[5]), 71, 是, 72, 否)
            else:
                层.api_确认条(框, x, y, 71, 是, 72, 否)
        elif op == "T":
            模, x, y, 大小, 旗 = map(int, 列[:5])
            式 = 文字样式_类(大小, 层.近白, bool(旗 & 2), bool(旗 & 1), bool(旗 & 4), 层.近黑)
            层.api_文字(框, 解(列[5]), x, y, 模, 式)
        else:
            raise ValueError(op)
        数 = [
            结果,
            self.时,
            int(层.api_活跃()),
            层.api_焦点() if 层.api_焦点() is not None else -1,
            int(层._已开始),
            int(层._即时),
            层._截止,
            self._字(层._最后气泡),
            len(层._照片缓存),
            len(层._队列),
        ]
        for 项 in 层._队列:
            数 += [
                int(项.种类),
                项.焦点 if 项.焦点 is not None else -1,
                项.人物,
                项.情绪,
                项.图语,
                项.声音,
                项.最少毫秒,
                int(项.等待声音),
                项.框x,
                项.照片,
                self._字(项.文字),
                self._字(项.标题),
                len(项.行),
            ]
            for 行 in 项.行:
                数 += [行.人物, 行.头像帧, self._字(行.文字)]
        数.append(len(框.按钮))
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用), *self.调用]
        像 = array("H", 框.画布.像素)
        if byteorder != "little":
            像.byteswap()
        return " ".join(map(str, 数)), 像.tobytes()

    def _命令(self, arg_素材: Path) -> list[str]:
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        文 = 原版文字_类(原版程序_类.api_读取(exe))
        组, 字 = [], self._字

        def 入(arg_项: 消息_类) -> None:
            项 = arg_项
            焦 = -1 if 项.焦点 is None else 项.焦点
            行 = " ".join(f"{r.人物} {r.头像帧} {字(r.文字)}" for r in 项.行)
            组.append(
                f"P {int(项.种类)} {项.人物} {项.情绪} {项.图语} {项.声音} {项.最少毫秒} "
                f"{int(项.等待声音)} {焦} {项.框x} {项.照片} "
                f"{字(项.文字)} {字(项.标题)} {len(项.行)} {行}"
            )

        for 人 in range(12):
            for 情 in range(4):
                组.append("C")
                行 = 文.api_台词("event", 人, 情)
                入(消息_类(人物=人, 情绪=情, 文字=行.文字, 声音=行.声音, 焦点=人 % 4))
                组 += ["B", "B", "H 900"]
        for 图 in range(1, self.美术.api_帧数("d", 519) + 1):
            入(消息_类(人物=11, 情绪=图 % 4, 图语=图, 声音=2000 + 图))
            组 += ["B", "K"]
        for x in (-30, 220, 320, 650):
            入(消息_类(消息种类_类.对话框, 文字="Aa\n\n大富翁4", 框x=x))
            组 += ["B", "K"]
        for i in range(36):
            项 = 消息_类(
                消息种类_类.新闻,
                文字=文.api_配音(149 + i).文字,
                声音=149 + i,
                等待声音=True,
                最少毫秒=2400,
                照片=441 + i,
                标题="大富翁4",
            )
            项.行 = [
                消息行_类((i + j) % 12, 3 if i % 2 else 4, f"{j * 100}" if i % 2 else "")
                for j in range(4)
            ]
            入(项)
            组 += ["B", "K"]
        照片 = (
            477,
            478,
            479,
            480,
            481,
            482,
            483,
            484,
            485,
            486,
            487,
            488,
            489,
            490,
            491,
            492,
            493,
            494,
            495,
            496,
            497,
            497,
            497,
            498,
            498,
            499,
            500,
            501,
            501,
            501,
            502,
            503,
            504,
            505,
            506,
            507,
            508,
            505,
            509,
            510,
            511,
            512,
            506,
            507,
            513,
            514,
            515,
            510,
            516,
        )
        for i, 照 in enumerate(照片):
            入(消息_类(消息种类_类.命运, 人物=i % 12, 文字=文.api_配音(185 + i).文字, 照片=照))
            组 += ["B", "K"]
        for i in range(12):
            入(消息_类(消息种类_类.神明字幕, 文字=文.api_神明(i)))
            组 += ["B", "K"]
        for 模 in (0, 4, 5, 7, 9):
            for 旗 in range(8):
                for t in ("", "Aa\n\n大富翁4", "🀄"):
                    组.append(f"T {模} 220 130 {16 if 旗 % 2 else 28} {旗} {字(t)}")
        for 模 in (0, 1):
            for x, y in ((220, 320), (320, 240), (-20, 20)):
                for px, py in (
                    (-1, -1),
                    (162, 286),
                    (219, 320),
                    (220, 320),
                    (277, 353),
                    (278, 354),
                ):
                    组 += [f"Y {模} {x} {y} {px} {py} {字('Aa 大富翁4')}", "H 71", "H 72"]
        组 += ["C", "S 0", "A 100"]
        for 声, 等待 in ((77, True), (78, False), (0, True)):
            入(消息_类(消息种类_类.对话框, 声音=声, 最少毫秒=1000, 等待声音=等待))
            组 += [
                "R",
                "B",
                "B",
                f"A {100 + max(1000, 声 * 37 % 3200 if 等待 else 0) - 1}",
                "R",
                "B",
                f"A {100 + max(1000, 声 * 37 % 3200 if 等待 else 0)}",
                "R",
                "A 100",
            ]
        for _ in range(2):
            入(消息_类(声音=1777, 文字="A"))
        组 += ["B", "K", "C"]
        入(消息_类(声音=1777, 文字="B"))
        组 += ["B", "S 1"]
        入(消息_类(消息种类_类.对话框))
        组 += ["R", "B", "R", "B", "C", "K"]
        return 组

    @classmethod
    def api_执行(
        cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_字体: Path, arg_报告: Path
    ) -> None:
        版 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        构 = arg_构建.resolve()
        头 = 构 / "message-overlay-shim/SDL3/SDL_timer.h"
        头.parent.mkdir(parents=True, exist_ok=True)
        头.write_text(
            '#pragma once\n#include <cstdint>\nextern "C" std::uint64_t SDL_GetTicks();\n'
        )
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        工具 = 构 / "message-overlay-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(头.parents[1]),
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("message_overlay_oracle.cpp")),
                str(arg_源码 / "tools/screens/messages.cpp"),
                str(构 / "librich4_core.a"),
                *链,
                "-liconv",
                "-o",
                str(工具),
            ],
            check=True,
        )
        自 = cls(arg_素材, arg_字体)
        进 = subprocess.Popen(
            [str(工具), str(arg_素材), str(arg_字体)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        报 = {
            "reference": 版,
            "status": "running",
            "commands": 0,
            "scope": ("direct original Overlay, explicit Items/clock/audio callbacks, "
                      "actual external assets/font; not gameplay or desktop/audio acceptance"),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/message_overlay.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            组 = 自._命令(arg_素材)
            for i, 行 in enumerate(组):
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                像 = 进.stdout.read(614400)
                预, py = 自._操作(行, i)
                if 实 != 预:
                    raise ValueError(f"step={i} op={行[:1]} metadata differs")
                if 像 != py:
                    位 = next(k for k, (a, b) in enumerate(zip(像, py)) if a != b)
                    raise ValueError(f"step={i} op={行[:1]} pixel={位 // 2 % 640},{位 // 2 // 640}")
                摘.update(像)
                摘.update(实.encode())
                输.update((行 + "\n").encode())
                报["commands"] = i + 1
                if not i % 100:
                    arg_报告.parent.mkdir(parents=True, exist_ok=True)
                    arg_报告.write_text(json.dumps(报, indent=2) + "\n")
            进.stdin.close()
            退出 = 进.wait()
            错误 = 进.stderr.read().decode()
            if 退出 or 错误:
                raise ValueError("参考消息层故障：" + 错误)
            报.update(
                status="passed",
                state_sha256=摘.hexdigest(),
                input_sha256=输.hexdigest(),
                complete_canvas_pixels=len(组) * 307200,
            )
        except (ValueError, OSError, IndexError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            if 进.poll() is None:
                进.terminate()
                进.wait()
            自.字体.api_关闭()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, indent=2) + "\n")
        print(json.dumps(报))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    消息差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
