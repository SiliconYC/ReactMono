# zawsstt/monopoly-rich-life 深度研究（Issue #103）

> **2026-10-21 后续补证**：Issue [#121](../../verification-issue-121/RESULTS.md) 已在本报告相同上游 SHA 下获得独立 [桌面](../../verification-issue-121/evidence/richlife-desktop.png) / [模拟手机](../../verification-issue-121/evidence/richlife-mobile.png) 游戏中 WebGL PNG（A）。桌面书桌包装明显丰富，中心仍有大面积 2D 插画；手机画面横向旋转显示，性能测量超时，未实测完整四级升楼/联机/真机 FPS。本文初查 “无 A” 是截至 10-19 的历史状态，不能直接作为最新状态。

> **定位：原创的 Monopoly 类 / 同类地产经营游戏，不是 1998 年《大富翁4》的忠实复刻。** 本报告是对指定提交的源码审计，非浏览器实测报告；**不能把作者海报、模型注释、60FPS 声称或静态代码审阅当成玩家体验的 A 级证据**。条目编号在 [evidence.json](evidence.json)，五组可复核源码锚点在 [source-index.md](source-index.md)。

## 1. 研究身份与复现基线

| 项 | 记录 |
| --- | --- |
| 上游 | [zawsstt/monopoly-rich-life](https://github.com/zawsstt/monopoly-rich-life)，默认 `main` |
| **固定上游提交** | [`307c1761b150a7179fb0353618a95bc6effe3fee`](https://github.com/zawsstt/monopoly-rich-life/commit/307c1761b150a7179fb0353618a95bc6effe3fee) |
| 最后推送 | 2026-10-10 14:36:14 UTC（GitHub 元数据）；仓库创建于 2026-09-12 |
| 研究核查 | 2026-10-19 UTC；GitHub REST 文件树及逐行源码、许可、文档 |
| fork | GitHub `fork=false`；**只表示平台元数据，不能证明无复制、无派生来源**；未做跨项目相似度检索或原始素材权属链确认 |
| 根许可 | [`LICENSE`](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/LICENSE)，自定义“学习专用（禁止商用）”，GitHub 标记 `NOASSERTION`，非标准可商用许可证 |
| 上游文件特征 | 198 条文件树记录（含目录）；静态 `index.html`、`src/*.js`、`assets/models/**/*.js`、`js/lib/three.min.js`、`supabase/migrations/*.sql`，无根 `package.json` |
| 独立执行 | OpenAI 容器 `git ls-remote` 失败：`Could not resolve host: github.com`；未克隆，未起静态服务器、未跑 Chromium、未执行 SQL/联机；GitHub 文本接口可读 |
| 证据分级 | B：已定位的上游源码和文件树；C：作者 README/海报/代码注释中的成效描述；D：仅作为未证假设。**本轮 A=0** |

**独立复现的后续最短路径（未执行）**：将固定 SHA 检出至隔离目录，以 `python -m http.server 8123` 静态服务；先加 `?auto=1&nofly=1&cdn=0` 检查单机，再以 `?auto=1&allmax=1&cdn=0` 检查全四级终点，`?theme=modern` 对比模型路径、`?legacychar=1` 检查角色回退。联机应使用自建 Supabase 或隔离 mock，不碰上游生产数据。有关上述调试参数的**出处是 [README](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/README.md)，不代表均已验证可用**。见 E01/E02/E14/E16。

## 2. 产品目标及与《大富翁4》的关系

作者将作品定义为“3D 沙盘大富翁”“六位奇人”、书桌模型、22 块地产、4 级建筑、2–4 人联机（C：E02）。源码定义了 [40 格八组的原创城市棋盘](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/src/data.js#L89-L150)，包括南锣鼓巷、铜锣湾、士林夜市等，联机/拍卖/禁锢有另一套自定义主题；[游戏引擎](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/src/game.js#L80-L169)自身构建新局和回合循环（B：E03/E04）。

这证明它是 **`inspired`（同类机制启发）**，而非原版资源抽取、逆向重编译、1:1 规则复原或资料片。其任何“有 40 格/有赌场式拍卖/有四级建筑”的现象，**不能计入《大富翁4》原版规则覆盖率**。即便玩法相似，也必须另行通过原版实际关卡、事件、经济、行为模型和资源来源对照才能作复刻判断。

## 3. 代码架构、数据流和美术资产管线

### 3.1 主路径与规则/渲染边界

`index.html` 先初始化全局 `SB`（素材寻址和 RPC），再按清单加载脚本；`src/main.js` 建立大厅和开局；`src/data.js` 持有 `BOARD`/角色/价格；`src/game.js` 管理全局 `G` 和 `newGame → runGame → playTurn/advanceTurn`；`src/ai.js` 决策；`src/uix.js` 接收游戏提示、弹窗和统计；`src/view3d.js` 读取 `G.tiles` 转换场景。此分层比把游戏规则塞进渲染帧好，但整体是共享全局对象/浏览器脚本，**并非 ReactMono 的可单测 TypeScript 纯命令式规则引擎**（B：E03/E05/E09）。

实际跨层升级路径：自己落地 → `decide` 是否花钱 → `charge` → `st.level++` → `ui.updateTile` → 3D 的 `syncBuilding` 检测等级并替换对应模型。零级不放置楼，1–4 级读取状态而不是靠动画临时造假；但 UI 具体监听触发时序尚未在浏览器核实（E03/E06）。

### 3.2 **真正的三层建筑来源**

1. **优先的逐格专用资产**：现代主题的 `window.Props3DModern[i](level)`，经典主题的 `window.Props3D[i](level)`。文件树包含现代/经典各 22 份 `prop_*.js` 定义，主入口按主题懒加载，均为生成 Three.js 对象的 JS 脚本，而非“每种等级一份 glTF 文件”。
2. **统一程序化兜底**：`Building3D.property(i,level)` 通过 `TILE_GROUP`/八地区 `REGIONS`，走 `stage1` 小屋、`stage2` 店铺/小楼、`stage3` 中层楼、`stage4` 地标建筑，配置屋顶、色板和局部装饰。工厂返回 `THREE.Group`，与专用资产具有相同地块级合约。
3. **渲染与资源控制层**：替换旧组、可选静态几何合并、固定位置/旋转、`shadowDirty` 请求更新；`index.html` 动态装载另一主题，`SB.asset` 将 `assets/` 指向 CDN 并在失败时本地回退。

这意味着“22×4”描述的是 **88 个状态组合**，并不等于 88 个完全独立的手工资产。可借鉴的是“**风格族谱—等级几何—资产回退—运行时契约**”的组织方式，不建议复制其大文件与全局注册器。代码参见 [个性化加载](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/src/view3d.js#L1608-L1639)、[地域表](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/src/buildings3d.js#L1200-L1250)、[四级入口](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/src/buildings3d.js#L1508-L1529)（E06/E09）。

### 3.3 角色、桌面场景与材质

模型树中有六个 [`assets/models/chars3d/*.js`](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/assets/models/chars3d/boss.js#L1-L45) 的专用角色脚本；`buildTokens` 优先 `Char3D`，其次 `Building3D.characters`，最后简单几何人。角色组含颜色环和名字精灵，不依赖原版《大富翁4》角色素材（是否原创完全授权**未知**）。模型头注提及“img2threejs 管线产出”“`refs/char_boss.png`”“`refs/prop_1.png`”，但这些 `refs/` 图像**不在被核对的 198 条固定文件树**，所以图像参考来源、AI 生成过程、许可链均不能由代码注释证实（E07/E12）。

`view3d` 先生成毛毡地面、木框、格子、环状马路；`environment.js` 再使用 `Environment3D.replace` 接管书房背景。环境工厂的源码头详细写有书架、灯、壁纸、窗外景、地球仪与程序化 Canvas 纹理，并声称控制灯光/动画和几何数量。它是**程序化场景搭建**的证据；每个细节是否在当前页面可见、画面是否精致，仍需真机逐对象截图验证（E05/E08）。

### 3.4 测试与复现条件

存在 `tools/mock-supabase.mjs`（Node `ws` 本地模拟信令），`tools/verify-assets.mjs` 与少量运维工具；根目录没有包清单，无法把它当作可一键安装、可持续单测的大型工程。作者 README 说明静态服务器即可本地运行，可能足以单人开局；**本轮没能独立执行**。另外引擎 [`rnd` 用 `Math.random`](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/src/game.js#L28-L33)，不具备已经验证的跨浏览器确定性测试契约；不能因此断言项目根本没做过测试（E03/E14）。

## 4. 功能完成度与原版规则对照矩阵

下表“部分”指**有源码实现路径、尚未运行验收**；“宣称/实现”表示源码和作者描述相互印证，却缺真实服务或跨端证明；“未知”不等于没有。ReactMono 一列只说明**兼容选择**，不是对当前游戏再次验收。

| 功能维度 | 上游代码证据 / 状态 | 与《大富翁4》忠实复刻关系 | ReactMono 取向 |
| --- | --- | --- | --- |
| 新局、回合、破产、结算 | 部分：`game.js` 状态与循环；E03 | 自定义规则，未逐项对照 | 保留现有确定性核心 |
| 地图及地产 | 部分：40 格、22 地、八地区与四级升级；E03/E04/E06 | 不是原版地图/资源 | 研究升级可读性，不照搬价格 |
| 银行、贷款、股票 | **未知**：本轮未在指定代码路径确认原版等价机制；E03/E04 | 不可以“都有经济系统”认定忠实 | 不倒退既有银行与股市 |
| 道具、机会、季节 | 部分：引擎逻辑、道具与季节声明；E03 | 事件表不同，需独立原版对照 | 只借鉴事件演出表达 |
| 神明、怪异事件 | 未建立原版逐项矩阵；E03/E04 | 未能评分 | 不按印象补全 |
| AI | 部分：`src/ai.js` 和游戏回合调用；E03 | 未验证原版 AI 行为一致性 | 坚持合法命令和固定种子测量 |
| 存读档 | **未知**：本轮未取得可靠完整局恢复/跨版本路径；E14 | 没有可验证的等价证据 | 保留 IndexedDB/PWA 方案 |
| 沙盘场景与镜头 | 部分：相机/灯光/木框/书房；E05/E08 | 独立视觉语言，不是复刻画面 | 仅借构图和镜头约束 |
| 四级建筑/角色 | 部分：专用脚本 + 程序化回退；E06/E07 | 原创主题角色与街区 | 可提炼模型接口和风格族谱 |
| 联机、断线恢复 | 宣称且有代码：RTC/信令；E10 | 不构成原版证据 | **不采用服务器/云联机** |
| 本机、云排行榜 | 本机部分、云端待实测；E11 | 独立衍生功能 | 仅保留本地数据，不做全网榜 |
| 安装、离线和移动性能 | **未知**：静态文件与 CDN 兜底≠离线 PWA；E09/E13 | 与原版完成度不同维度 | 必须在本地 PWA 验收 |

## 5. 五处核心技术深挖与视觉证据

**① 书桌沙盘的构图契约（S01，B）**：`buildBoardFrame` 用 44.6×32.6 的基座、四根木框与金属细边装饰；`buildTable` 做地面毛毡，`Environment3D.replace` 布局书房。场景形成视觉上可感的“**棋盘是桌上的一个物件**”，非无边界地图。但它是固定二维环形棋盘，不能直接满足 ReactMono 未来更复杂地形的自由镜头。需测试摄像机最低高度、遮挡/文字可读性和安全区。

**② 视角/照明/阴影（S01，B）**：透视相机视场角 45°；`homeDistFor(aspect)` 以棋盘边界、纵横比和 0.935 的 NDC 边缘预算计算初始距离。全局/跟随模式各有缩放和极角界限、手势/键盘支持。渲染器设置 `PCFSoftShadowMap`、`ACESFilmicToneMapping`、高/移动不同阴影分辨率，半球光＋主太阳＋冷补光。**这些都是代码设置，不是已经实测的阴影质量或手机帧率。** [`buildings3d.js` 局部 `castShadow=false`](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/src/buildings3d.js#L650-L752) 与 ReactMono **全局统一投/受影**约束冲突：只能借鉴镜头适配思路，不得照抄选择性关阴影（E05/E15）。

**③ 四级生长和负载（S02，B）**：`stage1..stage4` 并非逐级缩放同一个盒子，而是屋顶、层数、店面、阳台、旗饰和地域装饰的**轮廓进化**。专用 `Props3D` 比通用工厂更细，能让地块有地域辨识，但意味着每个主题为 22 格维护独立 JS，并在运行时缓存材质/合并几何；素材制造与回归成本不可忽视。ReactMono 应先实现少量原创风格族谱模板，建立可测的几何/阴影合约再铺满地图（E06/E07）。

**④ 角色可辨识度与美术血缘（S03，B/C）**：角色模型在 `buildTokens` 中抽象成挂载 `THREE.Group`，用 `parts` 支持局部动作；`legacychar=1` 为同一业务状态提供回退。`boss.js` 中精修笔记声称 218 mesh 的角色、三视图参考与精修差距清单；这些是**源码内的作者自述**，不能据此认定“已商业级”或成本可控（E07/E13）。且参考图片不在提交内，不应搬用角色脸、动画、音乐或视频。

**⑤ 云端割裂点（S04/S05，B）**：`SB.asset` 和 `__loadBoardTheme` 走在线 Storage → 同仓副本；`supa-rtc.js` 使用 Supabase Realtime WebSocket 完成 WebRTC 建连，`net.js` 房主快照/远程决策与重连；结算通过 `report_round` 写入云榜，SQL 建有 Storage 桶、`players`、`mp_rooms`、`mp_members` 和 RLS。**绝非纯前端离线多人联机：房间发现、信令、云榜显式需要运行中服务。** 本地 mock 只说明作者预备了测试替身，不能代替生产级测试。ReactMono 产品坚持零服务器，排除这条路线（E09–E11）。

### 图像证据的正确使用

| 对照样本 | 精确链接 | 证据层级 | 本轮能、不能得出的结论 |
| --- | --- | --- | --- |
| 上游作者海报 | [`assets/img/scene_poster.jpg`](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/assets/img/scene_poster.jpg) | C：作者提交的宣传图 | 证明有图像文件/可作未来同视角参考；**没有本轮的实时运行像素或真实性验证** |
| ReactMono 现有场景预览 | [`arrival-1440.png`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/docs/main-game-ui-redesign/previews/rebuild/arrival-1440.png) | 历史项目预览，非本次 A | 可定位已提交的历史图像；**本轮未独立重现** |
| ReactMono 回合界面预览 | [`turn-1440.png`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/docs/main-game-ui-redesign/previews/rebuild/turn-1440.png) | 历史项目预览，非本次 A | 可做未来信息密度对照，不能代表当前最新版的实时画面 |

本轮能对照的仅是**代码上的构图选择**：上游“书桌/木框/环路/书房”提供完整舞台物件，ReactMono 产品规范追求的是“可玩优先、商业级原创低多边形角色与地图、正确的全场景阴影”，应当比较镜头、安全区、遮挡和美术层级。容器 DNS 不可用，GitHub 图片二进制读取也失败，所以**没有实际看图后的审美排名、等视口截图差分或虚构的测量数值**。具体视觉完成度评分保留 `null`；此项未达到 A 级截图验收，后续补测单独登记。

## 6. 对 ReactMono 的优先级建议（不复制上游资源）

| 顺序 | 结论及价值 | 成本 / 风险 | 与 ReactMono 当前架构的执行建议与验收 |
| --- | --- | --- | --- |
| **R1 优先借鉴** | **场景层级/“桌上小世界”聚焦**：物件化桌边界、环路、衬景、交互焦点提升舞台感 | 中；镜头/遮挡/字标可能冲突 | 在独立方案中构建 **原创** 桌面舞台原型，保持 Three.js 现有场景树；等尺寸桌面/手机截图测量棋盘占屏率、交互可读性；不重排现有游戏规则 |
| **R2 优先借鉴** | **22 地产×4 阶“同一身份的轮廓增长”**：地块升一级时外观可一眼区分 | 中高；资产产能与绘制调用 | 为少量街区设定独立色板、屋顶/饰物/楼高语法，保持每级同一地块识别符；自动验证四级尺寸、阴影、贴地与存档读回 |
| **R3 借鉴接口，不借实现** | **主资产—地域兜底—简易占位**：避免缺失某地产导致白屏 | 中；不同来源模型比例/动画契约 | 在 React/TypeScript 资产注册层设计可测 `create(tileId, level, theme)`，明确销毁纹理/几何体和未找到素材时的降级事件；不采用动态执行字符串 JS |
| **R4 有条件借鉴** | **视口自适应镜头和质量档**：初始棋盘完整、手机画面不裁切 | 中；旧式阴影逻辑与 AGENTS 冲突 | 根据投影包围盒和 HUD 安全边距求相机距离；采用当前 Three.js 支持的统一场景阴影方案，移动端只调图形质量（阴影分辨率），不能逐物体关影 |
| **R5 明确排除** | **Supabase/WebRTC 信令、云榜、CDN 依赖及原版资产移植** | 高；服务器/隐私/许可与产品硬约束冲突 | 不开发账号、在线榜、运行时后端；保留 PWA 离线、IndexedDB 本地存档、已有 ReactMono 状态机；**严禁复制上游非商用角色、地产模型、音乐和视频** |

这些是下一轮候选，不在研究 Issue #103 中直接修改业务代码。若要升级为实施 Issue，须通过既有演进候选池去重/准入，且须独立浏览器视觉及规则回归，不把“程序化资产能生成”视作商业级验收通过。

## 7. 缺口、许可与声称—证据矛盾

1. **许可红线**：上游 [`LICENSE`](https://github.com/zawsstt/monopoly-rich-life/blob/307c1761b150a7179fb0353618a95bc6effe3fee/LICENSE) 明确仅允许个人学习、免费教学和非营利二创，禁止产品销售、广告变现及任何商业项目搭载；没有可商用的 SPDX 许可。README 另声明立绘/建筑/音频仅限其学习演示。ReactMono 不能把这套游戏源码、人物轮廓、逐格场景脚本和媒体当成可商用开源资产；仅研究抽象设计原则。Three.js 依赖的许可须与上游作者许可区分。
2. **素材归属不足**：提交包含六个音轨、角色立绘、声音、短片与大量专用脚本。注释引用不在仓库的 `refs/...`，未发现媒体逐项授权表；不能推断素材全部为作者原创、具有二次授权能力（E07/E12）。
3. **“纯浏览器” ≠ 全离线**：即使可把静态页面运行在本地，云排行榜、信令与 CDN 优先路径仍联网；`cdn=0` 只强制资源走本地，不能把房间 RPC 移除（E09–E11）。
4. **“60FPS”和“精细建模”**：前者 README 自述，后者来自源文件和作者注释。本轮未有 GPU、浏览器快照、手机实验，不能给予实测分（E13/E16）。
5. **工程可验证性不足**：未见根包管理契约与稳定测试入口；大量 JS 工厂靠 `window.*` 全局注册，`game.js` 中随机源非显式种子，截图/模型精修记录无法替代真实自动化回归（E03/E14）。
6. **光影规范不同**：几何工厂有显式 `castShadow=false`；直接粘贴将冲撞 ReactMono 的“全局一致投影者/受影者”规则。要研究其镜头尺度与材质选择，不拿局部禁影作为解决阴影伪影的手段（E15）。
7. **联机安全未验证**：虽然 SQL 声明 RLS 与 RPC，未运行 SQL/房间实测，也未对抗性分析匿名客户端防刷、座位令牌和断线处理；不能以“有 RLS”断言可靠/安全（E10/E11）。

## 8. 五维证据评分（0–5，未知填 null）

| 指标 | 分数 | 证据 / 置信度 |
| --- | ---: | --- |
| 《大富翁4》原版规则覆盖 | **null** | 本作目标非原版复刻，且缺原版逐项对照；不用原创游戏规则缺失虚构 0 分（E03/E04） |
| 代码可维护性 | **2/5** | B，低—中：模块角色分工存在，但大文件/全局脚本/根测试契约不足；不等于无法维护（E03/E05/E09/E14） |
| **独立可复现性** | **null** | 无 A 级执行，联网检出受阻，不能把未执行判为不可运行（E14/E16） |
| **画面与交互完成度** | **null** | 场景和模型代码存在；海报不是实机截图，未独立观察像素、交互和帧率（E05/E08/E13/E16） |
| 对 ReactMono 的实用价值 | **3/5** | B，中：构图、镜头、四级风格族谱及三层资产回退可作为原创设计思路；许可、云服务、阴影处理无法直接采用（E05/E06/E09/E12/E15） |

**不计算总分、不宣称“商业级”，也不与已有《大富翁4》逆向研究项目排综合名次。** 本分数仅评价可核对的工程思路和风险，不代表商业玩家视觉评分。

## 9. 结论及下一步

**结论：`read_only_reference`——只读研究参考，排除源码/美术资源直接复用。** 最有价值的是“微缩舞台的整体构图契约 + 成体系的地域四阶建筑风格 + 带兜底的资产工厂”，而非联机服务、人物资产或仓库作为可直接采用的游戏基础。

下一步优先为 R1/R2 建立**完全原创的最小美术原型**（不在本 Issue 编码）；使用同视口真实 Chromium 桌面/手机截图比较棋盘覆盖率、模型层级与人物辨识，并记录帧率、draw calls、阴影一致性、与既有 UI HUD 冲突。随后只挑可量化改善的点按正常提案准入流程晋升。

**明确未解决事项**：本 SHA 的真实 WebGL 截图和手机 GPU 性能；模型生成所据 `refs` 图片及媒体版权授权链；自建/隔离 Supabase RPC 与联机重连复现；PWA/弱网表现；与原版规则的逐项可靠对照。证据和可继续核查的精确地址见 [source-index.md](source-index.md) 和 [evidence.json](evidence.json)。研究者未获取私有素材、未修改 ReactMono 游戏代码、未宣称独立实测。
