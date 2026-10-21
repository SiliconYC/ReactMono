# Issue #121：独立实验验收与同视口比较

核验范围：本页是对 2026-10-20/21 已存档实验的**独立复核**，不是重新制作的画面。原始输出与每张 PNG、校验值、命令、失败历史位于 [evidence/](evidence/)、[run.py](run.py)、[run_economy.py](run_economy.py)、[failures.md](failures.md)。所有结论限定固定 SHA 和本轮观测。

## A：三个项目、六张真实 Chromium 画面

| 项目（固定上游 SHA） | 1440×900 桌面 | 390×844 模拟手机 | 实测和不能推断的事实 |
| --- | --- | --- | --- |
| Yakamozli/richman-3d `32e7f01f9888a28b8fd1267f5488c455e15abe4a` | [原始 PNG](evidence/richman3d-desktop.png) | [原始 PNG](evidence/richman3d-mobile.png) | Chromium 检测到 WebGL，进入游戏、出现角色/骰子/楼房/控制条；`node test/smoke.mjs 2` 退出 0；不是完整对局证明 |
| zawsstt/monopoly-rich-life `307c1761b150a7179fb0353618a95bc6effe3fee` | [原始 PNG](evidence/richlife-desktop.png) | [原始 PNG](evidence/richlife-mobile.png) | 静态入口 `?auto=1&nofly=1&cdn=0` 真正进入对局且能看到书桌、棋盘、角色及界面；性能样本在 6 秒内超时，未测得可信帧间隔 |
| ReactMono `dev@4494a16d017b0697fa7e74f9d450154e0c228ede` | [原始 PNG](evidence/reactmono-desktop.png) | [原始 PNG](evidence/reactmono-mobile.png) | 本次真实主程序开局，而非此前静态概念图；`dev` 后续提交不自动包含在这一画面基线 |

