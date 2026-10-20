# Issue #121：上游画面与经济机制独立验证

> 状态：实验中；仅当 `evidence/run.json` 与浏览器、编译原始日志显示成功，才将单项证据提升为 A。当前文档不是验收完成证明。

## 方法与研究基线

- ReactMono 源头：`dev@4494a16d017b0697fa7e74f9d450154e0c228ede`（2026-10-21 创建临时分支时远端 HEAD）。对照程序是这个快照及任务分支追加的研究脚本，**非旧报告的 `be88f...`**。
- 3D 目标一：`Yakamozli/richman-3d@32e7f01f9888a28b8fd1267f5488c455e15abe4a`。
- 3D 目标二：`zawsstt/monopoly-rich-life@307c1761b150a7179fb0353618a95bc6effe3fee`。
- 规则目标：`tytannial/rich4-re@b7b76570f445ad07c0788314062b8500e77259e7`。
- 上游源码为临时克隆，严格校验 `git rev-parse HEAD`；严禁提交整个上游镜像。Z 项目采用稀疏检出以避免下载无关大视频。
- 取相同 **1440×900** 桌面与 **390×844** 手机尺寸（手机为 Chromium 触摸 + 视口模拟，不是真机）；WebGL 场景必须实际加载，真实画面用脚本自动截图。记录 HTML 返回、Canvas/WebGL 检测、错误、浏览器版本、帧间隔；计时仅作 CI 软件渲染下参考，**不作为任何项目“60 帧”或硬件性能结论**。
- 构图评价必须区分静态画面、互动前后行为、低细节下的层级可读性、地块/建筑辨识和场景一致性。纯作者自述与历史截图不得升级证据。
- 执行 `tytannial/rich4-re` 的原生 C++ 单测并在**临时上游克隆**添加四个独立边界用例：同名街区的所有者筛选与倍率、连锁店人数与倍率、同目标挂单覆盖、七槽满额后删除重用。预期数值分别为 600、12000、400 和第七槽再写入对象 8。必须以实际编译后的断言为准，而非预期即结论。
- 上游测试的是**逆向重建版本**，没有商业原版可执行程序和资源的差分输入，不能证明原版二进制与重建一致，也不能直接证明 ReactMono 采用相同公式。

## 可复现执行

在拥有访问公共 GitHub、CMake/C++17、Node.js、Python、Chromium、Playwright 和所需外部依赖的环境中：

```bash
python -m pip install playwright
python -u docs/research/verification-issue-121/run.py
```

GitHub 上另有本 Issue 专用验收工作流：[`.github/workflows/issue121-research.yml`](../../.github/workflows/issue121-research.yml)，**只对隔离任务分支的实验脚本或工作流变化自动触发**。不得当成后续所有 PR 的常规 CI。

原始证据输出 `evidence/run.json`、`evidence/run.log`、`evidence/<项目>-<桌面/手机>.png`；失败仍保存日志，截图失败时另存 `-failed.png`。脚本使用固定 Git SHA，不下载或提交未授权游戏商业资源，不登录上游 Supabase，也不向上游服务写入任何数据。截图只用作非商业技术评述，不授权素材在 ReactMono 中复制。

## 关联与证据边界

- [Yakamozli 权威研究](../repositories/Yakamozli--richman-3d/README.md)：原报告 B/C/D 源码结论保留，动态观感必须对照本次结果。
- [zawsstt 权威研究](../repositories/zawsstt--monopoly-rich-life/README.md)：原自定义非商业许可继续有效；不能将作者海报当成本次截图。
- [tytannial 权威研究](../repositories/tytannial--rich4-re/README.md)：原 `estateRouteRent`、`queueTradeOrder` 仅 B 源码锚点；本次如真正执行，可对限定用例提升 A。
- [mytbk 原版逆向报告](../repositories/mytbk--rich4/README.md)：原始反汇编的“连锁/房租”仍只有 B；重建程序独立测试不等于原商业程序黑盒实测。
- [综合研究任务 #104](https://github.com/SiliconYC/ReactMono/issues/104) 应引用本次独立实测与所有失败证据，而不是把 B/C 结论合并升为 A。

每条试验的 A 等级必须有命令、固定 SHA、退出状态、测试 stdout 或截图哈希。B=固定源码，C=作者声明，D=未验证；无法运行或渲染则继续标 D（阻碍）而非声称 A。
