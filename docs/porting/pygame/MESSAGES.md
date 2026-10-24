# 原消息层与决策文字

## 实现与依据（2026-10-24，#148）

固定`3f4209a7dfb5b2f20799bf54e6c03c5faa11c557`的`tools/screens/messages.cpp/.hpp`。`message_overlay.py`261行实现原`Item/Audio/Overlay`、文字块模式、确认框与确认条；`message_rules.py`361行实现事件/台词/公告、目标名称、本地化决策及确认问题。代码规模不计测试与适配器，不代表整游戏移植覆盖率。

`original_text.py`增量只保存原文虚拟地址与外部读取接口：96股票名称按八图原索引读取，保留第八图复用地址；费用表、新闻标题和公告格式来自原PE。商业台词/格式表、EXE/MKF、解码图片及字体均不进入公开仓库。既有原文格式和许可边界见 [字体/原文说明](NATIVE_UI.md) 与`pygame/NOTICE.md`。

## 时钟、声音与输入契约

- 入队复制完整消息值。相邻气泡按声音编号抑制，最后气泡键不会因为清空、跳过或其它种类消息而重置；该行为依原源码保留。
- 首次画到消息才播放语音，停留取最短时间与可选真实语音长度的最大值。消息层声音0表示静音，外部配音表读取编号0有效，两者不可混淆。
- 先`api_退休()`再绘制板面/下一决策。正常退休不调用停止语音；点击跳过即使尚未开始也调用停止，未开始的清空不调用停止。
- 绘制消息先清空共用按钮，再注册原稳定编号900全屏跳过，覆盖后的操作不能透传。开发即时模式仍要实际画一帧才退休。
- 时钟由宿主注入，默认单调毫秒，截止按原`uint64`加法；不偷偷推进规则、重抽结果或消耗随机数。
- 确认条Data440三帧按悬停半区亮起，两个半区分别向外延伸10像素；原点抵消、强制不透明和稳定按钮编号保留。

原气泡云、头像/图语、偏移对话框、新闻/命运全屏背景及照片/人物行、神明底字幕均使用真实外部资源。照片固定388×251，按完整双字节读取、不足补零，并保留原16位最高位；不能复用会清最高位的普通原图辅助。文字模式使用原Font块范围，区别于其它屏幕的GDI行对齐。

## 事件与决策契约

卡道具语句优先于事件类别；空卡道具槽不虚构消息。事件类别0是有效值，只有`None`才表示无类别；消失中的人物依原门控不发事件气泡。新闻36类、命运49类、神明十二类、租金/免租、缺席、点券、道具/股票卡/抢夺公告保留原参数及时长。

名称来自实际World人物、原Big5街名/设施名、地图股票索引、公司股票索引、地上物件及卡道具编号；仅删除ASCII空格，不改规则名称数据。卡目标的两选项确认特例、地产零/一确认判定、选项值与顺序保持不变。`api_本地化()`返回独立决策副本，表现层不回写规则世界。

## 自动证据与具体失败

十二项新定向测试：消息层六项、外部文字一项、消息规则五项；完整Python414/414、Ruff通过。合成小图/PE只用于边界断言，不作为正式图片或台词。

[画面差分](evidence/message-overlay-differential.json)直接编译原`messages.cpp`，882命令、270950400完整640×480画布像素，以及完整消息队列、焦点、截止/开始状态、重复键、照片缓存数、按钮/回调/语音请求一致。覆盖十二人物四情绪、真实图语、全部新闻/命运照片、十二神明字幕、五种文字模式/八种样式组合、确认条位置/悬停/回调与语音等待精确边界。字体SHA256记录在报告，双方同为本机FreeType2.13.2；没有证明其它平台字体或1998年GDI像素一致。

[基础规则差分](evidence/message-rules-differential.json)6437命令：324事件台词、1416卡道具槽含越界空项、八图400名称查询/968目标名、2632显式事件、672决策和消失门控；完整输出消息/文字/行/声音/选项一致，两端逐条检查世界完整DAT不变。[扩展组](evidence/message-rules-expanded.json)7965命令再次通过，含4120事件、40项显式设施类型夹具；补齐五种设施类型的全部免租模板、正负/零金额与乘数、抢夺编号边界、事件分发台词优先级。基础与扩展是重叠语料，不相加冒充更多独立覆盖。

保留以下失败与修复，不把失败前部分通过算作全组通过：

1. [适配器字节读取失败](evidence/message-rules-byte-parser-failure.json)：C++流将`uint8_t`公告号/人物掩码当字符读取，命令1915后错位。改为整数临时值再赋回原字段，未修改原参考函数。
2. [费用映射失败](evidence/message-rules-fee-failure.json)：实际费用指针表0x47517c的索引2才是加油、3为修车；不能按原注释推断酒店/商场费用也在这四项内。租金加油改为索引2，免租酒店/商场分别读取0x4638ad/0x4638da。原C++实际使用的不同文字仍忠实保留，不擅自“统一”两种界面。
3. [免费卡地址失败](evidence/message-rules-va-failure.json)：初步定位把格式串前四字节浮点数据包含进来，产生两个问号；实际起点为0x465388。加入先失败的定向测试后修正，再完整重跑。

```sh
uv run --project pygame python pygame/tools/differential_message_overlay.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/message-overlay-differential.json
uv run --project pygame python pygame/tools/differential_message_rules.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --report .research-cache/message-rules-expanded.json
```

测试在忽略的构建目录生成最小`SDL3/SDL_timer.h`声明与虚拟`SDL_GetTicks`实现，直接编译未修改的原消息CPP；本机不因此需要SDL3。此时钟替身仅用于可重复测试，正式Python使用宿主时钟，不调用C++。

## 验收边界

以上事件/世界夹具是明确的组件输入，并非自然规则触发；图形差分按原`Item`绘制，音频回调只记录编号和返回片长。正式应用还须按`after_events`顺序接线消息、电影、移动、决策、菜单和实际语音。尚未完成完整Pygame窗口操作、语音听感/波形、自然长局逐帧、主游戏到互动小游戏及完整结局；不得据此宣称完整游戏或1998原版一致。
