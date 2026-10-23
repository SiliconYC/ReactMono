# SPDX-License-Identifier: GPL-3.0-or-later
# 原小游戏独立Pygame验收入口，使用真实规则和原资源；不替代主游戏会话。
# ◑ 导入
import argparse
import hashlib
import io
import json
import time
from pathlib import Path

import pygame

from rich4.artwork import 美术_类
from rich4.minigame_presentation import 小游戏演出_类
from rich4.minigames import 声音请求_类, 小游戏种类_类
from rich4.viewport import 视口_类


# ◕ 功能
class 小游戏窗口_类:
    """
    原640×480小游戏画布、真实鼠标、外部WAV/MIDI与可审计事件日志。

    更新日志：
    2026.10.23 - 固定步长/机器人只供开发验收，主游戏仍待GameSession接回。
    """

    @staticmethod
    def api_执行(
        arg_素材: Path,
        arg_游戏: int,
        arg_种子: int,
        arg_人物: int,
        arg_静音: bool,
        arg_自动: bool,
        arg_固定: int,
        arg_上限: int,
        arg_日志: Path | None,
        arg_截图: Path | None,
    ) -> None:
        美术 = 美术_类(arg_素材)
        if arg_固定 < 0 or arg_上限 < 0:
            raise ValueError("验收步长和帧数不能为负")
        日志 = arg_日志.open("w") if arg_日志 else None
        声缓存: dict[int, pygame.mixer.Sound] = {}
        循环, 当前音, 声数 = None, None, 0
        pygame.display.init()
        if not arg_静音:
            pygame.mixer.init(48000, -16, 2, 512)
            pygame.mixer.set_num_channels(32)
            pygame.mixer.set_reserved(1)
            循环 = pygame.mixer.Channel(0)
            名 = f"midi{13 - arg_游戏:02d}.mid"
            路 = next((p for p in arg_素材.iterdir() if p.name.lower() == 名), None)
            if 路 is None:
                raise ValueError(f"缺少小游戏音乐：{名}")
            pygame.mixer.music.load(str(路))
            pygame.mixer.music.set_volume(0.28)
            pygame.mixer.music.play(-1)
        pygame.display.set_caption("Rich4 Pygame — Original Mini-game Verification")
        窗口 = pygame.display.set_mode((640, 480), pygame.RESIZABLE)

        def 声音(arg_声: 声音请求_类) -> None:
            nonlocal 当前音, 声数
            声数 += 1
            if arg_静音:
                return
            if arg_声.操作 == 2:
                循环.stop()
                当前音 = None
                return
            if arg_声.音效 not in 声缓存:
                声 = pygame.mixer.Sound(file=io.BytesIO(美术.api_解码("e", arg_声.音效)))
                声.set_volume(0.6)
                声缓存[arg_声.音效] = 声
            if arg_声.操作 == 0:
                声缓存[arg_声.音效].play()
            elif 当前音 != arg_声.音效:
                循环.play(声缓存[arg_声.音效], loops=-1)
                当前音 = arg_声.音效

        演 = 小游戏演出_类(美术, 小游戏种类_类(arg_游戏), arg_种子, arg_人物, 声音, arg_自动)
        时钟, 前时, 计, 运行 = pygame.time.Clock(), time.monotonic_ns() // 1000000, 0, True
        上阶段, 已图 = -1, False
        待记: list[dict] = [
            {
                "event": "ready",
                "game": arg_游戏,
                "seed": arg_种子,
                "character": arg_人物,
                "silent": arg_静音,
                "bot": arg_自动,
                "fixed_ms": arg_固定,
            }
        ]
        try:
            while 运行:
                视口 = 视口_类(*窗口.get_size())
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        待记.append({"event": "close"})
                        运行 = False
                    elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                        待记.append({"event": "key", "key": "escape"})
                        运行 = False
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        逻辑点 = 视口.api_逻辑位置(e.pos)
                        待记.append({"event": "click", "logical": 逻辑点})
                        if 逻辑点:
                            演.api_点击(*逻辑点)
                    elif e.type == pygame.VIDEORESIZE:
                        待记.append({"event": "resize", "size": 窗口.get_size()})
                现在 = time.monotonic_ns() // 1000000
                dt, 前时 = arg_固定 or (现在 - 前时), 现在
                点 = 视口.api_逻辑位置(pygame.mouse.get_pos())
                图, 果 = 演.api_帧(dt, 点[0] if 点 else -1, bool(pygame.mouse.get_pressed()[0]))
                布 = pygame.image.frombytes(图.api_RGBA(), (640, 480), "RGBA")
                窗口.fill((0, 0, 0))
                x, y, 宽, 高 = 视口.矩形
                窗口.blit(pygame.transform.scale(布, (宽, 高)), (x, y))
                pygame.display.flip()
                if int(演.逻辑.阶段) != 上阶段:
                    上阶段 = int(演.逻辑.阶段)
                    待记.append({"event": "stage", "stage": 上阶段})
                if 果:
                    待记.append({"event": "result", "score": 果.分数, "draws": 果.随机次数})
                    运行 = False
                if 日志 and 待记:
                    摘 = hashlib.sha256(图.api_RGBA()).hexdigest()
                    for 项 in 待记:
                        项.update(
                            frame=计,
                            score=演.逻辑.api_得分(),
                            draws=演.逻辑.随机.次数,
                            random_state=演.逻辑.随机.随机.状态,
                            sound_requests=声数,
                            canvas_sha256=摘,
                        )
                        日志.write(json.dumps(项, ensure_ascii=False) + "\n")
                    日志.flush()
                待记.clear()
                if arg_截图 and not 已图 and 演.逻辑.阶段.value >= 2:
                    pygame.image.save(布, arg_截图)
                    已图 = True
                计 += 1
                if arg_上限 and 计 >= arg_上限:
                    运行 = False
                时钟.tick(60)
        finally:
            演.api_关闭()
            if 日志:
                日志.close()
            pygame.mixer.quit()
            pygame.display.quit()


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--game", choices=("penguin", "balloon", "catcher"), default="penguin")
    参数.add_argument("--seed", type=int, default=42)
    参数.add_argument("--character", type=int, default=0)
    参数.add_argument("--silent", action="store_true")
    参数.add_argument("--auto", action="store_true")
    参数.add_argument("--fixed-ms", type=int, default=0)
    参数.add_argument("--frames", type=int, default=0)
    参数.add_argument("--log", type=Path)
    参数.add_argument("--screenshot", type=Path)
    选项 = 参数.parse_args()
    小游戏窗口_类.api_执行(
        选项.assets,
        ("penguin", "balloon", "catcher").index(选项.game),
        选项.seed,
        选项.character,
        选项.silent,
        选项.auto,
        选项.fixed_ms,
        选项.frames,
        选项.log,
        选项.screenshot,
    )
