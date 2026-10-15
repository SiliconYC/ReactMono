# React + Three.js 离线依赖桥接实验

这是与游戏主体独立的最小验证项目。仅用于测试 **GitHub Runner 在线安装 → GitHub Actions 产物 → OpenAI 沙盒离线 npm ci → 离线构建 → Chromium 实际 WebGL 渲染与按钮操作**。

- 依赖锁定在 package.json / 在线安装产生的 package-lock.json 中。
- 工作流只在本实验分支推送时运行，不影响 dev / main / Pages。
- 离线产物包含 Linux x64 Node 22 的 node_modules、npm 离线缓存、源代码和构建输出。
- 所有代码完全本地运行，无 CDN 和外部 API。
- 网页测试结果以 OpenAI 沙盒的实际执行为准，不以 Runner 通过代替。
- 将来生产仓库切换版本、运行平台或依赖后，应重新制作离线依赖包。
