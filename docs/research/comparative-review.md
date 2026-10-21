# 九仓库跨源核验与 ReactMono 技术路线（Issue #104）

> 2026-10-21 UTC；ReactMono 基线：[`dev@6b87e4aed02e30235573bc0e12d8d6e215a6b603`](https://github.com/SiliconYC/ReactMono/commit/6b87e4aed02e30235573bc0e12d8d6e215a6b603)。此文是**源码交叉审计与有限独立实测汇总**，不是原版 1998 年商业程序差分报告，更不是九份报告的总分排名。相关逐项编号见 [核验矩阵](verification-matrix.md) 和 [机器清单](summary.json)。

## 1. 输入依赖、方法与证据界限

- #95–#103 均为 **closed 且 PR 已实际 merged 到 dev**，其中最新 #97 经 [PR #116](https://github.com/SiliconYC/ReactMono/pull/116) 合入；#121 经 [PR #122](https://github.com/SiliconYC/ReactMono/pull/122) 于 2026-10-21 00:53 UTC 合入当前基线并关闭。其 [RESULTS](verification-issue-121/RESULTS.md) 和六张原始 PNG、JSON、日志都已在 dev。
- 逐一阅读九个权威目录的 README、source-index、evidence.json；对每一仓库抽检至少三个**真实上游固定 SHA 文件位置**（27 处以上），再检查至少两个评价项与原始证据匹配。对功能表的每个 evidence_id 进行引用闭包检查。程序matic 解析与静态 URL 检查不等于批量运行九个项目。
- 等级 A = 独立执行/截图/数字输出；B = 指定 SHA 静态源码路径；C = 作者文字或状态；D = 未证实。**A 按用例粒度传播**，绝不从一张截图推断全功能合格，或从 C++ 重建版数值证明 1998 年官方二进制一致。JCRJPZB 的 A 仅限 JSON/地图数据静态检查，不是 Cocos 启动。
- #121 A：Chromium 155 Linux SwiftShader 的 [1440×900 与 390×844 六张首回合截图](verification-issue-121/RESULTS.md)，和 `rich4-re` C++ 无版权资源的四组边界断言：修正**旧测试及新测试的越界断言**后共 126 checks、0 failed、3 项商业资源条件跳过。这里的“126”是断言次数，不是 126 个独立测试。未验证完整对局、实体手机、真实 GPU 性能、原版运行。
- 采信顺序：原版带地址的逆向汇编（B，仍需校核版本/正确性）→ 两个独立实现的行为路径（B）→ 限定重建程序运行（A）→ 作者自述（C）；**来源不是民主投票**。反向亦然：多个作者重复同一个逆向表不会生成新的原作真值。
- 所有原研究版本都保留其锁定的 SHA，避免移用最新 `main` 代码来解释历史报告。研究基线后的 `dev` 产品演化须以当前源码为准。

## 2. 技术类别与真实完成度，不做混合排名

| 类别 | 对象 | 本轮可确定的价值 | 不能确定的事 |
| --- | --- | --- | --- |
| 逆向证据主链 | [mytbk/rich4](repositories/mytbk--rich4/README.md) | x86 地址、MAP/MKF、落地收费/股票/原始存档结构，B | 1998 首发与 v3.11 的一致性、可合法启动游戏 |
| 原版导向重建 | [tytannial/rich4-re](repositories/tytannial--rich4-re/README.md)、[lhr0909/richman4-remastered](repositories/lhr0909--richman4-remastered/README.md) | 前者经济 A 小样例，C++/SDL3 源码 B；后者原生 GameSession/界面源链 B | 原版商用程序差分、完整音画、真机发行质量、原生 47/47 或 20/20 独立重跑 |
| 高覆盖但非真值 | [iam567/rich4-renew-app](repositories/iam567--rich4-renew-app/README.md)、[oama1111/rich4-remake-public](repositories/oama1111--rich4-remake-public/README.md) | 分别有 TS generator 事件流和 action/reducer/replay 的 B 级实现 | 代码中称“零偏离原版”、素材依赖的测试必通过、云端联机适用于纯静态产品 |
| 高不确定性 | [nurockplayer/richman4-remake](repositories/nurockplayer--richman4-remake/README.md)、[JCRJPZB/Rich4](repositories/JCRJPZB--Rich4/README.md) | Godot 原始资源导入/路网/状态序列化 B；Cocos 日本地图数据校验 A（仅数据） | 最终像素保真、真实完整长局；前者 provisional，后者源码存在 AI/结算明显缺口 |
| **原创 3D 参考，不是《大富翁4》复刻** | [Yakamozli/richman-3d](repositories/Yakamozli--richman-3d/README.md)、[zawsstt/monopoly-rich-life](repositories/zawsstt--monopoly-rich-life/README.md) | 两者各两张**真实开局**截图 A；前者棋盘为整面 CanvasTexture，后者四级地产构建链 B | 原版规则正确率、完整建筑升级效果、真人触控/商业级帧率 |

九份报告的源码路径多数成立，最大的偏差是**测试定义、作者自述和已运行用例在语言上很容易混同**；因此本综述不用单一“完成率%”、不会把规则 4/5 理解为 80% 原版保真。详细评分仍保留原报告的 0–5 或 null，在 summary.json 显式标记证据限制。

## 3. 源码血缘与许可证：有联系≠可确定复制

```text
1998/后续 v3.11 商业游戏二进制及素材（法律权属独立）
  ├─ [逆向地址/资源表] → mytbk/rich4 (GPL-3.0-or-later)
  │                         ↘ 其他项目文档或注释引用其符号/原版地址 [线索，非代码复制鉴定]
  ├─ [独立 C++ 重建主张] → tytannial/rich4-re (MIT；固定 x86 地址注释)
  ├─ [原生重写主张]     → lhr0909/richman4-remastered (GPL-3.0-or-later)
  ├─ [TS 移植/扩展]     → iam567/rich4-renew-app (GPL-3.0-or-later)
  ├─ [另行核心架构]     → oama1111/rich4-remake-public (GPL-3.0-or-later)
  ├─ [Godot 资源导入]   → nurockplayer/richman4-remake (未确证统一许可)
  └─ [Cocos 早期项目]   → JCRJPZB/Rich4 (未确证许可证)

Monopoly/地产游戏构想 ──→ Yakamozli/richman-3d (MIT)
                       └──→ zawsstt/monopoly-rich-life (自定义非商业许可)
ReactMono (React+TS+Three.js 原创产品)：借鉴「问题/测试设计」，无代码继承已获证据。
```

- **代码级正证据**：`mytbk/asm/rich4_player_core_actions.asm` 含 `_rich4_calculate_land_toll`；`tytannial/src/app/game/turn_system.cpp::estateRouteRent` 明写反编译地址 `0x419744`；`iam567/game/src/core/game.ts::calcToll` 明写来源文档/汇编定位；`oama1111/packages/core/src/rng/policy.ts` 注释列三个原版汇编重播种点。这证明技术/符号参照路径，**不足以证明某源码文件逐字复制、法律派生关系或授权链**。平台 `fork=false` 亦不证明独立原创。未对全量函数做相似度或提交历史逐页归因，无法确证的边在矩阵标“未决”。
- **许可结论**：mytbk、lhr、iam、oama 属 GPL 家族；tytannial、Yakamozli 有 MIT 声明；nurockplayer、JCRJPZB 没有可确认的统一可复用许可；zawsstt 许可限制商业使用。原版 MKF/EXE、人物、图像、声音、文案不因某仓库附 GPL/MIT 而自动获准重新发行。**不得复制 GPL 实现到未确认兼容许可的 ReactMono，不得复制受限模型/图片；即使 MIT 也须核查上游原创性和依赖及保留声明**。许可证兼容性需按实际复制行为和代码许可由专业人员核定，本文不作法律鉴定。
- GPL 同族并不自动证明每项仓库合法承继；`oama1111` 服务端实际 `room.ts` 使用 reduce 镜像校验动作，与部分注释“服务端不跑规则”相矛盾，以调用实现为准。

## 4. 原版规则争议：回到三类来源

| 争议 | 原始链及交叉代码 | 裁定与边界 |
| --- | --- | --- |
| **同路段住宅租金** | [mytbk:汇编 199 起](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L199)、[tytannial:estateRouteRent](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/turn_system.cpp#L982-L1010)、[iam567:calcToll](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L1044-L1055) | B 多源一致支持按**同业主、同名路段**累加不同等级收费再乘物价指数；#121 在 C++ 重建版 A 校验 `(200+400)*2=1200`，非原作差分。须防「只按所停一格租金」被误标为原作算法。 |
| **连锁店租金** | 上述三链中 tytannial `e.type != 0 && e.owner == owner`、iam `l.chain` | B 代码将该业主名下每处连锁地产视作固定 2000 基数并乘物价；#121 重建版 A 两处 ×2000×3 得 12000。不能宣称全原作版本/所有例外均如此，联盟、免租、暂态另作断言。 |
| **股票系统有几只** | [tytannial:stockTick](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/stock_system.cpp#L105-L171) 的 `i<12`、[iam567:STOCK_TABLE](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/stocks.ts#L35-L77) 每组 12；[Godot 导入器](https://github.com/nurockplayer/richman4-remake/blob/961bdf47389a08e3143c0340490896b9f50edef9/tools/import_original.py#L28-L61) 声称按版读取 12 | B 只证明三个实现的 12 槽/模板，不等于 ReactMono 的五只**原创虚构股票**存在 bug；原版日期、流通股、企业控制与行情应独立约定，暂不直接替换。 |
| **原版版本/地图范围** | [mytbk docs/map.txt](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/docs/map.txt)、[nurockplayer importer](https://github.com/nurockplayer/richman4-remake/blob/961bdf47389a08e3143c0340490896b9f50edef9/tools/import_original.py#L30-L55) | v3.11/资料片的 8 图、版本股表不能倒推为 **1998 首发版** 8 图；首发/资料片/Steam 校验尚无合法原始字节金标。 |
| **读档随机与重播种** | [oama1111:rng/policy.ts](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/rng/policy.ts#L1-L61) 说原版三个 GetTickCount 位置，单机不存 RNG，联机仅开局播种 | B 证明它实现两套语义；“原版零偏差”仅代码注释，原始三个汇编调用与合法二进制结果尚缺闭环。ReactMono 保存固定 `randomState` 以追求可重现性，**不需要为了像原版而引入不可复现读档**。 |
| **确定性 1000 局** | [oama1111:replay.test.ts](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/state/replay.test.ts#L14-L72) | `const run = existsSync(MAP) ? it : it.skip`；无私有 `extracted/map/0001.bin` 即跳过。该文件存在只能计 B **测试定义**，不是 A「1000 局全过」。作者其它 soak 仅到回合上限，不等于自然分出胜负。 |
| **保存兼容** | [mytbk:旧式 loadsave.c](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/loadsave.c#L99-L147)、[tytannial:save_data.cpp](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/save_data.cpp#L453-L568) | 旧版二进制布局、指针和资源索引与 ReactMono 校验版 JSON 是两套数据契约；没有合法原版 SAVE.DAT 对照，不能声称跨版本导入已证实。 |

## 5. 同视口视觉：把 A、B、审美判断拆开

参阅 [#121 实证页与原始六张 PNG](verification-issue-121/RESULTS.md)。三者各 **1440×900** 与 **390×844**，但只有首次开局、Linux 软件 WebGL，不能证明升级动画、实际真机帧率、手机常规交互。对截图的审美判断是**基于该图的主观评价**，不伪装为用户测量。

- Yakamozli：A 截图桌面严重左偏、大片空白，手机 UI 溢出/棋盘截断；B 解释——`js/scene.js::_buildBoard` 在一个盒体顶部放完整 CanvasTexture，中心几栋装饰楼；`js/ai.js` 是简单启发式。它并非独立立体地砖城市，不可作为 ReactMono 的成熟场景模板。
- zawsstt：A 截图的**书桌/木框/台灯整体包装**视觉密度更高，但中心有大幅平面插画，房屋体量很小；竖屏截图是**旋转的横屏布局**，不等于优质竖屏体验。B 的 `src/view3d.js::syncBuilding` 和 `buildings3d.js` 有不同级地产工厂；**A 未验升级四阶段**、WebRTC、Supabase；其软件 WebGL rAF 样本超时，不能给 FPS。
- ReactMono：A #121 基线在两视口保持正向 UI、行动卡和操作区的可读布局；浅色低模、地块识别、建筑尺度、层次、独特地标与视觉叙事明显不足。当前 dev 在截图基线之后未见本审计新运行画面，不应以当时截图代替当前截图或认可 3D 商品级验收。
- **结论**：zawsstt 的桌面视觉包装值得**学习构图规则**，而非移用纹理/美术代码；ReactMono 应优先做自身原创建模和体验。三者的自动化绿灯均不等于商业级美术。

## 6. ReactMono `dev@6b87e4a` 的真实缺口与取舍

本轮直接核对 `src/core/{turns,property,stocks,bank,random,save,maps}.ts`、`src/demo3d/world/WorldCanvas.tsx`，不再假定 2026-10-19 单仓库报告里的旧 `dev` 仍代表今天。

| 优先级/处置 | 本仓库已实现的能力（B） | 缺口、建议与验收 |
| --- | --- | --- |
| **P0 必须修复产品观感** | [3D 主景](../../src/demo3d/world/WorldCanvas.tsx)、多地图、浏览镜头与手机面板已经存在 | 建立原创场景的**视觉验收关卡**：建筑等级 0/1/2、角色大小、地块颜色对照、桌面/竖屏首屏和操作连贯截图；明确 3D 体量而非大型平面画；真人 15 分钟体验。不能用第三方截图代替本作 |
| **P1 值得考虑规则扩展** | [turns.ts](../../src/core/turns.ts) 对当前落地格单独收租；[property.ts](../../src/core/property.ts) 等级 0–2；[bank.ts](../../src/core/bank.ts) 逐**整轮 1%** 利息；[stocks.ts](../../src/core/stocks.ts) 五个原创标的 | 独立建立“**可选街区联合租金**”设计与测试，原版相关 1200/12000 样例仅为参考；保留当前模式、版本化配置、净资产/破产和旧档迁移，综合平衡后方可改经济 |
| **P1 值得考虑地图能力** | [maps.ts](../../src/core/maps.ts)::advancePosition 以 route 数组线性下一格；多图已数据驱动/大地图扩展 | 如新关卡需要**多分叉方向选择**，设计可验证的图边+往返/事件返回契约；不是简单移植 40 字节原版节点或 Cocos 的游戏对象 |
| **P1 值得考虑可靠性** | [random.ts](../../src/core/random.ts) 固定种子、[save.ts](../../src/core/save.ts) 状态签名/旧档迁移、IndexedDB/PWA 与无头模拟 | 用同动作重放/存档恢复指纹，配合 100+ 固定种子回归；对照 `oama1111` 的测试边界，**不可把它的素材条件跳过算成通过**。 |
| **P2 值得考虑表达层** | [WorldCanvas](../../src/demo3d/world/WorldCanvas.tsx) 场景级阴影与自适应镜头、资产工厂 | 试做原创的风格族谱、材质基准、三级地产视觉成长和可读的动画反馈；有统一光影投受体、低端机预算、真机实测，不照搬上游局部关闭 `castShadow` |
| **明确不引入** | 已有纯静态 Pages、PWA、本地存档与简体中文 UI | 不引入 Supabase、WebSocket 房间服务器、账号云榜、C++/SDL、Godot/Cocos 引擎、不改成原版 640×480 拟真贴图、不默认改成读档不可复现 RNG，不抄录 GPL 核心与商业素材。 |

建议独立后续 Issue 顺序：**① 商品级 3D 美术及三等级同视口验收（P0）→ ② 复杂路径图模型设计及边界测试（P1，地图确需分叉时）→ ③ 原版风格联合租金的独立可选规则测试（P1）→ ④ 确定性重放/旧档可靠性实验（P1）**。先做第一项，避免研究阻塞已成形产品；Issue 成立前与现有开放任务去重，不在 #104 直接改游戏源码。

## 7. 报告质量审计、修正与保留疑点

本轮按九份报告每份最少 3 处固定 SHA 源码锚点和 2 项关键评价复核，明细见 [核验矩阵的审计日志](verification-matrix.md#逐仓库审计日志)。未查出这些抽检锚点的路径不存在；未对整个源码树做全量逐行校验。原报告缺陷与本次处置：

1. #98 `evidence.json` 把多项只有 **B 源码**的功能记成 `verified`，容易被机器消费者误读为独立可玩；本次统一降为 `partial` 并注明无 A，报告/矩阵同步改口径，**不否认逻辑实现存在**。
2. #121 升级了 #96/#102/#103 的局部 A 项，但三个 `execution.result` 仍写“没有 A/未运行”，这和各自新增 A evidence 自相矛盾；本次增量更新三个 JSON 的实验记录，保留 10-19 研究时的历史限制及原始固定 SHA。
3. #100 上游测试受私有文件门槛而 `it.skip`；无需伪称 1000 局通过；跨项目差异矩阵明示“作者/源码定义 ≠ 独立成功”。
4. 视觉 `presentation=null` 即使已有 A 首回合截图仍保留：**截图足以评价这一帧的构图缺陷，但不足以评分完整画面与交互产品质量**。#121 rAF 短样本/超时不是跨项目 FPS 排名。#97 作者的 47/47 CTest 与 20/20 验收仍是 C。
5. 法律未决：使用相同逆向地址、数字或调试标记**不证明源码版权派生**；tytannial MIT 与 mytbk GPL 血缘待鉴定。没有私有 EXE、Data.mkf、SAVE.DAT、iOS/Android 真机，本轮无法升级原作差分验证，均列入后续风险而非假阳性。

**本轮只交付研究文档与数据勘误**，没有运行九个完整上游游戏、没有升级 ReactMono 产品代码、没有发布原版资产。