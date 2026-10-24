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
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.player_info_screen import 玩家查询_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 玩家查询差分_类:
    """
    原玩家资产/地产/股票查询，完整画布与原世界只读边界对照。

    更新日志：
    2026.10.24 - 真实八地图/姓名/美术/字体；显式资产分配夹具不冒充自然对局。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        text = 原版文字_类(原版程序_类.api_读取(exe))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[tuple[int, int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append((0, n)))
        self.屏 = 玩家查询_类(text)

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        框, 屏 = self.框, self.屏
        old = self.世.api_导出() if op in ("D", "X") else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色 = (ch + 3 * i) % 12
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", m * 2 + 1), opt)
            self.屏 = 屏 = 玩家查询_类(屏._原文)
            框.按钮.clear()
        elif op == "V":
            seed = int(列[0])
            self.世.头.物价 = 1 + seed % 5
            for i, d in enumerate(self.世.地产):
                d.经济.业主, d.经济.连锁, d.经济.等级 = 1 + i % 4, int(i % 3 == 0), i % 6
                d.地价, d.每级造价 = 100 + i * 7, 20 + i
                d.到期日 = ((2030 << 16) | ((1 + i % 12) << 8) | (1 + i % 28)) if i % 2 else 0
            for i, d in enumerate(self.世.设施):
                d.业主, d.等级, d.地价, d.到期日 = (
                    1 + i % 4,
                    i % 6,
                    300 + i,
                    (2035 << 16) | (12 << 8) | 31,
                )
            for c in self.世.公司:
                c.业主 = 1 + c.编号 % 4
            for i, p in enumerate(self.世.玩家):
                p.记录.现金, p.记录.银行, p.记录.贷款 = 12345 + 1000 * i, 56789 - 1111 * i, 100 * i
                p.状态.保险天数 = 20 + i
                p.记录.道具 = [(t + i + seed) % 4 for t in range(15)]
                p.记录.卡片 = [(k * 3 + i + seed) % 33 for k in range(15)]
                for s, h in enumerate(p.持仓):
                    h.数量 = (s + 1) * 100 if (s + i + seed) % 4 else 0
                    h.成本位 = 0x41200000
        elif op == "G":
            slot, info, kind, days = map(int, 列)
            self.世.玩家[slot].状态.神明信息 = info
            if info and info <= len(self.世.物件):
                god = self.世.物件[info - 1]
                god.种类, god.剩余天数 = kind, days
        elif op == "O":
            屏.api_打开(int(列[0]))
        elif op == "S":
            屏._页, 屏._分类, 屏._滚动 = map(int, 列)
        elif op == "D":
            t, x, y, down = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下 = t, x, y, bool(down)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            屏.api_绘制(self.宿, self.世, lambda: self.调用.append((1, 0)))
        elif op == "X":
            for b in 框.按钮:
                if b.编号 == int(列[0]) and b.启用:
                    action = b.动作
                    框.按钮.clear()
                    action()
                    break
        else:
            raise ValueError(op)
        if old is not None and old != self.世.api_导出():
            raise ValueError("玩家查询改变世界DAT")
        数 = [-1, 屏._人, 屏._页, 屏._分类, 屏._滚动, len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += list(c)
        像 = b""
        if op == "D":
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        for m in range(8):
            for ch in range(12):
                player = ch % 4
                组 += [
                    f"N {m} {ch}",
                    f"V {ch}",
                    f"O {player}",
                    f"G {player} 1 {1 + ch % 15} {ch * 17}",
                    "D 0 500 20 1",
                    "X 166",
                    "D 1 60 360 1",
                ]
                for category in range(5):
                    组 += [
                        f"X {170 + category}",
                        "D 2 600 430 1",
                        "X 169",
                        "D 3 -1 -1 0",
                        "X 168",
                        "D 4 -1 -1 0",
                    ]
                组 += [
                    "X 167",
                    "D 5 60 430 1",
                    f"X {160 + (player + 1) % 4}",
                    "D 6 -1 -1 0",
                    "X 60",
                ]
        for player in (0, 1, 2, 3, 4, 4294967295):
            组 += ["N 0 3", "V 7", f"O {player}", "D 0 -1 -1 0"]
            for scroll in (0, 1, 10, 99999):
                组 += [f"S 1 0 {scroll}", "D 1 -1 -1 0"]
        for kind in range(16):
            组 += ["N 0 7", "O 0", f"G 0 1 {kind} 255", "D 0 -1 -1 0"]
        组 += ["G 0 999 0 0", "D 0 -1 -1 0", "G 0 0 0 0", "D 0 -1 -1 0"]
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
        工具 = 构 / "player-info-oracle"
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
                str(Path(__file__).with_name("player_info_oracle.cpp")),
                str(arg_源码 / "tools/screens/menus.cpp"),
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
                "direct original PlayerInfo, real maps and world records, "
                "private state and query callbacks, "
                "real sprites, internal state and callbacks; "
                "not actual window/financial rule integration"
            ),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "mode": "base",
            "runtime_sha256": {
                name: hashlib.sha256(
                    Path(__file__).parents[1].joinpath("src/rich4", name).read_bytes()
                ).hexdigest()
                for name in (
                    "player_info_screen.py",
                    "player_info_types.py",
                    "original_text.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/player_info_screen.py").read_bytes()
            ).hexdigest(),
        }
        摘, 输 = hashlib.sha256(), hashlib.sha256()
        try:
            for i, 行 in enumerate(cls._命令()):
                报["last_command"], 报["last_index"] = 行, i
                进.stdin.write((行 + "\n").encode())
                进.stdin.flush()
                实 = 进.stdout.readline().decode().strip()
                if not 实:
                    raise ValueError("C++提前结束：" + 进.stderr.read().decode())
                cpp = 进.stdout.read(614400) if 行[:1] == "D" else b""
                if 行[:1] == "D" and len(cpp) != 614400:
                    raise ValueError("C++画布输出截断")
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
                raise ValueError("参考玩家查询故障：" + 错)
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
    玩家查询差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
