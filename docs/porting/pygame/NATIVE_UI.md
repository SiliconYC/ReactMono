# 原生界面基础

## 字体与编码（2026-10-24）

`native_ui.py`对应固定参考`tools/native_ui.hpp`：CP950消费边界、UTF8码点、RGB555颜色/矩形、FreeType字形、文字测量/墨框、换行/裁切、粗体/阴影/描边/块居中。字体文件从外部路径读取，不包含或分发字体。

Python通过`ctypes`调用FreeType公开C接口，不调用C++游戏引擎。字槽布局使用宿主C类型自然对齐，缓存复制后的遮罩；原单色模式是灰度阈值56，不能替换为FreeType的一位栅格化。加载顺序为显式库、宿主库、Pygame随附库；不同字体或FreeType版本仍须重新比较。

首次完整编码差分发现`C6A1`：Python CP950输出日文字形，参考iconv输出问号。穷举发现Python复用Big5日文区的249项差异，现按参考拒绝该区，保留原先按首字节消费一/两字节的边界。失败与修复证据分别见[首次失败](evidence/native-ui-initial-failure.json)和[最终差分](evidence/native-ui-differential.json)。

## 自动证据

七项定向测试及完整Python360/360、Ruff通过。直接编译原`native_ui.hpp`的适配器比较66493条命令：65805项编码输入（含全部65536个双字节）、380个真实字形/遮罩、180幅普通文字画布、128幅样式块画布。308幅完整384×192 RGB555画布共22708224像素逐字节相同，测量/墨框/块尺寸也一致。

此结论使用同一外部`Hiragino Sans GB.ttc`字面0和FreeType2.13.2；具体字体哈希、库路径、输入种子和实现哈希见报告。没有证明其他字体/平台相同，也不是原版1998字体、主游戏窗口或真人试玩验收。测试适配器不进入运行包。

复现：

```sh
uv run --project pygame python pygame/tools/differential_native_ui.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/native-ui-repeat.json
```

## 后续界面与商业文字边界

原`native_frame.hpp`的Frame、正式MainScreen、菜单/表现队列/音频和结局仍待移植。C++的`message_strings.inc`包含从商业EXE提取的台词；不将这些长文本转抄进公开Python源码。下一步从用户外部原`rich4.exe`只读解析文字表，并对照参考的规范化、声音编号及图标标记。EXE、字体、画布与任何解码后的商业文本都不进入Git或发行包。
