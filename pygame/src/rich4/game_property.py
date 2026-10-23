# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ game.cpp 843..1503，地产/设施/公司落点和原轮盘/探望。
# ◑ 导入
from copy import deepcopy

from rich4.cards import 卡片目标_类, 目标种类_类
from rich4.economy import 经济_类
from rich4.events import 事件_类
from rich4.game_types import (
    公告种类_类,
    决策_类,
    决策位置_类,
    决策种类_类,
    决策选项_类,
    待选择异常_类,
    效果种类_类,
    游戏事件种类_类,
    游戏阶段_类,
    转盘状态_类,
)
from rich4.lottery import 彩票_类
from rich4.numeric import 扩展数_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类


# ◕ 功能
class 会话地产_类:
    """
    原地产/特殊设施/商业公司真实落点规则，支付/防御交给同一会话结算。

    更新日志：
    2026.10.24 - 保留轮盘、现金门槛、盟友分摊及源字段/调用次序。
    """

    _回绕 = staticmethod(股市_类._回绕)

    def _购地价(self, arg_地: int) -> int:
        地 = 事件_类._取(self.世界.地产, arg_地)
        return self._回绕(
            self.世界.头.物价 * self._回绕(地.地价 + self._回绕(地.经济.等级 * 地.每级造价))
        )

    def _升级价(self, arg_地: int) -> int:
        return self._回绕(self.世界.头.物价 * 事件_类._取(self.世界.地产, arg_地).每级造价)

    def _购买地产(self, arg_地: int, arg_升级: bool) -> None:
        地 = 事件_类._取(self.世界.地产, arg_地)
        费 = self._升级价(arg_地) if arg_升级 else self._购地价(arg_地)
        if 费 < 0 or self._玩家().现金 < 费:
            self._结束回合()
            return
        self._玩家().现金 = self._回绕(self._玩家().现金 - 费)
        self.已购地产 = True
        if arg_升级:
            地.经济.等级 = (地.经济.等级 + 1) & 255
        else:
            地.经济.业主, 地.到期日 = (self._当前() + 1) & 255, self._租约到期()
        self._发事件(
            游戏事件种类_类.已升级 if arg_升级 else 游戏事件种类_类.已购地,
            f"玩家{self._当前() + 1}" + ("升级房产" if arg_升级 else "买下房产"),
            费,
        )
        if arg_升级:
            self._顶楼闪光((2000 + arg_地) & 65535, 4)
        if arg_升级 and 地.经济.等级 == 5:
            self._语音(self._当前(), 15)
        else:
            数 = sum(
                另.经济.业主 == self._当前() + 1 and 另.经济.街道名 == 地.经济.街道名
                for 另 in self.世界.地产
            )
            if 数 >= 3 and (not arg_升级 or self.随机.api_下一个() % 3 == 0):
                self._语音(self._当前(), 17 if arg_升级 else 16)
        self._结束回合()

    def _普通地产(self, arg_地: int) -> None:
        if not 0 < arg_地 < len(self.世界.地产):
            self._不支持("房产记录无效，暂时无法结算")
            return
        地 = self.世界.地产[arg_地]
        经, 状 = 地.经济, self._状态()
        if not 经.业主 or 经.业主 == self._当前() + 1:
            if 状.梦游天数 or 状.神明信息 == 12:
                self._结束回合()
                return
            if 状.神明信息 in (7, 8, 15):
                self._发事件(游戏事件种类_类.提示, "神明阻止这次房产交易")
                self._结束回合()
                return
            升 = 经.业主 != 0
            if 升 and (经.连锁 or 经.等级 >= 5):
                self._结束回合()
                return
            费 = self._升级价(arg_地) if 升 else self._购地价(arg_地)
            if 费 < 0 or self._玩家().现金 < 费:
                if 费 >= 0:
                    self._公告(公告种类_类.现金不足, self._当前()).地产 = (2000 + arg_地) & 65535
                self._结束回合()
                return
            if self._人类():
                self.待决策 = 决策_类(
                    决策种类_类.升级地产 if 升 else 决策种类_类.购地,
                    self._当前(),
                    arg_地 & 65535,
                    费,
                    "升級這塊房產？" if 升 else "購買這塊房產？",
                    [决策选项_类("升級" if 升 else "購買", 1), 决策选项_类("放棄", 0)],
                )
                self._置阶段(游戏阶段_类.等待决策)
            elif 升 or self._电脑可购买(费):
                self._购买地产(arg_地, 升)
            else:
                self._结束回合()
            return
        主 = 经.业主 - 1
        if 主 >= len(self.世界.玩家):
            self._不支持("房产所有者无效，暂时无法结算")
            return
        主状 = self.世界.玩家[主].状态
        if (
            主状.盟友 == self._当前() + 1
            or 主状.神明信息 == 15
            or 主状.酒店天数
            or 主状.消失天数
            or 主状.监狱天数
            or 主状.医院天数
            or 主状.睡眠天数
            or 主状.梦游天数
            or (地.临时状态 & 0xF0 and 地.临时状态 & 15)
        ):
            self._公告免租(主状, 主, 地.临时状态, (2000 + arg_地) & 65535)
            self._结束回合()
            return
        记录 = [另.经济 for 另 in self.世界.地产[1:]]
        街 = None if 经.连锁 else 经.街道名
        租 = 经济_类.api_通行费(记录, 经.业主, self.世界.头.物价, 街)
        盟 = 主状.盟友
        盟租 = 经济_类.api_通行费(记录, 盟, self.世界.头.物价, 街) if 盟 else 0
        if 地.临时状态:
            租 = self._回绕(租 * 2)
        租 = self._回绕(租 + 盟租)
        盟比 = (
            (扩展数_类.api_从值(盟租) / 扩展数_类.api_从值(租)).api_单精度() if 盟 and 租 else 0.0
        )
        租 = self._神明租金(租)
        if not 租:
            self._结束回合()
            return

        def 动作() -> None:
            self._更新敌意(self._当前(), 主, 事件_类._除(self._回绕(租 - 盟租), 100))
            if 盟:
                self._更新敌意(self._当前(), 盟 - 1, 事件_类._除(盟租, 100))
            付者, 应付 = self._选择付租者(租, 主)
            if 付者 == 主 or (盟 and 付者 == 盟 - 1):
                return
            盟额 = (扩展数_类.api_从值(应付) * 扩展数_类.api_从值(盟比)).api_整数() if 盟 else 0
            self._付租(主, 应付, 付者, 盟 - 1 if 盟 else None, 盟额, (2000 + arg_地) & 65535)
            事件_类._取(self.世界.地产, arg_地).已移除建筑 = 应付 & 0xFFFFFFFF

        self._执行规则(动作)

    def _交易受阻(self) -> bool:
        return self._状态().神明信息 in (7, 8, 15)

    def _电脑可购买(self, arg_费: int) -> bool:
        留 = self._回绕(int(min(self.世界.头.初始资金 * 0.05, 7000.0)) * self.世界.头.物价)
        return self._玩家().现金 + self._玩家().银行 - arg_费 > 留

    def _购买设施(self, arg_设: int, arg_操作: int, arg_类: int = 0) -> None:
        设 = 事件_类._取(self.世界.设施, arg_设)
        费 = self._回绕((设.每级造价 if arg_操作 == 2 else 设.地价) * self.世界.头.物价)
        if arg_操作 == 1:
            设.类型 = arg_类 & 255
        if 费 < 0 or self._玩家().现金 < 费 or self._交易受阻():
            self._结束回合()
            return
        self._玩家().现金 = self._回绕(self._玩家().现金 - 费)
        if arg_操作 == 0:
            设.业主, 设.到期日 = (self._当前() + 1) & 255, self._租约到期()
        else:
            设.等级 = (设.等级 + 1) & 255
        self.已购地产 = True
        self._发事件(
            游戏事件种类_类.已升级 if arg_操作 else 游戏事件种类_类.已购地,
            "购买设施用地" if arg_操作 == 0 else "建设设施" if arg_操作 == 1 else "升级设施",
            费,
        )
        if arg_操作:
            self._顶楼闪光((4000 + arg_设) & 65535, 4)
        if 设.等级 == 5:
            self._语音(self._当前(), 15)
        self._结束回合()

    @staticmethod
    def _轮盘值(arg_类: int, arg_游标: int) -> int:
        行 = (
            (1, -1, 0, -1, 1, -1, 2, -1, 3, -1, 2, -1),
            (-1, -1, 1, -1, -1, 4, -1, 3, -1, -1, 2, -1),
            (1, -1, 6, -1, 5, -1, 4, -1, 3, -1, 2, -1),
            (5, -1, 3, -1, 30, -1, 20, -1, 15, -1, 10, -1),
        )[arg_类]
        while 行[arg_游标 % 12] < 0:
            arg_游标 += 1
        return 行[arg_游标 % 12]

    def _设施收费(self, arg_设: int, arg_倍: int) -> None:
        self._执行规则(lambda: self._设施收费动作(arg_设, arg_倍))

    def _神明租金(self, arg_租: int) -> int:
        神 = self._状态().神明信息
        return (
            arg_租 >> 1
            if 神 == 1
            else 0
            if 神 == 2
            else self._回绕(arg_租 + (arg_租 >> 1))
            if 神 == 5
            else self._回绕(arg_租 * 2)
            if 神 == 6
            else arg_租
        )

    def _设施收费动作(self, arg_设: int, arg_倍: int) -> None:
        设 = 事件_类._取(self.世界.设施, arg_设)
        主 = 设.业主 - 1
        if 设.类型 == 3:
            交 = self._玩家().交通 & 3
            if not 交:
                return
            总 = sum(self.骰面)
            if not self.骰面 and self._状态().龟行天数:
                总 = 1
            租 = self._回绕(self._回绕(总 * (500 if 交 == 1 else 1000)) * self.世界.头.物价)
        else:
            租 = self._回绕(
                self._回绕(事件_类._取(设.各级租金, 设.等级) * self.世界.头.物价) * arg_倍
            )
            if 设.临时状态:
                租 = self._回绕(租 * 2)
        租 = self._神明租金(租)
        if not 租:
            return
        self._更新敌意(self._当前(), 主, 事件_类._除(租, 100))
        付者, 租 = self._选择付租者(租, 主, 设.类型 == 1, 设.类型 != 1)
        if 付者 == 主:
            return
        self._付租(主, 租, 付者, None, 0, (4000 + arg_设) & 65535, 设.类型, arg_倍)
        设.已移除建筑 = 租 & 0xFFFFFFFF
        if self.阶段 == 游戏阶段_类.结束:
            return
        人, 状 = self.世界.玩家[付者].记录, self.世界.玩家[付者].状态
        if 设.类型 == 1 and 人.控制标志:
            self._清缺席(付者)
            状.酒店天数 = (arg_倍 - 1) & 255
            if not 状.酒店天数:
                状.酒店天数 = 128
            状.冬眠总天数 = (状.冬眠总天数 + arg_倍) & 255
            状.设施编号, 状.保存方向 = arg_设 & 65535, 人.方向
            事件_类._取(self.世界.节点, 人.节点).标志 &= ~(0x100 << 付者) & 0xFFFFFFFF
            人.x, 人.y = 设.x, 设.y
            self._更新敌意(付者, 主, self._回绕(self._回绕(arg_倍 * 20) * self.世界.头.物价))
            self._保险赔偿(付者, self._回绕(self._回绕(arg_倍 * 2000) * self.世界.头.物价))
            self._缺席语音(付者, arg_倍)
            self._发事件(游戏事件种类_类.提示, f"在旅馆住宿{arg_倍}天", arg_倍)

    def _特殊设施(self, arg_设: int) -> None:
        if not 0 < arg_设 < len(self.世界.设施):
            self._不支持("设施记录无效")
            return
        设, 状 = self.世界.设施[arg_设], self._状态()
        if not 设.业主 or 设.业主 == self._当前() + 1:
            if 状.梦游天数 or (not 设.业主 and 状.神明信息 == 12):
                self._结束回合()
                return
            操 = 0 if not 设.业主 else 1 if 设.等级 == 0 else 2
            上限 = (1, 5, 5, 1, 5)
            if 设.类型 >= 5 or (操 == 2 and 设.等级 >= 上限[设.类型]):
                self._结束回合()
                return
            费 = self._回绕((设.每级造价 if 操 == 2 else 设.地价) * self.世界.头.物价)
            if 费 < 0 or self._玩家().现金 < 费:
                if 费 >= 0:
                    self._公告(公告种类_类.现金不足, self._当前()).地产 = (4000 + arg_设) & 65535
                self._结束回合()
                return
            if self._人类():
                项 = (
                    [
                        决策选项_类(名, i)
                        for i, 名 in enumerate(("公園", "旅館", "百貨公司", "加油站", "研究所"))
                    ]
                    if 操 == 1
                    else [决策选项_类("購買" if 操 == 0 else "升級", 1), 决策选项_类("放棄", 0)]
                )
                类 = (
                    决策种类_类.购买设施
                    if 操 == 0
                    else 决策种类_类.建造设施
                    if 操 == 1
                    else 决策种类_类.升级设施
                )
                文 = "購買設施用地？" if 操 == 0 else "請選擇設施類別" if 操 == 1 else "升級設施？"
                self.待决策 = 决策_类(类, self._当前(), arg_设 & 65535, 费, 文, 项)
                self._置阶段(游戏阶段_类.等待决策)
            elif 操 != 0 or self._电脑可购买(费):
                类 = self.随机.api_下一个() % 4 + 1 if 操 == 1 else 0
                self._购买设施(arg_设, 操, 类)
            else:
                self._结束回合()
            return
        if 设.业主 > len(self.世界.玩家) or not 设.等级 or not 设.类型 or 设.类型 >= 4:
            self._结束回合()
            return
        主 = self.世界.玩家[设.业主 - 1].状态
        if (
            主.盟友 == self._当前() + 1
            or 主.神明信息 == 15
            or 主.酒店天数
            or 主.消失天数
            or 主.监狱天数
            or 主.医院天数
            or 主.睡眠天数
            or 主.梦游天数
            or (设.临时状态 & 0xF0 and 设.临时状态 & 15)
        ):
            self._公告免租(主, 设.业主 - 1, 设.临时状态, (4000 + arg_设) & 65535)
            self._结束回合()
            return
        if 设.类型 == 3:
            self._设施收费(arg_设, 1)
            return
        self.轮盘种类, self.轮盘设施 = 设.类型, arg_设
        self.轮盘游标, self.轮盘毫秒 = self.随机.api_下一个() % 12, 0
        盘 = 转盘状态_类(设.类型 & 255, 阶段=1, 游标=self.轮盘游标 & 255, 主体=设.业主 - 1)
        if not self._人类() or 状.梦游天数:
            倍 = self._轮盘值(设.类型, self.轮盘游标 + 51)
            self._轮盘效果(盘, 倍)
            self._设施收费(arg_设, 倍)
            return
        self.待决策 = 决策_类(
            决策种类_类.轮盘,
            self._当前(),
            arg_设 & 65535,
            提示="轉盤決定住宿天數，按停止選定" if 设.类型 == 1 else "轉盤決定消費倍數，按停止選定",
            选项=[决策选项_类("停止轉盤", 0)],
            转盘=盘,
        )
        self._置阶段(游戏阶段_类.等待决策)

    def _救援(self, arg_目标: int, arg_医院: bool, arg_人类: bool) -> None:
        名单 = self.世界.医院名单 if arg_医院 else self.世界.监狱名单
        if not 0 <= arg_目标 < len(名单) or not 名单[arg_目标]:
            return
        费 = 30 if arg_目标 < 4 else 300
        if self._玩家().点券 < 费:
            return
        if arg_目标 < len(self.世界.玩家):
            状 = self.世界.玩家[arg_目标].状态
            天 = 状.医院天数 if arg_医院 else 状.监狱天数
            if arg_人类:
                额 = self._回绕(-self._回绕(self._回绕(max(天 & 127, 1) * 100) * self.世界.头.物价))
                self._更新敌意(arg_目标, self._当前(), 额)
            if arg_医院:
                状.医院天数 = 128
            else:
                状.监狱天数 = 128
        elif arg_目标 >= 4:
            特 = 事件_类._取(self.世界.特殊角色, arg_目标 - 4)
            出 = next(
                (
                    i
                    for i, 节 in enumerate(self.世界.节点[1:], 1)
                    if 节.标志 & 255 == (5 if arg_医院 else 4)
                ),
                None,
            )
            if 出 is None:
                raise RuntimeError("rescue has no exit node")
            特.业主, 特.不活跃状态, 特.节点, 特.上次节点 = self._当前() & 255, 0, 出 & 65535, 0
            特.x, 特.y, 特.标志 = (
                self.世界.节点[出].x & 65535,
                self.世界.节点[出].y & 65535,
                0x80 | (2 if arg_医院 else 1),
            )
        else:
            return
        名单[arg_目标] = 0
        self._玩家().点券 = (self._玩家().点券 - 费) & 65535
        self._发事件(
            游戏事件种类_类.提示, f"救援玩家{arg_目标 + 1}" if arg_目标 < 4 else "释放特殊角色", 费
        )

    def _探望收容(self, arg_医院: bool) -> None:
        self.救援医院 = arg_医院
        名单 = self.世界.医院名单 if arg_医院 else self.世界.监狱名单
        if not any(名单):
            self._结束回合()
            return
        if self._人类():
            决 = 决策_类(
                决策种类_类.救援, self._当前(), 提示="探望住院角色" if arg_医院 else "探望入獄角色"
            )
            for i, 值 in enumerate(名单):
                if 值 and (i >= 4 or i < len(self.世界.玩家)):
                    名 = f"救援玩家{i + 1}" if i < 4 else f"釋放特殊角色{i - 3}"
                    决.选项.append(决策选项_类(名 + ("（30點）" if i < 4 else "（300點）"), i))
            决.选项.append(决策选项_类("離開", -1))
            self.待决策 = 决
            self._置阶段(游戏阶段_类.等待决策)
            return
        if not self.随机.api_下一个() & 1:
            self._结束回合()
            return
        策 = self._状态().救援策略
        普 = 策 in (0, 1)
        特 = 策 == 2 or (策 == 1 and self.随机.api_下一个() % 3 == 0)
        候 = [
            i for i in range(8) if 名单[i] and ((i < len(self.世界.玩家) and 普) or (i >= 4 and 特))
        ]
        if 候:
            目 = 候[self.随机.api_下一个() % len(候)]
            if (目 < 4 and self._玩家().点券 > 30) or (目 >= 4 and self._玩家().点券 >= 700):
                self._救援(目, arg_医院, False)
        self._结束回合()

    def _轮盘效果(self, arg_盘: 转盘状态_类, arg_值: int) -> None:
        盘 = deepcopy(arg_盘)
        盘.结果 = arg_值
        self._效果(效果种类_类.轮盘, self._当前(), self._角色点(self._当前()))
        self.效果队列[-1].转盘 = 盘

    def _停止轮盘效果(self, arg_决: 决策_类, arg_值: int) -> None:
        if arg_决.转盘 is None:
            return
        盘 = deepcopy(arg_决.转盘)
        盘.游标, 盘.阶段 = self.轮盘游标 & 255, 2
        self._轮盘效果(盘, arg_值)

    def _选择轮盘(self, arg_类: int, arg_司: int) -> int:
        初 = self.随机.api_下一个() % 12
        盘 = 转盘状态_类(arg_类 & 255, 阶段=1, 游标=初 & 255, 主体=arg_司)
        if not self._人类() or self._状态().梦游天数:
            值 = self._轮盘值(arg_类, 初 + 51)
            self._轮盘效果(盘, 值)
            return 值
        键 = self.选择序列
        self.选择序列 += 1
        if 键 in self.事件选择:
            return self.事件选择[键]
        self.轮盘种类, self.轮盘游标, self.轮盘毫秒 = arg_类, 初, 0
        决 = 决策_类(
            决策种类_类.轮盘,
            self._当前(),
            提示="按停止選定轉盤結果",
            选项=[决策选项_类("停止轉盤", 0)],
            转盘=盘,
        )
        raise 待选择异常_类(决, 键)

    def _公司建设目标(self) -> int:
        if self._人类():
            键 = self.选择序列
            self.选择序列 += 1
            if 键 in self.事件选择:
                return self.事件选择[键] & 65535
            决 = 决策_类(决策种类_类.地产目标, self._当前(), 提示="請選擇欲加蓋地點")
            for 表, 基, 名 in ((self.世界.地产, 2000, "房產"), (self.世界.设施, 4000, "設施")):
                for i, 地 in enumerate(表[1:], 1):
                    决.选项.append(
                        决策选项_类(
                            f"{名}{i}",
                            基 + i,
                            决策位置_类(地.x, 地.y),
                            卡片目标_类(目标种类_类.地产, (基 + i) & 65535),
                        )
                    )
            决.选项.append(决策选项_类("取消", 0))
            raise 待选择异常_类(决, 键)
        选, 分 = 0, 0
        for i, 地 in enumerate(self.世界.地产[1:], 1):
            经 = 地.经济
            if (
                经.业主 == self._当前() + 1
                and not 经.连锁
                and 经.等级 < 5
                and 经.各级租金[经.等级] > 分
            ):
                分, 选 = 经.各级租金[经.等级], (2000 + i) & 65535
        上限 = (1, 5, 5, 1, 5)
        for i, 设 in enumerate(self.世界.设施[1:], 1):
            if (
                设.业主 == self._当前() + 1
                and 设.类型 < 5
                and 设.等级 < 上限[设.类型]
                and 设.地价 > 分
            ):
                分, 选 = 设.地价, (4000 + i) & 65535
        return 选

    def _原始股(self, arg_司: int) -> None:
        司 = 事件_类._取(self.世界.公司, arg_司)
        if not self._玩家().控制标志 or self._状态().梦游天数 or 司.剩余股份 <= 0:
            return
        价 = 事件_类._除(司.估值, 10000)
        if 价 <= 0:
            return
        最多 = min(事件_类._除(self._玩家().现金, 价), 1000, 司.剩余股份)
        if 最多 <= 0:
            return
        数 = 0
        if self._人类():
            键 = self.选择序列
            self.选择序列 += 1
            if 键 in self.事件选择:
                数 = self.事件选择[键]
            else:
                决 = 决策_类(
                    决策种类_类.初级股票,
                    self._当前(),
                    arg_司 & 65535,
                    价,
                    f"认购原始股：每股{价}元，最多{最多}股",
                    [决策选项_类("認購", 1), 决策选项_类("放棄", 0)],
                    最多,
                )
                raise 待选择异常_类(决, 键)
        else:
            留 = self._回绕(int(self.世界.头.初始资金 * 0.3) * self.世界.头.物价)
            可花 = self._回绕(self._玩家().现金 - 留)
            if 可花 > 0:
                数 = min(最多, 事件_类._除(可花, 价))
        if 数 > 0:
            果 = 股市_类.api_买入(self.世界, self._当前(), 司.股票索引, 数, False)
            self._发事件(游戏事件种类_类.银行转账, f"认购原始股{数}股", 果.费用)

    def _商业公司(self, arg_司: int) -> None:
        if not 0 < arg_司 < len(self.世界.公司):
            self._不支持("商业公司记录无效")
            return

        def 动作() -> None:
            司 = 事件_类._取(self.世界.公司, arg_司)
            自有, 租, 离 = 司.业主 == self._当前() + 1, 0, 0
            if 司.业主:
                类 = 司.类型
                if 类 == 4:
                    期 = self._选择轮盘(3, arg_司)
                    self._状态().保险天数 = (self._状态().保险天数 + 期) & 127
                    if not 自有:
                        租 = self._回绕(self._回绕(司.通行费 * 期) * self.世界.头.物价)
                elif 类 == 11:
                    目 = self._公司建设目标()
                    if 目:
                        self._改建筑(目, True)
                        if 自有:
                            self._改建筑(目, True)
                        else:
                            基 = (
                                事件_类._取(self.世界.地产, 目 - 2000).地价
                                if 目 < 4000
                                else 事件_类._取(self.世界.设施, 目 - 4000).地价
                            )
                            租 = self._回绕(基 * self.世界.头.物价)
                    elif not 自有:
                        租 = self._回绕(1000 * self.世界.头.物价)
                elif not 自有:
                    if 类 == 1:
                        离 = self._选择轮盘(0, arg_司)
                        租 = self._回绕(self._回绕(司.通行费 * 离) * self.世界.头.物价)
                        if not 离:
                            self._语音(self._当前(), 2)
                    elif 类 == 3:
                        租 = self._回绕(司.通行费 * self._回绕(self.世界.轮数))
                    elif 类 in (5, 6, 12):
                        总 = sum(self.骰面) & 0xFFFFFFFF
                        if not self.骰面 and self._状态().龟行天数:
                            总 = 1
                        if 类 == 12 or self._玩家().交通:
                            因 = 1 if 类 == 12 else 1 << (((self._玩家().交通 & 3) - 1) & 31)
                            租 = self._回绕(
                                self._回绕(司.通行费 * self._回绕(总 * 因)) * self.世界.头.物价
                            )
            租 = self._神明租金(租)
            付者, 租 = self._选择付租者(租, -1, 离 != 0)
            if 付者 == self._当前():
                self._金额语音(self._当前(), 租, 9)
            已付 = self._付款(付者, arg_司 + 100, 租, 0)
            if 已付:
                self._发事件(游戏事件种类_类.已付租, "向公司支付费用", 已付)
            if self.阶段 == 游戏阶段_类.结束:
                return
            if 离 and self.世界.玩家[付者].记录.控制标志:
                self._消失(付者, 离, 0)
            self._原始股(arg_司)

        self._执行规则(动作)

    def _开彩票(self) -> None:
        if not self._人类():
            号 = 彩票_类.api_随机购票(self.世界, self.随机, self._当前())
            if 号 is not None:
                self._发事件(游戏事件种类_类.提示, f"购买彩票{号}", 1000)
            self._结束回合()
            return
        决 = 决策_类(决策种类_类.彩票, self._当前(), 金额=1000, 提示="選擇彩票號碼（每張1000元）")
        if self._玩家().现金 >= 1000:
            决.选项.extend(决策选项_类(str(号), 号) for 号 in 彩票_类.api_可售号码(self.世界))
        决.选项.append(决策选项_类("離開", 0))
        self.待决策 = 决
        self._置阶段(游戏阶段_类.等待决策)

    def _收随机卡(self) -> None:
        数 = sum(self.世界.卡供应)
        if 数:
            票, 卡 = self.随机.api_下一个() % 数, 0
            while 票 >= 事件_类._取(self.世界.卡供应, 卡):
                票 -= self.世界.卡供应[卡]
                卡 += 1
            服务_类._库存(self.世界, self._当前()).api_收卡((卡 + 1) & 255)
            价 = 服务_类.卡价[卡]
            if 价 > 100:
                self._语音(self._当前(), 0)
            elif 价 > 50:
                self._语音(self._当前(), self.随机.api_下一个() & 1)
            elif 价:
                self._语音(self._当前(), 2)
            self._发事件(游戏事件种类_类.提示, f"获得卡片{卡 + 1}")
        self._结束回合()
