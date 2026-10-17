# 07 · 证据与资料

## 本轮实际检查

日期：2026-10-17；代码基线：`a56058950966b1e4f3d56dec75caa250f1fcd0a3`；方案工作分支：`codex/art-direction-architecture`，从 `dev` 创建。`git ls-remote origin refs/heads/dev` 返回同一 SHA。

### 代码与任务状态

- 已阅读 README、产品宪章、路线图、候选池、自主演化协议，以及现有 P4 美术/棋盘/动画/性能规范。
- 检查了 `src/core`、保存/IndexedDB、902 行 `src/ui/app.tsx`、feedback、电脑调度、构建、PWA 和相关测试。
- GitHub 查询当时开放 Issue 仅 [#73](https://github.com/SiliconYC/ReactMono/issues/73)，开放 PR 为 0。#73 明确要求真正的画面/趣味审查与真人反馈，不能只靠 CI 通过。
- README 部分阶段说明落后于代码；本轮更新当前状态摘要和新设计入口，历史记录保留。

### 自动化基线

首次 `npm test` 因工作区尚未安装依赖，报 `tsc: command not found`。执行锁文件安装 `npm ci --ignore-scripts` 后，再运行完整 `npm test`：**119 tests / 119 pass / 0 fail / 0 skipped**。未添加或升级生产依赖，没有修改测试。

该次执行包括现有 1,000 局混合配置规则/资金/存档验收：241,239 个合法动作、0 拒绝；这是本地重新运行产生的数据，并非只转述历史 CI。

- [完整 Node 输出](evidence/baseline-node-test.log)
- [实测资产预算报告](evidence/baseline-asset-budgets.json)
- [模拟摘要与原始数据哈希](evidence/baseline-summary.json)

`dist` 共 78 个文件（原测试口径），总计 **485,783 B**，JS **389,874 B**，CSS **54,671 B**，art **3,555 B**，预缓存运行时模块 27 个。原测试的总预算为 2,000,000 B、JS 800,000 B。这些属于原 CSS/SVG 版本，不支持“未来 3D 也能达到相同体积”的结论。

约 10.9 MB 的 1,000 局原始模拟 JSON 没有塞进设计目录；摘要记录其 SHA-256，并可用本基线 `npm test` 再生成 `artifacts/issue45/p3-1000-raw.json`。本轮产生的完整临时运行产物移至 `/tmp/reactmono-art-audit-results/`，临时目录不保证长期保留；提交的日志和摘要是仓库内持久证据。

### 浏览器观察

在 Codex 内置浏览器打开本地构建，经典 24 格、默认双人、种子 17，实际点击开始与投骰：掷出 1 点、到达地产 1，出现售价 110、过路费 22 和购买/放弃按钮。查看了实际截图与可访问性树。

观察：格子沿 CSS 环线排列，中央大面积装饰插画，角色是 SVG 头像/座位号，移动表现为即时落点加踪迹，当前操作位于右侧面板。产品判断“缺少街区空间与角色动作”由代码和此局面共同支撑。

使用 `scripts/serve.mjs` 初看时 SVG 显示异常；它没有为 `.svg` 配置图像 MIME。换用标准 `python3 -m http.server 4188 --bind 127.0.0.1 --directory dist` 后角色图正常，故未将初次缺图推断为线上素材损坏。该开发服务问题本轮未修复。

**边界**：没有重新运行全部 Python/Playwright 浏览器套件，没有做手机真机或新的 3D 性能测试；截图用于当前会话人工审查，没有作为跨设备视觉回归基线入库。公开网站发布状态不在本轮验收范围。

## 事实、决定与待验证假设

| 类型 | 内容 |
| --- | --- |
| 已核实事实 | 引擎与 React 分离；有命令事件；地图单环且存档严格校验；UI/CSS 现状；119 项基线；旧资源预算 |
| 本方案决定 | 首选低多边形真 3D + 固定正交；保留核心；独立演出层；DOM HUD；GLB；先做完整对局切片 |
| 待验证假设 | 模块化 3D 的长期内容成本更低；现有团队能持续产出合格模型；建议的节奏比旧版更易懂；目标设备能满足预算 |
| 没有声称的成果 | 3D 已实现、用户已批准全部预算、真人满意度提高、手机流畅、正式版已完成 |

## 官方技术资料

资料核查日期同上；版本在实施时还需结合锁文件验证。下列是技术能力依据，不是本项目性能的证明。

| 资料 | 支撑的具体选择 |
| --- | --- |
| [R3F Introduction](https://r3f.docs.pmnd.rs/getting-started/introduction) | React 18/Fiber 8、React 19/Fiber 9 的主版本配对；Fiber 是 React 对 Three 的渲染适配 |
| [R3F Scaling performance](https://r3f.docs.pmnd.rs/advanced/scaling-performance) | demand 渲染、invalidate、共享资源与实例化 |
| [R3F Performance pitfalls](https://r3f.docs.pmnd.rs/advanced/pitfalls) | 帧内更新不通过 React setState，避免重复创建资源与对象 |
| [Three OrthographicCamera](https://threejs.org/docs/pages/OrthographicCamera.html) | 正交投影下物体尺寸不随距离缩小 |
| [Three WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html) | 当前渲染器要求 WebGL2；存在资源/绘制统计接口 |
| [Three Loading a GLTF File](https://threejs.org/manual/pages/load-gltf.html) | GLTFLoader 和浏览器内模型加载 |
| [Three Cleanup](https://threejs.org/manual/pages/cleanup.html) | 材质、几何、纹理需要显式资源管理 |
| [Khronos glTF 2.0](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) | 运行时模型、骨骼、材质、动画的数据交换规范 |
| [Blender Pipeline](https://www.blender.org/features/pipeline/) | Blender 对 glTF 等格式的导入导出能力 |
| [Vite Static Deploy](https://vite.dev/guide/static-deploy.html) | GitHub Pages 子路径 base 与静态产物部署 |
| [MDN WebGL context lost](https://developer.mozilla.org/en-US/docs/Web/API/WebGLRenderingContext/isContextLost) | GPU context 丢失需要处理，不可只认为页面成功加载就永远可绘制 |
| [Crossy Road 官网](https://www.crossyroad.com/) | 用户提出的视觉参照入口；不由此推断其内部技术或授权其素材 |

Blender 详细 glTF 手册页面本轮抓取失败，未据此声称核实了某个版本的导出开关。实际资产切片需固定所用 Blender 版本、导出预设，并对导出的 GLB 做浏览器往返检查。
