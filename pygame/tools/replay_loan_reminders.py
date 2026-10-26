# SPDX-License-Identifier: GPL-3.0-or-later
# 验收专用局面注入；正式会话/结算/绘图/输入均使用原应用，不改生产默认值。
# ◑ 导入
import argparse
import hashlib
import json
import os
from pathlib import Path

import pygame

from rich4.application import 游戏应用_类
from rich4.application_types import 应用设置_类
from rich4.calendar import 日期_类
from rich4.loan_notice import 贷款提醒_类
from rich4.new_game_types import 新局选择_类
from rich4.world_options import 新玩家_类


# ◕ 功能
class 贷款回放_类:
    """
    真实应用中的可重复贷款界面回放，截图与测试存档只写本机忽略目录。

    更新日志：
    2026.10.26 - 检查提醒、确认阻塞、缺席、真实收款和还清后的摘要移除。
    """

    def __init__(self, arg_素材: Path, arg_字体: Path, arg_输出: Path) -> None:
        self.素材, self.字体, self.输出 = arg_素材, arg_字体, arg_输出
        self.输出.mkdir(parents=True, exist_ok=True)
        self.报告: list[dict[str, str | int | bool]] = []

    def _截图(self, arg_应用: 游戏应用_类, arg_名称: str, arg_时: int) -> None:
        图 = arg_应用.api_绘制(arg_时)
        pygame.image.save(
            pygame.image.frombytes(图.api_RGBA(), (640, 480), "RGBA"),
            self.输出 / (arg_名称 + ".png"),
        )

    def _场景(
        self,
        arg_名称: str,
        arg_天数: int,
        arg_缺席: str,
        arg_现金: int,
        arg_存款: int,
    ) -> None:
        应用 = 游戏应用_类(
            应用设置_类(
                self.素材,
                self.字体,
                self.输出 / "saves",
                种子=123,
                日期=(1, 10, 2026),
                静音=True,
            )
        )
        try:
            应用.api_新局(
                新局选择_类(
                    玩家=[新玩家_类(10, 1), 新玩家_类(3, 1), 新玩家_类(0, 2), 新玩家_类(6, 2)]
                )
            )
            应用.开场.api_跳过()
            应用.消息.api_清空()
            应用.呈现.步骤.clear()
            会 = 应用.会话
            世 = 会.世界
            人 = 世.玩家[0]
            人.记录.贷款, 人.记录.现金, 人.记录.银行 = 50000, arg_现金, arg_存款
            期 = 日期_类(2026, 10, 1).api_加天数(arg_天数)
            人.状态.贷款到期 = (期.年 << 16) | (期.月 << 8) | 期.日
            if arg_缺席:
                setattr(人.状态, arg_缺席, 5)
            # 加速仅发生在此验收局面；由正式回合入口产生真实预警/收款事件。
            会._开始回合()
            文 = ""
            for 帧 in range(1000):
                时 = 帧 * 100
                应用.api_观察()
                应用.api_绘制(时)
                项 = 应用.消息.api_当前()
                if 项 is not None and 项.需确认:
                    文 = 项.文字
                    self._截图(应用, arg_名称, 时)
                    break
                if 项 is not None:
                    应用.api_输入([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
                应用.api_推进(100)
            else:
                raise ValueError("未到达贷款提醒：" + arg_名称)
            前 = 世.api_导出(), 会.随机.状态
            应用.api_推进(100)
            应用.api_绘制(时 + 60000)
            if 应用.消息.api_当前().文字 != 文 or (世.api_导出(), 会.随机.状态) != 前:
                raise ValueError("待确认通知未阻塞正式会话")
            应用.api_输入([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
            if 应用.消息.api_活跃():
                raise ValueError("确认后通知未关闭")
            if arg_天数 == 0:
                if 人.记录.贷款 or 人.状态.贷款到期:
                    raise ValueError("到期未实际清零贷款")
                if arg_现金 + arg_存款 >= 50000:
                    if 人.记录.现金 + 人.记录.银行 != arg_现金 + arg_存款 - 50000:
                        raise ValueError("到期真实扣款额错误")
                elif 人.记录.控制标志:
                    raise ValueError("到期资金不足未触发真实破产")
            else:
                for 视图 in range(3):
                    应用.主屏.视图 = 视图
                    self._截图(应用, f"{arg_名称}-persistent-{视图}", 时 + 60001)
                if 贷款提醒_类.api_读取(世, 0) is None:
                    raise ValueError("确认后常驻贷款信息丢失")
                if arg_现金 + arg_存款 >= 50000:
                    if not 会._还款(50000, True):
                        raise ValueError("真实还款入口未接受合法全额还款")
                    if 贷款提醒_类.api_读取(世, 0) is not None:
                        raise ValueError("还清后仍展示贷款")
                    self._截图(应用, arg_名称 + "-repaid", 时 + 60002)
                else:
                    路 = self.输出 / (arg_名称 + ".DAT")
                    路.write_bytes(世.api_导出())
                    路.with_suffix(".DAT.rng").write_text(f"RICH4-RNG-1 {会.随机.状态}\n")
                    if not 应用.api_读取(路):
                        raise ValueError("实际应用未能读回临期贷款存档")
                    应用.api_观察()
                    已载 = 应用.消息.api_当前()
                    if 已载 is None or not 已载.需确认 or "贷款剩余" not in 已载.文字:
                        raise ValueError("读档当天漏掉临期提醒")
                    self._截图(应用, arg_名称 + "-loaded", 时 + 60003)
            self.报告.append(
                {
                    "scenario": arg_名称,
                    "days": arg_天数,
                    "absence": arg_缺席,
                    "message": 文,
                    "confirmation_blocks": True,
                    "world_sha256": hashlib.sha256(世.api_导出()).hexdigest(),
                    "random_state": 会.随机.状态,
                }
            )
        finally:
            应用.api_关闭()

    def api_执行(self) -> None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        pygame.display.init()
        pygame.display.set_mode((640, 480), pygame.HIDDEN)
        try:
            for 场景 in (
                ("15-days-funded", 15, "", 30000, 30000),
                ("7-days-shortfall", 7, "", 1000, 2000),
                ("3-days-hospital", 3, "医院天数", 1000, 2000),
                ("1-day-prison", 1, "监狱天数", 1000, 2000),
                ("due-collected", 0, "", 30000, 30000),
                ("due-bankrupt", 0, "", 1000, 2000),
            ):
                self._场景(*场景)
            (self.输出 / "report.json").write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "scope": "injected scenarios, actual game rules/rendering/Pygame input; "
                        "not natural long play or OS desktop interaction",
                        "scenarios": self.报告,
                    },
                    ensure_ascii=False,
                    indent=2,
                ) + "\n"
            )
        finally:
            pygame.quit()


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--font", type=Path, required=True)
    参数.add_argument("--output", type=Path, required=True)
    选项 = 参数.parse_args()
    贷款回放_类(选项.assets, 选项.font, 选项.output).api_执行()
