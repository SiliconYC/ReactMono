# 源码证据索引：Yakamozli/richman-3d

- 上游仓库：https://github.com/Yakamozli/richman-3d
- **固定提交**：`32e7f01f9888a28b8fd1267f5488c455e15abe4a`（以下 URL 均固定到此 SHA）
- 本页是 **B 级源码审阅索引**，并非运行日志。下述本地命令仅供复核，**未声称执行**。

## 五组关键锚点（精确文件及行号）

| 组 | 定位（链接直接指向固定 SHA） | 读码证实的机制 | 可复制的复核命令 |
| --- | --- | --- | --- |
| S1 地图数据、平面贴图 | [`js/config.js:6-18,52-107,109-122`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/config.js#L109-L122)、[`js/draw.js:76-134`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/draw.js#L76-L134) | 52 格、14×14 外环、城市与规则定义来自常量；`boardCanvas` 将整个棋盘栅格化为 2940×2940 Canvas。不是 52 块独立 3D 地砖。 | `git show 32e7f01:js/config.js | sed -n '109,122p'`；`git show 32e7f01:js/draw.js | sed -n '76,134p'` |
| S2 3D 场景、相机、阴影 | [`js/scene.js:19-110,117-190`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/scene.js#L19-L190) | WebGLRenderer、透视相机、OrbitControls、半球+定向光、2048 阴影；把 CanvasTexture 贴在单个 BoxGeometry 顶面，四栋几何装饰楼位于棋盘内部。 | `git show 32e7f01:js/scene.js | sed -n '19,190p'` |
| S3 角色、地产房屋与动效 | [`js/scene.js:233-402,405-462,542-568`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/scene.js#L405-L462) | 角色用球、胶囊、锥体、环等代码组装（非骨骼模型）；1–4 间房/酒店使用方盒与锥形屋顶，弹出缩放；走格通过插值跳跃。 | `git show 32e7f01:js/scene.js | sed -n '405,462p'` |
| S4 纸币、卡牌与 UI、规则隔离 | [`js/draw.js:353-433,435-1004`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/draw.js#L353-L433)、[`js/ui.js:544-583`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/ui.js#L544-L583)、[`js/game.js:265-334`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/game.js#L265-L334) | 2D Canvas 绘制卡面/地契/纸币/金币等；HTML 弹层负责五选一翻牌；落地结算由 `game.land` 完成并通过 hook 调用 UI/场景。 | `git show 32e7f01:js/ui.js | sed -n '544,583p'` |
| S5 AI、测试及可复现缺陷 | [`js/ai.js:5-73`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/ai.js#L5-L73)、[`test/smoke.mjs:1-128`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/test/smoke.mjs#L1-L128)、[`test/shot.html:7-13`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/test/shot.html#L7-L13) | AI 基于现金阈值及随机启发式；冒烟脚本使用场景/UI 桩，并含清算、初始资金断言。截图页 importmap 的 `./vendor/` 相对 `/test/` 解析到不存在的 `/test/vendor/`，而仓库仅有根 `/vendor/`，静态结构可复核。 | `node test/smoke.mjs 8`（**建议执行，非本次运行结果**）；`git show 32e7f01:test/shot.html` |

## 额外的交叉核对

1. [`index.html:9-10`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/index.html#L9-L10) 中根目录的 `./vendor/three.module.js` 路径正确，能和测试页错误形成对照；[`test/shot.js:31-42`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/test/shot.js#L31-L42) 还会写入 `document.body.textContent`，覆盖原 Canvas，故不能将该页面当作现成的可靠实景截屏凭据。
2. [`js/config.js:6-18`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/js/config.js#L6-L18) 中 `GO_BONUS=3000`；[`docs/research.md:19,39`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/docs/research.md#L17-L39) 仍写“40 格”与“2000 工资”，属文档历史描述不一致；以配置和执行代码为实现依据。
3. [`LICENSE:1-14`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/LICENSE#L1-L14) 为作者 MIT 声明；[`docs/research.md:26-35`](https://github.com/Yakamozli/richman-3d/blob/32e7f01f9888a28b8fd1267f5488c455e15abe4a/docs/research.md#L26-L35) 提供角色原作参考映射，**不能推导商业角色授权已经取得**。
4. ReactMono 对照源码（核查基线 `be88f92936e553bd369fe3c142394cd612659f5f`）：[`WorldCanvas.tsx:90-164,203-263`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/demo3d/world/WorldCanvas.tsx#L90-L164)、[`MiniatureTown.tsx:196-278`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/demo3d/world/MiniatureTown.tsx#L196-L278)、[`layout.ts:31-48`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/demo3d/world/layout.ts#L31-L48)：ReactMono 根据真实地图数据布置网格/地块和几何，采用 React Three Fiber 场景，不是把 52 格绘在一整张纹理上。

> 复核建议：下载**独立的**上游仓库（仅本地暂存、不提交 ReactMono），运行 `git checkout 32e7f01f9888a28b8fd1267f5488c455e15abe4a` 后逐点审阅；需要真实截图时修正测试入口路径后在有 WebGL 的浏览器采集，标注设备与视口。
