# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/effects.cpp::EffectPlayer；独立Python时序/绘制，素材外部只读。
# ◑ 导入
import logging
import math
from collections import deque
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field

from rich4.artwork import 美术_类
from rich4.board_models import 地产外观_类, 场景_类, 玩家精灵_类, 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.effect_scene import 待播人物_类, 演出场景_类
from rich4.effect_spec import 演出规格_类, 演员模式_类
from rich4.flc import 动画_类
from rich4.game import 游戏会话_类
from rich4.game_types import 效果_类, 效果种类_类
from rich4.graphics import 图像_类
from rich4.native_ui import 原生界面_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass
class _播放_类:
    """
    原Playing逐电影私有状态，解码帧与规则世界分离。

    更新日志：
    2026.10.24 - 保留未开始的工程车烟帧、抛物路径和单次声音标志。
    """

    效果: 效果_类
    规格: 演出规格_类
    影片: 动画_类 | None = None
    帧图: 图像_类 = field(default_factory=lambda: 图像_类(0, 0, []))
    已过: int = 0
    间隔: int = 100
    已响: bool = False
    路径: list[tuple[int, int]] = field(default_factory=list)


class 电影播放_类:
    """
    原EffectPlayer的空闲快照、顺序播放、提交帧、精灵抛物及神明末帧保留。

    更新日志：
    2026.10.24 - 规则已结算时只修改独立场景，破损素材仅跳过当前电影并明确记录。
    """

    视口 = (0, 40, 440, 480)

    def __init__(self, arg_美术: 美术_类) -> None:
        self.美术 = arg_美术
        self._跳过 = False
        self._队列: deque[效果_类] = deque()
        self._当前: _播放_类 | None = None
        self._留帧: _播放_类 | None = None
        self._快照: 场景_类 | None = None
        self._快照所有者: 游戏会话_类 | None = None
        self._影片数据: dict[tuple[str, int], bytes] = {}
        self._服装 = (0, 0, 0, 0)
        self._待播人物: list[待播人物_类] = []

    def api_跳过(self, arg_跳过: bool) -> None:
        self._跳过 = arg_跳过

    def api_活跃(self) -> bool:
        return self._当前 is not None or bool(self._队列)

    def api_保留中(self) -> bool:
        return self._留帧 is not None

    def api_丢弃末帧(self) -> None:
        self._留帧 = None

    def api_服装(self, arg_服装: tuple[int, int, int, int]) -> None:
        self._服装 = arg_服装

    def api_设置待播(self, arg_待播: list[待播人物_类]) -> None:
        self._待播人物 = deepcopy(arg_待播)

    def api_记忆(self, arg_世: 世界_类, arg_会话: 游戏会话_类, arg_时钟: int) -> None:
        if self.api_活跃():
            return
        self._快照 = 演出场景_类.api_静止快照(arg_世, arg_时钟, self._服装)
        self._快照所有者 = arg_会话

    def api_入队(self, arg_效果: list[效果_类], arg_会话: 游戏会话_类) -> None:
        if not arg_效果:
            return
        if arg_会话 is not self._快照所有者:
            self.api_清空()
            self._快照所有者 = arg_会话
        if self._跳过:
            return
        for 效果 in deepcopy(arg_效果):
            if (
                效果.种类 in (效果种类_类.抛物, 效果种类_类.抛卡, 效果种类_类.神明离开)
                or 演出规格_类.api_查询(效果).资源 >= 0
            ):
                self._队列.append(效果)

    def api_抛物待落地(self, arg_点: tuple[int, int], arg_种: int) -> bool:
        def 匹配(arg_效: 效果_类) -> bool:
            return (
                arg_效.种类 == 效果种类_类.抛物
                and arg_效.物件种类 == arg_种
                and (arg_效.目标.x, arg_效.目标.y) == arg_点
            )

        return bool(self._当前 is not None and 匹配(self._当前.效果)) or any(
            匹配(e) for e in self._队列
        )

    def api_清空(self) -> None:
        self._队列.clear()
        self._当前 = self._留帧 = None
        self._快照 = None

    def _读片(self, arg_库: str, arg_条: int) -> bytes:
        键 = arg_库, arg_条
        if not self._影片数据.get(键):
            self._影片数据[键] = self.美术.api_解码(arg_库, arg_条)
        return self._影片数据[键]

    def _开始(self, arg_效果: 效果_类) -> None:
        self._留帧 = None
        播 = _播放_类(arg_效果, 演出规格_类.api_查询(arg_效果))
        if 播.规格.资源 >= 0:
            播.影片 = 动画_类(self._读片(播.规格.库, 播.规格.资源))
            播.间隔 = 播.影片.间隔毫秒 or 100
        self._当前 = 播

    def api_绘留帧(
        self,
        arg_画: 图像_类,
        arg_板: 棋盘绘制_类,
        arg_世: 世界_类,
        arg_转: int,
        arg_时: int,
    ) -> None:
        if self._留帧 is None:
            return
        播 = self._留帧
        相机 = 相机_类((播.效果.目标.x, 播.效果.目标.y), arg_转 & 7)
        arg_板.api_绘制(arg_画, 演出场景_类.api_静止快照(arg_世, arg_时, self._服装), 相机)
        arg_画.api_绘制(播.帧图, 播.规格.x, 播.规格.y, self.视口)

    def _时序(
        self,
        arg_播: _播放_类,
        arg_相机: 相机_类,
        arg_演员: tuple[int, int],
        arg_声: Callable[[int], None] | None,
    ) -> tuple[int, bool, bool, int]:
        播, e, 规 = arg_播, arg_播.效果, arg_播.规格
        帧, 结束, 提交, 姿态 = 0, False, True, 0

        def 声(arg_号: int) -> None:
            if arg_号 >= 0 and arg_声:
                arg_声(arg_号)

        if e.种类 == 效果种类_类.工程车拆屋 and 播.影片 is not None:
            步, 数 = 播.已过 // 80, 播.影片.帧数
            姿态 = 0 if 步 == 0 else 1 if 步 <= 7 else 步 - 6
            帧 = 步 - 8
            while 帧 >= 0 and 播.影片.已解帧 <= 帧 and 播.影片.api_下一帧():
                播.帧图 = 播.影片.api_图像()
            if not 播.已响 and 步 >= 8:
                声(规.声音)
                播.已响 = True
            提交, 结束 = 步 >= 9, 帧 >= 数
        elif 播.影片 is not None:
            数 = max(1, 播.影片.帧数)
            帧 = min(播.已过 // 播.间隔, 数 - 1)
            结束 = 播.已过 >= 数 * 播.间隔 + 规.停留毫秒
            while 播.影片.已解帧 <= 帧 and 播.影片.api_下一帧():
                播.帧图 = 播.影片.api_图像()
            if not 播.已响 and 帧 >= 规.声音帧:
                声(规.声音)
                播.已响 = True
            提交 = 帧 >= 规.提交帧
        elif e.种类 == 效果种类_类.神明离开:
            帧 = min(播.已过 // 60, 23)
            结束 = 播.已过 >= 1440 or 棋盘投影_类.api_投影(arg_演员, arg_相机) is None
        else:
            if not 播.路径:
                起 = 棋盘投影_类.api_投影(arg_演员, arg_相机)
                终 = 棋盘投影_类.api_投影((e.目标.x, e.目标.y), arg_相机)
                if 起 is not None and 终 is not None:
                    dx, dy = float(终[0] - 起[0]), float(终[1] - 起[1])
                    步数 = int(math.sqrt(dx * dx + dy * dy) * 0.125 + 1)
                    播.路径 = [
                        (起[0] + int(dx * j / 步数), 起[1] + int(dy * j / 步数))
                        for j in range(1, 步数 + 1)
                    ]
                else:
                    播.路径 = [(-1000, -1000)]
            步数 = len(播.路径)
            帧 = min(播.已过 // 24, 步数 - 1)
            if not 播.已响 and 播.已过 >= 步数 * 24:
                声(规.声音)
                播.已响 = True
            结束, 提交 = 播.已过 >= 步数 * 24 + 规.停留毫秒, False
        return 帧, 结束, 提交, 姿态

    def _场景(
        self,
        arg_播: _播放_类,
        arg_世: 世界_类,
        arg_提交: bool,
        arg_时: int,
        arg_姿态: int,
    ) -> 场景_类:
        e, 规 = arg_播.效果, arg_播.规格
        工程车 = e.种类 == 效果种类_类.工程车拆屋
        if arg_提交 or self._快照 is None:
            if arg_提交:
                self._快照 = None
            场 = 演出场景_类.api_静止快照(arg_世, arg_时, self._服装)
        else:
            场 = deepcopy(self._快照)
        待 = deepcopy(self._待播人物)
        for 后 in self._队列:
            演出场景_类.api_加入待播(待, 后)
        if 规.演员 != 演员模式_类.世界 or 工程车:
            待[:] = [p for p in 待 if p.槽 != e.玩家]
        if 待:
            帧 = ((arg_时 & 0xFFFFFFFFFFFFFFFF) // 120) % 6
            演出场景_类.api_应用待播(场.玩家, arg_世, 待, 帧, self._服装)
            场.物件 = 演出场景_类.api_物件(arg_世, 场.玩家, 帧)
        演出场景_类.api_隐藏物件(场.物件, self.api_抛物待落地)
        模式 = 规.演员
        if (模式 != 演员模式_类.世界 or 工程车) and e.玩家 < len(arg_世.玩家):
            记 = arg_世.玩家[e.玩家].记录
            精灵 = None
            for p in 场.玩家:
                if p.槽位 == 记.槽位:
                    精灵 = deepcopy(p)
            场.玩家[:] = [p for p in 场.玩家 if p.槽位 != 记.槽位]
            if (
                (模式 == 演员模式_类.离开 and not arg_提交) or 模式 == 演员模式_类.停留
            ) and e.起点 is not None:
                if 精灵 is None:
                    精灵 = 玩家精灵_类(
                        角色=记.角色,
                        方向=记.方向,
                        交通=记.交通 & 3,
                        颜色=原生界面_类.api_玩家色(记.颜色),
                        槽位=记.槽位,
                        活跃=True,
                        特殊姿态=self._服装[e.玩家] if e.玩家 < 4 else 0,
                    )
                精灵.位置 = e.起点.x, e.起点.y
                精灵.受伤 = 精灵.受伤 or 规.受伤
                场.玩家.append(精灵)
            elif 模式 == 演员模式_类.到达 and arg_提交 and 精灵 is not None:
                场.玩家.append(精灵)
            elif 工程车 and 精灵 is not None:
                精灵.方向, 精灵.特殊姿态 = e.物件种类 & 7, 12
                精灵.投骰, 精灵.走动, 精灵.动画帧 = False, False, arg_姿态 & 255
                场.玩家.append(精灵)
        if 工程车 and not arg_提交:
            设施 = e.地产 > 4000
            列 = 场.设施 if 设施 else 场.地产
            编号 = (e.地产 - (4000 if 设施 else 2000)) & 0xFFFFFFFF
            列[:] = [p for p in 列 if p.编号 != 编号]
            主 = 0
            if 设施 and 编号 < len(arg_世.设施):
                主 = arg_世.设施[编号].业主
            elif not 设施 and 编号 < len(arg_世.地产):
                主 = arg_世.地产[编号].经济.业主
            列.append(地产外观_类(编号, 主, e.原等级, e.原类型))
        return 场

    def _画面(
        self,
        arg_播: _播放_类,
        arg_画: 图像_类,
        arg_世: 世界_类,
        arg_转: int,
        arg_相机: 相机_类,
        arg_演员: tuple[int, int],
        arg_帧: int,
    ) -> None:
        播, e, 规 = arg_播, arg_播.效果, arg_播.规格
        if e.种类 == 效果种类_类.神明离开:
            起 = 棋盘投影_类.api_投影(arg_演员, arg_相机)
            if 起 is None or not 1 <= e.物件种类 <= 20:
                return
            近 = (
                (-10, -22),
                (-22, -10),
                (-22, 10),
                (-10, 22),
                (10, 22),
                (22, 10),
                (22, -10),
                (10, -22),
            )
            d = (e.方向 + 8 - arg_转) & 7
            图 = self.美术.api_帧("d", 0x18C + e.物件种类 - 1, (d + 4 + arg_帧 + 1) & 7)
            x, y = 起[0] + 近[d][0], 起[1] + 近[d][1] - 10 * (arg_帧 + 1)
            if y - 图.原点y + 图.高 < 40:
                播.已过 = 1440
                return
            arg_画.api_绘制(图, x, y, self.视口)
            return
        if 播.影片 is None:
            点 = 播.路径[arg_帧]
            if e.种类 == 效果种类_类.抛卡:
                arg_画.api_绘制(self.美术.api_帧("d", 0x19F, 0), *点, self.视口)
                return
            方向 = 0
            for 物 in arg_世.物件:
                if 物.节点 == e.节点 and 物.种类 == e.物件种类:
                    方向 = 物.方向
            图 = self.美术.api_帧("d", 0x18C + e.物件种类 - 1, (8 - arg_转 + 方向) & 7)
            arg_画.api_绘制(图, *点, self.视口)
            return
        工程车 = e.种类 == 效果种类_类.工程车拆屋
        if 工程车 and arg_帧 < 0:
            return
        x, y = 规.x, 规.y
        if e.种类 == 效果种类_类.恶魔烟 or 工程车:
            锚 = 棋盘投影_类.api_投影((e.目标.x, e.目标.y), arg_相机)
            if 锚 is None:
                return
            x, y = 锚[0] - 播.影片.宽 // 2, 锚[1] - 播.影片.高 // 2
        arg_画.api_绘制(播.帧图, x, y, self.视口)

    def api_绘制(
        self,
        arg_画: 图像_类,
        arg_板: 棋盘绘制_类,
        arg_世: 世界_类,
        arg_转: int,
        arg_毫秒: int,
        arg_时: int,
        arg_声音: Callable[[int], None] | None = None,
    ) -> None:
        try:
            if self._当前 is None:
                if not self._队列:
                    return
                self._开始(self._队列.popleft())
                arg_毫秒 = 0
            播 = self._当前
            播.已过 = (播.已过 + min(arg_毫秒 & 0xFFFFFFFF, 100)) & 0xFFFFFFFF
            e, 规 = 播.效果, 播.规格
            演员 = (e.目标.x, e.目标.y) if e.起点 is None else (e.起点.x, e.起点.y)
            if e.种类 == 效果种类_类.恶魔烟 and e.玩家 < len(arg_世.玩家):
                记 = arg_世.玩家[e.玩家].记录
                演员 = (记.x, 记.y)
            相机 = 相机_类((e.目标.x, e.目标.y) if 规.相机目标 else 演员, arg_转 & 7)
            帧, 完成, 提交, 姿 = self._时序(播, 相机, 演员, arg_声音)
            if 完成:
                if 规.保留末帧 and 播.影片 is not None and 播.帧图.宽:
                    self._留帧, self._当前 = 播, None
                    self.api_绘留帧(arg_画, arg_板, arg_世, arg_转, arg_时)
                    return
                self._当前 = None
                return
            arg_板.api_绘制(arg_画, self._场景(播, arg_世, 提交, arg_时, 姿), 相机)
            self._画面(播, arg_画, arg_世, arg_转, 相机, 演员, 帧)
        except (ValueError, OSError, IndexError, RuntimeError) as 错:
            # 与原播放器一样，坏素材只使当前演出终止；不回滚或重结算规则世界。
            logging.getLogger(__name__).warning("跳过损坏效果：%s", 错)
            self._当前 = None
