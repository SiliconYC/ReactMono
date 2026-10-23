# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/world.cpp；所有未解释字节与历史快照保留在原 backing。
# ◑ 导入
import struct
from dataclasses import asdict, astuple

from rich4.direction import 方向_类
from rich4.economy import 地产经济_类
from rich4.inventory import 库存_类
from rich4.random import 随机数_类
from rich4.save import 存档_类
from rich4.save_records import 地图表_类
from rich4.world_actors import 地图物件_类, 特殊角色_类
from rich4.world_defaults import 初始资料_类
from rich4.world_map import (
    公司_类,
    地产_类,
    景物_类,
    节点_类,
    设施_类,
)
from rich4.world_options import 新局设置_类
from rich4.world_player import 世界玩家_类, 玩家状态_类
from rich4.world_stocks import 出售项_类, 持仓_类, 股票状态_类


# ◕ 功能
class 世界_类:
    """
    运行世界的全部已解读原字段；编辑后按原位置回填，禁止改变表规模。

    更新日志：
    2026.10.23 - 实现 from_save/export_save、活跃玩家与破产字段清除。
    """

    状态字节 = (
        ("卡片策略", 22),
        ("救援策略", 23),
        ("贷款比例", 24),
        ("初始现金比例", 25),
        ("股票投资比例", 26),
        ("保存方向", 27),
        ("酒店天数", 50),
        ("消失天数", 51),
        ("监狱天数", 52),
        ("医院天数", 53),
        ("睡眠天数", 54),
        ("梦游天数", 55),
        ("停留天数", 56),
        ("龟行天数", 57),
        ("银行拒绝天数", 59),
        ("银行禁贷天数", 60),
        ("结盟天数", 61),
        ("保险天数", 62),
        ("神明信息", 63),
        ("附身炸弹", 64),
        ("盟友", 65),
        ("冬眠总天数", 66),
        ("标志100", 100),
        ("标志101", 101),
        ("标志102", 102),
        ("标志103", 103),
    )
    记录字段 = (
        ("颜色", 4, "I"),
        ("x", 8, "H"),
        ("y", 10, "H"),
        ("节点", 12, "H"),
        ("上次节点", 14, "H"),
        ("方向", 16, "B"),
        ("交通", 17, "B"),
        ("骰数", 18, "B"),
        ("角色", 19, "B"),
        ("性别", 20, "B"),
        ("控制标志", 21, "B"),
        ("现金", 28, "I"),
        ("银行", 32, "I"),
        ("贷款", 36, "I"),
        ("特殊融资", 40, "I"),
        ("点券", 48, "H"),
    )

    def __init__(self, arg_存档: 存档_类) -> None:
        self.头 = arg_存档.api_头()
        self.地图摘要 = arg_存档.api_地图摘要()
        self.原字节 = bytearray(arg_存档.api_导出())
        self.初始随机状态 = 0
        self.有初始随机状态 = False
        self.玩家: list[世界玩家_类] = []
        for 槽位 in range(self.头.人数):
            偏移 = 0x10 + 槽位 * 104
            字节字段 = {名称: self.原字节[偏移 + x] for 名称, x in self.状态字节}
            状态 = 玩家状态_类(
                **字节字段,
                贷款到期=self._数(偏移 + 44),
                神运修正=self._数(偏移 + 68, "h"),
                财运修正=self._数(偏移 + 70, "h"),
                其他运修正=self._数(偏移 + 72, "h"),
                设施编号=self._数(偏移 + 74, "H"),
                敌意=self._阵列(偏移 + 76, 4),
                累计支出=self._数(偏移 + 92),
                累计收入=self._数(偏移 + 96),
            )
            玩家 = 世界玩家_类(arg_存档.api_玩家(槽位), 状态)
            玩家.持仓 = [
                持仓_类(
                    self._数(0x21F6 + 槽位 * 96 + i * 8, "i"), self._数(0x21FA + 槽位 * 96 + i * 8)
                )
                for i in range(12)
            ]
            self.玩家.append(玩家)
        self.卡供应 = self._阵列(0x6CC, 30, "B")
        self.道具供应 = self._阵列(0x6EA, 8, "B")
        self.新闻牌堆 = self._阵列(0x26FA, 36, "B")
        self.命运牌堆 = self._阵列(0x271E, 37, "B")
        self.监狱名单 = self._阵列(0x26E2, 8, "B")
        self.医院名单 = self._阵列(0x26EA, 8, "B")
        self.彩票 = self._阵列(0x26BE, 36, "B")
        self.新闻游标 = self._数(0x26F2)
        self.命运游标 = self._数(0x26F6)
        self.公共基金 = self._数(0x26BA, "i")
        self.新闻影响天数 = self._数(0x269A, "i")
        self.租约模式 = self._数(0x267E)
        self.相机旋转 = self._数(0x2743)
        self.轮数 = self._数(0x2692)
        self.月数 = self._数(0x2696)
        self.股市指数 = self._数(0x26A2, "i")
        self.股市走势位 = self._数(0x26A6)
        self.股史游标 = self._数(0x6F2, "i")
        self.出售表 = [
            [
                出售项_类(*struct.unpack_from("<BBHiHBB", self.原字节, 0x2526 + 卖家 * 84 + i * 12))
                for i in range(7)
            ]
            for 卖家 in range(4)
        ]
        self.特殊角色 = [
            特殊角色_类(*struct.unpack_from("<4H8B", self.原字节, 0x1B4 + i * 16)) for i in range(5)
        ]
        self.股票: list[股票状态_类] = []
        self.股史: list[list[int]] = []
        for i in range(12):
            偏移 = 0x2376 + i * 36
            self.股票.append(
                股票状态_类(
                    self._数(偏移 + 4, "H"),
                    self.原字节[偏移 + 6],
                    self.原字节[偏移 + 7],
                    self._数(偏移 + 8, "H"),
                    self._数(偏移 + 10, "H"),
                    self._阵列(偏移 + 12, 5),
                    self._数(偏移 + 32),
                )
            )
            self.股史.append(self._阵列(0x6F6 + i * 576, 144))
        self.物件: list[地图物件_类] = []
        for i in range(46):
            偏移 = 0x204 + i * 24
            self.物件.append(
                地图物件_类(
                    *struct.unpack_from("<BBH4B", self.原字节, 偏移),
                    self._阵列(偏移 + 8, 4),
                )
            )
        self.节点: list[节点_类] = []
        self.地产: list[地产_类] = []
        self.设施: list[设施_类] = []
        self.公司: list[公司_类] = []
        self.景物: list[景物_类] = []
        self._读地图()

    def _数(self, arg_位置: int, arg_格式: str = "I") -> int:
        return struct.unpack_from("<" + arg_格式, self.原字节, arg_位置)[0]

    def _阵列(
        self,
        arg_位置: int,
        arg_数量: int,
        arg_格式: str = "I",
    ) -> list[int]:
        return list(struct.unpack_from(f"<{arg_数量}{arg_格式}", self.原字节, arg_位置))

    def _名字(self, arg_位置: int) -> bytes:
        return bytes(self.原字节[arg_位置 : arg_位置 + 16]).split(b"\0", 1)[0]

    @classmethod
    def api_从存档(cls, arg_存档: 存档_类) -> "世界_类":
        return cls(arg_存档)

    def _读地图(self) -> None:
        for 表号, 表 in enumerate(self.地图摘要.表):
            for i in range(表.数量 + 1):
                p = 0x274B + 表.偏移 + i * 表.步长
                if 表号 == 0:
                    self.节点.append(
                        节点_类(
                            i,
                            self._数(p, "h"),
                            self._数(p + 2, "h"),
                            self._阵列(p + 24, 4, "H"),
                            self._数(p + 32, "H"),
                            self._数(p + 34, "H"),
                            self._数(p + 36),
                            self._名字(p + 4),
                        )
                    )
                elif 表号 == 1:
                    经济 = 地产经济_类(
                        self._名字(p + 4),
                        self.原字节[p + 24],
                        self.原字节[p + 25],
                        self.原字节[p + 26],
                        tuple(self._阵列(p + 32, 6, "H")),
                    )
                    self.地产.append(
                        地产_类(
                            i,
                            self._数(p, "H"),
                            self._数(p + 2, "H"),
                            经济,
                            self.原字节[p + 23],
                            self.原字节[p + 27],
                            self._数(p + 30, "H"),
                            self._数(p + 28, "H"),
                            self._数(p + 44),
                            self._数(p + 48),
                        )
                    )
                elif 表号 == 2:
                    self.设施.append(
                        设施_类(
                            i,
                            self._数(p, "H"),
                            self._数(p + 2, "H"),
                            self._名字(p + 4),
                            *self.原字节[p + 24 : p + 29],
                            self.原字节[p + 30],
                            self._数(p + 34, "H"),
                            self._阵列(p + 36, 6, "H"),
                            self._数(p + 48),
                            self._数(p + 52),
                        )
                    )
                elif 表号 == 3:
                    self.公司.append(
                        公司_类(
                            i,
                            self._数(p, "H"),
                            self._数(p + 2, "H"),
                            self.原字节[p + 24],
                            self.原字节[p + 26],
                            self.原字节[p + 27],
                            self._数(p + 32, "H"),
                            self._数(p + 34, "H"),
                            self.原字节[p + 25],
                            self._数(p + 40, "i"),
                            self._数(p + 44, "i"),
                            self._数(p + 48, "i"),
                            self._阵列(p + 28, 4, "B"),
                            self._数(p + 36, "i"),
                            self._名字(p + 4),
                        )
                    )
                else:
                    self.景物.append(
                        景物_类(
                            i,
                            self._数(p, "H"),
                            self._数(p + 2, "H"),
                            self.原字节[p + 24],
                            self._数(p + 26, "H"),
                            self._名字(p + 4),
                        )
                    )

    def api_活跃玩家(self) -> 世界玩家_类:
        if not 0 <= self.头.当前玩家 < len(self.玩家):
            raise IndexError("活跃玩家越界")
        return self.玩家[self.头.当前玩家]

    def api_清破产字段(self, arg_槽位: int) -> None:
        if not 0 <= arg_槽位 < len(self.玩家):
            raise IndexError("破产玩家越界")
        if arg_槽位 >= self._数(12):
            raise ValueError("破产玩家不在原 backing 中")
        玩家 = self.玩家[arg_槽位]
        偏移 = 0x10 + arg_槽位 * 104 + 28
        self.原字节[偏移 : 偏移 + 76] = bytes(76)
        玩家.记录.现金 = 玩家.记录.银行 = 玩家.记录.贷款 = 玩家.记录.特殊融资 = 玩家.记录.点券 = 0
        旧 = 玩家.状态
        玩家.状态 = 玩家状态_类(
            初始现金比例=旧.初始现金比例,
            救援策略=旧.救援策略,
            卡片策略=旧.卡片策略,
            贷款比例=旧.贷款比例,
            股票投资比例=旧.股票投资比例,
            保存方向=旧.保存方向,
        )

    @staticmethod
    def _写(
        arg_目标: bytearray,
        arg_位置: int,
        arg_值: int,
        arg_格式: str = "I",
    ) -> None:
        位数 = struct.calcsize(arg_格式) * 8
        struct.pack_into("<" + arg_格式, arg_目标, arg_位置, arg_值 & ((1 << 位数) - 1))

    @staticmethod
    def _写阵列(
        arg_目标: bytearray,
        arg_位置: int,
        arg_值: list[int],
        arg_数量: int,
        arg_格式: str = "I",
    ) -> None:
        if len(arg_值) != arg_数量:
            raise ValueError("不能改变原固定数组大小")
        步长 = struct.calcsize(arg_格式)
        for i, 值 in enumerate(arg_值):
            世界_类._写(arg_目标, arg_位置 + i * 步长, 值, arg_格式)

    def _写名字(self, arg_字节: bytearray, arg_位置: int, arg_值: bytes) -> None:
        if arg_值 == self._名字(arg_位置):
            return
        if len(arg_值) > 15 or b"\0" in arg_值:
            raise ValueError("变更后的地图名必须为最多 15 个非 NUL 原编码字节")
        arg_字节[arg_位置 : arg_位置 + 16] = arg_值.ljust(16, b"\0")

    @staticmethod
    def _检查表(
        arg_记录: list[节点_类] | list[地产_类] | list[设施_类] | list[公司_类] | list[景物_类],
        arg_表: 地图表_类,
    ) -> None:
        if len(arg_记录) != arg_表.数量 + 1 or any(r.编号 != i for i, r in enumerate(arg_记录)):
            raise ValueError("原地图表规模或编号不能改变")

    def api_导出(self) -> bytes:
        if self.头.签名 != 0x26 or len(self.玩家) != self._数(12) or self.头.人数 != len(self.玩家):
            raise ValueError("世界头与玩家数量不一致")
        if not 0 <= self.头.当前玩家 < len(self.玩家) or not 0 <= self.头.人类人数 <= len(
            self.玩家
        ):
            raise ValueError("世界头玩家索引不一致")
        for 记录, 表 in zip(
            (self.节点, self.地产, self.设施, self.公司, self.景物), self.地图摘要.表
        ):
            self._检查表(记录, 表)
        字节 = self.原字节.copy()
        日, 月, 年 = self.头.日期
        for 偏移, 值, 格式 in [
            (4, 日, "B"),
            (5, 月, "B"),
            (6, 年, "H"),
            (8, self.头.地图, "H"),
            (10, self.头.阶段, "H"),
            (0x1B0, self.头.人类人数, "I"),
            (0x2676, self.头.当前玩家, "I"),
            (0x268A, self.头.初始资金, "I"),
            (0x268E, self.头.物价, "I"),
        ]:
            self._写(字节, 偏移, 值, 格式)
        for 槽位, 玩家 in enumerate(self.玩家):
            if 玩家.记录.槽位 != 槽位:
                raise ValueError("玩家编号不等于槽位")
            p = 0x10 + 槽位 * 104
            记录值 = asdict(玩家.记录)
            for 名称, 偏移, 格式 in self.记录字段:
                self._写(字节, p + 偏移, 记录值[名称], 格式)
            状态值 = asdict(玩家.状态)
            for 名称, 偏移 in self.状态字节:
                self._写(字节, p + 偏移, 状态值[名称], "B")
            s = 玩家.状态
            for 偏移, 值, 格式 in [
                (44, s.贷款到期, "I"),
                (68, s.神运修正, "H"),
                (70, s.财运修正, "H"),
                (72, s.其他运修正, "H"),
                (74, s.设施编号, "H"),
                (92, s.累计支出, "I"),
                (96, s.累计收入, "I"),
            ]:
                self._写(字节, p + 偏移, 值, 格式)
            self._写阵列(字节, p + 76, s.敌意, 4)
            self._写阵列(字节, 0x654 + 槽位 * 15, 玩家.记录.卡片, 15, "B")
            self._写阵列(字节, 0x690 + 槽位 * 15, 玩家.记录.道具, 15, "B")
            if len(玩家.持仓) != 12:
                raise ValueError("原持仓数组大小不能改变")
            for i, 持仓 in enumerate(玩家.持仓):
                self._写(字节, 0x21F6 + 槽位 * 96 + i * 8, 持仓.数量)
                self._写(字节, 0x21FA + 槽位 * 96 + i * 8, 持仓.成本位)
        for 值, 偏移, 数量 in [
            (self.卡供应, 0x6CC, 30),
            (self.道具供应, 0x6EA, 8),
            (self.新闻牌堆, 0x26FA, 36),
            (self.命运牌堆, 0x271E, 37),
            (self.监狱名单, 0x26E2, 8),
            (self.医院名单, 0x26EA, 8),
            (self.彩票, 0x26BE, 36),
        ]:
            self._写阵列(字节, 偏移, 值, 数量, "B")
        for 偏移, 值 in [
            (0x26F2, self.新闻游标),
            (0x26F6, self.命运游标),
            (0x26BA, self.公共基金),
            (0x269A, self.新闻影响天数),
            (0x267E, self.租约模式),
            (0x2743, self.相机旋转),
            (0x2692, self.轮数),
            (0x2696, self.月数),
            (0x26A2, self.股市指数),
            (0x26A6, self.股市走势位),
            (0x6F2, self.股史游标),
        ]:
            self._写(字节, 偏移, 值)
        if (
            len(self.出售表),
            len(self.特殊角色),
            len(self.股票),
            len(self.股史),
            len(self.物件),
        ) != (4, 5, 12, 12, 46):
            raise ValueError("固定世界数组大小不能改变")
        for 卖家, 出售列 in enumerate(self.出售表):
            if len(出售列) != 7:
                raise ValueError("原出售表大小不能改变")
            for i, 项 in enumerate(出售列):
                p = 0x2526 + 卖家 * 84 + i * 12
                for 偏移, 值, 格式 in zip(
                    (0, 1, 2, 4, 8, 10, 11), astuple(项), ("B", "B", "H", "I", "H", "B", "B")
                ):
                    self._写(字节, p + 偏移, 值, 格式)
        for i, 角色 in enumerate(self.特殊角色):
            p = 0x1B4 + i * 16
            for 偏移, 值, 格式 in zip(
                (0, 2, 4, 6, 8, 9, 10, 11, 12, 13, 14, 15), astuple(角色), ("H",) * 4 + ("B",) * 8
            ):
                self._写(字节, p + 偏移, 值, 格式)
        for i, 股 in enumerate(self.股票):
            p = 0x2376 + i * 36
            for 偏移, 值, 格式 in [
                (4, 股.标志4, "H"),
                (6, 股.停牌天数, "B"),
                (7, 股.新闻走势, "B"),
                (8, 股.可购股数, "H"),
                (10, 股.标志10, "H"),
                (32, 股.原值32, "I"),
            ]:
                self._写(字节, p + 偏移, 值, 格式)
            self._写阵列(字节, p + 12, 股.浮点位, 5)
            self._写阵列(字节, 0x6F6 + i * 576, self.股史[i], 144)
        for i, 物件 in enumerate(self.物件):
            p = 0x204 + i * 24
            for 偏移, 值, 格式 in zip(
                (0, 1, 2, 4, 5, 6, 7), astuple(物件)[:-1], ("B", "B", "H", "B", "B", "B", "B")
            ):
                self._写(字节, p + 偏移, 值, 格式)
            self._写阵列(字节, p + 8, 物件.运动位, 4)
        self._写地图(字节)
        return bytes(字节)

    def _写地图(self, arg_字节: bytearray) -> None:
        for 表号, 记录列 in enumerate((self.节点, self.地产, self.设施, self.公司, self.景物)):
            表 = self.地图摘要.表[表号]
            for 记录 in 记录列:
                p = 0x274B + 表.偏移 + 记录.编号 * 表.步长
                self._写(arg_字节, p, 记录.x, "H")
                self._写(arg_字节, p + 2, 记录.y, "H")
                if 表号 == 0:
                    self._写阵列(arg_字节, p + 24, 记录.邻居, 4, "H")
                    self._写(arg_字节, p + 32, 记录.类型索引, "H")
                    self._写(arg_字节, p + 34, 记录.地面精灵, "H")
                    self._写(arg_字节, p + 36, 记录.标志)
                elif 表号 == 1:
                    self._写名字(arg_字节, p + 4, 记录.经济.街道名)
                    for 偏移, 值 in [
                        (23, 记录.临时状态),
                        (24, 记录.经济.连锁),
                        (25, 记录.经济.业主),
                        (26, 记录.经济.等级),
                        (27, 记录.方向),
                    ]:
                        self._写(arg_字节, p + 偏移, 值, "B")
                    self._写(arg_字节, p + 28, 记录.地价, "H")
                    self._写(arg_字节, p + 30, 记录.每级造价, "H")
                    self._写阵列(arg_字节, p + 32, list(记录.经济.各级租金), 6, "H")
                    self._写(arg_字节, p + 44, 记录.已移除建筑)
                    self._写(arg_字节, p + 48, 记录.到期日)
                elif 表号 == 2:
                    self._写名字(arg_字节, p + 4, 记录.名字)
                    for 偏移, 值 in [
                        (24, 记录.类型),
                        (25, 记录.业主),
                        (26, 记录.等级),
                        (27, 记录.方向),
                        (28, 记录.临时状态),
                        (30, 记录.标志30),
                    ]:
                        self._写(arg_字节, p + 偏移, 值, "B")
                    self._写(arg_字节, p + 34, 记录.地价, "H")
                    self._写阵列(arg_字节, p + 36, 记录.各级租金, 6, "H")
                    self._写(arg_字节, p + 48, 记录.已移除建筑)
                    self._写(arg_字节, p + 52, 记录.到期日)
                elif 表号 == 3:
                    for 偏移, 值 in [
                        (24, 记录.业主),
                        (25, 记录.股票索引),
                        (26, 记录.类型),
                        (27, 记录.方向),
                    ]:
                        self._写(arg_字节, p + 偏移, 值, "B")
                    self._写阵列(arg_字节, p + 28, 记录.股东排名, 4, "B")
                    self._写(arg_字节, p + 32, 记录.精灵, "H")
                    self._写(arg_字节, p + 34, 记录.通行费, "H")
                    for 偏移, 值 in [
                        (36, 记录.估值),
                        (40, 记录.资金),
                        (44, 记录.资金变化),
                        (48, 记录.剩余股份),
                    ]:
                        self._写(arg_字节, p + 偏移, 值)
                else:
                    self._写(arg_字节, p + 24, 记录.方向, "B")
                    self._写(arg_字节, p + 26, 记录.精灵, "H")

    @staticmethod
    def _洗牌(arg_牌: list[int], arg_随机: 随机数_类) -> None:
        # 与参考的“从剩余有序候选选第 k 项”相同；Fisher–Yates 会改变序列与随机消费。
        候选 = list(range(len(arg_牌)))
        for i in range(len(arg_牌)):
            arg_牌[i] = 候选.pop(arg_随机.api_下一个() % len(候选))

    @classmethod
    def api_从地图(
        cls,
        arg_地图: bytes,
        arg_设置: 新局设置_类 | None = None,
    ) -> "世界_类":
        设置 = 新局设置_类() if arg_设置 is None else arg_设置
        if not 40 <= len(arg_地图) <= 0xFFFFFFFF:
            raise ValueError("地图资源大小超出原格式")
        if (
            not 1 <= len(设置.玩家) <= 4
            or not 0 <= 设置.初始资金 <= 2147483647
            or not 0 <= 设置.地图 <= 3
            or not 0 <= 设置.阶段 <= 1
            or not 0 <= 设置.租约模式 <= 5
        ):
            raise ValueError("新局参数无效")
        长度 = 0x274B + len(arg_地图) + len(设置.玩家) * (0x2718 + len(arg_地图))
        数据 = bytearray(长度)
        cls._写(数据, 0, 0x26)
        cls._写(数据, 12, len(设置.玩家))
        cls._写(数据, 0x2747, len(arg_地图))
        数据[0x274B : 0x274B + len(arg_地图)] = arg_地图
        世 = cls.api_从存档(存档_类.api_解码(bytes(数据)))
        if not 2 <= len(世.节点) <= 256:
            raise ValueError("原出生算法要求 1..255 个地图节点")
        世.头.日期 = 设置.日期
        世.头.地图 = 设置.地图
        世.头.阶段 = 设置.阶段
        世.头.初始资金 = 设置.初始资金
        世.头.物价 = 1
        世.租约模式 = 设置.租约模式
        世.卡供应 = list(初始资料_类.卡供应)
        世.道具供应[:] = [10] * 8
        世.监狱名单[4:6] = [1, 1]
        世.医院名单[6:8] = [1, 1]
        for i, 角色 in enumerate(世.特殊角色):
            角色.不活跃状态 = i // 2 + 1
        for i, 物件 in enumerate(世.物件):
            物件.种类 = i + 1 if i < 14 else 15 if i < 16 else 16 + (i - 16) // 10
        for i, 股 in enumerate(世.股票):
            标志, 股数, 价位, 波位 = 初始资料_类.股票[(设置.阶段 * 4 + 设置.地图) * 12 + i]
            股.标志4 = 标志
            股.可购股数 = 股数
            股.浮点位 = [价位, 价位, 价位, 波位, 0]
        for 公司 in 世.公司[1:]:
            if 公司.股票索引 >= len(世.股票):
                raise ValueError("公司股票索引越界")
            公司.剩余股份 = 10000 - 世.股票[公司.股票索引].可购股数
            世.股票[公司.股票索引].标志4 = 公司.编号
        随机 = 随机数_类(设置.随机种子)
        for 节点 in 世.节点[1:]:
            if any(n >= len(世.节点) for n in 节点.邻居):
                raise ValueError("新局地图邻居链接越界")
        if any(p.起点 == 0 for p in 设置.玩家) and not any(
            n.标志 & 0x80FFFF00 == 0 and any(n.邻居) for n in 世.节点[1:]
        ):
            raise ValueError("地图没有可出生的连通节点")
        for 槽位, 选项 in enumerate(设置.玩家):
            if (
                not 0 <= 选项.角色 < 12
                or 选项.控制 not in (1, 2)
                or not 0 <= 选项.交通 <= 2
                or not 0 <= 选项.起点 < len(世.节点)
            ):
                raise ValueError("新局玩家参数无效")
            颜色, 性别, 救援, 贷款, 现金比例, 股票比例 = 初始资料_类.人物[选项.角色]
            玩家 = 世.玩家[槽位]
            记录, 状态 = 玩家.记录, 玩家.状态
            记录.角色, 记录.颜色, 记录.性别 = 选项.角色, 颜色, 性别
            记录.控制标志 = 状态.标志100 = 选项.控制
            状态.初始现金比例, 状态.股票投资比例 = 现金比例, 股票比例
            状态.救援策略, 状态.卡片策略, 状态.贷款比例 = 救援, 3, 贷款
            记录.交通, 记录.骰数 = 选项.交通, 选项.交通 + 1
            比例 = 50 if 选项.控制 == 1 else 现金比例
            记录.现金 = 设置.初始资金 * 比例 // 100
            记录.银行 = 设置.初始资金 - 记录.现金
            if 选项.控制 == 1:
                世.头.人类人数 += 1
            if 选项.起点:
                记录.节点 = 选项.起点
                节点 = 世.节点[记录.节点]
                邻居 = [n for n in 节点.邻居 if n]
                if not 邻居:
                    raise ValueError("玩家起点没有路线")
                记录.上次节点 = 邻居[随机.api_下一个() % len(邻居)]
                记录.x, 记录.y = 节点.x & 0xFFFF, 节点.y & 0xFFFF
                前 = 世.节点[记录.上次节点]
                记录.方向 = 方向_类.api_计算(节点.x - 前.x, 节点.y - 前.y)
                节点.标志 |= 0x100 << 槽位
            库存 = 库存_类(道具=记录.道具, 道具供应=世.道具供应)
            for 道具 in (1, 2, 3, 4, 8, 9):
                库存.api_收道具(道具)
            if 选项.交通:
                世.道具供应[选项.交通 + 3] -= 1
            p = 0x10 + 槽位 * 104
            for 偏移, 值 in [(22, 3), (23, 救援), (24, 贷款), (26, 股票比例)]:
                世.原字节[p + 偏移] = 值
        cls._洗牌(世.新闻牌堆, 随机)
        cls._洗牌(世.命运牌堆, 随机)
        世.初始随机状态 = 随机.状态
        世.有初始随机状态 = True
        return 世
