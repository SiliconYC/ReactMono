# SPDX-License-Identifier: GPL-3.0-or-later
# 开发验收：实际应用绘制/按钮/输入/核心完整路径，非OS桌面操作，不篡改游戏状态。
# ◑ 导入
import argparse
import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path

import pygame

from rich4.application import 游戏应用_类
from rich4.application_types import 应用设置_类, 应用页面_类
from rich4.game_types import 决策种类_类, 游戏事件种类_类, 游戏阶段_类
from rich4.services import 服务_类


# ◕ 功能
class 应用重放_类:
    """
    原控件驱动的加速图形流程，按已存在合法选项选择，不改资金/骰子/随机/结果。

    更新日志：
    2026.10.24 - 每帧实际绘图；输入为Pygame事件批次，不当作真人或OS点击验收。
    """

    @staticmethod
    def api_执行(
        arg_素材: Path,
        arg_字体: Path,
        arg_输出: Path,
        arg_地图: int,
        arg_种子: int,
        arg_天数: int,
        arg_帧上限: int,
        arg_观察: Callable[[str, 游戏应用_类], None] | None = None,
        arg_浏览页面: bool = False,
        arg_正常流程: bool = False,
        arg_存读: bool = False,
        arg_读档: Path | None = None,
    ) -> None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        arg_输出.mkdir(parents=True, exist_ok=True)
        app = 游戏应用_类(
            应用设置_类(
                arg_素材,
                arg_字体,
                arg_输出 / "saves",
                种子=arg_种子,
                日期=(5, 10, 2026),
                地图=arg_地图,
                输出=arg_输出,
                静音=True,
                验证天数=0 if arg_正常流程 else arg_天数,
            )
        )
        report = {
            "status": "running",
            "scope": "actual application software drawing and Pygame event batches; "
            + (
                "normal flow with virtual clock, animations and interactive minigames"
                if arg_正常流程
                else "reference fast replay mode"
            )
            + "; no OS desktop or listening proof",
            "map": arg_地图,
            "seed": arg_种子,
            "requested_days": arg_天数,
            "frames": 0,
            "inputs": [],
            "screens": [],
            "decisions": [],
        }
        capture_keys = set()
        trace = hashlib.sha256()
        pygame.display.init()
        pygame.display.set_mode((640, 480), pygame.HIDDEN)
        try:
            if arg_读档 is not None:
                if not app.api_读取(arg_读档):
                    raise ValueError("跨进程应用重放无法读档")
                report["load_sha256"] = hashlib.sha256(arg_读档.read_bytes()).hexdigest()
                if arg_观察 is not None:
                    arg_观察("L " + json.dumps(str(arg_读档.resolve()), ensure_ascii=False), app)
            stall = 0
            last_progress = None
            shop_attempted: set[int] = set()
            shop_wanted: dict[int, int] = {}
            shop_confirming = False
            toolbar = [75, 76, 77, 78, 79, 80, 71, 72, 81, 82] if arg_浏览页面 else []
            toolbar_index, closing = 0, False
            step_ms = 100 if arg_正常流程 else 500
            for frame in range(arg_帧上限):
                image = app.api_绘制(frame * step_ms)
                if arg_观察 is not None:
                    arg_观察(f"D {frame * step_ms}", app)
                ids = {b.编号 for b in app.按钮 if b.启用}
                chosen = None
                page, S = app.页面, 应用页面_类
                report["screens"] = sorted(set(report["screens"]) | {int(page)})
                key = f"screen-{int(page)}"
                if app.会话 is not None and app.会话.待决策 is not None:
                    kind = int(app.会话.待决策.种类)
                    report["decisions"] = sorted(set(report["decisions"]) | {kind})
                    key = f"decision-{kind}"
                if key not in capture_keys:
                    capture_keys.add(key)
                    pygame.image.save(
                        pygame.image.frombytes(image.api_RGBA(), (640, 480), "RGBA"),
                        arg_输出 / (key + ".png"),
                    )
                if page == S.菜单 and app.会话 is None:
                    chosen = 4 if arg_地图 >= 4 else 1
                elif page == S.新局:
                    if app.新局.api_地图() != arg_地图 % 4:
                        chosen = 30 + arg_地图 % 4
                    elif not app.新局.api_人选():
                        chosen = 20
                    elif not app.新局.api_忙():
                        chosen = 40
                elif arg_存读 and closing and page in (S.保存, S.读取):
                    chosen = 531 if page == S.保存 else 521
                    closing = False
                elif closing and (app.帮助.api_活跃() or page != S.游戏):
                    app.api_输入(
                        [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, repeat=False)]
                    )
                    if arg_观察 is not None:
                        arg_观察("K 27", app)
                    report["inputs"].append([frame, int(page), "Escape"])
                    closing = False
                elif app.数字板.api_活跃():
                    d = app.会话.待决策 if app.会话 is not None else None
                    target = (
                        min(100, d.金额上限)
                        if d is not None and d.种类 == 决策种类_类.初级股票
                        else 1000
                    )
                    chosen = app.数字板.api_下一键(target)
                elif app.会话 is not None and app.呈现.api_可推进():
                    session = app.会话
                    if session.完成天数 >= arg_天数 or session.阶段 == 游戏阶段_类.结束:
                        report.update(
                            status="passed",
                            completed_days=session.完成天数,
                            finished=session.阶段 == 游戏阶段_类.结束,
                            random_state=session.随机.状态,
                            world_sha256=hashlib.sha256(session.世界.api_导出()).hexdigest(),
                            events={str(int(k)): v for k, v in sorted(app.事件计数.items())},
                        )
                        break
                    if session.阶段 == 游戏阶段_类.人类待命:
                        if toolbar_index < len(toolbar):
                            chosen = toolbar[toolbar_index]
                            toolbar_index += 1
                            closing = True
                        else:
                            chosen = 100
                    elif session.待决策 is not None:
                        d = session.待决策
                        if d.种类 == 决策种类_类.银行:
                            app.api_输入(
                                [
                                    pygame.event.Event(
                                        pygame.KEYDOWN, key=pygame.K_ESCAPE, repeat=False
                                    )
                                ]
                            )
                            if arg_观察 is not None:
                                arg_观察("K 27", app)
                            report["inputs"].append([frame, int(page), "Escape"])
                        elif d.种类 == 决策种类_类.商店:
                            turn = app.事件计数[游戏事件种类_类.回合开始]
                            leave = next(i for i, o in enumerate(d.选项) if o.值 == 0)
                            if turn not in shop_attempted:
                                player = session.世界.玩家[d.玩家].记录
                                for i, option in enumerate(d.选项):
                                    v = option.值
                                    if (
                                        100 < v <= 130
                                        and player.点券 >= 服务_类.卡价[v - 101]
                                        and sum(c != 0 for c in player.卡片) < 15
                                    ) or (
                                        200 < v <= 213
                                        and player.点券 >= 服务_类.道具价[v - 201]
                                        and player.道具[v - 201] < 9
                                    ):
                                        shop_wanted[turn] = v
                                        break
                                shop_attempted.add(turn)
                            pending = app.物品.api_商店待选()
                            wanted = pending if pending is not None else shop_wanted.get(turn)
                            index = next((i for i, o in enumerate(d.选项) if o.值 == wanted), leave)
                            chosen = 210 + index
                            if chosen not in ids and 280 in ids:
                                chosen = 280
                            elif pending is not None:
                                shop_confirming = True
                        elif app.设施.api_接管(d):
                            chosen = 207 if 207 in ids else 210
                        elif app.api_地图决策():
                            chosen = 207 if 207 in ids else 210
                        elif d.种类 == 决策种类_类.彩票 and app.彩票告别.选项 is not None:
                            pass
                        elif 210 in ids:
                            chosen = 210
                        elif 208 in ids:
                            chosen = 208
                        elif 900 in ids:
                            chosen = 900
                        elif 902 in ids:
                            chosen = 902
                        else:
                            raise ValueError(
                                "待决策无已接线合法控件：" + d.提示 + " " + str(sorted(ids))
                            )
                if chosen is not None:
                    button = next((b for b in app.按钮 if b.编号 == chosen and b.启用), None)
                    if button is None:
                        raise ValueError(f"未找到启用控件{chosen}：{sorted(ids)}")
                    a, b, c, d = button.区域
                    position = ((a + c) // 2, (b + d) // 2)
                    app.api_输入(
                        [
                            pygame.event.Event(t, button=1, pos=position)
                            for t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)
                        ]
                    )
                    if shop_confirming:
                        shop_wanted.pop(turn, None)
                        shop_confirming = False
                    if arg_观察 is not None:
                        arg_观察(f"I {chosen}", app)
                    report["inputs"].append([frame, int(page), chosen])
                app.api_推进(step_ms)
                if arg_观察 is not None:
                    arg_观察(f"U {step_ms}", app)
                if app.会话 is not None:
                    session = app.会话
                    trace.update(session.世界.api_导出())
                    trace.update(
                        str((int(session.阶段), session.完成天数, session.随机.状态)).encode()
                    )
                    progress = (
                        session.完成天数,
                        session.世界.头.当前玩家,
                        int(session.阶段),
                        session.随机.状态,
                        app.页面,
                        tuple(sorted(ids)),
                    )
                    stall = stall + 1 if progress == last_progress else 0
                    last_progress = progress
                    if stall > (1000 if arg_正常流程 else 100):
                        raise ValueError("实际应用重放停滞：" + str(progress))
                report["frames"] = frame + 1
                if frame % 128 == 0:
                    (arg_输出 / "report.json").write_text(
                        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
                    )
                    print(
                        f"[信息] 应用重放{frame}帧，"
                        + str(app.会话.完成天数 if app.会话 else 0)
                        + "日。",
                        flush=True,
                    )
            if report["status"] != "passed":
                raise ValueError("应用重放达到帧上限")
            report["state_sha256"] = trace.hexdigest()
            report["visited_toolbar"] = toolbar[:toolbar_index]
        except (ValueError, RuntimeError, AttributeError, OSError) as error:
            report.update(
                status="failed", failure=str(error), buttons=[b.编号 for b in app.按钮 if b.启用]
            )
            if app.会话 is not None:
                (arg_输出 / "failure.DAT").write_bytes(app.会话.世界.api_导出())
            raise
        finally:
            app.api_关闭()
            pygame.quit()
            (arg_输出 / "report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            )
        print(json.dumps(report, ensure_ascii=False))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--font", type=Path, required=True)
    参数.add_argument("--output", type=Path, required=True)
    参数.add_argument("--map", type=int, default=0)
    参数.add_argument("--seed", type=int, default=123)
    参数.add_argument("--days", type=int, default=3)
    参数.add_argument("--frames", type=int, default=10000)
    参数.add_argument("--exercise-screens", action="store_true")
    参数.add_argument("--normal-flow", action="store_true")
    参数.add_argument("--exercise-save", action="store_true")
    参数.add_argument("--load", type=Path)
    选项 = 参数.parse_args()
    应用重放_类.api_执行(
        选项.assets,
        选项.font,
        选项.output,
        选项.map,
        选项.seed,
        选项.days,
        选项.frames,
        arg_浏览页面=选项.exercise_screens,
        arg_正常流程=选项.normal_flow,
        arg_存读=选项.exercise_save,
        arg_读档=选项.load,
    )
