# 固定源码规模与迁移依赖

基准为 `3f4209a7dfb5b2f20799bf54e6c03c5faa11c557`，本机独立读取；清单工具为 `pygame/tools/source_inventory.py`，解析器为 `tree-sitter-cpp 0.23.4` / `tree-sitter 0.25.2`。逐文件 SHA-256、本地 `#include` 依赖和逐函数声明/行号见 [source-inventory.json](source-inventory.json)。[mapping.json](mapping.json) 是对应 Python 职责及测试的增量来源。

## 统计口径

统计 `src/include/tools/tests/android/ios` 下 `.cpp/.hpp/.h/.c/.inc/.mm/.m`；物理行包括空行、注释与查找表。函数为语法树 `function_definition` 节点，排除 lambda，包含构造/成员/局部辅助函数，不是功能总数或移植完成率。

| 目录 | 文件数 | 物理行 | 语法函数定义 |
| --- | ---: | ---: | ---: |
| `src` | 31 | 15601 | 620 |
| `include` | 29 | 2573 | 89 |
| `tools` | 66 | 19219 | 707 |
| `tests` | 31 | 8527 | 280 |
| `android` | 2 | 208 | 8 |
| `ios` | 3 | 179 | 4 |
| 合计 | 162 | 46307 | 1708 |

28 个文件有语法错误节点（含 Objective-C、C、宏与语法扩展），逐文件 `parser_has_error` 明示。因此函数数是**语法清单基线，不保证语义完备**；不能当精确百分比分母。固定核心 CMake 列出 29 个 `.cpp` 编译单元，另有 2 个 `.inc` 查找表。宿主、屏幕、音频、数据表也在目标范围，不能只移植核心便称完整。

## 迁移顺序与依赖

1. `assets → graphics/flc/terrain → board_renderer`：MKF 解码供所有格式；图形保留原点与索引透明；地形投影不能以总览图代替。
2. `random/calendar/direction/inventory/economy → save/world`：日期、数值与字节语义是恢复和差分基础；地图节点、地产、设施、公司均保留原编号与零号占位。
3. `world → services/stocks/auction/lottery/holidays/cards/tools/gods/events/trading/special_actors`：规则模块操作完整世界，并返回有序事件/特效。
4. `cards_ai/tools_ai/stocks_ai → game`：AI 的消费随机次数、合法目标和操作顺序属于可观察行为，不能改成任意合理策略。
5. `game → native_game + screens/* + native_audio`：宿主实现决策窗口、动画阻塞顺序、声音/语音、小游戏、开始/结束、保存恢复等完整体验；SDL/FreeType/FluidSynth 接口换为 Python/Pygame 对应功能。

本地头依赖是源码直接引用关系，不等于运行时调用图。每次迁移新模块前继续读其头文件、完整实现、原测试与调用者；遇到新增依赖同步更新计划与覆盖表。Android/iOS 包装、原程序捕获 oracle 和外部研究工具不是纯 Python 游戏的功能移植目标，但保留索引以审查来源和测试边界。

## Python规模增量（2026-10-24，表现队列阶段）

按`pygame/src/rich4/*.py`直接统计：70个运行时Python文件、21933物理行；测试51个Python文件/5587行，研究与验收工具45个Python文件/12489行。物理行包含空行、注释与固定查找表；测试专用C++适配器另计，不进入运行时包。这些数值不能与46307行相除当作功能覆盖率，正式应用/原专属菜单与屏幕、音频/结局及运行恢复仍有缺口。

清单工具新增映射ID存在性检查。自审发现`present`错误映射到函数内部1094行，实际定义起点为1090；已修正并验证全部映射有真实语法ID。额外用错误ID确认工具拒绝且不产生输出，避免静默漏映射造成误读；原162文件/1708词法定义基线未改变。
