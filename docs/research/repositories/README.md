# 已研究与待研究的外部仓库索引

**本目录是多仓库研究产物的容器，不是游戏源码目录。**

每个外部仓库一份独立子目录：`<GitHub owner>--<GitHub repo>/`。例如：
`mytbk--rich4/README.md`、`mytbk--rich4/source-index.md`、`mytbk--rich4/evidence.json`。

研究开展前不要创建空目录或占位文件。完成每个研究 Issue 后再把真实报告目录和仓库链接添加到本页；一仓库只有一个权威目录，fork 不重复计算原创项目。

研究标准见 [`../RESEARCH_STANDARD.md`](../RESEARCH_STANDARD.md)；候选清单见 [`../README.md`](../README.md)。已交付的研究以对应 Issue 和实际报告为准，勿将候选清单混同独立验收。

详见 [待执行的九项研究 Issue](../README.md#已创建研究任务2026-10-19)。正式报告交付后将相应链接从“待执行”更新到“已合并/已验证”。

## 已交付的单仓库研究

- [JCRJPZB/Rich4（Cocos Creator 2.4.3）](JCRJPZB--Rich4/README.md)：[Issue #101](https://github.com/SiliconYC/ReactMono/issues/101)，2026-10-19 UTC，固定上游 `0c86a1b7fc889ff2f3a1f3cba7f5947f5e291ea0`；[源码锚点](JCRJPZB--Rich4/source-index.md)｜[结构化证据](JCRJPZB--Rich4/evidence.json)。仅静态数据核验，未独立启动引擎；授权不明，建议只读参考。

- [nurockplayer/richman4-remake（Godot 高保真重制）](nurockplayer--richman4-remake/README.md)：[Issue #99](https://github.com/SiliconYC/ReactMono/issues/99)，固定上游 `961bdf47389a08e3143c0340490896b9f50edef9`；[源码索引](nurockplayer--richman4-remake/source-index.md)｜[结构化证据](nurockplayer--richman4-remake/evidence.json)。源数据和十二股路径已作固定源码审计；历史完整对局不能替代尚未通过的主棋盘/股市视觉验收。仅 B/C/D 级证据，无本轮独立 Godot 运行和原版私有素材；许可证未明确，建议只读参考。
