# 3D 主程序的浏览器验收迁移

2026-10-19，#92。旧 CI 在 `browser_p4_release_e2e.py:127` 的新局准备页等待 `.board`，此二维棋盘 DOM 自 3D 接管后不存在，导致后续功能回归全部不执行。本次改为验证生产构建的真实 3D 主程序。历史脚本保留用于追溯，不通过恢复无用二维 DOM 冒充 3D 验收。

规则、经济、存档校验、1000 局/交叉模拟、包体/许可/离线资源预算等 Node 门槛全部保留；独立 3D demo 和美术样例的测试继续执行。原脚本中纯实现约束（如 `.board` 网格、`.character-image` 和多个原生 `details`）改为对应用户能力，不将不存在的旧布局当功能。

| 原验收主题/脚本 | 新主程序检查 | 保留的行为 |
| --- | --- | --- |
| `browser_main_game_ui_redesign` / `p4_action_layout` / `p4_baseline` | `browser_ui_rebuild_e2e` | 七视口标题、新局直接可见席位、购地两选项及余额、主操作无需滚动、窗口焦点/背景隔离/关闭恢复、画面截图 |
| `map_layout` / `p4_board` / `second_map` / `p4_characters` | `browser_ui_rebuild_e2e`、`browser_main_game_acceptance` + `camera-layout`、`demo3d-layout`、`demo3d-outcomes` Node 测试 | 真正 Canvas 渲染和中间帧、两图/四席、统一身份颜色/站位、地图模型与投影安全区，不再断言二维 CSS grid |
| `live` / `multiplayer` / `local_multiplayer` / `p4_cpu_pace` / `agent_styles` | `browser_main_game_acceptance`、`browser_main_runtime_e2e`，原策略 Node 测试 | 两图四人完整正常/快速局状态等价，真人交接、人机人交接、菜单取消已有 AI 计时器并恢复；原有所有策略规则回归仍运行 |
| `bank` / `loan` / `stocks` / `assets` / `liquidation` | `browser_main_game_acceptance`，原金融/清算 Node 测试 | 现金/存款分账、存取款、买卖股与手续费、抵押借还/释放、产权、直接到访建设、旧规则异地升级、真实破产与胜负 |
| `strategy` / `facilities` | `browser_main_game_acceptance` | 五种卡片的使用与目标选择、商店购买、医院监狱停留与跳过，文件存档真实校验 |
| `p4_motion` | `browser_main_game_acceptance`、`browser_main_runtime_e2e` + 扩充的 `p4-motion.test` | 1～6 点实际逐步回调/Canvas中间帧、正常与跳过完整状态等价、终局路径仍绑定行动者、减少动态双击不误购 |
| `saves` / `import` / `offline` / `p2_acceptance` | `browser_main_game_acceptance`、`browser_main_runtime_e2e` | 真实下载/上传往返、校验损坏拒绝不改局面和档位、同名副本、自动存档、生产 PWA 断网启动/续局与帮助 |
| `sw_upgrade` | `browser_main_runtime_e2e` 复用原 `UpdateHandler` | 两个真实SW版本安装、等待玩家显式更新、缓存清理、IndexedDB存档保留、断网重载 |
| `p4_audio` / `p4_release` | `browser_main_runtime_e2e`，原 `p4-audio`/`p4-release-budget` Node 测试 | WebAudio启动/节点结束、音量持久化、减少动态闲置及模态GPU停止绘制；保留长任务、帧间隔、资源字节与IDB写计数原始指标；静态包体/许可/缓存预算继续是硬门槛 |
| `p4_visual_lab` / `demo3d` | 原脚本继续执行 | 独立美术样例的规则、主题、离线资源；8项独立3D demo地产/金融/租金/完整结局/动态减少/短屏回归 |

公开 Pages 验收与真人试玩仍属于 #73。此轮不发布正式服务，因此不把旧公网版本当作新代码验收，也不声称真机 GPU/发热或真人满意度通过。历史 `p3_public_final` 等远端脚本保留，在正式发布后对相应版本运行。
