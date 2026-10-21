# Issue #104：统一证据矩阵、规则争议与抽样审计

研究基线：ReactMono `dev@6b87e4aed02e30235573bc0e12d8d6e215a6b603`；日期：2026-10-21 UTC。所有上游结论绑定本矩阵列出的精确提交。汇总研究见 [comparative-review.md](comparative-review.md)；机器结构见 [summary.json](summary.json)。

**解读规则：** 下表从每份 `evidence.json` 选出与标准问题最接近的一项原始特性；“partial/verified/claimed/unknown/absent”是**原记录特性范围内的状态**，不代表完整商业级游戏是否通过。A 只限其选定 ID 对应的有限测试/截图，B 仅证实源码路径，C 仅作者自述，D 未证实；等级栏展示选定 ID 中最强一级，**不迁移至其他功能**。某些项目没有对应规则（特别是原创 Monopoly 3D），其未知项不构成否定证据。同一源特性被映射进多个通用类别仅为方便查询，不构成两项独立验证。

## 上游固定版本与证据规模

| 仓库 | 上游 SHA（不可移动） | 原作关系 | A/B/C/D 数量 | 可追溯原始文件 |
| --- | --- | --- | ---: | --- |
| mytbk/rich4 | `f81954d6a5675f63297036f9252720c6ca32a2b4` | tool | 0/21/4/2 | [报告](repositories/mytbk--rich4/README.md) · [源码](repositories/mytbk--rich4/source-index.md) · [JSON](repositories/mytbk--rich4/evidence.json) |
| tytannial/rich4-re | `b7b76570f445ad07c0788314062b8500e77259e7` | faithful | 1/15/1/3 | [报告](repositories/tytannial--rich4-re/README.md) · [源码](repositories/tytannial--rich4-re/source-index.md) · [JSON](repositories/tytannial--rich4-re/evidence.json) |
| lhr0909/richman4-remastered | `3f4209a7dfb5b2f20799bf54e6c03c5faa11c557` | faithful | 0/18/2/1 | [报告](repositories/lhr0909--richman4-remastered/README.md) · [源码](repositories/lhr0909--richman4-remastered/source-index.md) · [JSON](repositories/lhr0909--richman4-remastered/evidence.json) |
| iam567/rich4-renew-app | `1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79` | derived | 0/20/4/0 | [报告](repositories/iam567--rich4-renew-app/README.md) · [源码](repositories/iam567--rich4-renew-app/source-index.md) · [JSON](repositories/iam567--rich4-renew-app/evidence.json) |
| nurockplayer/richman4-remake | `961bdf47389a08e3143c0340490896b9f50edef9` | faithful | 0/12/6/1 | [报告](repositories/nurockplayer--richman4-remake/README.md) · [源码](repositories/nurockplayer--richman4-remake/source-index.md) · [JSON](repositories/nurockplayer--richman4-remake/evidence.json) |
| oama1111/rich4-remake-public | `42ad97ad31f07541a9af35415e36be4da4147484` | faithful | 0/15/6/0 | [报告](repositories/oama1111--rich4-remake-public/README.md) · [源码](repositories/oama1111--rich4-remake-public/source-index.md) · [JSON](repositories/oama1111--rich4-remake-public/evidence.json) |
| JCRJPZB/Rich4 | `0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0` | derived | 2/13/0/1 | [报告](repositories/JCRJPZB--Rich4/README.md) · [源码](repositories/JCRJPZB--Rich4/source-index.md) · [JSON](repositories/JCRJPZB--Rich4/evidence.json) |
| Yakamozli/richman-3d | `32e7f01f9888a28b8fd1267f5488c455e15abe4a` | inspired | 1/17/2/1 | [报告](repositories/Yakamozli--richman-3d/README.md) · [源码](repositories/Yakamozli--richman-3d/source-index.md) · [JSON](repositories/Yakamozli--richman-3d/evidence.json) |
| zawsstt/monopoly-rich-life | `307c1761b150a7179fb0353618a95bc6effe3fee` | inspired | 1/13/2/1 | [报告](repositories/zawsstt--monopoly-rich-life/README.md) · [源码](repositories/zawsstt--monopoly-rich-life/source-index.md) · [JSON](repositories/zawsstt--monopoly-rich-life/evidence.json) |

