# 数据关卡与显式场景创作

2026-10-20：[P008](../proposals/P008-authored-level-worlds.md) 将地形、植被、设施和道路世界坐标提升为关卡数据；不再散布自动背景。当前验收见[显式世界报告](AUTHORED_WORLD_ACCEPTANCE.md)。下面的规则轮廓是历史逻辑坐标，实际画面使用 `world`。

来源：[P007 背景艺术方案与规格](../proposals/P007-scalable-world-maps.md) · [Issue #94](https://github.com/SiliconYC/ReactMono/issues/94)。数据任务 #94 当时只提背景设计；后续 #107 已实现连续地表与大地图显示，见[渲染画面与验收](RENDERING_ACCEPTANCE.md)。

## 三张地图

![真实路线数据缩略图](route-overview.svg)

| 名称 / 标识 | 格数 | 坐标范围 | 特征 | 独立数据容器 |
| --- | ---: | --- | --- | --- |
| 柳湾漫游 `bend-60` | 60 | 19×13 | 沿河湾展开的弧形街道 | [JSON](containers/bend-60.json) |
| 双湖水城 `bays-120` | 120 | 31×25 | 双湖、湖心洲与城郊回湾 | [JSON](containers/bays-120.json) |
| 青麓长途 `ridges-360` | 360 | 71×71 | 山麓、湖城、牧场三个区域 | [JSON](containers/ridges-360.json) |

这三张图都是真实关卡，选图后可使用既有规则、AI 和存档系统。用于扩展性测试，尚未进行局长、租金、银行利息或真人趣味性的平衡验收。格数不等于轮数：一轮是所有玩家各行动一次，不是绕地图一周。

## 唯一运行时数据源

`src/data/levels.json` 包含六个完整关卡容器：五张可选地图与内部 16 格 demo。`containers/` 是从该目录导出的交换副本，`outlines/` 是三张新图的创作轮廓。修改游戏应更新运行时目录；交付交换文件时同步导出，避免将副本误当成第二个运行时来源。

没有按地图 ID 分支的形状生成逻辑。规则注册、UI 列表、路线缩略图、开局、地块坐标和存档识别都读取同一目录；旧 API 的三张固定导出只作兼容别名。旧 demo 的地名、经济与坐标也来自目录。地图规则不依赖 React。

目录外层对象包含 `schemaVersion: 2` 和 `levels` 数组；每项是包含 `world` 的完整关卡。版本1作为历史规则草稿兼容。上方三个 JSON 都是可以独立校验的实际容器。

每个关卡字段：

| 字段 | 含义与约束 |
| --- | --- |
| `name` / `description` / `playable` | 简体中文名称、说明与是否出现在选图页 |
| `map.id` / `map.version` | 稳定身份与正整数版本；ID 使用小写字母、数字、连字符，`custom-N` 保留给历史存档 |
| `map.columns` / `map.rows` | 正整数坐标边界，最大 10000，不代表全部格点必须占满 |
| `map.cells` | 按地块 ID 索引的 `{column,row}`，从 1 开始，无重叠、无越界 |
| `map.route` | 从地块 0 开始、包含全部 ID 一次的循环顺序；相邻项及末项→首项曼哈顿距离为 1 |
| `tiles` | 与 cells 等长，`id` 连续；0 为 `start`，其余为 `property` / `neutral`；地块名最多 100 字，地产有非负整数 `price` / `rent` |
| `initialCash` / `maxRounds` | 开局现金与默认轮数；选图应用默认轮数，玩家可再修改 |
| `eventRules` | 中立格 `tileIds`、奖金 `bonus`、费用 `fee` |
| `cardRules` | 中立格 `tileIds`、`rewardCash` / `moveBonus` / `maxHand`，参数遵循现有存档范围；不与事件站点重叠 |
| `facilityConfig` | 医院/监狱/商店的地块 ID、停留回合、费用、五类卡片价格与库存；或 `null` 表示无特殊设施。地点必须是不同的中立格，可与事件/卡站共用原有中立格语义；启用特殊设施时由设施接管停留行为 |

当前规则/存档支持 **4～512 格、正交相邻单闭环** 的正式关卡；历史 2 格等小测试存档继续兼容。这是现有游戏格式的边界，不是新背景方案的尺寸/形状边界。分叉、跨层与非格点路线需要另行版本化规则拓扑。地图可以凹入、多拐角、细长，不要求矩形周界。

已发布 ID 的规则几何不能直接改写，即使增加 version 也不能删除旧定义：否则原存档会被正确拒绝。变更规则拓扑使用新 ID，并保留旧定义；可令旧定义 `playable:false`，继续支持读档。表现坐标独立存在 `world`，可以重新绘制而不改变对局规则。

## 用 JSON 快速创作关卡

1. 参考 [60](outlines/bend-60.json)、[120](outlines/bays-120.json)、[360](outlines/ridges-360.json) 格轮廓文件，编辑 `id`、中文名称和轴对齐的拐点。最后一个拐点自动连接第一个，不重复写首点；所有线段长度之和就是格数。
2. 通用离线工具将轮廓展开为完整坐标、route、地块价格、事件/卡站及设施模板。它不包含任何具体地图 ID 或形状的分支；输出文件已存在时拒绝覆盖。

```sh
npm run maps:generate -- docs/maps/outlines/bend-60.json /tmp/bend-60.catalog.json
npm run maps:validate -- /tmp/bend-60.catalog.json
```

3. 工具只输出版本1规则草稿，不设计背景。完成地名、价格、站点编辑后，按下方格式逐项创作 `world`，将目录升级为版本2，再将关卡加入 `src/data/levels.json`。不要重复已有 ID；无需修改 TypeScript 注册表或 UI。
4. 运行校验与验证：

```sh
npm run maps:validate
npm test
python3 -u tests/browser_stress_maps_e2e.py
```

生成模板的经济参数只是起点，不代替平衡设计。也可以绕过轮廓工具，直接从外部编辑器输出同格式目录。运行时离线使用已打包目录，不从远程取图，不提供在游戏中导入未注册关卡的功能。

## 本地验证入口

- 主程序：[127.0.0.1:4174](http://127.0.0.1:4174/) → 开始游戏 → 选择地图；新图在原两图之后，准备面板可滚动。
- 原迁移 demo：[127.0.0.1:4173](http://127.0.0.1:4173/)，继续保留。

## 背景已知问题

压力地图已经实际暴露圆形地表漏承载、固定海面不足、远景雾/裁切及凹段地产仍按矩形外缘取锚点的问题。下列图片是本轮真实浏览器截图，**不是背景修复完成图**：

- [60 格桌面](evidence/bend-60-desktop.png)、[120 格桌面](evidence/bays-120-desktop.png)
- [360 格桌面](evidence/ridges-360-desktop.png)、[360 格手机](evidence/ridges-360-phone.png)
- [选图桌面](evidence/selection-desktop.png)、[选图手机](evidence/selection-phone.png)

上述截图是 #94 的历史缺陷基线。后续 #107 完成连续地表和显示修复，见[当时验收](RENDERING_ACCEPTANCE.md)。P008 进一步实现显式地形区域与景物数据；本地通过不等于正式发布或物理设备验收完成。

## 显式世界格式（world.version = 1）

`map.cells` / `map.route` 继续决定规则身份、存档与移动顺序；`world.tiles` 按相同地块 ID 索引，决定实际显示坐标。弯道不再受规则行列的形状限制。当前三张大图名称为柳湾漫游、双湖水城、青麓长途，标识和格数保持兼容。

| 字段 | 约定 |
| --- | --- |
| `background` | 六位十六进制背景色 |
| `base` | `{kind,color}`，kind 为 grass/water；作者明确指定延展基底，不根据道路推测土地，也不产生景物 |
| `tiles` | 每格 `{x,z,lotX,lotZ,rotation}`：道路与所属地产坐标、路砖朝向（弧度），必须完整且无重复，道路与地产至少相距1.7单位 |
| `surfaces` | 每面 `{id,kind,color,points,holes}`，kind 为 grass/sand/water/plaza；轮廓及洞均为 `{x,z}` 顶点数组。简单多边形，不重复首点；洞在外轮廓内，彼此不相交 |
| `objects` | 逐个 `{id,kind,x,z,rotation,scale,color}`；每棵树、每株花及设施各有独立记录。kind 为 tree/pine/flower/rock/bench/lamp/tower/bank/clinic/shop/prison/gazebo/boat/dock |

路砖1.78×1.78，地产底板1.18×1.18；地表高度-0.29，水面低0.07。水中岛屿、沙岸都需指定轮廓，洞在3D与SVG中含义一致。缩放只改变细节与可见性，不改变景物记录。植物模型自身的枝冠/花瓣是复用几何，不是散布额外植株。

先画场景构图与路线，再逐项确定坐标。可用离线绘图工具烘焙曲线，最终必须交付完整坐标；运行时不读取随机种子、植被散布规则或道路外扩地形配方。不要把大量自动生成的背景记录当作精心设计。预览与小地图直接使用地形和道路数据。

运行 `npm run maps:validate`、`npm test`；重点检查 authored-world/scalable-world 测试的旋转足迹、道路连接、陆水支撑、规则摘要与联排检查。随后在真实浏览器查看全景、近景及满建存档；数值合格不能代替构图判断。
