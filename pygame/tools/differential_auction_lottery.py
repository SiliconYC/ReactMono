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
from rich4.auction_room_screen import 拍卖室_类
from rich4.flc import 动画_类
from rich4.game_types import 决策_类, 决策种类_类, 决策选项_类
from rich4.graphics import 图像_类
from rich4.lottery_bar_screen import 彩票告别_类, 彩票柜台_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.screen_draw import 屏幕宿主_类
from rich4.world import 世界_类
from rich4.world_options import 新局设置_类


# ◕ 功能
class 拍卖彩票差分_类:
    """
    原拍卖/彩票组件的实际图片、霓虹、完整私有等待状态与回调对照。

    更新日志：
    2026.10.24 - 语音回调返回明确时长，不冒充实际听感或完整核心触发。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path) -> None:
        self.字体, self.美术 = 字体_类(arg_字体), 美术_类(arg_素材)
        exe = next(p for p in arg_素材.iterdir() if p.name.lower() == "rich4.exe")
        text = 原版文字_类(原版程序_类.api_读取(exe))
        self.框 = 画框_类(图像_类(0, 0, []), self.美术, self.字体, [])
        self.调用: list[tuple[int, int]] = []
        self.宿 = 屏幕宿主_类(self.框, lambda n: self.调用.append((0, n)))
        self.拍卖, self.彩票, self.告别 = 拍卖室_类(), 彩票柜台_类(text), 彩票告别_类()
        movie = 动画_类(self.美术.api_解码("p", 14))
        frames = self.彩票._霓虹帧(self.美术)
        if len(frames) != movie.帧数 or not frames[0].像素:
            raise ValueError("霓虹预检未完整解码")
        self.霓虹数, self.时长 = len(frames), 0

    def _答(self, arg_i: int) -> None:
        self.调用.append((1, arg_i))

    def _再见(self, arg_买: bool) -> int:
        self.调用.append((2, int(arg_买)))
        return self.时长

    @staticmethod
    def _串(arg_文: str) -> list[int]:
        data = arg_文.encode()
        h = 14695981039346656037
        for b in data:
            h = ((h ^ b) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return [len(data), h]

    def _操作(self, arg_行: str, arg_步: int) -> tuple[str, bytes]:
        op, *列 = arg_行.split()
        self.调用.clear()
        框, 宿 = self.框, self.宿
        old = self.世.api_导出() if op in ("D", "F", "L", "X") else None
        if op == "N":
            m, ch = map(int, 列)
            opt = 新局设置_类(地图=m % 4, 阶段=m // 4)
            for i, p in enumerate(opt.玩家):
                p.角色 = (ch + 3 * i) % 12
            self.世 = 世界_类.api_从地图(self.美术.api_解码("m", m * 2 + 1), opt)
            self.拍卖.api_重置()
            self.告别.api_清空()
            self.决 = 决策_类(决策种类_类.购地, 0)
            框.按钮.clear()
        elif op == "B":
            kind, player, land, price, mask, count, *values = map(int, 列)
            if len(values) != count:
                raise ValueError("决策选项数不符")
            self.决 = 决策_类(
                决策种类_类(kind),
                player,
                地产=land,
                金额=price,
                不活跃玩家=mask,
                选项=[决策选项_类("", v) for v in values],
            )
        elif op == "W":
            pool, level, owner, mask = map(int, 列)
            self.世.公共基金 = pool
            if len(self.世.地产) > 1:
                self.世.地产[1].经济.等级, self.世.地产[1].经济.业主 = level, owner
            if len(self.世.设施) > 1:
                self.世.设施[1].业主 = owner
            self.世.彩票 = [i % 5 if mask else 0 for i in range(36)]
        elif op == "S":
            winner, price, land = map(int, 列)
            self.拍卖.api_成交(winner, price, land)
        elif op == "R":
            self.拍卖.api_重置()
        elif op in ("D", "F", "L"):
            t, x, y, down, instant, has, voice, self.时长 = map(int, 列)
            框.时钟, 框.指针x, 框.指针y, 框.按下, 宿.即时 = t, x, y, bool(down), bool(instant)
            框.画布 = 图像_类(640, 480, [(i * 1103515245 + arg_步) & 65535 for i in range(307200)])
            框.按钮.clear()
            if op == "D":
                self.拍卖.api_绘制(宿, self.世, self.决, self._答)
            elif op == "F":
                self.拍卖.api_画成交(宿, self.世)
            else:
                self.彩票.api_绘制(
                    宿,
                    self.世,
                    self.决,
                    self._答,
                    self.告别 if has else None,
                    self._再见 if voice else None,
                )
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
            raise ValueError("拍卖/彩票界面改变世界DAT")
        b, sold, bye = self.拍卖._出价, self.拍卖._成交, self.告别
        数 = [-1, int(b is not None)]
        if b is not None:
            数 += self._串(b.键) + [b.索引, b.行动, b.价格, b.开始]
        数 += [int(sold is not None)]
        if sold is not None:
            数 += [sold.赢家, sold.价格, sold.地产, sold.开始, int(sold.已响)]
        数 += [int(bye.选项 is not None)]
        if bye.选项 is not None:
            数.append(bye.选项)
        数 += [bye.号码, bye.开始, bye.语音毫秒, self.霓虹数, len(框.按钮)]
        for b in 框.按钮:
            数 += [b.编号, *b.区域, int(b.启用), int(b.点击声音)]
        数 += [len(self.调用)]
        for c in self.调用:
            数 += list(c)
        像 = b""
        if op in ("D", "F", "L"):
            raw = array("H", 框.画布.像素)
            if byteorder != "little":
                raw.byteswap()
            像 = raw.tobytes()
        return " ".join(map(str, 数)), 像

    @staticmethod
    def _命令() -> list[str]:
        组 = []
        for m in range(8):
            for level in range(6):
                组 += [
                    f"N {m} {level}",
                    f"W 1234567 {level} {level % 5} 0",
                    f"B 13 0 2001 1000 {level % 16} 7 0 1 2 3 4 5 6",
                    "D 100 -1 -1 0 0 1 1 0",
                    "B 13 1 4001 2000 0 3 6 0 2",
                    "D 101 400 220 1 0 1 1 0",
                ]
        for ch in range(12):
            for player in range(4):
                组 += [
                    f"N 0 {ch}",
                    f"B 13 {player} 2001 1000 0 1 1",
                    "D 100 -1 -1 0 0 1 1 0",
                    "X 210",
                ]
                for t in (200, 399, 400, 599, 600, 799, 800, 999, 1000, 1199, 1200):
                    组.append(f"D {t} -1 -1 0 0 1 1 0")
                组 += [f"S {player} 1100 2001"]
                for t in (1, 100, 200, 300, 400, 1749, 1750, 1751, 3499, 3500, 3501):
                    组.append(f"F {t} -1 -1 0 0 1 1 0")
        for action in range(7):
            for instant in (0, 1):
                组 += [
                    "N 0 9",
                    f"B 13 0 2001 5000 0 1 {action}",
                    f"D 0 400 130 1 {instant} 1 1 0",
                    "X 210",
                    f"D 0 -1 -1 0 {instant} 1 1 0",
                    f"D 100 -1 -1 0 {instant} 1 1 0",
                    "X 210",
                    f"D 101 -1 -1 0 {instant} 1 1 0",
                ]
        组 += [
            "N 0 0",
            "S 0 1000 2001",
            "F 0 -1 -1 0 0 1 1 0",
            "S 99 1000 2001",
            "F 1 -1 -1 0 0 1 1 0",
            "S 1 1000 2001",
            "F 2 -1 -1 0 0 1 1 0",
            "X 1650",
            "F 3 -1 -1 0 0 1 1 0",
            "R",
        ]
        for m in range(8):
            for slot in range(4):
                values = [i + 1 for i in range(36) if not i % 5] + [0]
                组 += [
                    f"N {m} {m}",
                    "W 2147483647 0 1 1",
                    f"B 14 {slot} 0 0 0 {len(values)} " + " ".join(map(str, values)),
                ]
                for t in (0, 99, 100, 199, 200, 300, 400, 500, 3499, 3500):
                    组.append(f"L {t} 62 295 0 0 1 1 3500")
                组 += [
                    "X 210",
                    "L 3501 -1 -1 0 0 1 1 3500",
                    "L 6999 -1 -1 0 0 1 1 3500",
                    "L 7000 -1 -1 0 0 1 1 3500",
                ]
        for voice_ms in (0, 1999, 2000, 2001, 3500):
            for has in (0, 1):
                for instant in (0, 1):
                    组 += [
                        "N 0 10",
                        "W 0 0 0 0",
                        "B 14 0 0 0 0 2 1 0",
                        f"L 0 -1 -1 0 {instant} {has} 1 {voice_ms}",
                        "X 211",
                        f"L 1999 -1 -1 0 {instant} {has} 1 {voice_ms}",
                        "X 211",
                        f"L 3500 -1 -1 0 {instant} {has} 1 {voice_ms}",
                    ]
        组 += [
            "N 0 0",
            "B 14 0 0 0 0 1 0",
            "L 0 -1 -1 0 0 1 1 1000",
            "X 210",
            "B 14 0 0 0 0 0",
            "L 1 -1 -1 0 0 1 1 1000",
        ]
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
        工具 = 构 / "auction-lottery-oracle"
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
                str(Path(__file__).with_name("auction_lottery_oracle.cpp")),
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
                "direct original AuctionRoom and lottery bar, real maps and assets, "
                "private timers/farewell states and callbacks, "
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
                    "auction_room_screen.py",
                    "auction_room_draw.py",
                    "auction_room_types.py",
                    "lottery_bar_screen.py",
                    "original_text.py",
                    "screen_draw.py",
                )
            },
            "python_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/auction_room_screen.py").read_bytes()
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
                cpp = 进.stdout.read(614400) if 行[:1] in ("D", "F", "L") else b""
                if 行[:1] in ("D", "F", "L") and len(cpp) != 614400:
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
                raise ValueError("参考拍卖/彩票故障：" + 错)
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
    拍卖彩票差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.font, 选项.report)
