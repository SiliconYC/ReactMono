# 已研究与待研究的外部仓库索引

**本目录是多仓库研究产物的容器，不是游戏源码目录。**

每个外部仓库一份独立子目录：`<GitHub owner>--<GitHub repo>/`，按上游仓库名称原样记录大小写。研究开展前不创建空目录或占位文件；一个外部上游只对应一个权威报告，fork 与实际代码血缘需要有证据才能归类。

研究标准：[RESEARCH_STANDARD.md](../RESEARCH_STANDARD.md)；候选任务与范围：[研究入口](../README.md)。

## 已提交的逐仓库深入研究

| Issue | 上游 / 锁定提交 | 交付文件 | 实测级别与使用建议 |
| --- | --- | --- | --- |
| [#95](https://github.com/SiliconYC/ReactMono/issues/95) | [mytbk/rich4](https://github.com/mytbk/rich4) @ [f81954d6](https://github.com/mytbk/rich4/commit/f81954d6a5675f63297036f9252720c6ca32a2b4) | [九章报告](mytbk--rich4/README.md) · [30 处源码索引](mytbk--rich4/source-index.md) · [证据 JSON](mytbk--rich4/evidence.json) | **B/C/D 静态核查**；不具备原版资产、编译工具与 Wine，未独立运行（A=0）。建议仅参考事实与测试方法，不移植汇编/GPL 代码或原版素材。 |

上表的“提交”指研究报告已经写入 Git、可被审查；**不表示上游游戏已成功编译、完成全部玩法或获得原版权素材授权**。Issue/PR 最终合并、关闭状态以 GitHub 实际结果为准。

## 尚待独立研究

[#96](https://github.com/SiliconYC/ReactMono/issues/96) tytannial/rich4-re、[#97](https://github.com/SiliconYC/ReactMono/issues/97) lhr0909/richman4-remastered、[#98](https://github.com/SiliconYC/ReactMono/issues/98) iam567/rich4-renew-app、[#99](https://github.com/SiliconYC/ReactMono/issues/99) nurockplayer/richman4-remake、[#100](https://github.com/SiliconYC/ReactMono/issues/100) oama1111/rich4-remake-public、[#101](https://github.com/SiliconYC/ReactMono/issues/101) JCRJPZB/Rich4、[#102](https://github.com/SiliconYC/ReactMono/issues/102) Yakamozli/richman-3d、[#103](https://github.com/SiliconYC/ReactMono/issues/103) zawsstt/monopoly-rich-life。

跨仓库综合综述由 [#104](https://github.com/SiliconYC/ReactMono/issues/104) 另行交付；**不能仅依据 #95 的第三方引用证据代替 #96/#97 的深入研究与独立验收**。
