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
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.number_pad import 数字板_类
from rich4.screen_draw import 屏幕宿主_类


# ◕ 功能
class 数字板差分_类:
    """
    固定原NumberPad的真实图片、鼠标/键盘/稳定按钮、回调与内部数值对照。

    更新日志：
    2026.10.24 - 1/2倍几何、数额边界、拖尺及可重入确认，不代替金融规则验收。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体 = 字体_类(arg_字体)
        self.框 = 画框_类(图像_类(0, 0, []), 美术_类(arg_素材), self.字体, [])
        self.声音, self.完成 = [], []
        self.宿 = 屏幕宿主_类(self.框, self.声音.append)
        self.板 = 数字板_类()

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.声音.clear()
        self.完成.clear()
        结果 = -1
        板, 框, 宿 = self.板, self.框, self.宿
        if op == "S":
            板.api_缩放(int(列[0]))
        elif op == "O":
            maximum, nxt = map(int, 列)

            def 完成(arg_数: int) -> None:
                self.完成.append(arg_数)
                if nxt >= 0:
                    板.api_打开(nxt, self.完成.append)

            板.api_打开(maximum, 完成)
        elif op == "D":
            框.指针x, 框.指针y, down = map(int, 列)
            框.按下 = bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            板.api_绘制(宿)
        elif op == "K":
            板.api_键(宿, chr(int(列[0]) & 255))
        elif op == "X":
            for b in 框.按钮:
                if b.编号 == int(列[0]) and b.启用:
                    动作 = b.动作
                    框.按钮.clear()
                    动作()
                    break
        elif op == "Q":
            结果 = 板.api_下一键(int(列[0]))
        elif op == "B":
            板.api_取消(宿)
        elif op == "C":
            板.api_关闭()
        elif op == "I":
            结果 = 板.api_数字号(int(列[0]))
        else:
            raise ValueError(op)
        数 = [
            结果,
            int(板._活跃),
            int(板._拖),
            板._x,
            板._y,
            板.api_比例(),
            板.api_提示顶(),
            板.api_上限(),
            板.api_值(),
            板.api_数字(),
            int(板._完成 is not None),
            len(框.按钮),
        ]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.声音), *self.声音, len(self.完成), *self.完成]
        像 = b""
        if op == "D":
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _命令() -> list[str]:
        组 = [f"I {i}" for i in range(-2, 13)]
        for scale in (-1, 1, 2, 3):
            组.append(f"S {scale}")
            for maximum in (-2147483648, -1, 0, 1, 42, 999999999, 2147483647):
                组 += [f"O {maximum} -1", "D -1 -1 0"]
                for code in (49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 255, 63, 8, 67, 72, 77):
                    组 += [f"K {code}", "D -1 -1 0"]
                for target in (-1, 0, 1, 17, 12345, 2147483647):
                    组.append(f"Q {target}")
                组 += ["K 13", "D 0 0 0", "B"]
            组 += ["O 2147483647 50", "K 77", "K 13", "D -1 -1 0", "B", "B"]
            for id in range(900, 917):
                组 += ["O 12345 -1", "D 270 210 1", f"X {id}", "D 500 230 1", "D 500 230 0"]
            for x in (-10, 0, 191, 192, 255, 256, 266, 320, 370, 448, 999):
                组 += ["O 999999999 -1", f"D {x} 210 1", "X 916", f"D {x + 7} 230 1", "D -1 -1 0"]
            组 += ["O 100 -1", "D -1 -1 0", "X 901", "D -1 -1 0"]
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
        工具 = 构 / "number-pad-oracle"
        链 = shlex.split(
            subprocess.check_output(["pkg-config", "--cflags", "--libs", "freetype2"], text=True)
        )
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("number_pad_oracle.cpp")),
                str(arg_源码 / "tools/screens/finance.cpp"),
                str(arg_源码 / "tools/screens/draw.cpp"),
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
            "painted_frames": 0,
            "scope": (
                "direct original NumberPad, explicit keyboard/pointer/id inputs, "
                "real sprites, internal state and callbacks; "
                "not actual window/financial rule integration"
            ),
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/number_pad.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            for i, 行 in enumerate(cls._命令()):
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                cpp = 进.stdout.read(614400) if 行[:1] == "D" else b""
                预, py = 自._操作(行, i)
                if 实 != 预:
                    报["failure_command"] = 行
                    报["cpp"] = 实
                    报["python"] = 预
                    raise ValueError(f"step={i} metadata differs")
                if cpp != py:
                    位 = next(j for j, (a, b) in enumerate(zip(cpp, py)) if a != b)
                    报["failure_command"] = 行
                    raise ValueError(f"step={i} pixel={位 // 2 % 640},{位 // 2 // 640}")
                摘.update(实.encode())
                摘.update(cpp)
                输.update((行 + "\n").encode())
                报["commands"] = i + 1
                报["painted_frames"] += int(bool(cpp))
            进.stdin.close()
            退 = 进.wait()
            错 = 进.stderr.read().decode()
            if 退 or 错:
                raise ValueError("参考数字板故障：" + 错)
            报.update(
                status="passed",
                state_sha256=摘.hexdigest(),
                input_sha256=输.hexdigest(),
                compared_pixels=报["painted_frames"] * 307200,
            )
        except (ValueError, OSError, IndexError, AttributeError) as 错:
            报.update(status="failed", failure=str(错))
            raise
        finally:
            if 进.poll() is None:
                进.terminate()
                进.wait()
            自.字体.api_关闭()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(报))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("source", "build", "assets", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    选项 = 参数.parse_args()
    数字板差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
