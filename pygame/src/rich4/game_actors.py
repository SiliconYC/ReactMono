# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ game.cpp 1711..2197；角色状态、防御、建筑与原物件生命周期。
# ◑ 导入
from rich4.auction import 拍卖会话_类, 拍卖结果_类
from rich4.cards import 卡片目标_类, 目标种类_类
from rich4.direction import 方向_类
from rich4.events import 事件_类
from rich4.game_types import (
    决策_类,
    决策种类_类,
    决策选项_类,
    待选择异常_类,
    效果点_类,
    效果种类_类,
    游戏事件_类,
    游戏事件种类_类,
)
from rich4.gods import 神明_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类


# ◕ 功能
class 会话角色_类:
    """
    原角色/被动卡与物件操作；随机抽取、嵌套选择和调用顺序由同一会话持有。

    更新日志：
    2026.10.24 - 原收容、全旅馆释放、配对神明重生及拍卖重放接线。
    """

    _回绕 = staticmethod(股市_类._回绕)

    def _同步附身(self, arg_槽: int) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        for 号 in (人.状态.神明信息, 人.状态.附身炸弹):
            if 号:
                事件_类._取(self.世界.物件, 号 - 1).节点 = 人.记录.节点

    def _清缺席(self, arg_槽: int) -> None:
        状 = 事件_类._取(self.世界.玩家, arg_槽).状态
        if arg_槽 < len(self.服装) and (状.监狱天数 or 状.医院天数):
            self.服装[arg_槽] = 19 if 状.医院天数 else 20
            self.服装键[arg_槽] = self._服装键(arg_槽)
        if 状.监狱天数:
            self.世界.监狱名单[arg_槽] = 0
        if 状.医院天数:
            self.世界.医院名单[arg_槽] = 0
        状.酒店天数 = 状.消失天数 = 状.监狱天数 = 状.医院天数 = 0

    def _搬走破产者(self, arg_槽: int) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽).记录
        旧 = 人.节点
        事件_类._取(self.世界.节点, 旧).标志 &= ~(0x100 << arg_槽)
        去 = self._随机空节点(旧)
        节 = 事件_类._取(self.世界.节点, 去)
        前 = next((i for i in 节.邻居 if i), 0)
        人.节点, 人.上次节点, 人.x, 人.y = 去, 前, 节.x & 65535, 节.y & 65535
        前节 = 事件_类._取(self.世界.节点, 前)
        人.方向 = 方向_类.api_计算(节.x - 前节.x, 节.y - 前节.y)
        self.世界.节点[去].标志 |= 0x100 << arg_槽

    def _受伤(self, arg_槽: int) -> None:
        if not 0 <= arg_槽 < len(self.世界.玩家):
            return
        人 = self.世界.玩家[arg_槽]
        记, 状 = 人.记录, 人.状态
        if not 记.控制标志:
            self._搬走破产者(arg_槽)
            return
        if 状.酒店天数 or 状.消失天数 or 状.监狱天数 or 状.医院天数:
            return
        if 记.交通:
            交通 = 记.交通 & 3
            if 交通 in (1, 2):
                self.世界.道具供应[交通 + 3] = (self.世界.道具供应[交通 + 3] + 1) & 255
            记.交通, 记.骰数 = 0, 1
        记.控制标志 |= 0x40

    def _收容(self, arg_槽: int, arg_天: int, arg_医院: bool) -> None:
        if 4 <= arg_槽 < 8:
            特 = 事件_类._取(self.世界.特殊角色, arg_槽 - 4)
            事件_类._取(self.世界.节点, 特.节点).标志 &= ~(0x100 << arg_槽)
            特.不活跃状态 = 2 if arg_医院 else 1
            特.标志 = 特.睡眠天数 = 特.梦游天数 = 特.停留天数 = 特.龟行天数 = 0
            (self.世界.医院名单 if arg_医院 else self.世界.监狱名单)[arg_槽] = 1
            return
        if not 0 <= arg_槽 < len(self.世界.玩家):
            raise RuntimeError("invalid confinement player")
        人 = self.世界.玩家[arg_槽]
        记, 状 = 人.记录, 人.状态
        字段 = "医院天数" if arg_医院 else "监狱天数"
        if not getattr(状, 字段):
            旧点, 旧在场 = self._角色点(arg_槽), self._在场(arg_槽)
            self._清缺席(arg_槽)
            self._缺席语音(arg_槽, arg_天)
            记.控制标志 &= 15
            事件_类._取(self.世界.节点, 记.节点).标志 &= ~(0x100 << arg_槽)
            # 原版按地图建筑码 8001/8002 定位收容节点，不按道路事件标志 5/4。
            建筑码 = 8001 if arg_医院 else 8002
            去 = next(
                (
                    i
                    for i in range(len(self.世界.节点) - 1, 0, -1)
                    if self.世界.节点[i].类型索引 == 建筑码
                ),
                None,
            )
            if 去 is None:
                raise RuntimeError("map has no confinement building node")
            记.节点, 记.上次节点, 状.保存方向 = 去 & 65535, 0, 15
            楼 = 事件_类._取(self.世界.景物, 1 if arg_医院 else 2)
            记.x, 记.y = 楼.x & 65535, 楼.y & 65535
            self._同步附身(arg_槽)
            setattr(状, 字段, arg_天 & 255)
            (self.世界.医院名单 if arg_医院 else self.世界.监狱名单)[arg_槽] = 1
            self._地图影片(
                效果种类_类.救护车 if arg_医院 else 效果种类_类.警车,
                arg_槽,
                旧点,
                旧点 if 旧在场 else None,
            )
        else:
            setattr(状, 字段, (getattr(状, 字段) + arg_天) & 127)
        self._语音(arg_槽, 20 if arg_医院 else 19)
        self._保险赔偿(arg_槽, self._回绕(self._回绕(arg_天 * 2000) * self.世界.头.物价))
        状.冬眠总天数 = (状.冬眠总天数 + arg_天) & 255
        self.事件队列.append(
            游戏事件_类(
                游戏事件种类_类.提示,
                arg_槽,
                arg_天,
                记.节点,
                f"玩家{arg_槽 + 1}" + ("住院" if arg_医院 else "入狱") + f"{arg_天}天",
            )
        )

    def _消失(self, arg_槽: int, arg_天: int, arg_模式: int) -> None:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        状, 编码 = 人.状态, ((arg_模式 << 6) | arg_天) & 255
        if not 状.消失天数:
            self._清缺席(arg_槽)
            self._缺席语音(arg_槽, arg_天)
            self._保险赔偿(arg_槽, self._回绕(self._回绕(arg_天 * 2000) * self.世界.头.物价))
            状.冬眠总天数 = (状.冬眠总天数 + arg_天) & 255
            状.消失天数 = 编码
            节 = 事件_类._取(self.世界.节点, 人.记录.节点)
            节.标志 &= ~(0x100 << arg_槽)
            旧点 = self._角色点(arg_槽)
            self._地图影片(效果种类_类.飞碟 if arg_模式 else 效果种类_类.飞机, arg_槽, 旧点, 旧点)
            人.记录.x, 人.记录.y = 节.x & 65535, 节.y & 65535
        else:
            状.消失天数 = ((状.消失天数 & 63) + 编码) & 255
        self.事件队列.append(
            游戏事件_类(
                游戏事件种类_类.提示,
                arg_槽,
                arg_天,
                人.记录.节点,
                f"玩家{arg_槽 + 1}暂时离开{arg_天}天",
            )
        )

    def _尝试免付卡(self, arg_槽: int, arg_接收: int, arg_额: int) -> bool:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        库 = 服务_类._库存(self.世界, arg_槽)
        if not 库.api_有卡(20):
            return False
        if 人.记录.控制标志 == 1:
            键 = self.选择序列
            self.选择序列 += 1
            if 键 not in self.事件选择:
                raise 待选择异常_类(
                    决策_类(
                        决策种类_类.卡片目标,
                        arg_槽,
                        金额=arg_额,
                        提示="是否使用免費卡？",
                        选项=[决策选项_类("使用免費卡", 1), 决策选项_类("保留卡片", 0)],
                    ),
                    键,
                )
            用 = self.事件选择[键] != 0
        else:
            限 = self._回绕((self.随机.api_下一个() % 3000 + 3000) * self.世界.头.物价)
            用 = arg_额 > 人.记录.现金 or arg_额 > 限
        if 用:
            库.api_用卡(20)
            self.事件队列.append(
                游戏事件_类(
                    游戏事件种类_类.提示, arg_槽, 节点=人.记录.节点, 消息="使用免費卡", 卡片=20
                )
            )
            self._卡片语句(arg_槽, 0, 20, 0)
            self._卡片语句(arg_接收, 2, 20, 1)
        return 用

    def _尝试嫁祸卡(self, arg_槽: int, arg_模式: int, arg_额: int = 0) -> int:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        库 = 服务_类._库存(self.世界, arg_槽)
        if not 库.api_有卡(19):
            return -1
        对 = -1
        if 人.记录.控制标志 == 1:
            键 = self.选择序列
            self.选择序列 += 1
            if 键 in self.事件选择:
                对 = self.事件选择[键]
            else:
                决 = 决策_类(决策种类_类.卡片目标, arg_槽, 金额=arg_额, 提示="請選擇嫁禍對象...")
                for i, 另 in enumerate(self.世界.玩家):
                    if i != arg_槽 and 另.记录.控制标志:
                        决.选项.append(
                            决策选项_类(
                                f"嫁禍給玩家{i + 1}",
                                i,
                                对象=卡片目标_类(目标种类_类.角色, i & 65535),
                            )
                        )
                if len(决.选项) == 1:
                    决.提示 = f"是否嫁禍給玩家{决.选项[0].值 + 1}？"
                决.选项.append(决策选项_类("保留卡片", -1))
                raise 待选择异常_类(决, 键)
        else:
            最大 = 0
            for i, 另 in enumerate(self.世界.玩家):
                if i == arg_槽 or not 另.记录.控制标志:
                    continue
                恨 = self._回绕(人.状态.敌意[i])
                if 恨 > 最大:
                    最大, 对 = 恨, i
            if 对 < 0:
                可选 = [
                    i
                    for i, 另 in enumerate(self.世界.玩家)
                    if i != arg_槽
                    and 另.记录.控制标志
                    and not (
                        另.状态.酒店天数 or 另.状态.消失天数 or 另.状态.监狱天数 or 另.状态.医院天数
                    )
                ]
                if 可选:
                    对 = 可选[self.随机.api_下一个() % len(可选)]
            if arg_模式 == 1:
                限 = self._回绕((self.随机.api_下一个() % 4000 + 4000) * self.世界.头.物价)
                if not (arg_额 > 人.记录.现金 or arg_额 > 限):
                    对 = -1
            elif arg_模式 == 2 and 人.记录.现金 < self._回绕(20000 * self.世界.头.物价):
                对 = -1
        if 对 >= 0:
            库.api_用卡(19)
            self.事件队列.append(
                游戏事件_类(
                    游戏事件种类_类.提示,
                    arg_槽,
                    节点=人.记录.节点,
                    消息=f"使用嫁禍卡，目標是玩家{对 + 1}",
                    卡片=19,
                )
            )
            self._卡片语句(arg_槽, 0, 19, 0)
            self._卡片语句(对, 2, 19, 2)
        return 对

    def _尝试防御卡(self, arg_槽: int) -> int:
        人 = 事件_类._取(self.世界.玩家, arg_槽)
        库 = 服务_类._库存(self.世界, arg_槽)
        if 库.api_有卡(21):
            库.api_用卡(21)
            self.事件队列.append(
                游戏事件_类(
                    游戏事件种类_类.提示, arg_槽, 节点=人.记录.节点, 消息="使用免罪卡", 卡片=21
                )
            )
            self._卡片语句(arg_槽, 0, 21, 0)
            return -1
        对 = self._尝试嫁祸卡(arg_槽, 0)
        return 对 if 对 >= 0 else arg_槽

    def _选择受害卡(self, arg_槽: int, arg_受害: int) -> int:
        键 = self.选择序列
        self.选择序列 += 1
        if 键 in self.事件选择:
            return self.事件选择[键] & 255
        决 = 决策_类(决策种类_类.选择卡片, arg_槽, 提示="請選擇一張卡片")
        for 卡 in 事件_类._取(self.世界.玩家, arg_受害).记录.卡片:
            if 卡 and not any(项.值 == 卡 for 项 in 决.选项):
                决.选项.append(决策选项_类(事件_类._取(服务_类.卡名, 卡 - 1), 卡))
        if not 决.选项:
            return 0
        决.选项.append(决策选项_类("放棄", 0))
        raise 待选择异常_类(决, 键)

    def _释放旅馆住客(self) -> None:
        for 人 in self.世界.玩家:
            if 人.记录.控制标志 and 人.状态.酒店天数:
                人.状态.酒店天数 = 128

    def _改建筑(self, arg_码: int, arg_升: bool) -> None:
        if 2000 < arg_码 < 4000:
            地 = 事件_类._取(self.世界.地产, arg_码 - 2000).经济
            if arg_升:
                if (not 地.连锁 and 地.等级 < 5) or (地.连锁 == 1 and 地.等级 < 1):
                    地.等级 = (地.等级 + 1) & 255
            elif 地.等级:
                地.等级 -= 1
                if 地.连锁:
                    地.等级 = 地.连锁 = 0
        elif 4000 < arg_码 < 6000:
            设 = 事件_类._取(self.世界.设施, arg_码 - 4000)
            if arg_升:
                if not 设.等级:
                    if self._玩家().控制标志 & 6:
                        设.类型 = (
                            self.随机.api_下一个() % 4 + 1 if 设.业主 == self._当前() + 1 else 0
                        )
                    else:
                        键 = self.选择序列
                        self.选择序列 += 1
                        if 键 not in self.事件选择:
                            raise 待选择异常_类(
                                决策_类(
                                    决策种类_类.建造设施,
                                    self._当前(),
                                    (arg_码 - 4000) & 65535,
                                    提示="請選擇設施類別",
                                    选项=[
                                        决策选项_类(名, i)
                                        for i, 名 in enumerate(
                                            ("公園", "旅館", "百貨公司", "加油站", "研究所")
                                        )
                                    ],
                                ),
                                键,
                            )
                        设.类型 = self.事件选择[键] & 255
                    设.等级 = (设.等级 + 1) & 255
                elif 设.类型 < 5 and 设.等级 < (1, 5, 5, 1, 5)[设.类型]:
                    设.等级 = (设.等级 + 1) & 255
            elif 设.等级:
                设.等级 -= 1
                if not 设.等级:
                    设.类型 = 0
                    self._释放旅馆住客()

    def _工程车拆屋(self) -> None:
        人, 状 = self._玩家(), self._状态()
        if not 人.控制标志 or 人.交通 & 0x83 != 3 or 状.梦游天数 or 状.酒店天数:
            return
        码 = 事件_类._取(self.世界.节点, 人.节点).类型索引
        if 2000 < 码 < 4000:
            地 = 事件_类._取(self.世界.地产, 码 - 2000).经济
            if 地.业主 == self._当前() + 1 or not 地.等级:
                return
            主, 级, 类 = 地.业主, 地.等级, 地.连锁
            地.等级 = 地.连锁 = 0
        elif 4000 < 码 < 6000:
            设 = 事件_类._取(self.世界.设施, 码 - 4000)
            if 设.业主 == self._当前() + 1 or not 设.等级:
                return
            主, 级, 类 = 设.业主, 设.等级, 设.类型
            设.等级 = 设.类型 = 0
            self._释放旅馆住客()
        else:
            return
        if 主:
            self._更新敌意(主 - 1, self._当前(), self._回绕(30 * self.世界.头.物价))
        状.保存方向 = 人.方向
        节, 楼点 = self.世界.节点[人.节点], self._地产点(码)
        self._效果(效果种类_类.工程车拆屋, self._当前(), 楼点, 码)
        效 = self.效果队列[-1]
        效.起点, 效.物件种类 = (
            self._角色点(self._当前()),
            方向_类.api_计算(楼点.x - 节.x, 楼点.y - 节.y),
        )
        效.原等级, 效.原类型 = 级, 类
        self._发事件(游戏事件种类_类.提示, "工程车拆除脚下建筑")

    def _实例位置(self, arg_码: int) -> 效果点_类:
        if arg_码 < 2000:
            物 = 事件_类._取(self.世界.节点, arg_码)
        elif arg_码 < 4000:
            物 = 事件_类._取(self.世界.地产, arg_码 - 2000)
        elif arg_码 < 6000:
            物 = 事件_类._取(self.世界.设施, arg_码 - 4000)
        elif arg_码 & 255:
            位 = arg_码 & 255
            槽 = (位 & -位).bit_length() - 1
            物 = (
                事件_类._取(self.世界.玩家, 槽).记录
                if 槽 < 4
                else 事件_类._取(self.世界.特殊角色, 槽 - 4)
            )
        else:
            号 = ((arg_码 >> 8) & 63) - 1
            物 = 事件_类._取(self.世界.节点, 事件_类._取(self.世界.物件, 号).节点)
        return 效果点_类(物.x, 物.y)

    def _掉头(self, arg_槽: int) -> None:
        人 = (
            事件_类._取(self.世界.玩家, arg_槽).记录
            if arg_槽 < 4
            else 事件_类._取(self.世界.特殊角色, arg_槽 - 4)
        )
        人.方向 = (人.方向 + 4) & 7
        节 = 事件_类._取(self.世界.节点, 人.节点)
        路 = [
            号
            for i, 号 in enumerate(节.邻居)
            if 号 and 号 != 人.上次节点 and not 节.标志 & (0x40000000 >> i)
        ]
        人.上次节点 = 路[self.随机.api_下一个() % len(路)] if 路 else 0
        self._音效(arg_槽, 56)

    def _拍卖(self, arg_码: int, arg_卖: int = -1) -> 拍卖结果_类:
        会 = 拍卖会话_类(self.世界, self.随机, arg_码, arg_卖)
        标签 = ("不加價", "加價100", "加價500", "加價1000", "加價5000", "加價10000", "退出拍賣")
        次 = 0
        while not 会.已结束:
            if 次 >= 100000:
                raise RuntimeError("auction action limit reached")
            次 += 1
            投 = 会.api_决策()
            if 投 is not None:
                键 = self.选择序列
                self.选择序列 += 1
                if 键 not in self.事件选择:
                    raise 待选择异常_类(
                        决策_类(
                            决策种类_类.拍卖,
                            投.玩家,
                            arg_码,
                            投.价格,
                            f"地產拍賣：當前出價{投.价格}",
                            [决策选项_类(标签[行], int(行)) for 行 in 投.行动],
                            不活跃玩家=投.已退出,
                        ),
                        键,
                    )
                if not 会.api_竞价(self.事件选择[键]):
                    raise RuntimeError("cached auction bid no longer legal")
            elif not 会.api_推进():
                raise RuntimeError("auction made no progress")
        结果 = 会.结果
        if 结果.赢家 is not None:
            self._发事件(游戏事件种类_类.提示, "拍卖成交", 结果.价格)
            self.事件队列[-1].主体, self.事件队列[-1].地产 = 结果.赢家, arg_码
        else:
            self._发事件(游戏事件种类_类.提示, "地产拍卖流拍")
        return 结果

    def _随机空节点(self, arg_参考: int = 0) -> int:
        可选 = []
        for i in range(1, len(self.世界.节点)):
            节 = self.世界.节点[i]
            if not 节.标志 & 0x80FFFF00 and any(节.邻居):
                if i > 255:
                    raise RuntimeError("original random node exceeds byte range")
                可选.append(i)
        if not 可选:
            raise RuntimeError("no free object node")
        for _ in range(100000):
            去 = 可选[self.随机.api_下一个() % len(可选)]
            if not arg_参考:
                return 去
            参, 节 = 事件_类._取(self.世界.节点, arg_参考), self.世界.节点[去]
            if abs(节.x - 参.x) >= 300 or abs(节.y - 参.y) >= 300:
                return 去
        raise RuntimeError("original distant-node selection cannot find an eligible node")

    def _放现有物件(self, arg_索: int, arg_节: int) -> None:
        物 = 事件_类._取(self.世界.物件, arg_索)
        if 物.节点:
            return
        物.节点, 物.剩余天数, 物.附身玩家 = arg_节, 0, 0
        if not arg_节:
            return
        节 = 事件_类._取(self.世界.节点, arg_节)
        前 = 事件_类._取(self.世界.节点, next((i for i in 节.邻居 if i), 0))
        物.方向 = 方向_类.api_计算(节.x - 前.x, 节.y - 前.y)
        节.标志 = (节.标志 | ((arg_索 + 1) << 16)) & 0xFFFFFFFF

    def _移除物件(self, arg_号: int) -> None:
        if not arg_号:
            return
        物 = 事件_类._取(self.世界.物件, arg_号 - 1)
        旧 = 物.节点
        if 16 <= 物.种类 <= 18:
            索 = 物.种类 - 15
            self.世界.道具供应[索] = (self.世界.道具供应[索] + 1) & 255
        if 物.附身玩家 and 物.附身玩家 <= len(self.世界.玩家):
            状 = self.世界.玩家[物.附身玩家 - 1].状态
            if 物.种类 == 18:
                状.附身炸弹 = 0
            else:
                if 物.种类 >= len(神明_类.神运):
                    raise RuntimeError("invalid attached god type")
                状.神明信息 = 0
                for 名, 表 in (
                    ("神运修正", 神明_类.神运),
                    ("财运修正", 神明_类.财运),
                    ("其他运修正", 神明_类.其他运),
                ):
                    setattr(状, 名, ((getattr(状, 名) - 表[物.种类] + 32768) & 65535) - 32768)
        if not 物.附身玩家:
            事件_类._取(self.世界.节点, 旧).标志 &= ~0x00FF0000
        物.节点 = 物.剩余天数 = 物.附身玩家 = 0
        if arg_号 <= 12:
            对 = (arg_号 - 1) ^ 1
            去 = self._随机空节点(旧)
            self._放现有物件(对, 去)
