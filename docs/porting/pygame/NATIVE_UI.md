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

## 外部原程序文字（2026-10-24）

`original_text.py`现已只读解析外部`rich4.exe`的PE32头、区表、VA指针和NUL字符串。原Watcom各区`VirtualSize=0`，使用有内容的`RawPointer/RawSize`定位；`.bss`的零`RawPointer`不可映射为文件头。负数/跨区/截断/未终止读取拒绝，不加载或执行EXE。只在`DGROUP`扫描声音前缀；自审发现`.reloc`偶然含有`#2228`机器字节，新增先失败的测试后排除该区。

| 固定参考数据 | Python接口 | 保留的格式行为 |
| --- | --- | --- |
| `message_strings.inc`事件表，VA`0x48084a` | `api_台词("event", 人物, 槽)` | 12×27指针，`#NNNN`前缀和`@NN`图标文字 |
| 同文件道具表，VA`0x480d5a` | `api_台词("tool", 人物, 槽)` | 12×26指针，120空槽仍为`None` |
| 同文件卡表，VA`0x48123a` | `api_台词("card", 人物, 槽)` | 12×90指针，456空槽仍为`None` |
| 新闻36/命运49正文 | `api_配音(149+新闻号/185+命运号)` | 格式占位符和换行原样保留 |
| 神明12条到达文字 | `api_神明(索引)` | 明确VA`0x463250..0x463495`，不虚构声音编号 |
| `voices.hpp`店员表65条 | `api_配音(声音, 变体)` | 声音0有效；89的两种措辞显式区分 |

解码沿用已验证的原CP950边界。按参考将`U+223C/U+FE52`规范为全宽标点；仅声音752/753删除无Unicode映射的`0x9DDD`自造字。`api_配音()`默认保留EXE原文；`89,1`仅执行GPL原生界面新增的两字措辞替换，原文仍可读取。其他缺少的声音和变体拒绝，重复声音仅允许同文。

九项定向测试和完整Python369/369通过。直接编译固定原表的测试适配器，1878条记录的全部Unicode文字/声音编号一致，含576个真实空槽、十二条神明文字和两种银行89提示；索引有1354个实际声音编号。报告只保存数量、版本和哈希，见[对照结果](evidence/original-text-differential.json)。这是文字层自动验收，显示、语音同步和正式窗口仍待集成。

复现：

```sh
uv run --project pygame python pygame/tools/differential_original_text.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --exe /Users/laocao/Downloads/Rich4/rich4.exe \
  --report .research-cache/original-text-differential.json
```
