# Issue #121：第一手验证结果及收口门槛

> **研究进行中／不可据此关闭 Issue。** 本文件仅记录已经观察的独立执行结果；最新完整机器记录仍须以 `evidence/run.json` / `evidence/run.log` 和最终 Actions 任务为准。链接与证据级别以逐条材料为单位，不给整个仓库一概升级。

## 第一手 Chromium 画面：Yakamozli/richman-3d

- 固定 SHA：`32e7f01f9888a28b8fd1267f5488c455e15abe4a`。使用临时 git checkout、仓库根静态服务器、真实 Chromium（无头、WebGL 软件渲染）；不是作者 README 宣传图。
- 统一视口：桌面 **1440×900**、手机 **390×844**（手机是有触控模拟的 Chromium 视口，不是实机）。
- 可靠运行证据：[`39468181596` 原始桌面/手机 PNG](https://github.com/SiliconYC/ReactMono/actions/runs/39468181596/artifacts/12285243710)，两页脚本日志均显示 `render True error None`；[`39470642742` 补装简体中文字体的二次截图](https://github.com/SiliconYC/ReactMono/actions/runs/39470642742/artifacts/12286503535)，两页同样 `render True error None`。
- **A 级可见事实**：桌面棋盘呈明显左偏，视窗右侧大范围缺少游戏场景，整体镜头未有效利用屏幕。手机棋盘的左端超出视窗，上排顶栏按钮从右端被裁断，底部操作卡与日志区域相互遮挡；虽然角色/建筑三维网格和掷骰 HUD 真的出现，但此手机布局不能判定正常适配。
- **B 级结构解释**：`js/scene.js` 与 `js/draw.js` 中完整棋盘主要是一张 CanvasTexture 贴到盒几何体的顶面；棋盘中心楼宇和棋子为程序构造的几何体。A 级像素证据只支持画面中的具体表现，不自动证明每个模型有独立建筑等级或所有作者功能声明已经运行。
- `node test/smoke.mjs 2` 独立执行退出码 0（A，仅该上游的有限烟测）；这不意味着《大富翁4》原作规则已验证。
- **注意**：首轮未安装中文字形的截图存在方框字，不能拿它评价中文字体可读性。已另行在安装中文字形后的 Chromium 重新截图，仍可观察到手机溢出和棋盘裁切。

## 第二个 3D 上游：zawsstt/monopoly-rich-life

- 固定 SHA：`307c1761b150a7179fb0353618a95bc6effe3fee`。
- 已在独立运行容器成功克隆、稀疏读取所需源码和本地图形素材，入口尝试 `?auto=1&nofly=1&cdn=0&allmax=1` 以及回退的**普通开局** `?auto=1&nofly=1&cdn=0`。
- 压力场景由于 Chromium 长时间卡住而未获得可验收原始截图；普通开局第 5 次工作流在桌面视口出现 `Page.screenshot: Timeout 30000ms exceeded`，不能因页面可以访问、源码有四级模型、程序检测到 Canvas 就声明截图实测成功。**画面结果目前 D（未证实），源码的四级模型为 B，作者“60FPS”仍为 C。**
- 许可仅允许学习且禁止商业使用；只评价通用设计原则，不能移植模型、图、音频和短片。

## 经济机制：源码实质核查与独立测试

固定 `tytannial/rich4-re@b7b76570f445ad07c0788314062b8500e77259e7`：

1. `src/app/game/turn_system.cpp` 的 `estateRouteRent`：同名、同类型、同业主的普通地产累加各自对应 `fees[level]`，同业主连锁地产每处加 2,000，结果再乘 `moneyMul`。**B 级**，本实验边界期望包含普通用地 1,200、连锁 12,000。
2. `src/app/game/trade_market.cpp` 的 `queueTradeOrder`、`removeTradeOrder`：同类型/对象覆盖报价、七个合法交易槽满额拒绝、撤单后压紧队列。**B 级**，本实验期望相同挂单价格更新至 400 且撤单后第七槽可复用。

真正将两个机制升级为 **A** 的必要条件是实际构建 `rich4_tests`，独立运行固定上游源码与这轮新增边界测试并获得 `ctest` 通过，记录真实 stdout、退出码及构建环境。无论单测结论如何，都不能把逆向重建程序的结果外推为原始商业二进制的差分验证。本轮没有原版商业数据或原版二进制。

## 同视口 ReactMono 主程序与比较

最新研究基线为 `dev@4494a16d017b0697fa7e74f9d450154e0c228ede`；必须拿研究脚本当天打开的**主程序**截图来评判，不能用 `docs/main-game-ui-redesign/` 历史预览图假冒本次新实测。如果最终 ReactMono 截图缺失，保持该项 D，不生成伪比较结论。

## 证据与工作边界

- 机器产物统一收于 `evidence/`；失败台账在 [failures.md](failures.md)，方法与 SHA 在 [README.md](README.md)，关联权威上游研究目录在 [repositories/](../repositories/)。
- **A**：固定环境、命令与退出码支持的运行或原始浏览器截图，只在成功样例的范围内成立；**B**：固定版本源码能证实的实现；**C**：作者或文档声称；**D**：运行失败或尚未验证。
- 画面截图包含上游可识别的游戏内容，限本次技术研究评述，不能把其中素材当作 ReactMono 的商业素材资源。
- 未修改 `src/`、`demo3d/` 或 `main`。
