# 存读档与异常边界

## 与固定参考保持一致的恢复合同

依据`tools/native_game.cpp::Application::load/write_save`与`GameSession::can_save`。原DAT保存世界/玩家/股市等已解读状态及未知字节，另以`RICH4-RNG-1`旁车保存Watcom状态；人类待命或已结束时可以保存。加载先验证候选世界并构造候选会话/棋盘，再替换当前对象；坏DAT保留旧会话、棋盘和随机状态。

读取会重新创建会话，与C++一样不保留四个历史快照、累计会话日计数、闭包事务或未完成表现。兼容存档与任意时刻完整运行检查点是不同能力；当前提供原合同，不将未保存的运行对象宣称为已经恢复。跨进程退出/加载后继续的真实比较见 [应用记录](APPLICATION.md) 与 [证据](evidence/application-cross-process.json)。

正常退出、可保存日及托管前的AUTO行为、手动五槽与读取六槽按原应用执行。异常诊断`failure-world.DAT`及JSON明确`resumable_save:false`；它是调试证据，不等于合法运行检查点。最近合法AUTO/手动槽可由原读取界面继续。两文件写入中断恢复已由下述事务协议与真实强杀验证补齐；不是把旁车解析通过冒充事务保障。

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

## 两文件提交与强杀恢复（2026-10-25，#158）

`save_transaction.py`在每槽旁建立隐藏的`.Save1.DAT.rich4-save/`，固定锁文件保留以避免inode锁失效。正常主文件仍是原DAT和原文本RNG；JSON提交日志只保存两份原字节的Base64、SHA256及版本，不接受外部目标路径。所有日志和临时文件位于存档所在目录，正式缺省即游戏自身`userdata/saves/`。

准备记录先完整写入并flush/fsync，原子替换为`pending.json`是提交点；其前中断保留旧对，其后中断在下一次读档、列槽或保存时完成新对。两个主文件各原子替换并同步后才删日志，因此恢复自身再次被杀仍可重做。进程锁最长等3秒，强杀后由OS释放；普通无事务目录的原DAT读取不创建目录或锁，原可选旁车回退合同不变。首次保存提交后尚无DAT，列槽及F9最近档选择也能恢复。

损坏、未知版本、错误哈希、错误类型或深层JSON日志拒绝恢复，不覆盖已有主文件；列槽把坏槽禁用，真正读档提示失败并保留当前会话和棋盘。符号链接及非普通目标文件在提交之前拒绝，避免留下已知无法完成的日志。普通窗口异常现在与原`std::exception`边界对应：写诊断后重新抛出，不跳规则或把失败局当成功；异常快照依然不可称为运行检查点。

合法输入来自自然菜单重放产生且已做C++存档字节比较的`Save1.DAT`和`Autosave.DAT`；两者世界和RNG都不同。首次、已有槽分别22个I/O边界，恢复过程16个边界：60个不同中断案例、139个实际子进程、78个确认SIGKILL退出（含建立待恢复日志和锁释放验证的进程），57次独立新进程读取均核对DAT哈希和RNG；另有读写错误、锁等待、并发首次写入、无写来源读取和坏日志用例。见 [真实强杀证据](evidence/save-transaction-crashes.json) 和 [失败记录](evidence/save-transaction-failures.json)。

实际正式入口的八地图各三天、全部工具栏和手动槽/自动槽，1982命令、874完整画布及真实DAT/RNG仍与固定C++逐字节一致，见 [存档事务应用差分](evidence/application-save-transaction-eight-maps.json)。该报告记录当时代码哈希，随后只增加深层坏日志的列槽异常分类；正常规则和保存合同未变。音频探针时钟判据修正及独立数值对照见 [音频判据](AUDIO_DUMMY_CLOCK.md)，不将dummy功能通过说成硬件性能通过。

这是对原参考顺序写文件的工程保障扩展，已经明确记录差异。它不保证不遵守本协议的其它程序同时写同一槽，也不保证硬件断电、损坏磁盘或Windows等未做同等实机验证的平台。四历史快照、闭包和任意表现中途检查点仍按参考不保存；没有为此改变游戏规则或原存档封装。

复现合法输入和定向强杀（均在仓库根目录，声音库按子项目说明部署）：

```sh
mkdir -p pygame/.local/tmp
TMPDIR="$PWD/pygame/.local/tmp" uv run --project pygame python pygame/tools/replay_application.py \
  --assets pygame/assets --font pygame/assets/fonts/ui.ttc \
  --output pygame/userdata/validation/save-producer --seed 123 --days 3 \
  --exercise-screens --exercise-save
RICH4_TEST_NATURAL_SAVES="$PWD/pygame/userdata/validation/save-producer/saves" \
TMPDIR="$PWD/pygame/.local/tmp" uv run --project pygame python -m pytest \
  pygame/tests/test_save_transaction.py --basetemp pygame/.local/save-crash-tests -q
```
