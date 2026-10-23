# Pygame 忠实移植工作区

**尚未完成完整游戏移植。** 总任务 [#139](https://github.com/SiliconYC/ReactMono/issues/139) 保持开放，首阶段 [#140](https://github.com/SiliconYC/ReactMono/issues/140) 建立资源、画布与差分基础。

## 导航

- [设计、参考和最终验收门槛](DESIGN.md)。
- [逐阶段实施计划](PLAN.md) 与 [持续执行台账](PROGRESS.md)。
- [源码规模与依赖说明](SOURCE_SCALE.md)；[完整语法清单与逐函数矩阵](source-inventory.json)。
- [功能覆盖与规则依据](COVERAGE.md)。
- [资源和动画接口](RESOURCES.md)。
- [验收、失败与修复记录](ACCEPTANCE.md)。
- [可复现资源差分报告](evidence/assets-differential.json)。
- [子项目运行说明](../../../pygame/README.md) 与 [许可证边界](../../../pygame/NOTICE.md)。

## 证据约定

「源码推断」只说明固定源码中的行为；「自动测试」须有运行命令、输入与结果；「Agent 图形操作」须真实窗口与交互证据；「真人试玩」须真实人的验收记录。「未验证」不得折算成功。C++ 差分一致不等于已证明与 1998 年官方版完全一致。

原版商业素材、解码图像、动画及截图只保存在本机忽略目录。公开证据只保留不包含商业内容的数值、版本、哈希与文字结论。
