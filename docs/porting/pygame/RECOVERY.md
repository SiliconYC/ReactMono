# 存读档与异常边界

## 与固定参考保持一致的恢复合同

依据`tools/native_game.cpp::Application::load/write_save`与`GameSession::can_save`。原DAT保存世界/玩家/股市等已解读状态及未知字节，另以`RICH4-RNG-1`旁车保存Watcom状态；人类待命或已结束时可以保存。加载先验证候选世界并构造候选会话/棋盘，再替换当前对象；坏DAT保留旧会话、棋盘和随机状态。

读取会重新创建会话，与C++一样不保留四个历史快照、累计会话日计数、闭包事务或未完成表现。兼容存档与任意时刻完整运行检查点是不同能力；当前提供原合同，不将未保存的运行对象宣称为已经恢复。跨进程退出/加载后继续的真实比较见 [应用记录](APPLICATION.md) 与 [证据](evidence/application-cross-process.json)。

正常退出、可保存日及托管前的AUTO行为、手动五槽与读取六槽按原应用执行。异常诊断`failure-world.DAT`及JSON明确`resumable_save:false`；它是调试证据，不等于合法运行检查点。最近合法AUTO/手动槽可由原读取界面继续；两文件写入中途被杀的事务一致性尚未验收，不以旁车解析通过替代这项。

## 可选RNG旁车的原流语义

原C++用字节流提取签名与`uint32_t`，没有UTF-8协议或整词整数校验。缺失、目录、打不开、签名错误或溢出的旁车沿用启动种子，不能连带拒绝已有效的DAT；这不是对主DAT校验的放宽。

| 旁车数字部分 | 提取值/行为 |
| --- | --- |
| `12`后接`FF`字节 | 12，非UTF-8尾字节不影响前缀 |
| `1junk` | 1 |
| `0x10` | 十进制提取前缀0 |
| `-1` | 4294967295 |
| `-4294967295` | 1 |
| `4294967296`或`-4294967296` | 溢出，沿用启动种子 |
| 数千个前导零后接17 | 17，不受Python十进制字符串转换长度上限影响 |
| 无数字、坏签名、缺失或不可读 | 沿用启动种子 |

`save_random.py`按此处理字节；主应用设置也归一化为原无符号32位种子，保证菜单、规则和结局共用同一值。保存格式没有改变。

## 已验、失败和边界

修复前的真实资源回归先观察到：UTF-8解码错误拒绝有效DAT；负数旁车错误回退；窗口创建失败未关闭应用；音频关闭报错跳过字体/显示清理；配置种子未保持32位。失败值与RED记录见 [失败记录](evidence/application-load-recovery-failures.json)。对应测试修复后通过，错误仍向调用方传播。

使用自然应用产生的DAT及两份本机原DAT，各配25组旁车，直接调用未修改原`Application::load/draw`：合计150命令、75完整640×480画布、完整世界DAT及所有已序列化应用状态一致。覆盖缺失、目录、空/非UTF-8字节、符号、数值前缀、溢出与5000个前导零。原DAT与商业画布只留临时/忽略目录，公开报告只含元数据/哈希：

- [自然对局DAT](evidence/application-load-boundaries.json)。
- [原DAT一](evidence/application-load-official-save1.json)。
- [原DAT二](evidence/application-load-official-save0.json)。
- [负种子应用/真实槽位三天](evidence/application-negative-seed.json)。

窗口/音频关闭错误通过定向故障注入验证真实应用资源释放，不称OS桌面或真人试玩。`596`项完整Python测试在显式外部素材/字体/SDL3/FluidSynth/GM音库环境通过；原退出诊断、旁车回退与完整检查点的能力边界继续保留。

复现（存档应是调用方持有的合法原DAT或自然Python对局导出）：

```sh
PKG_CONFIG_PATH="$PWD/.research-cache/audio-runtime/lib/pkgconfig" \
uv run --project pygame python pygame/tools/differential_load.py \
  --source .research-upstreams/richman4-remastered --build .research-cache/cpp-core \
  --assets /path/to/Rich4 --font /path/to/chinese-font.ttc \
  --library .research-cache/audio-runtime/lib/libSDL3.dylib \
  --save /path/to/save.DAT --report .research-cache/load-boundaries.json
```
