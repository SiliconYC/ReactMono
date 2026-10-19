# JCRJPZB/Rich4：源码证据定位（Issue #101）

- 固定上游 Commit：`0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0`（2021-08-07 UTC，唯一初始提交）。
- 核查日：2026-10-19 UTC；所有链接固定 SHA，而非浮动 `main`。
- 等级：B = 定位到固定 SHA 的源码；A = 研究者独立执行的数据级检查。**没有 Cocos Creator 运行截图或通关实测。**

## 五个主证据锚点

| 锚点 | 文件与定位 | 实际核查事实 | 复核方式 |
| --- | --- | --- | --- |
| S1 | [`assets/Script/GameCore/Game.js` L8–55](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/GameCore/Game.js#L8-L55) | 加载三类模块后启动；`Japan` 与四角色硬编码；GameOver 只有日志和“界面待编辑” | 对照 `onLoad/modelLoaded/gameStart/gameOver` |
| S2 | [`assets/Script/Map/PointMgr.js` L104–176](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Map/PointMgr.js#L104-L176) | JSON 节点、正反路线段与路径、地产映射和岔路候选；[地图加载入口](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Map/Map.js#L16-L63) | 对照 `assets/resources/config/Japan.json` 的节点、边和路线 |
| S3 | [`assets/Script/Player/PlayerRound.js` L17–113](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Player/PlayerRound.js#L17-L113) | 回合、骰子、移动、地块分派与 AI 分支；`isBot` 初始化使用尚未装载的值，AI 回合依赖 `aiLogic` 回调 | 联读 [`PlayerAttr.js` 的 `isBot=false`](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Player/PlayerAttr.js#L8-L19) 和 S4 |
| S4 | [`assets/Script/AI/AICtrl.js` L26–90](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/AI/AICtrl.js#L26-L90) | AI 卡片被注释、无卡片路径没有调用回调、股票交易存在使用 `stock` 前引用与未定义 `vlo`，且 [`PlayerRound.init`](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Player/PlayerRound.js#L17-L36) 传参不匹配 | 检查 `aiLogic/useCard/stockTrade/init` 及调用者；**属于源码可见风险，未经运行复现** |
| S5 | [`assets/Script/Player/PlayerLandActivity.js` L25–125](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Player/PlayerLandActivity.js#L25-L125) | 购地、加盖、租金、设施事件已有代码，但 `upgradeLand` 无扣款步骤；[地图设施操作](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Map/PointMgr.js#L196-L239) 使用错误的 `this.point` 字段 | 对照收支与地块所有权修改路径 |

## 补充交叉证据

- **版本与结构**：[project.json L1–7](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/project.json#L1-L7) 标明 Cocos Creator 2.4.3；[settings/project.json L31–44](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/settings/project.json#L31-L44) 给出画布 960×640；仓库提交树只含单一初始提交，库页 `fork=false`，并不能证明所有素材自主原创。
- **银行/股票**：[BankPane.js L42–82](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/UI/NodePane/BankPane.js#L42-L82) 有存取款；[StockMgr.js L186–229](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/UI/Stock/StockMgr.js#L186-L229) 有交易与波动实现，交易接口依赖选中的 UI 股票；[PlayerAttrDirector.js L104–132](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Player/PlayerAttrDirector.js#L104-L132) 净资产读取处出现 `==`，不是 `=`。
- **卡片/道具**：[CardMgr.js L80–148](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/UI/Card/CardMgr.js#L80-L148) 有发卡、使用和出售；[ToolMgr.js L9–170](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/UI/Tool/ToolMgr.js#L9-L170) 绝大多数道具逻辑注释关闭；[PlayerLandActivity.js L131–142](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Player/PlayerLandActivity.js#L131-L142) 明写随机道具尚未做。
- **岔路操作**：[PlayerCtrlDirector.js L95–117](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Player/PlayerCtrlDirector.js#L95-L117) 在多出口时使用第一个出口，注释“还没有实现”；[DiceControler.js L66–78](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/GameCore/DiceControler.js#L66-L78) 的 `exchangeMode` 设置了 `this.node = mode` 而不是 `this.mode`。
- **测试性质**：[Test.ts L1–32](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Test/Test.ts#L1-L32)、[TestPlayer.ts L1–28](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Script/Test/TestPlayer.ts#L1-L28) 是编辑器场景的演示组件，不是附带断言/持续集成的独立规则测试。
- **场景和地图**：[Game.fire](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Scene/Game.fire)、[TestScene.fire](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/Scene/TestScene.fire)、[Japan.json](https://github.com/JCRJPZB/Rich4/blob/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0/assets/resources/config/Japan.json)。研究者使用 GitHub 读取的源码内容独立执行 JSON.parse 和引用边界检查：96/96 节点、3/3 路线段、3/3 路径、15/15 道路、2/2 建筑，边界越界数 0；这**仅证明静态配置可解析**，不证明 Cocos 场景能启动。
- **许可/可运行性**：固定提交完整文件树（444 条树项）中没有 README、LICENSE、package.json 或编译产物；无法据此认定源码获得开源许可证授权，也无法证明缺失项不会由 Cocos 编辑器生成。

建议复核的 API 入口：[`git/trees/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0?recursive=1`](https://api.github.com/repos/JCRJPZB/Rich4/git/trees/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0?recursive=1)；[`commits/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0`](https://api.github.com/repos/JCRJPZB/Rich4/commits/0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0)。
