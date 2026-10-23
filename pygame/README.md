# Pygame《大富翁4》移植子项目

状态：**移植进行中，尚不是完整可玩游戏**。现有入口是读取真实 MKF 的资源验收工具；当前进度与缺口见 [移植台账](../docs/porting/pygame/README.md)。原 React 游戏保持独立。

## 环境与运行

使用 Python 3.12 与 Pygame 2.6.1。推荐独立 CPython，避免本机 Conda 的 `readline` 原生扩展冲突。以下命令在仓库根目录执行；`/path/to/Rich4` 必须是自己合法持有的外部原版素材目录。

```sh
uv sync --project pygame --python 3.12
uv run --project pygame rich4-pygame --assets /path/to/Rich4 --archive Data.mkf --entry 601
uv run --project pygame rich4-pygame --assets /path/to/Rich4 --archive Data.mkf --entry 128
```

窗口保持 640×480 逻辑画布，缩放时等比留黑边；左右键切换资源内精灵帧，`Esc` 退出。`--frame` 指定初始帧；`--screenshot` 只写本地忽略目录，`--frames` 用于有限帧窗口冒烟运行。不接收或假装执行任何尚未实现的游戏指令。

## 测试

```sh
uv run --project pygame python -m pytest pygame/tests -q
uv run --project pygame ruff check pygame
uv run --project pygame python pygame/tools/source_inventory.py \
  --source /path/to/pinned-cpp --output /tmp/source-inventory.json
uv run --project pygame python pygame/tools/differential_assets.py \
  --source /path/to/pinned-cpp --build /tmp/rich4-cpp-core \
  --assets /path/to/Rich4 --report /tmp/assets-differential.json
```

差分工具会核对参考提交、构建固定 C++ 核心，在临时目录比较全部解码字节及首尾图像/动画帧，退出后移除商业解码文件；报告只含元数据和哈希。C++ 不参与正常 Pygame 运行。合成样本为格式边界测试，不作为真实游戏事件或规则替代。

源码及素材权利边界见 [NOTICE.md](NOTICE.md)。
