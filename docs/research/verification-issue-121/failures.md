# Issue #121：执行失败与重试台账

本页保留失败实况，避免后续成功覆盖早期错误；**失败记录不是 A 级功能通过证据**。

| 轮次 | Actions 运行 | 状态和真实现象 | 处理 |
| --- | --- | --- | --- |
| 1 | [39468013284](https://github.com/SiliconYC/ReactMono/actions/runs/39468013284) | 失败。三方克隆中 Y 与 tytannial 成功，Y 的 `node test/smoke.mjs 2` 退出 0；Z 稀疏检出错误地把普通根文件 `index.html` 当目录；截图阶段，脚本函数名 `http` 遮蔽 `http.server`，抛出 `AttributeError`，浏览器截图 0 张。 | 已修改稀疏模式和静态服务器函数名。原始 `run.log`、`run.json` 见 [首轮 Actions artifact](https://github.com/SiliconYC/ReactMono/actions/runs/39468013284/artifacts/12284939090)。 |
| 2 | [39468181596](https://github.com/SiliconYC/ReactMono/actions/runs/39468181596) | 被后续推送的并发取消机制中止：终止前 **Y 的桌面与手机视口 WebGL 均检测成功并产生本轮真实 PNG**；尚不能算 Z / ReactMono 画面完成，更不能算经济机制通过。机器人提交 PNG 时与后续人工分支提交竞争，推送因非快进被拒。 | 修正证据推送为 fetch+rebase+push；保留 [第二轮 artifact](https://github.com/SiliconYC/ReactMono/actions/runs/39468181596/artifacts/12285243710)。 |
| 3 | [39468485789](https://github.com/SiliconYC/ReactMono/actions/runs/39468485789) | 为修订经济测试断言，新脚本推送触发并发取消。这是 CI 调度中断，不是已证实的上游测试失败。 | 修正同路段租金独立样例预期：`(200 + 400) × 2 = 1200`；后续不再中途变更实验脚本。 |
| 4 | [39469127907](https://github.com/SiliconYC/ReactMono/actions/runs/39469127907) | 后续实验完整度以该次作业最终状态、`evidence/run.json`、`evidence/run.log` 和截图文件为准；**不可仅以此表声称已成功**。 | 待真实结果审查。 |

不要用 Actions 工作流自身状态替代实际功能验证：即使脚本 0 退出，也须逐张核实 Canvas/WebGL 对应真实游戏画面，以及 CMake、CTest 的独立退出状态。
