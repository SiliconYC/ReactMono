# 《大富翁 4》外部开源项目研究入口

本目录是既有 ReactMono 游戏仓库的**增量研究区**，不是新建游戏架构，也不是替换现有代码的迁移工程。游戏代码仍位于原来的 `src/`、`demo3d/` 等目录；现有 `README.md`、`AGENTS.md`、P0–P5 路线图和验收纪律继续生效。

## 研究目的

1. 核验 1998 年大宇《大富翁 4》的规则、资源结构、地图、经济、卡片、股市、电脑行为、交互与存档机制；区分原版、资料片和民间二创。
2. 比较外部项目在玩法完整度、逆向证据、工程成熟度、画面及现代平台兼容性上的实际效果。
3. 为 ReactMono 提供可验证的**借鉴建议**，不默认移植任何外部代码或原版商业素材；保留 React + TypeScript + Three.js、静态 GitHub Pages、PWA、本地存档、简体中文界面和原创现代视觉方向。
4. 明确区分「代码可见」「开发者声称可用」「自动化验证」「研究者独立运行与截图」「真人完整对局」等不同证据级别。

## 历史候选清单（立项时的假设，不等于 2026-10-21 的验收状态）

| 上游仓库 | 主要研究问题 | 方向 / 优先级 |
| --- | --- | --- |
| [mytbk/rich4](https://github.com/mytbk/rich4) | 原始 x86、资源/存档格式及汇编逆向的证据可靠度、被其他项目引用的血缘 | 原版逆向 / P0 |
| [tytannial/rich4-re](https://github.com/tytannial/rich4-re) | C++/SDL3 重建、事件/经济/卡片覆盖、无头测试与规则可追溯性 | 原版重建 / P0 |
| [lhr0909/richman4-remastered](https://github.com/lhr0909/richman4-remastered) | 原生跨平台版本、界面/音视频、完成度与实际设备验收 | 原版移植 / P0 |
| [iam567/rich4-renew-app](https://github.com/iam567/rich4-renew-app) | TypeScript 规则引擎、高分辨率 UI、手机封装、扩展玩法 | 网页/移动重制 / P0 |
| [nurockplayer/richman4-remake](https://github.com/nurockplayer/richman4-remake) | Godot 原版一致性、可玩证据、被退回的视觉验收 | Godot 重制 / P1 |
| [oama1111/rich4-remake-public](https://github.com/oama1111/rich4-remake-public) | 确定性规则、原版素材导入、Tauri、联机与公开镜像缺口 | 桌面/网页重制 / P1 |
| [JCRJPZB/Rich4](https://github.com/JCRJPZB/Rich4) | Cocos Creator 老项目的地图、角色、AI、可运行程度 | 早期图形引擎复刻 / P2 |
| [Yakamozli/richman-3d](https://github.com/Yakamozli/richman-3d) | Three.js 代码生成三维棋盘、角色、建筑和真实观感 | 同类玩法视觉参考，非原作忠实复刻 / P1 |
| [zawsstt/monopoly-rich-life](https://github.com/zawsstt/monopoly-rich-life) | Three.js 风格化沙盘、美术资产管线、建筑成长与联机架构取舍 | 同类玩法视觉参考，非原作忠实复刻 / P1 |

边界项目 [Infinicken/Richman4L](https://github.com/Infinicken/Richman4L) 与其他 forks 可作为历史背景、代码血缘材料；如果初查发现独立研究价值，再另建非重复 Issue，不要机械拆单。

**以上表格为 2026-10-19 立项时研究方向/优先级历史快照，不是当前候选进度，更不是研究后评分。** 2026-10-21 九项均已交付并合并；仅 #121 涉及范围的两个 3D 上游截图和一项 C++ 原生经济小样例有独立 A 补证。没有合法原版程序实测。实际状态见下述验收导航。

## 组织结构与产物

- 规范：[`RESEARCH_STANDARD.md`](RESEARCH_STANDARD.md)，包含证据分级、九章研究报告、可追溯 JSON、评分和验收。
- 一仓库一子目录：`docs/research/repositories/<owner>--<repo>/`，例如 `repositories/mytbk--rich4/`（保留大小写），**只有开始正式研究并提交真实文件时才创建**。
- 每个研究子目录至少交付 `README.md`（九章深度报告）、`evidence.json`（结构化证据与判断）、`source-index.md`（代码路径、行号/符号/提交与运行命令）；如有合法截图或测试报告按需添加，杜绝空目录与占位文件。
- 跨仓库已交付 [综合研究](comparative-review.md)（原版机制源码交叉判断与产品路线）、[99 格核验矩阵](verification-matrix.md)（逐功能等级和抽样日志）、[机器可读九仓证据](summary.json)（固定版本/关系/评分/限制），而非各自报告简单拼接。
- 文件索引与规则见 [`repositories/README.md`](repositories/README.md)，待真实研究合并时更新。
- 原版商业素材、未获公开许可的游戏程序、各仓库完整镜像与大型生成文件一律不提交本仓库。

## 已合并的九项单仓库研究（2026-10-21 核对）

以下九项 **全部已关闭并以 PR 合入 `dev`**；「单仓库研究已合并」不表示原版游戏、完整玩家体验或合法商业资源已获 A 级验证。

| Issue | 上游 | 预期目录 |
| --- | --- | --- |
| [#95](https://github.com/SiliconYC/ReactMono/issues/95) | [mytbk/rich4](https://github.com/mytbk/rich4) | `repositories/mytbk--rich4/` |
| [#96](https://github.com/SiliconYC/ReactMono/issues/96) | [tytannial/rich4-re](https://github.com/tytannial/rich4-re) | `repositories/tytannial--rich4-re/` |
| [#97](https://github.com/SiliconYC/ReactMono/issues/97) | [lhr0909/richman4-remastered](https://github.com/lhr0909/richman4-remastered) | `repositories/lhr0909--richman4-remastered/` |
| [#98](https://github.com/SiliconYC/ReactMono/issues/98) | [iam567/rich4-renew-app](https://github.com/iam567/rich4-renew-app) | `repositories/iam567--rich4-renew-app/` |
| [#99](https://github.com/SiliconYC/ReactMono/issues/99) | [nurockplayer/richman4-remake](https://github.com/nurockplayer/richman4-remake) | `repositories/nurockplayer--richman4-remake/` |
| [#100](https://github.com/SiliconYC/ReactMono/issues/100) | [oama1111/rich4-remake-public](https://github.com/oama1111/rich4-remake-public) | `repositories/oama1111--rich4-remake-public/` |
| [#101](https://github.com/SiliconYC/ReactMono/issues/101) | [JCRJPZB/Rich4](https://github.com/JCRJPZB/Rich4) | `repositories/JCRJPZB--Rich4/` |
| [#102](https://github.com/SiliconYC/ReactMono/issues/102) | [Yakamozli/richman-3d](https://github.com/Yakamozli/richman-3d) | `repositories/Yakamozli--richman-3d/` |
| [#103](https://github.com/SiliconYC/ReactMono/issues/103) | [zawsstt/monopoly-rich-life](https://github.com/zawsstt/monopoly-rich-life) | `repositories/zawsstt--monopoly-rich-life/` |

[综合综述 #104](https://github.com/SiliconYC/ReactMono/issues/104) 已据上述九份原始成果和独立 [#121](verification-issue-121/RESULTS.md) 完成跨源审查；九仓详细差异参见 [统一矩阵](verification-matrix.md)。

## 落地步骤（在既有仓库上补做八步 SOP）

1. **检查现状**：保留游戏代码、原 README/AGENTS、既有文档、已有 Issue/PR 和测试；先去重。
2. **确定分支**：只以 `dev` 为基线和合并目标；绝不因研究工作改写 `main`。
3. **补充 README**：仅追加外部研究导航、范围及边界，不替换产品目标。
4. **补充 AGENTS**：仅添加研究者规范、证据与交付约束，与现有游戏代理规范并行。
5. **核对 .gitignore**：仅排除外部克隆、临时反汇编/生成与本地缓存；跟踪可复现研究资料。
6. **建立逐仓库研究任务**：优先研究有独立来源价值的项目，每个 GitHub 仓库一个独立 Issue 和子目录。
7. **跨仓库证据汇总**：待子研究合并后，交叉核查作者/代码来源、矛盾、许可证、视觉与游戏完成度，形成综述。
8. **提交和验收**：细粒度提交、必要检查、通过 PR 合并到 `dev`；有障碍保留可续接提交并说明。

## 当前验收分层与后续入口

| 分类 | 当前状态 | 证据边界与阅读入口 |
| --- | --- | --- |
| 历史候选 | 九项已经从候选完成研究；边界项目 `Infinicken/Richman4L` 没有单独立项 | 上文候选表只供回看，不可当最新排名 |
| 在研单仓库 | **本轮九项中 0 项**（#95～#103 已关） | 后续新增必须按去重准入再开 Issue |
| 已合并单仓库 | **九项全部合并，含 B/C/D 源码结论和局部原有 A 数据级检查** | [报告索引](repositories/README.md) 与各自固定 SHA |
| 已验收的独立运行补证 | **#121 已完成，PR #122 已合并至 `dev@6b87e4a`** | [六张浏览器原始截图及经济 126 条断言](verification-issue-121/RESULTS.md)；3 个商业资源测试跳过 |
| 综述 | **#104 综合分析交付** | [综述](comparative-review.md) / [99 格机制矩阵](verification-matrix.md) / [JSON](summary.json) |
| 尚未独立证明 | 原版 1998 程序逐字节差分、全项目连续玩家对局与手机实体设备/硬件性能 | 不把历史静态审查升级为成功，也不据这些未验证项否定独立的源码研究价值 |

实际开发建议先复核是否与 [#73](https://github.com/SiliconYC/ReactMono/issues/73) 正式版综合验收或既有 P4 美术任务重复，再按 [定向进化池](../EVOLUTION_POOL.md) 评审、立单、独立验收；#104 不改游戏代码。

## 2026-10-21 独立实验补证

[Issue #121 六幅真实 Chromium 对比与原生经济边界验证](verification-issue-121/RESULTS.md) 已收口：仅将可复现的首回合画面、两类经济机制的有限 C++ 重建实验升级为 A；其它历史 B/C/D 证据仍按原报告限定。三份上游权威 `evidence.json` 已同步，禁止理解为原商业版差分或真机性能验证。
