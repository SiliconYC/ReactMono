# Pygame 忠实移植工作区

**尚未完成完整游戏移植。** 总任务 [#139](https://github.com/SiliconYC/ReactMono/issues/139) 保持开放，首阶段 [#140](https://github.com/SiliconYC/ReactMono/issues/140) 建立资源、画布与差分基础。

## 导航

- [设计、参考和最终验收门槛](DESIGN.md)。
- [逐阶段实施计划](PLAN.md) 与 [持续执行台账](PROGRESS.md)。
- [源码规模与依赖说明](SOURCE_SCALE.md)；[完整语法清单与逐函数矩阵](source-inventory.json)。
- [功能覆盖与规则依据](COVERAGE.md)。
- [资源和动画接口](RESOURCES.md)、[世界/存档接口](WORLD.md) 与 [数值/股市契约](NUMERIC.md)。
- [原股票电脑评分、排序与贷款门控](STOCKS_AI.md)。
- [原道具电脑策略、投影选择缓冲与EDX边界](TOOLS_AI.md)。
- [原卡片电脑策略、八槽访问与持续参数](CARDS_AI.md)。
- [三个原小游戏逐tick逻辑及场景/声音接口](MINIGAMES.md)。
- [小游戏原画面像素对照与可操作Pygame入口](MINIGAME_PRESENTATION.md)。
- [原生界面字体、编码与商业文字边界](NATIVE_UI.md)。
- [原MainScreen、GO/骰子时钟与界面集成进度](MAIN_SCREEN.md)。
- [原卡片/道具、目标、商店、魔法与医院/监狱屏幕](ITEM_SCREENS.md)。
- [原地图信息、帮助、开局与结局组件](AUXILIARY_UI.md)。
- [主音频策略、WAV转换、限幅及待完成播放链](AUDIO.md)；[正式主应用接线记录](APPLICATION.md)。
- [板面场景、待播人物和电影规格/播放进度](EFFECTS.md)。
- [主会话实施顺序](GAMESESSION_PLAN.md) 与 [事务/表现增量和真实闭环缺口](GAMESESSION.md)。
- 主会话增量：[金融结算](GAMESESSION_FINANCE.md)、[角色与被动防御](GAMESESSION_ACTORS.md)；公开会话自然差分继续在上述主会话记录更新。
- [商店/魔法接口](SERVICES.md) 与 [节日/彩票规则](CALENDAR_LOTTERY.md)。
- [拍卖会话和数值依据](AUCTION.md)。
- [私下交易与电脑市场](TRADING.md)。
- [特殊移动角色、回调顺序与部分失败](SPECIAL_ACTORS.md)。
- [神明、地上对象与原金钱转盘](GODS.md)。
- [新闻/命运牌堆、原事件与数值顺序](EVENTS.md)。
- [十三道具、交通、传送与消耗顺序](TOOLS.md)。
- [主动卡片、目标与被动反制接口](CARDS.md)。
- [GND与原定点地形扫描](TERRAIN.md)。
- [原查表投影、反投影与渲染快照](PROJECTION.md)。
- [原地图合成、遮挡与性能边界](BOARD.md)。
- [验收、失败与修复记录](ACCEPTANCE.md)。
- [可复现资源差分报告](evidence/assets-differential.json)。
- [子项目运行说明](../../../pygame/README.md) 与 [许可证边界](../../../pygame/NOTICE.md)。

## 证据约定

「源码推断」只说明固定源码中的行为；「自动测试」须有运行命令、输入与结果；「Agent 图形操作」须真实窗口与交互证据；「真人试玩」须真实人的验收记录。「未验证」不得折算成功。C++ 差分一致不等于已证明与 1998 年官方版完全一致。

原版商业素材、解码图像、动画及截图只保存在本机忽略目录。公开证据只保留不包含商业内容的数值、版本、哈希与文字结论。

- [原消息层、公告与决策文字](MESSAGES.md)：真实画布/时钟与外部PE规则映射、失败及验收边界。

- [移动主板面场景](MAIN_SCENE.md)：端点插值、旧人物/地产覆盖、相机优先级与源码切片验证边界。

- [原顺序表现队列](PRESENTATION_QUEUE.md)：事件位置交错、暂停/忙碌门控及真实宿主接线要求。

- [原金额机与爱神轮盘](SPINNERS.md)：原屏幕、私有重放、声音/按钮时序和实际画布差分。

- [原股利、开奖与月末报告](MONTHLY.md)：真实电影/状态/画布对照、引用修复与票面暗化性能。

数字输入与原键盘/量尺边界见 [数字板](NUMBER_PAD.md)，已完成组件差分，金融界面接线与完整窗口操作仍待验。

银行ATM/柜台/董事室与一级股提示的直接原组件差分见 [银行屏幕](BANK_SCREENS.md)，正式主程序、股票及其它金融界面继续实施。

原股票报价、持仓、公司资讯/历史图/股权饼图及红黑卡目标组件见 [股票屏幕](STOCK_SCREENS.md)，实际主程序与规则接线仍在实施。

原Data517设施选择与Panel77托管设置组件见 [设施与托管](FACILITY_AI_UI.md)，真实主应用和自然操作流程仍待接线。

原Data1主菜单与Jump新局设置/骑乘/私有MT见 [主菜单与新局](MAIN_MENU_SETUP.md)，完整应用仍待接通其真实回调。

原Data3选项与Data520存读档槽见 [选项与存档槽](OPTIONS_SAVE_SLOTS.md)，真实文件/音频及完整应用仍待接通。

原Panel9资产/地产/股票查询和源码估价口径见 [玩家查询](PLAYER_INFO.md)，完整主应用接线仍在实施。

原Panel26出价/成交和Panel12/14彩票柜台见 [拍卖与彩票屏幕](AUCTION_LOTTERY_UI.md)，完整应用及自然触发仍待接线。

原Panel73公告栏、分类挂牌/详情与真实交易回调对照见 [交易屏幕](TRADING_UI.md)，完整主应用仍待接线。

原卡片/道具库存、按住/释放/下一帧动作和原卡图见 [物品屏幕](ITEM_SCREENS.md)，目标与服务屏幕继续分阶段实施。
