# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_game.cpp::Application::run的桌面事件批次，不绕过真实控件。
# ◑ 导入
import pygame

from rich4.application_types import 应用页面_类
from rich4.game_types import 游戏阶段_类
from rich4.native_ui import 原生界面_类


# ◕ 功能
class 应用输入_类:
    """
    原鼠标按下/释放、开场跳过门控、模态数字板和快捷键的批次派发。

    更新日志：
    2026.10.24 - 首个启用命中后清掉整批旧控件，Pygame位置已由窗口转为逻辑画布坐标。
    """

    def api_输入(self, arg_事件: list[pygame.event.Event]) -> None:
        S = 应用页面_类
        pointer = (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)
        intro_inputs = (
            *pointer,
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.TEXTINPUT,
            pygame.FINGERDOWN,
            pygame.FINGERUP,
            pygame.FINGERMOTION,
            pygame.MOUSEWHEEL,
        )
        for event in arg_事件:
            repeat = event.dict.get("repeat", False)
            if self.开场.api_活跃() and self.页面 == S.游戏:
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    or event.type == pygame.KEYDOWN
                    and not repeat
                ):
                    self.开场按下 = True
                if event.type == pygame.MOUSEBUTTONUP:
                    self.框.按下 = False
                if event.type in (pygame.MOUSEBUTTONUP, pygame.KEYUP) and self.开场按下:
                    self.开场.api_跳过()
                    continue
                if event.type in intro_inputs:
                    continue
            if event.type == pygame.QUIT:
                if self.页面 == S.股票:
                    self.api_关股票()
                elif self.页面 == S.交易:
                    self.api_关交易()
                self.运行 = False
                continue
            if event.type in pointer:
                self.框.指针x, self.框.指针y = event.pos
                motion = event.type == pygame.MOUSEMOTION
                if not motion:
                    self.框.按下 = event.type == pygame.MOUSEBUTTONDOWN
                if self.页面 == S.游戏 and self.会话 is not None:
                    if motion:
                        self.主屏.api_指针移动(*event.pos, bool(event.buttons[0]))
                    elif event.type == pygame.MOUSEBUTTONUP:
                        self.主屏.api_指针释放(*event.pos, event.button == 3)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 3 and self.api_可取消():
                self.按钮.clear()
                self.api_取消()
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 3
                and self.页面 == S.游戏
                and self.会话 is not None
                and not self.消息.api_活跃()
                and self.会话.待决策 is not None
                and self.消息规则.api_是确认(self.会话.待决策)
            ):
                self.按钮.clear()
                self.api_回答(self.api_确认索引(0))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.按钮:
                    if button.启用 and 原生界面_类.api_包含(button.区域, *event.pos):
                        if button.编号 != 95:
                            self.地图弹框 = None
                        action = button.动作
                        if button.点击声音 and button.编号 != 900:
                            self.api_声音(9)
                        self.按钮.clear()
                        action()
                        break
            if (
                event.type == pygame.KEYDOWN
                and not repeat
                and self.页面 == S.游戏
                and self.消息.api_活跃()
            ):
                self.按钮.clear()
                self.消息.api_跳过()
                continue
            if event.type == pygame.KEYDOWN and not repeat:
                self.按钮.clear()
                if self.数字板.api_活跃():
                    self.api_数字键(event.key)
                    continue
                if event.key == pygame.K_ESCAPE:
                    # ESC 只取消当前局部界面，绝不跳回标题或终止活动对局。
                    if self.api_可取消():
                        self.api_取消()
                    continue
                if (
                    event.key in (pygame.K_SPACE, pygame.K_RETURN)
                    and self.页面 == S.游戏
                    and self.会话 is not None
                ):
                    if self.会话.阶段 == 游戏阶段_类.人类待命 and self.呈现.api_可推进():
                        self.会话.api_掷骰()
                    elif self.会话.待决策 is not None and self.呈现.api_可推进():
                        if self.api_地图决策():
                            if self.选目标 is not None:
                                self.api_回答(self.选目标)
                        else:
                            self.api_回答(0)
                if event.key == pygame.K_LEFT and self.页面 == S.游戏:
                    self.api_转图(7)
                if event.key == pygame.K_RIGHT and self.页面 == S.游戏:
                    self.api_转图(1)
                if event.key == pygame.K_v and self.页面 == S.游戏:
                    self.主屏.api_切视图()
                if event.key == pygame.K_F5 and self.会话 is not None and self.会话.api_可保存():
                    self.api_保存()
                if event.key == pygame.K_F9 and self.api_载入路径().exists():
                    self.api_读取(self.api_载入路径())

    def api_数字键(self, arg_键: int) -> None:
        if arg_键 == pygame.K_ESCAPE:
            self.数字板.api_取消(self.api_宿主())
            return
        keypad = {
            key: str(i)
            for i, key in enumerate(
                (
                    pygame.K_KP0,
                    pygame.K_KP1,
                    pygame.K_KP2,
                    pygame.K_KP3,
                    pygame.K_KP4,
                    pygame.K_KP5,
                    pygame.K_KP6,
                    pygame.K_KP7,
                    pygame.K_KP8,
                    pygame.K_KP9,
                )
            )
        }
        if pygame.K_0 <= arg_键 <= pygame.K_9:
            key = chr(ord("0") + arg_键 - pygame.K_0)
        elif arg_键 in keypad:
            key = keypad[arg_键]
        elif arg_键 == pygame.K_BACKSPACE:
            key = "\b"
        elif arg_键 in (pygame.K_RETURN, pygame.K_KP_ENTER):
            key = "\r"
        elif arg_键 in (pygame.K_m, pygame.K_c, pygame.K_h):
            key = chr(arg_键).upper()
        else:
            return
        self.数字板.api_键(self.api_宿主(), key)
