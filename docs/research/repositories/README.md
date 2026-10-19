# 已研究与待研究的外部仓库索引

**本目录是多仓库研究产物的容器，不是游戏源码目录。**

每个外部仓库一份独立子目录：`<GitHub owner>--<GitHub repo>/`。例如：
`mytbk--rich4/README.md`、`mytbk--rich4/source-index.md`、`mytbk--rich4/evidence.json`。

研究开展前不要创建空目录或占位文件。完成每个研究 Issue 后再把真实报告目录和仓库链接添加到本页；一仓库只有一个权威目录，fork 不重复计算原创项目。

研究标准见 [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md)；候选清单及任务见 [`../README.md`](../README.md)。

## 已交付的独立仓库研究

| Issue / 上游 | 研究报告 | 固定证据 | 实测边界 |
| --- | --- | --- | --- |
| [#103](https://github.com/SiliconYC/ReactMono/issues/103) / [zawsstt/monopoly-rich-life](https://github.com/zawsstt/monopoly-rich-life) | [九章报告](zawsstt--monopoly-rich-life/README.md) | [五组源码锚点](zawsstt--monopoly-rich-life/source-index.md) · [16 条分级证据 JSON](zawsstt--monopoly-rich-life/evidence.json) · 上游 `307c1761b150a7179fb0353618a95bc6effe3fee` | **B/C 级源码/文档核查完成；无 A 级浏览器截图或联机实测**，画面、独立复现分数均为 null |

未列入此表的 [#95–#102](../README.md#已创建研究任务2026-10-19) 不因创建 Issue 就视为完成；每项须以最新 `dev` 中实际存在的报告和合并记录为准。后续若其他研究合并，以真实结果更新本索引，避免覆盖其他研究者并发成果。