**链式证据：** [run.json](evidence/run.json) 六条 `views` 均有 HTTP 200、WebGL/Canvas 检测、统一视口、PNG 文件名与 SHA-256；对应 [run.log](evidence/run.log) 的 Git 克隆、固定 SHA 检出、依赖/浏览器记录；[首次完整截图作业](https://github.com/SiliconYC/ReactMono/actions/runs/39471057645) 的原始产物由 [恢复作业](https://github.com/SiliconYC/ReactMono/actions/runs/39473338522)归档入 Git。六张仓库内文件均经独立打开目视核查。Chromium 155、Linux CI、SwiftShader 软件 WebGL；触屏只是模拟视口。

### 同视口画面比较（A：截图可见；其他一律另标）

- **Yakamozli**：地契路径主要像印在一块薄棋盘上的图案，局部人物/高楼为简单三维几何；桌面镜头严重左偏，右侧大片纯色空白，画面中心和棋盘区域利用差；手机画面左缘棋盘被截断、顶栏溢出，卡片与日志遮挡。视觉层级不足，存在明确的狭屏布局缺陷。
- **zawsstt**：桌面书桌、木纹、地球仪、台灯、棋盘边框、人物肖像的整体彩绘与装饰明显更丰富；但中部大面积是**平面人物插画**，画面中的地产楼宇体量小，不得当成全部楼宇的 3D 建模验收。390×844 截图采用**旋转横屏界面**，直立查看时文字和棋盘横向旋转，不能据此认定竖屏易用。四级建筑模型存在属 B 源码，截图只显示首回合小模型，**未实测升级的四层演变**。
- **ReactMono**：两视口都保持正向可读的玩家卡、动作按钮和棋盘；竖屏控件相对完整。但桌面/手机主地图均以稀疏浅色低模及小体量建筑为主，地块辨识、街道层次、模型丰富度、主题场景细节明显不足；仅凭这些静态样张不能判断动态建筑升级、长期可玩性。

**相对结论：** zawsstt 的桌面书桌主题包装与绘制密度优于另两项；ReactMono 的手机竖屏信息排布比 Yakamozli 和 zawsstt 的本轮竖屏采样更直接；三者都不能由本轮首回合截图证明商业级成熟画面。以上为相同窗口下的定性观察，不是归一化 FPS 或玩家满意度排名。

**交互/性能边界：** 已观测进入开局、可见按钮和界面状态；没有完整购地、升级、回合操作录屏或手机实机触控测试。run.json 中 requestAnimationFrame 的中位数：Y 桌面约 248ms / 手机 80ms、ReactMono 桌面 122ms / 手机 36ms；zawsstt 两视口均超时。样本短、系统软件渲染并受工作负载影响，**不可据此推断真实 GPU FPS、真机 60FPS 或跨项目严谨性能排序**。

## A：原生重建版经济规则——有限边界样例

上游固定 `tytannial/rich4-re@b7b76570f445ad07c0788314062b8500e77259e7`，独立在 Linux GitHub Actions 编译 C++ `rich4_tests` 并运行 `ctest` 及二进制 stdout；原始 [economy-run.json](evidence/economy-run.json)、[economy-run.log](evidence/economy-run.log)。`SDL_UNIX_CONSOLE_BUILD=ON` 是无图形控制台构建参数。

| 运行的额外边界样例 | 期望和实际 |
| --- | --- |
| 同名街区、同业主筛选、二倍价格 | `(200+400)×2=1200`；排除其他业主 |
| 连锁地产仅本业主两处、三倍价格 | `2×2000×3=12000`；排除其他业主 |
| 相同对象再次挂单覆盖报价 | 同一槽价由 250 改为 `400`，不新增槽 |
| 七个交易槽满额、拒绝第八笔、撤单再加入 | 原七条保持，拒绝第八条；撤单后新对象 `8` 出现在第七槽（下标 6） |

**重要质量审计：** 之前报告的 `114 checks, 0 fails` 指**断言检查数**，非 114 个独立测试用例；三个依赖商业资源（`Data.mkf`、`SAVE0.DAT` 两项）的用例输出 `SKIP`，但上游微型测试库仍标记 `[ OK ]`，不得算为真正资源验证。旧编译日志中**上游旧测试和本轮新增测试各有一次 `tradeSlots[0][7]` 越界读取警告**，因为合法下标仅为 0..6；旧的绿灯不能替越界断言背书。

已在**临时克隆的测试文件**中把这两处非法断言替换为“前七槽在超额写入后保持不变”，未改租金/交易业务逻辑。复验 [Actions #39522311357](https://github.com/SiliconYC/ReactMono/actions/runs/39522311357) 成功：**126 项断言检查、0 失败、0 数组越界警告、4 项指定边界样例全部通过、3 项原版资源依赖案例跳过**；`ctest` 与二进制均退出 0。测试数量增加来自修正断言中对七个合法槽位的逐一检查，不代表新增了十二个独立测试。另有仅修正 `Application::init` 默认实参兼容性的 [临时补丁](evidence/compiler-compatibility.patch)，以及 [测试越界补丁说明](evidence/test-bounds-compatibility.patch)；原版资源没有被获取或提交。

**原版对应关系：** 这是逆向**重建版生产逻辑**的样例 A 级运行证据；函数位置 `src/app/game/turn_system.cpp::estateRouteRent`、`src/app/game/trade_market.cpp::queueTradeOrder/removeTradeOrder` 是 B 级源码锚点。没有对 1998 年商业版二进制/素材做逐输入差分验证，不能声称“原版一致”。许可证和素材只用于研究取证，未移植。

## 验收界限

本 Issue 的核心要求是两上游+本项目的真实双视口采样，以及**至少两项重建版机制**的有限独立规则验证；已有材料能证明以上限定事实。不能泛化为完整游戏、四级楼宇过渡、联网、人类操作体验或原版商业程序准确性。研究权威原文仍见 [Yakamozli](../repositories/Yakamozli--richman-3d/README.md)、[zawsstt](../repositories/zawsstt--monopoly-rich-life/README.md)、[tytannial](../repositories/tytannial--rich4-re/README.md)，历史 B/C/D 范围保留，仅在本次有对应 A 证据的细项升级。
