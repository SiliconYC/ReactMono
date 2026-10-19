# 《大富翁 4》外部开源项目研究入口

本目录是既有 ReactMono 游戏仓库的**增量研究区**，不是新建游戏架构，也不是替换现有代码的迁移工程。游戏代码仍位于原来的 `src/`、`demo3d/` 等目录；现有 `README.md`、`AGENTS.md`、P0–P5 路线图和验收纪律继续生效。

## 研究目的

1. 核验 1998 年大宇《大富翁 4》的规则、资源结构、地图、经济、卡片、股市、电脑行为、交互与存档机制；区分原版、资料片和民间二创。
2. 比较外部项目在玩法完整度、逆向证据、工程成熟度、画面及现代平台兼容性上的实际效果。
3. 为 ReactMono 提供可验证的**借鉴建议**，不默认移植任何外部代码或原版商业素材；保留 React + TypeScript + Three.js、静态 GitHub Pages、PWA、本地存档、简体中文界面和原创现代视觉方向。
4. 明确区分「代码可见」「开发者声称可用」「自动化验证」「研究者独立运行与截图」「真人完整对局」等不同证据级别。

## 初步候选清单（截至 2026-10-19，尚非深入验收结论）

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

**上述描述只是候选研究假设**。GitHub 仓库存在、README 声称功能齐全，不代表已由本项目安装、运行或审美验收。禁止以候选表作为完成度排名。

## 组织结构与产物

- 规范：[`RESEARCH_STANDARD.md`](RESEARCH_STANDARD.md)，包含证据分级、九章研究报告、可追溯 JSON、评分和验收。
- 一仓库一子目录：`docs/research/repositories/<owner>--<repo>/`，例如 `repositories/mytbk--rich4/`（保留大小写），**只有开始正式研究并提交真实文件时才创建**。
- 每个研究子目录至少交付 `README.md`（九章深度报告）、`evidence.json`（结构化证据与判断）、`source-index.md`（代码路径、行号/符号/提交与运行命令）；如有合法截图或测试报告按需添加，杜绝空目录与占位文件。
- 汇总研究完成后交付 `comparative-review.md`（跨仓库综合研究）、`verification-matrix.md`（证据与争议矩阵）及 `summary.json`（机器可读的比较结果），**现在不提前写空报告**。
- 文件索引与规则见 [`repositories/README.md`](repositories/README.md)，待真实研究合并时更新。
- 原版商业素材、未获公开许可的游戏程序、各仓库完整镜像与大型生成文件一律不提交本仓库。

## 已创建研究任务（2026-10-19）

以下是 2026-10-19 建立的九项研究任务，**创建 Issue 不等于完成**；交付状态以对应研究报告、PR 合并和验收为准。#103 已交付 B/C 级静态源码审计，其余按实际远端成果更新。

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
| [#103](https://github.com/SiliconYC/ReactMono/issues/103) | [zawsstt/monopoly-rich-life](https://github.com/zawsstt/monopoly-rich-life) | [九章报告与证据](repositories/zawsstt--monopoly-rich-life/README.md)（源码 B / 作者 C；浏览器实测未完成） |

[综合综述 #104](https://github.com/SiliconYC/ReactMono/issues/104) 依赖这些研究真实合并成果，届时才创建 `comparative-review.md`、`verification-matrix.md` 与 `summary.json`。

## 落地步骤（在既有仓库上补做八步 SOP）

1. **检查现状**：保留游戏代码、原 README/AGENTS、既有文档、已有 Issue/PR 和测试；先去重。
2. **确定分支**：只以 `dev` 为基线和合并目标；绝不因研究工作改写 `main`。
3. **补充 README**：仅追加外部研究导航、范围及边界，不替换产品目标。
4. **补充 AGENTS**：仅添加研究者规范、证据与交付约束，与现有游戏代理规范并行。
5. **核对 .gitignore**：仅排除外部克隆、临时反汇编/生成与本地缓存；跟踪可复现研究资料。
6. **建立逐仓库研究任务**：优先研究有独立来源价值的项目，每个 GitHub 仓库一个独立 Issue 和子目录。
7. **跨仓库证据汇总**：待子研究合并后，交叉核查作者/代码来源、矛盾、许可证、视觉与游戏完成度，形成综述。
8. **提交和验收**：细粒度提交、必要检查、通过 PR 合并到 `dev`；有障碍保留可续接提交并说明。

## 执行状态

研究基础设施与九项研究 Issue 已于初始化时建立。随后 #103 已补交 `zawsstt/monopoly-rich-life` 的独立九章源码审计、精确 SHA 证据索引、分级 JSON；因环境限制未独立运行浏览器/联机，也未生成真实对照截图，视觉及可复现性未评分。见[已交付研究索引](repositories/README.md)；其他研究以真实合并记录为准，综合 #104 仍需跨仓库复核。
