# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/native_game.cpp::Application::draw_board的板面构造段；不执行规则。
# ◑ 导入
from collections.abc import Sequence
from dataclasses import dataclass

from rich4.board_models import 场景_类, 相机_类
from rich4.direction import 方向_类
from rich4.effect_player import 电影播放_类
from rich4.effect_scene import 待播人物_类, 演出场景_类
from rich4.game import 游戏会话_类
from rich4.game_types import 效果_类, 效果种类_类, 游戏事件_类, 游戏事件种类_类, 移动动画_类
from rich4.main_screen import 主屏幕_类
from rich4.native_frame import 画框_类


# ◕ 功能
@dataclass
class 表现步_类:
    """
    原PresentationStep的可选事件/电影值，供原顺序队列和板面未提交覆盖共用。

    更新日志：
    2026.10.24 - 原应用每步仅放事件或效果之一，不把两种输出分批播放。
    """

    事件: 游戏事件_类 | None = None
    效果: 效果_类 | None = None


class 主板场景_类:
    """
    原主板面移动插值、待播演员/地产、显示回合和相机优先级。

    更新日志：
    2026.10.24 - 只构造独立Scene；调用方先同步决策，再绘制并推进各表现组件。
    """

    @staticmethod
    def _移动点(arg_动画: 移动动画_类) -> tuple[int, int]:
        m = arg_动画
        return (
            m.起x + 画框_类._零除((m.终x - m.起x) * m.已过毫秒, m.时长毫秒),
            m.起y + 画框_类._零除((m.终y - m.起y) * m.已过毫秒, m.时长毫秒),
        )

    @classmethod
    def api_构建(
        cls,
        arg_会话: 游戏会话_类,
        arg_屏: 主屏幕_类,
        arg_电影: 电影播放_类,
        arg_步骤: Sequence[表现步_类],
        arg_呈现中: bool,
        arg_呈现玩家: int | None,
        arg_旋转: int,
        arg_时: int,
        arg_目标: tuple[int, int] | None = None,
        arg_说话槽: int | None = None,
    ) -> tuple[场景_类, 相机_类]:
        会, 屏, 世 = arg_会话, arg_屏, arg_会话.世界
        屏.api_显示玩家(None if not arg_步骤 and not arg_呈现中 else arg_呈现玩家)
        活 = 世.玩家[屏.api_显示槽位(世)].记录
        帧 = ((arg_时 & 0xFFFFFFFFFFFFFFFF) // 120) % 6
        服装 = tuple(会.api_服装(i) for i in range(4))
        场 = 演出场景_类.api_静止快照(世, arg_时, 服装)
        场.玩家.clear()
        for i, 人 in enumerate(世.玩家):
            记 = 人.记录
            if not 演出场景_类.api_在棋盘(世, 记.槽位):
                continue
            精 = 演出场景_类._人物(世, i, 帧, 会.api_服装(记.槽位))
            精.活跃 = 记.槽位 == 活.槽位
            if 会.动画 is not None and 会.动画.玩家 == 记.槽位:
                m = 会.动画
                精.位置, 精.走动 = cls._移动点(m), True
                if m.终x != m.起x or m.终y != m.起y:
                    精.方向 = 方向_类.api_计算(m.终x - m.起x, m.终y - m.起y)
            投 = 屏.api_投掷帧(记.槽位)
            if 投 is not None:
                精.投骰, 精.动画帧 = True, 投
            场.玩家.append(精)
        待: list[待播人物_类] = []
        for 步 in arg_步骤:
            if 步.效果 is not None:
                演出场景_类.api_加入待播(待, 步.效果)
        演出场景_类.api_应用待播(场.玩家, 世, 待, 帧, 服装)
        for 人 in 场.玩家:
            人.活跃 = 人.槽位 == 活.槽位
        arg_电影.api_设置待播(待)
        for 步 in reversed(arg_步骤):
            e = 步.事件
            if e is None or e.节点 >= len(世.节点):
                continue
            购 = e.种类 == 游戏事件种类_类.已购地
            升 = e.种类 == 游戏事件种类_类.已升级 or (
                e.种类 == 游戏事件种类_类.提示
                and e.消息 in ("福神帮助房屋升级", "神明帮助房屋升级")
            )
            if not 购 and not 升:
                continue
            码 = 世.节点[e.节点].类型索引
            地 = None
            if 2000 < 码 < 4000 and 码 - 2000 <= len(场.地产):
                地 = 场.地产[码 - 2001]
            elif 4000 < 码 < 6000 and 码 - 4000 <= len(场.设施):
                地 = 场.设施[码 - 4001]
            if 地 is not None:
                if 购:
                    地.业主 = 0
                elif 地.等级:
                    地.等级 -= 1
        中心 = (活.x, 活.y)
        for 人 in 场.玩家:
            if 人.活跃:
                中心 = 人.位置
        中心 = 屏.api_相机中心(中心)
        if arg_目标 is not None and 会.待决策 is not None:
            中心 = arg_目标
        if arg_说话槽 is not None and arg_说话槽 < len(世.玩家):
            记 = 世.玩家[arg_说话槽].记录
            中心 = 记.x, 记.y
            for 人 in 场.玩家:
                if 人.槽位 == arg_说话槽:
                    中心 = 人.位置
        场.物件 = 演出场景_类.api_物件(世, 场.玩家, 帧)

        def 隐藏(arg_点: tuple[int, int], arg_种: int) -> bool:
            if arg_电影.api_抛物待落地(arg_点, arg_种):
                return True
            return any(
                步.效果 is not None
                and 步.效果.种类 == 效果种类_类.抛物
                and 步.效果.物件种类 == arg_种
                and (步.效果.目标.x, 步.效果.目标.y) == arg_点
                for 步 in arg_步骤
            )

        演出场景_类.api_隐藏物件(场.物件, 隐藏)
        for 人 in 场.特殊人物:
            if 会.动画 is not None and 会.动画.玩家 == 人.槽位:
                人.位置, 人.走动 = cls._移动点(会.动画), True
        return 场, 相机_类(中心, arg_旋转 & 255)