## 全能力横向矩阵（99 格，全部回链源证据）

| 仓库 | 能力类别 | 原报告具体能力 | 状态 | 证据等级和 ID | 现阶段能认定什么 |
| --- | --- | --- | --- | --- | --- |
| mytbk/rich4 | 开局与回合 | 原版启动/完整对局 | `claimed` | [`C01`](repositories/mytbk--rich4/evidence.json)·C [`B01`](repositories/mytbk--rich4/evidence.json)·B [`D01`](repositories/mytbk--rich4/evidence.json)·D | 仅原作者陈述/配置 |
| mytbk/rich4 | 地图与路径 | 地图节点/资源读取 | `partial` | [`B02`](repositories/mytbk--rich4/evidence.json)·B [`B03`](repositories/mytbk--rich4/evidence.json)·B [`B15`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 地产与租金 | 地产买卖/升级/租金 | `partial` | [`B04`](repositories/mytbk--rich4/evidence.json)·B [`B05`](repositories/mytbk--rich4/evidence.json)·B [`B07`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 银行与贷款 | 银行/存款贷款 | `partial` | [`B06`](repositories/mytbk--rich4/evidence.json)·B [`B08`](repositories/mytbk--rich4/evidence.json)·B [`B13`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 股票与市场 | 股市买卖/上市公司 | `partial` | [`B06`](repositories/mytbk--rich4/evidence.json)·B [`B07`](repositories/mytbk--rich4/evidence.json)·B [`B20`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 卡片和道具 | 卡片/道具 | `partial` | [`B09`](repositories/mytbk--rich4/evidence.json)·B [`B18`](repositories/mytbk--rich4/evidence.json)·B [`B21`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 神明与事件 | 神明/事件 | `partial` | [`B10`](repositories/mytbk--rich4/evidence.json)·B [`B13`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 电脑对手 | 电脑对手 | `partial` | [`B11`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 存档恢复 | 原版二进制存读档 | `partial` | [`B12`](repositories/mytbk--rich4/evidence.json)·B [`B13`](repositories/mytbk--rich4/evidence.json)·B | 仅部分源码/限定功能 |
| mytbk/rich4 | 画面和交互 | 图形音效/交互 | `unknown` | [`B01`](repositories/mytbk--rich4/evidence.json)·B [`B08`](repositories/mytbk--rich4/evidence.json)·B [`D01`](repositories/mytbk--rich4/evidence.json)·D | 未知/未获足量证据 |
| mytbk/rich4 | 跨平台/离线 | 浏览器/PWA/现代原生平台 | `unknown` | [`B01`](repositories/mytbk--rich4/evidence.json)·B [`C01`](repositories/mytbk--rich4/evidence.json)·C [`D01`](repositories/mytbk--rich4/evidence.json)·D | 未知/未获足量证据 |
| tytannial/rich4-re | 开局与回合 | new_game_turn_ai | `partial` | [`B02`](repositories/tytannial--rich4-re/evidence.json)·B [`B03`](repositories/tytannial--rich4-re/evidence.json)·B [`B04`](repositories/tytannial--rich4-re/evidence.json)·B [`B11`](repositories/tytannial--rich4-re/evidence.json)·B | 仅部分源码/限定功能 |
| tytannial/rich4-re | 地图与路径 | 地图数据资源载入（无单独全路径 A） | `partial` | [`B03`](repositories/tytannial--rich4-re/evidence.json)·B | 仅部分源码/限定功能 |
| tytannial/rich4-re | 地产与租金 | residential_property_rent_alliance | `partial` | [`B04`](repositories/tytannial--rich4-re/evidence.json)·B [`B05`](repositories/tytannial--rich4-re/evidence.json)·B [`B10`](repositories/tytannial--rich4-re/evidence.json)·B [`B12`](repositories/tytannial--rich4-re/evidence.json)·B [`A121_ECONOMY`](repositories/tytannial--rich4-re/evidence.json)·A | 仅部分源码/限定功能 |
| tytannial/rich4-re | 银行与贷款 | bank_loans_dividends | `partial` | [`B05`](repositories/tytannial--rich4-re/evidence.json)·B [`B06`](repositories/tytannial--rich4-re/evidence.json)·B [`B12`](repositories/tytannial--rich4-re/evidence.json)·B | 仅部分源码/限定功能 |
| tytannial/rich4-re | 股票与市场 | stock_market | `partial` | [`B06`](repositories/tytannial--rich4-re/evidence.json)·B [`B12`](repositories/tytannial--rich4-re/evidence.json)·B | 仅部分源码/限定功能 |
| tytannial/rich4-re | 卡片和道具 | cards_and_items | `partial` | [`B07`](repositories/tytannial--rich4-re/evidence.json)·B [`C01`](repositories/tytannial--rich4-re/evidence.json)·C | 仅部分源码/限定功能 |
| tytannial/rich4-re | 神明与事件 | gods_news_fate_events | `partial` | [`B04`](repositories/tytannial--rich4-re/evidence.json)·B [`B12`](repositories/tytannial--rich4-re/evidence.json)·B | 仅部分源码/限定功能 |
| tytannial/rich4-re | 电脑对手 | new_game_turn_ai | `partial` | [`B02`](repositories/tytannial--rich4-re/evidence.json)·B [`B03`](repositories/tytannial--rich4-re/evidence.json)·B [`B04`](repositories/tytannial--rich4-re/evidence.json)·B [`B11`](repositories/tytannial--rich4-re/evidence.json)·B | 仅部分源码/限定功能 |
| tytannial/rich4-re | 存档恢复 | save_load_binary_snapshot | `partial` | [`B09`](repositories/tytannial--rich4-re/evidence.json)·B [`B10`](repositories/tytannial--rich4-re/evidence.json)·B [`B12`](repositories/tytannial--rich4-re/evidence.json)·B | 仅部分源码/限定功能 |
| tytannial/rich4-re | 画面和交互 | sdl_visual_audio_interaction | `partial` | [`B08`](repositories/tytannial--rich4-re/evidence.json)·B [`B13`](repositories/tytannial--rich4-re/evidence.json)·B [`D02`](repositories/tytannial--rich4-re/evidence.json)·D | 仅部分源码/限定功能 |
| tytannial/rich4-re | 跨平台/离线 | browser_pwa | `unknown` | [`B02`](repositories/tytannial--rich4-re/evidence.json)·B [`B03`](repositories/tytannial--rich4-re/evidence.json)·B [`B15`](repositories/tytannial--rich4-re/evidence.json)·B | 未知/未获足量证据 |
| lhr0909/richman4-remastered | 开局与回合 | new_game_turns_maps_property | `partial` | [`E04`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E05`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E15`](repositories/lhr0909--richman4-remastered/evidence.json)·B | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 地图与路径 | new_game_turns_maps_property | `partial` | [`E04`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E05`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E15`](repositories/lhr0909--richman4-remastered/evidence.json)·B | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 地产与租金 | new_game_turns_maps_property | `partial` | [`E04`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E05`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E15`](repositories/lhr0909--richman4-remastered/evidence.json)·B | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 银行与贷款 | stocks_bank_financing_auctions | `partial` | [`E09`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 股票与市场 | stocks_bank_financing_auctions | `partial` | [`E09`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 卡片和道具 | cards_tools_shops_gods | `partial` | [`E08`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E15`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 神明与事件 | cards_tools_shops_gods | `partial` | [`E08`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E15`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 电脑对手 | computer_ai_managed_mode | `partial` | [`E05`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E09`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 存档恢复 | saves_slots_autosave | `partial` | [`E10`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 画面和交互 | original_style_toolbar_minimap_ui | `partial` | [`E06`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E12`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅部分源码/限定功能 |
| lhr0909/richman4-remastered | 跨平台/离线 | android_real_device_install | `claimed` | [`E13`](repositories/lhr0909--richman4-remastered/evidence.json)·B [`E16`](repositories/lhr0909--richman4-remastered/evidence.json)·C | 仅原作者陈述/配置 |
| iam567/rich4-renew-app | 开局与回合 | new_game_turns | `partial` | [`E01`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E02`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 地图与路径 | board_original_parsing | `partial` | [`E07`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E12`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 地产与租金 | property_and_rent | `partial` | [`E03`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 银行与贷款 | bank_and_loans | `partial` | [`E03`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E15`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 股票与市场 | stocks_and_company | `partial` | [`E04`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E15`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E16`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 卡片和道具 | cards | `partial` | [`E05`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E15`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 神明与事件 | events_npc | `partial` | [`E01`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E06`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 电脑对手 | computer_ai | `partial` | [`E02`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E15`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 存档恢复 | normal_save | `partial` | [`E10`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E13`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E15`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅部分源码/限定功能 |
| iam567/rich4-renew-app | 画面和交互 | visual_audio_quality | `unknown` | [`E11`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E12`](repositories/iam567--rich4-renew-app/evidence.json)·B | 未知/未获足量证据 |
| iam567/rich4-renew-app | 跨平台/离线 | mobile_native_packaging | `claimed` | [`E14`](repositories/iam567--rich4-renew-app/evidence.json)·B [`E20`](repositories/iam567--rich4-renew-app/evidence.json)·C [`E21`](repositories/iam567--rich4-renew-app/evidence.json)·C [`E23`](repositories/iam567--rich4-renew-app/evidence.json)·B | 仅原作者陈述/配置 |
| nurockplayer/richman4-remake | 开局与回合 | 2–4人开局/人机回合 | `partial` | [`B04`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C01`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅部分源码/限定功能 |
| nurockplayer/richman4-remake | 地图与路径 | 原版4+8地图数据 | `claimed` | [`B01`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`B03`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C03`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅原作者陈述/配置 |
| nurockplayer/richman4-remake | 地产与租金 | 路网/分岔/地产升级租金结算 | `partial` | [`B03`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`B04`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`B09`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C01`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅部分源码/限定功能 |
| nurockplayer/richman4-remake | 银行与贷款 | 银行ATM/贷款/途中暂停与续走 | `partial` | [`B04`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C04`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅部分源码/限定功能 |
| nurockplayer/richman4-remake | 股票与市场 | 十二股源目录/价格历史/持股 | `partial` | [`B02`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`B03`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`B05`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`B08`](repositories/nurockplayer--richman4-remake/evidence.json)·B | 仅部分源码/限定功能 |
| nurockplayer/richman4-remake | 卡片和道具 | 卡片/道具/神明/事件 | `partial` | [`B04`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C06`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅部分源码/限定功能 |
| nurockplayer/richman4-remake | 神明与事件 | 卡片/道具/神明/事件 | `partial` | [`B04`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C06`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅部分源码/限定功能 |
| nurockplayer/richman4-remake | 电脑对手 | AI接手与长局结算 | `claimed` | [`B04`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C01`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅原作者陈述/配置 |
| nurockplayer/richman4-remake | 存档恢复 | 序列化存档/恢复固定RNG | `partial` | [`B04`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`B09`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C01`](repositories/nurockplayer--richman4-remake/evidence.json)·C | 仅部分源码/限定功能 |
| nurockplayer/richman4-remake | 画面和交互 | 原版主棋盘视觉逐幕最终验收 | `unknown` | [`B07`](repositories/nurockplayer--richman4-remake/evidence.json)·B [`C02`](repositories/nurockplayer--richman4-remake/evidence.json)·C [`D01`](repositories/nurockplayer--richman4-remake/evidence.json)·D | 未知/未获足量证据 |
| nurockplayer/richman4-remake | 跨平台/离线 | 浏览器/PWA/Pages端运行 | `unknown` | [`B10`](repositories/nurockplayer--richman4-remake/evidence.json)·B | 未知/未获足量证据 |
| oama1111/rich4-remake-public | 开局与回合 | 新局/回合/骰子 | `partial` | [`E01`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E02`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E03`](repositories/oama1111--rich4-remake-public/evidence.json)·B | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 地图与路径 | 地图/地块/地产/租金 | `partial` | [`E01`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E10`](repositories/oama1111--rich4-remake-public/evidence.json)·B | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 地产与租金 | 地图/地块/地产/租金 | `partial` | [`E01`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E10`](repositories/oama1111--rich4-remake-public/evidence.json)·B | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 银行与贷款 | 银行/股票/商用经济 | `partial` | [`E01`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E18`](repositories/oama1111--rich4-remake-public/evidence.json)·C | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 股票与市场 | 银行/股票/商用经济 | `partial` | [`E01`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E18`](repositories/oama1111--rich4-remake-public/evidence.json)·C | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 卡片和道具 | 卡片/道具 | `partial` | [`E01`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E18`](repositories/oama1111--rich4-remake-public/evidence.json)·C | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 神明与事件 | 神明/事件/特殊场所 | `partial` | [`E18`](repositories/oama1111--rich4-remake-public/evidence.json)·C | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 电脑对手 | 电脑玩家和策略 | `partial` | [`E03`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E18`](repositories/oama1111--rich4-remake-public/evidence.json)·C [`E19`](repositories/oama1111--rich4-remake-public/evidence.json)·C | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 存档恢复 | 本地存读档及原版导入 | `partial` | [`E08`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E12`](repositories/oama1111--rich4-remake-public/evidence.json)·B | 仅部分源码/限定功能 |
| oama1111/rich4-remake-public | 画面和交互 | 浏览器交互/动画/配乐 | `claimed` | [`E08`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E20`](repositories/oama1111--rich4-remake-public/evidence.json)·C | 仅原作者陈述/配置 |
| oama1111/rich4-remake-public | 跨平台/离线 | Tauri 原生桌面/外部素材目录 | `partial` | [`E09`](repositories/oama1111--rich4-remake-public/evidence.json)·B [`E20`](repositories/oama1111--rich4-remake-public/evidence.json)·C | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 开局与回合 | turn_dice_movement | `partial` | [`R07`](repositories/JCRJPZB--Rich4/evidence.json)·B [`R08`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 地图与路径 | map_and_routes | `partial` | [`R04`](repositories/JCRJPZB--Rich4/evidence.json)·A [`R06`](repositories/JCRJPZB--Rich4/evidence.json)·B [`R07`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 地产与租金 | property_purchase_rent_upgrade | `partial` | [`R09`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 银行与贷款 | bank_deposits | `partial` | [`R10`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 股票与市场 | stock_market | `partial` | [`R10`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 卡片和道具 | cards | `partial` | [`R11`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 神明与事件 | special_events_magic | `partial` | [`R11`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 电脑对手 | computer_ai | `partial` | [`R08`](repositories/JCRJPZB--Rich4/evidence.json)·B [`R13`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 存档恢复 | save_load | `unknown` | [`R12`](repositories/JCRJPZB--Rich4/evidence.json)·B | 未知/未获足量证据 |
| JCRJPZB/Rich4 | 画面和交互 | presentation_animation | `partial` | [`R02`](repositories/JCRJPZB--Rich4/evidence.json)·B [`R03`](repositories/JCRJPZB--Rich4/evidence.json)·B | 仅部分源码/限定功能 |
| JCRJPZB/Rich4 | 跨平台/离线 | mobile_web_pwa | `unknown` | [`R02`](repositories/JCRJPZB--Rich4/evidence.json)·B [`R12`](repositories/JCRJPZB--Rich4/evidence.json)·B | 未知/未获足量证据 |
| Yakamozli/richman-3d | 开局与回合 | 开局/本地2–4人设置 | `partial` | [`B09`](repositories/Yakamozli--richman-3d/evidence.json)·B [`C01`](repositories/Yakamozli--richman-3d/evidence.json)·C | 仅部分源码/限定功能 |
| Yakamozli/richman-3d | 地图与路径 | 52格/16色组地图 | `partial` | [`B01`](repositories/Yakamozli--richman-3d/evidence.json)·B [`B02`](repositories/Yakamozli--richman-3d/evidence.json)·B | 仅部分源码/限定功能 |
| Yakamozli/richman-3d | 地产与租金 | 地产买卖/收租/房屋/酒店 | `partial` | [`B05`](repositories/Yakamozli--richman-3d/evidence.json)·B [`B09`](repositories/Yakamozli--richman-3d/evidence.json)·B | 仅部分源码/限定功能 |
| Yakamozli/richman-3d | 银行与贷款 | 银行与独立账户 | `unknown` | [`B09`](repositories/Yakamozli--richman-3d/evidence.json)·B | 未知/未获足量证据 |
| Yakamozli/richman-3d | 股票与市场 | 股票 | `unknown` | [`B09`](repositories/Yakamozli--richman-3d/evidence.json)·B | 未知/未获足量证据 |
| Yakamozli/richman-3d | 卡片和道具 | 道具/路障 | `partial` | [`B09`](repositories/Yakamozli--richman-3d/evidence.json)·B [`B10`](repositories/Yakamozli--richman-3d/evidence.json)·B | 仅部分源码/限定功能 |
| Yakamozli/richman-3d | 神明与事件 | 神明/复杂原版事件 | `unknown` | [`B01`](repositories/Yakamozli--richman-3d/evidence.json)·B [`B09`](repositories/Yakamozli--richman-3d/evidence.json)·B | 未知/未获足量证据 |
| Yakamozli/richman-3d | 电脑对手 | AI决策 | `partial` | [`B10`](repositories/Yakamozli--richman-3d/evidence.json)·B [`B11`](repositories/Yakamozli--richman-3d/evidence.json)·B | 仅部分源码/限定功能 |
| Yakamozli/richman-3d | 存档恢复 | 保存与读取存档 | `unknown` | [`B09`](repositories/Yakamozli--richman-3d/evidence.json)·B [`B16`](repositories/Yakamozli--richman-3d/evidence.json)·B | 未知/未获足量证据 |
| Yakamozli/richman-3d | 画面和交互 | 独立真实截图 | `verified` | [`C02`](repositories/Yakamozli--richman-3d/evidence.json)·C [`D01`](repositories/Yakamozli--richman-3d/evidence.json)·D [`A121_CHROMIUM`](repositories/Yakamozli--richman-3d/evidence.json)·A | 独立限项可验，不代表整局 |
| Yakamozli/richman-3d | 跨平台/离线 | 端侧静态网页部署 | `claimed` | [`B16`](repositories/Yakamozli--richman-3d/evidence.json)·B [`C01`](repositories/Yakamozli--richman-3d/evidence.json)·C | 仅原作者陈述/配置 |
| zawsstt/monopoly-rich-life | 开局与回合 | 开局/回合及胜负 | `partial` | [`E03`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 仅部分源码/限定功能 |
| zawsstt/monopoly-rich-life | 地图与路径 | 40 格/22 地产 | `partial` | [`E04`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 仅部分源码/限定功能 |
| zawsstt/monopoly-rich-life | 地产与租金 | 购地/升楼/收租 | `partial` | [`E03`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B [`E06`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 仅部分源码/限定功能 |
| zawsstt/monopoly-rich-life | 银行与贷款 | 银行与股市（与大富翁4） | `unknown` | [`E04`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 未知/未获足量证据 |
| zawsstt/monopoly-rich-life | 股票与市场 | 银行与股市（与大富翁4） | `unknown` | [`E04`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 未知/未获足量证据 |
| zawsstt/monopoly-rich-life | 卡片和道具 | 卡片/道具/机会事件 | `partial` | [`E03`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B [`E04`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 仅部分源码/限定功能 |
| zawsstt/monopoly-rich-life | 神明与事件 | 神明/复杂随机事件 | `unknown` | [`E03`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 未知/未获足量证据 |
| zawsstt/monopoly-rich-life | 电脑对手 | 电脑对手 | `partial` | [`E03`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 仅部分源码/限定功能 |
| zawsstt/monopoly-rich-life | 存档恢复 | 存读档/跨版本兼容 | `unknown` | [`E03`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B [`E14`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 未知/未获足量证据 |
| zawsstt/monopoly-rich-life | 画面和交互 | 独立 Chromium 游戏首回合截图 | `verified` | [`A121_CHROMIUM`](repositories/zawsstt--monopoly-rich-life/evidence.json)·A | 独立限项可验，不代表整局 |
| zawsstt/monopoly-rich-life | 跨平台/离线 | 离线 PWA 安装/缓存 | `unknown` | [`E09`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B [`E14`](repositories/zawsstt--monopoly-rich-life/evidence.json)·B | 未知/未获足量证据 |

> 特别审计：#98 的无 A `verified` 已在此分支降为 `partial`；JCRJPZB 的两项 A 是本地 JSON/地图数据解析而非 Cocos 可玩；#96 C++ A 是规则微型断言；#102/#103 A 是首回合双视口截图。视觉一格如关联 A 截图，仅对画面可见物适用，不能以其给长期画面/交互维度打分。

## 原版机制与跨项目矛盾裁定

| 争议 | 对应证据/源码（固定 SHA） | 可确定 | 不能确定/开发选择 |
| --- | --- | --- | --- |
| 同名街道联合租金与物价指数 | [mytbk B04](repositories/mytbk--rich4/evidence.json) [tytannial B04 + A121_ECONOMY](repositories/tytannial--rich4-re/evidence.json) [iam567 E03](repositories/iam567--rich4-renew-app/evidence.json) | 三套源码共享同业主同街名累加乘倍率的路径；独立重建版 1200 元测试 A | 不是 1998 exe 独立等价；ReactMono 单地块收费是**原创设计差异**，非必然缺陷 |
| 连锁店跨图计数 | [mytbk 原版汇编](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L199) [tytannial](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/turn_system.cpp#L982-L1010) [iam567](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L1044-L1055) | B 多实现代码 + #121 重建版 A 12000 元 | 临时免租/同盟/跨版本例外未独立差分 |
| 12 支股票还是 ReactMono 5 支 | [tytannial B06](repositories/tytannial--rich4-re/evidence.json) [iam567 E04](repositories/iam567--rich4-renew-app/evidence.json) [Godot B02](repositories/nurockplayer--richman4-remake/evidence.json) | 上游原版导向实现多见 12 槽/各地图 12 公司模板 | ReactMono 5 支是自有规则，目前无义务复制名称、行情公式或企业控制 |
| 原版资料片版本 | [mytbk B03](repositories/mytbk--rich4/evidence.json) [Godot B01/B02](repositories/nurockplayer--richman4-remake/evidence.json) | 有 v3.11/资料片地图与市场结构线索 | 无原游戏样本，不能宣称首发同样八图、同存档布局 |
| 单机读档 vs 可重放随机 | [oama1111 E02/E03](repositories/oama1111--rich4-remake-public/evidence.json) | 代码对单机/联机使用不同 reseed 策略 | 作者注释声称原版三处调用，尚未完成二进制差分；ReactMono 保留确定性 |
| “1000 局通过” | [oama1111 源测试](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/state/replay.test.ts#L14-L72) | 只有私有地图文件存在时运行 `it`，否则 `it.skip` | B 测试设计，不是 A 执行统计；long soak 上限非胜负自然结束 |
| 多人服务器与纯静态冲突 | [oama1111 E05–E07](repositories/oama1111--rich4-remake-public/evidence.json) [zawsstt E10/E11](repositories/zawsstt--monopoly-rich-life/evidence.json) | 上游云端架构真实存在调用链，且 oama 服务端做 reduce 镜像验证 | 不能直接进入 ReactMono 的纯 Pages/PWA/无后端硬约束 |
| 街区四级建筑视觉 | [zawsstt E06](repositories/zawsstt--monopoly-rich-life/evidence.json) [#121 A 首回合截图](verification-issue-121/RESULTS.md) | 四级工厂 B 和首回合场景 A 各自成立 | 二者**合并不产生“四级升级已实测”的 A**，需专门录四态 |
| AI/完成度 | [JCRJPZB R05/R13](repositories/JCRJPZB--Rich4/evidence.json) [lhr E15/E16](repositories/lhr0909--richman4-remastered/evidence.json) | Cocos 硬编码和 TODO/AI 代码缺口可定位；lhr 原生 AI/小游戏代码存在 | Cocos 未独立 Cocos 整局，lhr 的 47/47 和 20/20 仍属作者报告 |

## 逐仓库审计日志

这是**27 个实际打开的固定 SHA 文件位置**与每份至少两项评价复核；不是用文本包含关键词冒充源码核查。审计 B 与 A/C/D 严格分离，执行时间限本次 GitHub 仓库接口读取；目前不能对涉及商业资源的完整游戏运行。文件路径相对各自上游根目录，原文件的定位与行号以 [各仓库源码索引](repositories/README.md) 为准。

| 仓库 | 三项实际打开的原始源码/配置 | 至少两项评价核对、修正/风险 |
| --- | --- | --- |
| mytbk/rich4 | `asm/rich4_player_core_actions.asm:190–240`；`csrc/loadsave.c:94–147`；`csrc/mkf/mkf.c:30–72` | 规则 3（B、地址/数据结构），价值 4（B、仅只读参考）；尚无 A 运行；v3.11 不能等同 1998 首发。 |
| tytannial/rich4-re | `src/app/game/turn_system.cpp:975–1025`；`src/app/game/stock_system.cpp:104–155`；`src/app/game/trade_market.cpp:1–90` | 规则 4（B 覆盖而非保真率）、独立复现 2（资料受限）；纠正历史 `execution.result`“无 A”：#121 已实测经济四例。 |
| lhr0909/richman4-remastered | `tools/native_game.cpp:913–970`；`src/game.cpp:516–570`；`tools/screens/main_screen.cpp:273–312` | 规则 3（B 逻辑）、画面 null（无独立画面）；47/47/20/20 全保留 C，未错升 A。 |
| iam567/rich4-renew-app | `game/src/core/game.ts:803–855`；同文件 `1004–1056`；`game/src/core/modules/stocks.ts:35–77` | 规则 3（B 而非原版完整）、价值 4（可借鉴 TS 事件流）；**7 项无 A 的 verified→partial**。 |
| nurockplayer/richman4-remake | `tools/import_original.py:1–76`；`game/content/original_maps.gd:1–78`；`game/core/game_state.gd:1–77` | 规则 null（尚无原始金标）、价值 4（资源校验/存档结构）；provisional 明言仍属暂拟规则，不能称完整保真。 |
| oama1111/rich4-remake-public | `packages/core/src/state/reduce.ts:1–80`；`packages/core/src/rng/policy.ts:1–84`；`packages/core/src/state/replay.test.ts:1–89` | 规则 3（B 设计）、复现 1（缺原版文件）；replay `it.skip`，作者宣称与执行混同不可取。 |
| JCRJPZB/Rich4 | `project.json:1–12`；`assets/Script/GameCore/Game.js:8–55`；`assets/Script/Map/PointMgr.js:104–158` | 维护 1（硬编码/TODO，B）与复现 1（数据 A，游戏未执行）；不得把地图 JSON 检查当作整局测试。 |
| Yakamozli/richman-3d | `js/config.js:1–65`；`js/scene.js:141–194`；`js/ai.js:1–77` | 规则 1（Monopoly 衍生非原版）、presentation null（有首回合 A 但无全程用户交互）；补 `execution` #121。 |
| zawsstt/monopoly-rich-life | `src/game.js:20–100`；`src/view3d.js:1608–1646`；`src/net.js:62–108` | 规则 null（类别不适用）、presentation null（首回合 A 不等于完整视觉体验）；修复旧执行口径，显式排除非商业许可复制。 |

## 结构化完整性结果与保留条件

- 9 份权威 `evidence.json` 在读取时均可 JSON 解析。所有 `features[].evidence_ids` 都能在同文件 `evidence[].id` 找到，抽样固定 SHA 链接与源码路径均成功读取；各文件 `license.spdx=null` 代表无可确认许可证或特殊非 SPDX 授权，不是“自由可用”。
- 检查 27 处上游文件不等于**九仓库所有 URL、所有 1000+ 文件、版权归属和具体语句逐行全量鉴定**，不制造“全部无误”断言。
- 图片真正跑出来的是 [#121](verification-issue-121/RESULTS.md)，且 zawsstt 模拟手机为旋转横屏；六张图未作为源码抄入新目录。不重复跑工作流或混合时间段测试。
- [summary.json](summary.json) 保存实际九份报告的评分；`presentation=null` 是完整演出/交互未验证，不是把静帧美术评为零；只允许引用单项的 A 证据。
- 永久开放：1998 原版/v3.11 素材差分、逆向 GPL/MIT 代码血缘法律鉴定、完整长局/真机/WebGL GPU、云端可靠性。继续前须有合法自有商业资源与真实可复现输入；否则保持未验证，不因此阻断**已达范围的研究总综述**。
