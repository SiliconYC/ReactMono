# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/inventory.cpp，原卡/道具字节语义不能用集合替代。
# ◑ 导入
from dataclasses import dataclass, field


# ◕ 功能
@dataclass
class 库存_类:
    """
    原顺序手牌及共享供应；收卡不检查供应是原调用方契约。

    更新日志：
    2026.10.23 - 实现全部 inventory 模块操作，保留序列化未知道具槽位。
    """

    卡片: list[int] = field(default_factory=lambda: [0] * 15)
    卡供应: list[int] = field(default_factory=lambda: [0] * 30)
    卡价: list[int] = field(default_factory=lambda: [0] * 30)
    道具: list[int] = field(default_factory=lambda: [0] * 15)
    道具供应: list[int] = field(default_factory=lambda: [0] * 8)
    道具价格: list[int] = field(default_factory=lambda: [0] * 13)

    @staticmethod
    def _编号(arg_编号: int, arg_上限: int) -> int:
        if not 1 <= arg_编号 <= arg_上限:
            raise ValueError(f"编号必须在 1..{arg_上限}")
        return arg_编号 - 1

    def _验证手牌(self, arg_密集: bool = False) -> None:
        空 = False
        for 卡 in self.卡片:
            if 卡 == 0:
                空 = True
            else:
                self._编号(卡, 30)
                if arg_密集 and 空:
                    raise ValueError("丢半手要求手牌密集排列")

    def api_卡数(self) -> int:
        return sum(卡 != 0 for 卡 in self.卡片)

    def api_有卡(self, arg_编号: int) -> bool:
        return arg_编号 in self.卡片

    def api_最便宜卡(self) -> int:
        self._验证手牌()
        最低 = 10000
        选中 = 0
        for 卡 in self.卡片:
            if 卡 and self.卡价[卡 - 1] < 最低:
                最低 = self.卡价[卡 - 1]
                选中 = 卡
        return 选中

    def api_用卡(self, arg_编号: int) -> bool:
        索引 = self._编号(arg_编号, 30)
        if arg_编号 not in self.卡片:
            return False
        槽位 = self.卡片.index(arg_编号)
        self.卡片[槽位:] = self.卡片[槽位 + 1 :] + [0]
        self.卡供应[索引] = (self.卡供应[索引] + 1) & 255
        return True

    def api_收卡(self, arg_编号: int) -> None:
        索引 = self._编号(arg_编号, 30)
        self._验证手牌()
        if self.api_卡数() == len(self.卡片):
            self.api_用卡(self.api_最便宜卡())
        self.卡片[self.卡片.index(0)] = arg_编号
        self.卡供应[索引] = (self.卡供应[索引] - 1) & 255

    def api_丢半手(self) -> bool:
        self._验证手牌(True)
        数量 = self.api_卡数()
        if 数量 <= 1:
            return False
        # 每次读取的是压紧后的当前槽；预先切片会错误地丢掉 A/B 而非 A/C。
        for 槽位 in range(数量 // 2):
            self.api_用卡(self.卡片[槽位])
        return True

    def api_卖卡(self) -> int:
        self._验证手牌()
        点数 = 0
        for 槽位, 卡 in enumerate(self.卡片):
            if 卡:
                索引 = 卡 - 1
                self.卡供应[索引] = (self.卡供应[索引] + 1) & 255
                点数 += self.卡价[索引]
                self.卡片[槽位] = 0
        return 点数

    def api_收道具(self, arg_编号: int) -> bool:
        索引 = self._编号(arg_编号, 13)
        if self.道具[索引] >= 9:
            return False
        if 索引 < 8:
            if self.道具供应[索引] == 0:
                return False
            self.道具供应[索引] -= 1
        self.道具[索引] += 1
        return True

    def api_用道具(self, arg_编号: int) -> bool:
        索引 = self._编号(arg_编号, 13)
        if self.道具[索引] == 0:
            return False
        self.道具[索引] -= 1
        if 索引 < 8:
            self.道具供应[索引] = (self.道具供应[索引] + 1) & 255
        return True

    def api_卖库存道具(self) -> int:
        点数 = 0
        for 索引 in range(13):
            if 索引 < 8:
                self.道具供应[索引] = (self.道具供应[索引] + self.道具[索引]) & 255
            点数 += self.道具价格[索引] * self.道具[索引]
            self.道具[索引] = 0
        return 点数
