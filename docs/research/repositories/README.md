# 已研究与待研究的外部仓库索引

**本目录是多仓库研究产物的容器，不是游戏源码目录。**

每个外部仓库一份独立子目录：`<GitHub owner>--<GitHub repo>/`。例如：
`mytbk--rich4/README.md`、`mytbk--rich4/source-index.md`、`mytbk--rich4/evidence.json`。

研究开展前不要创建空目录或占位文件。完成每个研究 Issue 后再把真实报告目录和仓库链接添加到本页；一仓库只有一个权威目录，fork 不重复计算原创项目。

研究标准见 [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md)；候选清单见 [`../README.md`](../README.md)。已交付的研究以对应 Issue 和实际报告为准，勿将候选清单混同独立验收。

详见 [待执行的九项研究 Issue](../README.md#已创建研究任务2026-10-19)。正式报告交付后将相应链接从“待执行”更新到“已合并/已验证”。

## 已交付的单仓库研究

- [JCRJPZB/Rich4（Cocos Creator 2.4.3）](JCRJPZB--Rich4/README.md)：[Issue #101](https://github.com/SiliconYC/ReactMono/issues/101)，2026-10-19 UTC，固定上游 `0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0`；[源码锚点](JCRJPZB--Rich4/source-index.md)｜[结构化证据](JCRJPZB--Rich4/evidence.json)。仅静态数据核验，未独立启动引擎；授权不明，建议只读参考。

- [oama1111/rich4-remake-public（确定性规则与跨端联机研究）](oama1111--rich4-remake-public/README.md)：[Issue #100](https://github.com/SiliconYC/ReactMono/issues/100)，固定上游 `42ad97ad31f07541a9af35415e36be4da4147484`；[源码索引](oama1111--rich4-remake-public/source-index.md)｜[证据 JSON](oama1111--rich4-remake-public/evidence.json)。只读参考；独立原版游玩未验证，不移植 GPL 源码、后端或素材。
- [iam567/rich4-renew-app（TypeScript + Capacitor）](iam567--rich4-renew-app/README.md)：[Issue #98](https://github.com/SiliconYC/ReactMono/issues/98)，固定上游 `1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79`；[源码索引](iam567--rich4-renew-app/source-index.md)｜[结构化证据](iam567--rich4-renew-app/evidence.json)。仅源码审计、无独立测试或截图；GPL 与商业素材风险，建议只读参考。

- [tytannial/rich4-re（C++17 / SDL3 原版导向重建）](tytannial--rich4-re/README.md)：[Issue #96](https://github.com/SiliconYC/ReactMono/issues/96)，2026-10-19 UTC，固定上游 `b7b76570f445ad07c0788314062b8500e77259e7`；[源码锚点](tytannial--rich4-re/source-index.md)｜[结构化证据](tytannial--rich4-re/evidence.json)。核查联合收租、股票银行、存档与99场景脚本；未独立运行L0/L1或验收音画，建议只读规则契约参考。
- [mytbk/rich4（原版 v3.11 逆向与规则）](mytbk--rich4/README.md)：[Issue #95](https://github.com/SiliconYC/ReactMono/issues/95)，2026-10-19 UTC，固定上游 `f81954d6a5675f63297036f9252720c6ca32a2b4`；[30 处源码索引](mytbk--rich4/source-index.md)｜[结构化证据](mytbk--rich4/evidence.json)。六条调用链，B/C/D 静态核查（A=0），未运行旧版程序或 MKF 测试，GPL/版权边界建议只读参考。
