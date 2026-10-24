# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ game.cpp 2198..2797，前瞻与实例位置由相邻会话组件实现。
# ◑ 导入
from copy import deepcopy

from rich4.board_models import 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.cards import 卡片回调_类, 卡片目标_类, 目标种类_类
from rich4.direction import 方向_类
from rich4.events import 事件_类, 事件回调_类
from rich4.game_types import (
    公告种类_类,
    决策_类,
    决策位置_类,
    决策种类_类,
    决策选项_类,
    待选择异常_类,
    效果种类_类,
    未支持规则异常_类,
    游戏事件_类,
    游戏事件种类_类,
    游戏阶段_类,
    语句表_类,
    转盘状态_类,
)
from rich4.gods import 神明_类, 神明回调_类, 神明结果_类, 金钱转盘_类
from rich4.holidays import 节日_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类
from rich4.tools import 道具_类, 道具回调_类


# ◕ 功能
class 会话动作_类:
    """
    原范围/目标、神明/事件/卡片/道具真实回调与机器人/时光机。

    更新日志：
    2026.10.24 - 保留稀疏或合成扫描、共享随机与原暂停选择次序。
    """

    _回绕 = staticmethod(股市_类._回绕)

    def _实例编码(self, arg_x: int, arg_y: int, arg_半径: int) -> list[int]:
        if self.世界.相机旋转 > 7:
            raise RuntimeError("invalid world camera rotation")
        相机, 像素 = 相机_类((arg_x, arg_y), self.世界.相机旋转), {}

        def 放(arg_点: tuple[int, int], arg_码: int) -> None:
            屏 = 棋盘投影_类.api_投影(arg_点, 相机)
            if 屏 is not None and 0 <= 屏[0] < 440 and 40 <= 屏[1] < 480:
                键 = (屏[1] - 40) * 440 + 屏[0]
                像素[键] = 像素.get(键, 0) | (arg_码 & 65535)

        for i, 人 in enumerate(self.世界.玩家):
            if 人.记录.x and not 人.状态.消失天数:
                放((人.记录.x, 人.记录.y), 0x8000 | (1 << i))
        for i, 特 in enumerate(self.世界.特殊角色[:4]):
            if 特.x and not 特.不活跃状态:
                放((特.x, 特.y), 0x8000 | (0x10 << i))
        for i, 物 in enumerate(self.世界.物件):
            if 物.节点 and not 物.附身玩家:
                节 = 事件_类._取(self.世界.节点, 物.节点)
                放((节.x, 节.y), 0x8000 | ((i + 1) << 8))
        for i, 地 in enumerate(self.世界.地产[1:], 1):
            if 地.经济.等级 or 地.经济.业主:
                放((地.x, 地.y), 2000 + i)
        for i, 设 in enumerate(self.世界.设施[1:], 1):
            if 设.等级 or 设.业主:
                放((设.x, 设.y), 4000 + i)
        for i, 公 in enumerate(self.世界.公司[1:], 1):
            if 公.精灵:
                放((公.x, 公.y), 6000 + i)
        首, 末 = (0, 440) if arg_半径 < 0 else (220 - arg_半径, 220 + arg_半径)
        if 首 < 0 or 末 > 440:
            raise ValueError("pick radius outside viewport")
        return [
            值
            for 键, 值 in sorted(像素.items())
            if 值 and 首 <= 键 // 440 < 末 and 首 <= 键 % 440 < 末
        ]

    def _范围损坏(
        self,
        arg_x: int,
        arg_y: int,
        arg_模式: int,
        arg_人物: bool,
        arg_源: int = -1,
        arg_半径: int = 100,
    ) -> None:
        目标 = self._实例编码(arg_x, arg_y, arg_半径)
        for 码 in 目标:
            if 2000 < 码 < 4000:
                地 = 事件_类._取(self.世界.地产, 码 - 2000)
                if arg_源 >= 0 and 地.经济.业主:
                    怒 = 地.经济.等级 * 30 if arg_模式 else 30
                    self._更新敌意(地.经济.业主 - 1, arg_源, self._回绕(怒 * self.世界.头.物价))
                if arg_模式:
                    地.经济.业主 = 地.经济.等级 = 地.经济.连锁 = 地.到期日 = 0
                else:
                    if 地.经济.等级:
                        地.经济.等级 -= 1
                    if 地.经济.连锁:
                        地.经济.等级 = 地.经济.连锁 = 0
            elif 4000 < 码 < 6000:
                设 = 事件_类._取(self.世界.设施, 码 - 4000)
                if arg_源 >= 0 and 设.业主:
                    怒 = 设.等级 * 30 if arg_模式 else 30
                    self._更新敌意(设.业主 - 1, arg_源, self._回绕(怒 * self.世界.头.物价))
                if arg_模式:
                    设.业主 = 设.等级 = 设.类型 = 设.到期日 = 0
                    self._释放旅馆住客()
                else:
                    if 设.等级:
                        设.等级 -= 1
                    if not 设.等级:
                        设.类型 = 0
                        self._释放旅馆住客()
            elif arg_人物 and 码 & 0x8000:
                for i in range(len(self.世界.玩家)):
                    if 码 & (1 << i):
                        self._受伤(i)
                for i in range(4, 8):
                    if 码 & (1 << i):
                        self._收容(i, 0, True)
                号 = (码 >> 8) & 63
                if 号:
                    self._移除物件(号)
        if arg_人物:
            for i, 人 in enumerate(self.世界.玩家):
                if 人.记录.控制标志 & 0x40:
                    self._收容(i, 3, True)

    def _检查神明(self, arg_果: 神明结果_类) -> None:
        if not arg_果.支持:
            raise 未支持规则异常_类(arg_果.消息)
        if arg_果.消息:
            self._发事件(游戏事件种类_类.提示, arg_果.消息)

    def _选择神明金额(self, arg_类: int) -> int:
        if not self._人类() or self._状态().梦游天数:
            示 = 转盘状态_类(arg_类, 阶段=1, 种子=self.随机.状态)
            示.结果 = 神明_类.api_自动金额(arg_类, self.随机)
            self._效果(效果种类_类.金额转盘, self._当前(), self._角色点(self._当前()))
            self.效果队列[-1].物件种类, self.效果队列[-1].转盘 = arg_类, 示
            return 示.结果
        键 = self.选择序列
        self.选择序列 += 1
        if 键 in self.事件选择:
            if 键 not in self.选择随机状态:
                raise IndexError("missing spinner random state")
            self.随机.状态 = self.选择随机状态[键]
            return self.事件选择[键]
        self.金钱转盘, self.转盘随机.状态, self.转盘毫秒 = 金钱转盘_类(arg_类), self.随机.状态, 0
        raise 待选择异常_类(
            决策_类(
                决策种类_类.金额转盘,
                self._当前(),
                提示="按停止決定金額",
                选项=[决策选项_类("停止", 1)],
                转盘=转盘状态_类(arg_类),
            ),
            键,
        )

    def _神明升级(self, arg_码: int) -> int:
        上限 = 5
        if 2000 < arg_码 < 4000:
            前 = 事件_类._取(self.世界.地产, arg_码 - 2000).经济.等级
        elif 4000 < arg_码 < 6000:
            前 = 事件_类._取(self.世界.设施, arg_码 - 4000).等级
        else:
            return 0
        self._改建筑(arg_码, True)
        self._顶楼闪光(arg_码, 前)
        if arg_码 < 4000:
            地 = self.世界.地产[arg_码 - 2000].经济
            后 = 地.等级
            if 地.连锁:
                上限 = 1
        else:
            设 = self.世界.设施[arg_码 - 4000]
            后 = 设.等级
            if 设.类型 < 5:
                上限 = (1, 5, 5, 1, 5)[设.类型]
        return 1 | (0x80 if 后 == 上限 else 0) if 后 > 前 else 0

    def _神明回调(self) -> 神明回调_类:
        def 医院(arg_槽: int, arg_额: int) -> None:
            if self.地雷待处理:
                self._效果(效果种类_类.爆炸, arg_槽, self._角色点(arg_槽))
                self._语句(arg_槽, 语句表_类.道具, 15, 1)
            self._受伤(arg_槽)
            self._收容(arg_槽, arg_额, True)

        def 降级(arg_码: int) -> None:
            self._改建筑(arg_码, False)
            self._效果(效果种类_类.恶魔烟, self._当前(), self._地产点(arg_码), arg_码)

        def 现身(arg_槽: int, arg_类: int) -> None:
            self._效果(效果种类_类.神明出现, arg_槽, self._角色点(arg_槽))
            self.效果队列[-1].物件种类 = arg_类

        def 离开(arg_槽: int, arg_类: int) -> None:
            self._效果(效果种类_类.神明离开, arg_槽, self._角色点(arg_槽))
            self.效果队列[-1].物件种类 = arg_类
            self.效果队列[-1].方向 = 事件_类._取(self.世界.玩家, arg_槽).记录.方向

        def 狗(arg_槽: int, arg_步行: bool) -> None:
            点 = self._角色点(arg_槽)
            self._地图影片(
                效果种类_类.狗打架 if arg_步行 else 效果种类_类.狗撞车,
                arg_槽,
                点,
                点 if arg_步行 else None,
            )

        return 神明回调_类(
            移除物件=self._移除物件,
            金额=self._选择神明金额,
            付款=self._付款,
            游戏结束=lambda: self.阶段 == 游戏阶段_类.结束,
            医院=医院,
            语音=self._语音,
            升级=self._神明升级,
            降级=降级,
            敌意=self._更新敌意,
            现身=现身,
            到达=lambda 槽, 类: self._公告(公告种类_类.神明出现, 槽, 类),
            离开=离开,
            声音=self._音效,
            狗=狗,
        )

    def _事件回调(self) -> 事件回调_类:
        def 医院(arg_槽: int, arg_天: int) -> None:
            self._受伤(arg_槽)
            self._收容(arg_槽, arg_天, True)

        def 新闻(arg_号: int, arg_码: int) -> None:
            self._效果(效果种类_类.新闻影片, self._当前(), self._地产点(arg_码), arg_码)
            self.效果队列[-1].物件种类 = arg_号

        return 事件回调_类(
            语音=self._语音,
            付款=self._付款,
            监狱=lambda 槽, 天: self._收容(槽, 天, False),
            医院=医院,
            消失=self._消失,
            防御=self._尝试防御卡,
            新闻画面=新闻,
            贷款到期=self._设置贷款日,
            选卡=self._选择受害卡,
            拍卖=self._拍卖,
            范围损坏=self._范围损坏,
            卖股=lambda 槽, 股, 数, 银: 股市_类.api_卖出(self.世界, 槽, 股, 数, 银),
            更新股票=lambda 股: 股市_类.api_强制行情(self.世界, 股),
        )

    @staticmethod
    def _目标编码(arg_对: 卡片目标_类) -> int:
        return (int(arg_对.种类) << 16) | arg_对.数值

    @staticmethod
    def _目标名(arg_对: 卡片目标_类) -> str:
        类, 值 = arg_对.种类, arg_对.数值
        if 类 == 目标种类_类.角色:
            return f"玩家{值 + 1}" if 值 < 4 else f"特殊角色{值 - 3}"
        if 类 == 目标种类_类.地产:
            return f"房產{值 - 2000}" if 值 < 4000 else f"設施{值 - 4000}"
        if 类 == 目标种类_类.股票:
            return f"股票{值 + 1}"
        if 类 == 目标种类_类.物件:
            return f"地圖物件{值}"
        if 类 == 目标种类_类.卡片:
            return 事件_类._取(服务_类.卡名, 值 - 1)
        if 类 == 目标种类_类.道具:
            return 事件_类._取(服务_类.道具名, 值 - 1)
        raise RuntimeError("invalid card target kind")

    def _选择目标(
        self, arg_选: list[卡片目标_类], arg_标题: str, arg_受害: int | None = None
    ) -> 卡片目标_类 | None:
        键 = self.选择序列
        self.选择序列 += 1
        if 键 in self.事件选择:
            答 = self.事件选择[键]
            if 答 < 0:
                return None
            for 对 in arg_选:
                if self._目标编码(对) == 答:
                    return 对
            raise RuntimeError("cached card target no longer valid")
        决 = 决策_类(决策种类_类.行动目标, self._当前(), 提示=arg_标题)
        for 对 in arg_选:
            项 = 决策选项_类(self._目标名(对), self._目标编码(对), 对象=对)
            码 = None
            if 对.种类 == 目标种类_类.角色:
                码 = (0x8000 | (1 << 对.数值)) & 65535
            elif 对.种类 == 目标种类_类.地产:
                码 = 对.数值
            elif 对.种类 == 目标种类_类.物件:
                码 = (0x8000 | (对.数值 << 8)) & 65535
            if 码 is not None:
                点 = self._实例位置(码)
                项.位置 = 决策位置_类(点.x, 点.y)
            决.选项.append(项)
        决.选项.append(决策选项_类("取消", -1))
        决.被抢玩家 = arg_受害
        raise 待选择异常_类(决, 键)

    def _选择设施(self, arg_槽: int) -> int | None:
        if 事件_类._取(self.世界.玩家, arg_槽).记录.控制标志 != 1:
            return self.随机.api_下一个() % 4 + 1
        键 = self.选择序列
        self.选择序列 += 1
        if 键 in self.事件选择:
            return None if self.事件选择[键] < 0 else self.事件选择[键] & 255
        raise 待选择异常_类(
            决策_类(
                决策种类_类.行动目标,
                arg_槽,
                提示="請選擇設施類別",
                选项=[
                    决策选项_类(名, i)
                    for i, 名 in enumerate(("公園", "旅館", "百貨公司", "加油站", "研究所"))
                ]
                + [决策选项_类("取消", -1)],
            ),
            键,
        )

    def _卡片回调(self) -> 卡片回调_类:
        def 选目标(arg_卡: int, arg_选: list[卡片目标_类]) -> 卡片目标_类 | None:
            对 = self._选择目标(arg_选, 事件_类._取(服务_类.卡名, arg_卡 - 1) + "：選擇目標")
            self.选定卡目标 = 对
            return 对

        def 选库存(arg_卡: int, arg_受害: int) -> 卡片目标_类 | None:
            选 = []
            人 = 事件_类._取(self.世界.玩家, arg_受害).记录
            for 卡 in 人.卡片:
                对 = 卡片目标_类(目标种类_类.卡片, 卡)
                if 卡 and 对 not in 选:
                    选.append(对)
            for i in range(13):
                if 人.道具[i]:
                    选.append(卡片目标_类(目标种类_类.道具, i + 1))
            return self._选择目标(选, "請選擇要搶的卡片或道具", arg_受害)

        def 抢得(arg_槽: int, arg_受害: int, arg_物: 卡片目标_类, arg_预置: bool) -> None:
            if arg_预置:
                框 = self._公告(
                    公告种类_类.抢得, self._当前(), 1 if arg_物.种类 == 目标种类_类.道具 else 0
                )
                框.主体, 框.值 = arg_受害, arg_物.数值

        def 说(arg_槽: int, arg_行: int, arg_卡: int, arg_表情: int) -> None:
            if arg_行 == 2 and arg_卡 in (11, 12):
                self._卡图()
            self._卡片语句(arg_槽, arg_行, arg_卡, arg_表情)

        def 被动卡(arg_槽: int, arg_卡: int) -> None:
            人 = 事件_类._取(self.世界.玩家, arg_槽).记录
            self.事件队列.append(
                游戏事件_类(
                    游戏事件种类_类.提示,
                    arg_槽,
                    节点=人.节点,
                    消息="使用" + 事件_类._取(服务_类.卡名, arg_卡 - 1),
                    卡片=arg_卡,
                )
            )

        return 卡片回调_类(
            **vars(self._事件回调()),
            敌意=self._更新敌意,
            转身=self._掉头,
            改建筑=self._改建筑,
            释放酒店=lambda 槽: self._释放旅馆住客(),
            拍卖地产=lambda 码, 卖: self._拍卖(码, 卖).赢家 is not None,
            选择目标=选目标,
            选择库存=选库存,
            抢得=抢得,
            选择设施=self._选择设施,
            卡片语音=说,
            被动卡=被动卡,
            免付=self._尝试免付卡,
            嫁祸=self._尝试嫁祸卡,
            移除物件=self._移除物件,
            神明附身=lambda 槽, 号: self._检查神明(
                神明_类.api_附身(
                    self.世界, self.随机, 槽, 号, self.世界.玩家[槽].记录.节点, self._神明回调()
                )
            ),
            神明脱离=lambda 槽: self._检查神明(神明_类.api_脱离(self.世界, 槽, self._神明回调())),
            休市=lambda: self.世界.新闻影响天数 != 0
            or 节日_类.api_休市(self._日期(), self.世界.头.地图, self.世界.头.阶段),
            前瞻节点=self._前瞻,
            附近实例=lambda 槽: self._实例编码(
                self.世界.玩家[槽].记录.x, self.世界.玩家[槽].记录.y, -1
            ),
        )

    def _道具目标(self, arg_物: int, arg_源: int = 0) -> list[int]:
        标 = 道具_类.api_选择位(arg_物, arg_源)
        掩 = 标 & 255
        if 掩 & 0x40:
            掩 = (掩 & 0x80) | 0x37
        筛 = (标 >> 8) & 255
        相机 = 相机_类((self._玩家().x, self._玩家().y), self.世界.相机旋转 & 255)

        def 可见(arg_x: int, arg_y: int) -> bool:
            if 掩 & 0x80:
                return True
            屏 = 棋盘投影_类.api_投影((arg_x, arg_y), 相机)
            return 屏 is not None and 0 <= 屏[0] < 440 and 40 <= 屏[1] < 480

        选 = []
        if 掩 & 1:
            for i, 节 in enumerate(self.世界.节点[1:], 1):
                if 可见(节.x, 节.y) and (arg_物 not in (2, 3, 4) or not 节.标志 & 0x00FFFF00):
                    选.append(i & 65535)
        if 掩 & 2:
            for i, 地 in enumerate(self.世界.地产[1:], 1):
                if 可见(地.x, 地.y) and (筛 != 8 or not (地.经济.业主 or 地.经济.等级)):
                    选.append((2000 + i) & 65535)
        if 掩 & 4:
            for i, 设 in enumerate(self.世界.设施[1:], 1):
                if 可见(设.x, 设.y) and (筛 != 8 or not (设.业主 or 设.等级)):
                    选.append((4000 + i) & 65535)
        if 掩 & 0x10:
            for i, 人 in enumerate(self.世界.玩家):
                if (
                    人.记录.x
                    and 人.记录.控制标志
                    and not 人.状态.消失天数
                    and 可见(人.记录.x, 人.记录.y)
                ):
                    选.append((0x8000 | (1 << i)) & 65535)
            for i, 特 in enumerate(self.世界.特殊角色[:4]):
                if 特.x and not 特.不活跃状态 and 可见(特.x, 特.y):
                    选.append((0x8000 | (0x10 << i)) & 65535)
        if 掩 & 0x20:
            for i, 物 in enumerate(self.世界.物件):
                if 物.节点:
                    节 = 事件_类._取(self.世界.节点, 物.节点)
                    if 可见(节.x, 节.y):
                        选.append((0x8000 | ((i + 1) << 8)) & 65535)
        return 选

    def _选择道具目标(self, arg_物: int, arg_源: int) -> int:
        键 = self.选择序列
        self.选择序列 += 1
        if 键 in self.事件选择:
            return self.事件选择[键] & 65535
        标题 = "選擇目的地" if arg_源 else "選擇點數" if arg_物 == 8 else "選擇目標"
        决 = 决策_类(决策种类_类.行动目标, self._当前(), 提示=标题)
        if arg_物 == 8:
            决.选项 = [决策选项_类(f"{i}點", i) for i in range(1, 7)]
        else:
            for 码 in self._道具目标(arg_物, arg_源):
                对 = None
                if 2000 <= 码 < 6000:
                    对 = 卡片目标_类(目标种类_类.地产, 码)
                elif 码 >= 6000 and 码 & 255:
                    位 = 码 & 255
                    对 = 卡片目标_类(目标种类_类.角色, (位 & -位).bit_length() - 1)
                elif 码 >= 6000:
                    对 = 卡片目标_类(目标种类_类.物件, (码 >> 8) & 63)
                点 = self._实例位置(码)
                决.选项.append(
                    决策选项_类(
                        self._目标名(对) if 对 is not None else "道路",
                        码,
                        决策位置_类(点.x, 点.y),
                        对,
                    )
                )
        决.选项.append(决策选项_类("取消", 0))
        raise 待选择异常_类(决, 键)

    def _机器人(self, arg_槽: int) -> None:
        主 = deepcopy(事件_类._取(self.世界.玩家, arg_槽).记录)
        特 = self.世界.特殊角色[4]
        特.x, 特.y, 特.节点, 特.上次节点 = 主.x, 主.y, 主.节点, 主.上次节点
        特.业主, 特.方向, 特.不活跃状态 = arg_槽 & 255, 主.方向, 0
        for _ in range(9):
            旧 = 事件_类._取(self.世界.节点, 特.节点)
            路 = [
                号
                for i, 号 in enumerate(旧.邻居)
                if 号 and 号 != 特.上次节点 and not 旧.标志 & (0x40000000 >> i)
            ]
            去 = 路[self.随机.api_下一个() % len(路)] if 路 else 特.上次节点
            节 = 事件_类._取(self.世界.节点, 去)
            特.上次节点, 特.节点 = 特.节点, 去
            特.方向 = 方向_类.api_计算(节.x - 特.x, 节.y - 特.y)
            特.x, 特.y = 节.x & 65535, 节.y & 65535
            物 = (节.标志 >> 16) & 255
            if 物:
                self._移除物件(物)
            self.事件队列.append(
                游戏事件_类(游戏事件种类_类.提示, arg_槽, 节点=去, 消息="机器娃娃清理道路")
            )
        特.不活跃状态 = 3

    def _恢复上次(self) -> bool:
        槽 = self._当前()
        if self.上一回合[槽] is None:
            return False
        头, 旋转, 租期 = deepcopy(self.世界.头), self.世界.相机旋转, self.世界.租约模式
        self.世界.api_覆盖(self.上一回合[槽])
        日期, 物价, 初始 = self.世界.头.日期, self.世界.头.物价, self.世界.头.初始资金
        self.世界.头 = 头
        self.世界.头.日期, self.世界.头.物价, self.世界.头.初始资金 = 日期, 物价, 初始
        self.世界.相机旋转, self.世界.租约模式 = 旋转, 租期
        self._发事件(游戏事件种类_类.提示, "时光机回到上次出发前")
        return True

    def _道具回调(self) -> 道具回调_类:
        def 遥控骰(arg_槽: int, arg_数: int) -> None:
            self.强制骰 = arg_数
            self._开始掷骰()

        def 升级(arg_码: int) -> None:
            前 = self._地产层(arg_码)
            self._改建筑(arg_码, True)
            self._效果(效果种类_类.免费建设, self._当前(), self._地产点(arg_码), arg_码)
            self._顶楼闪光(arg_码, 前)

        def 传送前(arg_槽: int) -> None:
            if arg_槽 == self._当前() and self._玩家().控制标志 & 1:
                self.上一回合[arg_槽] = deepcopy(self.世界)
            self._清缺席(arg_槽)

        def 爆炸(arg_码: int, arg_核弹: bool, arg_槽: int) -> None:
            点 = self._实例位置(arg_码)
            self._范围损坏(
                点.x & 65535,
                点.y & 65535,
                1 if arg_核弹 else 0,
                True,
                arg_槽,
                -1 if arg_核弹 else 100,
            )
            self._效果(
                效果种类_类.核弹 if arg_核弹 else 效果种类_类.飞弹,
                arg_槽,
                点,
                arg_码 if 2000 < arg_码 < 6000 else 0,
            )

        return 道具回调_类(
            机器人=self._机器人,
            语音=lambda 槽, 行: self._语句(槽, 语句表_类.道具, 行, 0),
            恢复上次=self._恢复上次,
            遥控骰=遥控骰,
            升级=升级,
            传送前=传送前,
            爆炸=爆炸,
        )
