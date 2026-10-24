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

正式MainScreen、菜单/表现队列/音频和结局仍待移植。C++的`message_strings.inc`包含从商业EXE提取的台词；不将这些长文本转抄进公开Python源码。下文记录外部原`rich4.exe`文字表及原Frame绘制基础的增量。EXE、字体、画布与任何解码后的商业文本都不进入Git或发行包。

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

## 原Frame与通用绘图（2026-10-24，#148）

`native_frame.py`对应原Frame/Button：共用按钮列表、稳定编号/启用/声音策略、真实回调、半开命中、原精灵原点处理、按钮缩字/居中、对话框、字体与指针时钟。`Frame.picture`先加原点再交给减原点的底层blit，结果是Frame局部左上角，不可直接套用地图精灵的世界锚点。

`screen_draw.py`对应`tools/screens/draw.cpp`：八种GDI对齐（包括竖排）、基线和粗体/阴影/描边、RGB555暗化/灰阶、按下斜面、局部/整数缩放/不透明背景、真实节庆图、弹框与金额分组、专用点击音先于动作。坏日期/地图按参考保留季节图；没有改写规则世界或生成替代图片。字体夹具移到测试共用`conftest.py`，没有运行时假字体。

十三项新增测试及完整Python382/382、Ruff通过。直接编译原Frame和`draw.cpp`，733场景逐幅完整640×480 RGB555画布共225177600像素、按钮编号/区域/启用/通用声音标志、回调与声音请求顺序一致。包含320文字对齐/样式场景、100真实精灵绘制/局部/缩放/背景、40八图日期/节庆场景、15弹框及八个有符号64位金额边界；完整操作计数见[报告](evidence/native-frame-differential.json)。

这些是直接绘制及回调探针；禁用按钮探针可以直接调用已注册回调，不能据此声称应用会派发禁用按钮。未验收正式MainScreen、真实窗口输入、播放时序或完整游戏，后续跟踪[#148](https://github.com/SiliconYC/ReactMono/issues/148)。

```sh
uv run --project pygame python pygame/tools/differential_native_frame.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/native-frame-repeat.json
```

## 单色文字性能增量（2026-10-24）

主屏日历暖缓存绘制仍超出28毫秒骰子帧间隔。剖析一帧得到总46毫秒、302次`Font.draw`共39毫秒；原单色模式的每个遮罩值已是0或255，仍逐像素做三通道混合造成主要开销。现复用原图像的不可变连续行段缓存，以列表切片写入RGB555。灰度分支不变，字体/字号/描粗/时钟/动画帧未简化。

这里不能直接调用普通透明blit：黑字颜色0必须被写入，原字体也不更新目标透明遮罩；满覆盖时原混合会清除颜色最高位。两项新增测试明确保护黑字、目标遮罩、裁切与最高位，完整Python396/396、Ruff通过。

同一机器/字体/世界、每视图预热五帧并测量40帧：

| 主屏视图 | 优化前中位数（毫秒） | 优化后中位数（毫秒） | 优化后P95（毫秒） |
| --- | --- | --- | --- |
| 0 | 45.84 | 7.90 | 10.39 |
| 1 | 10.77 | 4.71 | 4.95 |
| 2 | 40.76 | 6.94 | 7.40 |

[前测](evidence/main-screen-font-before.json)和[后测](evidence/main-screen-font-after.json)保留平台、字体/实现哈希与范围。这只测暖缓存主屏界面CPU绘制，没有板面、SDL窗口、声音，不得换算为完整游戏FPS；地图冷相机中心停顿仍未解决。

完整重跑66493字体命令、308画布，以及原MainScreen两组3620完整画布；所有输入/状态/像素摘要与优化前报告相同，见[字体回归](evidence/native-ui-spans.json)及[主屏回归](evidence/main-screen-font-regression.json)。没有为了性能略过动画帧或更换字体。

```sh
uv run --project pygame python pygame/tools/benchmark_main_screen.py \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --samples 40 --report .research-cache/main-screen-font-benchmark.json
```

## 消息原文索引增量（2026-10-24）

`original_text.py`新增外部股票96索引、费用四指针、新闻六标题及按虚拟地址读取公告格式；不提交对应商业字符串。股票第八图存在复用地址，不能用连续NUL串或猜测排序代替。全部八图名称/公告/确认的7965命令直接固定消息CPP差分通过；费用实际索引与免费卡格式起点偏差及修复证据见 [消息说明](MESSAGES.md)。旧1878台词报告对应其原版本，新扩展报告记录当前实现哈希，不篡改旧证据。

## 票面暗化行映射增量（2026-10-24）

原四票面暗化CPU内核中位34.35毫秒，改为有界RGB555表和逐行映射后2.69毫秒，相同输入输出摘要不变。39全颜色画布覆盖全部16位颜色/33等级及钳制/裁切，原733画布绘图回归摘要仍相同；两项新测试保护最高位/黑色/透明掩码和空区域。完整月结扩展在改动后直接对照通过，详见 [月结](MONTHLY.md)。不改变字体/图片/时序，也不把内核时间称为完整游戏FPS。

## 数字输入板增量（2026-10-24）

原Panel21精灵、量尺/按压/缩放、17按钮和可重入回调已直接组件差分852完整画布一致，详见 [数字板](NUMBER_PAD.md)。完整金融界面/实际主程序仍待接线。

## 银行与一级股组件增量（2026-10-24）

原三层银行与Panel73认购提示已完成4876实际完整画布差分，私有时钟/按钮/声音请求/数额回调相同。长对白外部读取，原门控及未验范围见 [银行屏幕](BANK_SCREENS.md)。

## 股票组件增量（2026-10-24）

原Panel75的完整报价/持仓/资讯图表和红黑卡目标已对照911实际画布；binary32边界、当前玩家持股和失败修复见 [股票屏幕](STOCK_SCREENS.md)。正式交易与完整窗口接线仍待验。

## 设施与托管组件增量（2026-10-24）

原五设施条、改建取消与四人托管编辑已逐画布/状态/声音请求验证4872次；副本、门控和异常边界见 [设施与托管](FACILITY_AI_UI.md)。

## 主菜单与新局组件增量（2026-10-24）

原菜单/新局及全部36骑乘条目461帧已做2376完整画布、私有MT与回调差分；源码灰态功能、时序与未验范围见 [主菜单与新局](MAIN_MENU_SETUP.md)。

## 选项与存读档槽组件增量（2026-10-24）

原配置控件/确认、六读五存槽已做2133完整画布及状态/回调差分，曲名外部读取；真实保存恢复与音频等未验项见 [选项与存档槽](OPTIONS_SAVE_SLOTS.md)。
