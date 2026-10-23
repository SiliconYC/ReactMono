# Pygame 移植实施计划

> **For agentic workers:** 使用 `superpowers:executing-plans` 独立逐任务实施；用户已授权自主执行，不等待计划审批，不使用子 Agent。

**Goal:** 完成可独立运行且经差分、长局、图形操作验收的忠实 Python 移植。

**Architecture:** 固定 C++ 模块逐项迁移，资源与规则不依赖 Pygame 窗口。测试端单独构建 C++ oracle，正式游戏只运行 Python。

**Tech Stack:** Python 3.12、Pygame 2.6.1、pytest；C++20 仅用于测试参考。

**Spec:** [设计与验收契约](DESIGN.md)。

## 全局约束

只在独立 Worktree 开发；目标 `dev`，不修改 `main`。商业资源及解码输出不入 Git。不改 React 游戏逻辑、美术与设计。不伪造事件、结果和 UI，不通过隐藏 C++ 后端提供功能。未知规则必须查固定源码并记录。

## 审查重点

损坏资源必须及时报错且限制分配；透明索引零与黑色像素分开；缩放留边外点击不得变成游戏操作；随机流保存恢复不得漂移；八地图逐一核对而非抽样后宣称全覆盖。

## 阶段和任务

### 任务 1：清单与资源基础设施（#140）

文件：`pygame/pyproject.toml`、`src/rich4/assets.py`、`graphics.py`、`app.py`、`tests/test_assets.py`、`test_graphics.py`、`tools/source_inventory.py`、`tools/differential_assets.py`。

接口：`资源包_类.api_解码(index) -> bytes`；`图像_类.api_解码(data, frame) -> 图像_类`；图像保存 RGB555、原点和透明掩码。解析只接受经范围验证的 MKF / SPR / SMP。预览有独立明确名称，不伪装游戏。

- [x] 生成全部 C++ 文件、函数定义和本地头依赖清单，保存固定版本/工具信息。
- [x] 写解压/索引/透明与颜色/原点/留边的行为测试并观察缺少实现失败。
- [x] 依固定源实现 MKF 自适应树与图像解码，通过上述测试。
- [x] 真实资源对 C++ 提取与帧输出逐字节比较，记录样本覆盖和未覆盖格式。
- [ ] 启动真实 Pygame 窗口并操作、保存本机证据；验证后提交、独立集成、快进并推送 `dev`。

### 任务 2：确定性基础规则

接口：每局独占 Watcom 32 位随机流；日期按 C++ 四年闰规则；库存字节回绕；经济按原数值域。文件对应 `random/calendar/direction/inventory/economy`，每模块先写边界测试，再移植和 C++ 批量差分，提交映射及失败修复。

### 任务 3：地图、玩家与回合闭环

移植 `save/world/world_validation/board_renderer/game`；结构化玩家、地块和阶段与 C++ 对应。先读取八图并比初始世界，再比掷骰移动、停留、买地、租金、破产、日期。完成真实可玩原版地图界面后独立合并。存档完整性和恢复测试随模型建立。

### 任务 4：完整规则

按依赖依次迁移 `services/stocks/auction/lottery/holidays/cards/tools/gods/events/trading/special_actors` 与四类 AI。逐模块翻译原测试并增加跨语言动作流，不能仅检查卡片/道具库存。每个可验收模块细粒度提交、合并、推送；总任务保持开放。

### 任务 5：完整视听与体验

补齐地形投影、FLC、原 UI、人物动作、遮挡、特效队列、音效/语音/MIDI、三个小游戏、菜单设置和结局。按全部八图、角色、规则/事件和终局覆盖矩阵跑截图/帧/交互差分。完成自然长局、保存跨进程重放、异常恢复与人工操作验收；逐项报告尚未验证内容。所有门槛满足才关闭总任务。
