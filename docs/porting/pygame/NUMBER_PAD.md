# 原数字输入板

## 规则与输入边界（2026-10-24，#148）

`number_pad.py`264物理行对应固定`tools/screens/finance.cpp::NumberPad`与头文件访问器。它只采集数额并调用真实金融回调，不执行存取、借贷或交易规则。原`Panel21`精灵、量尺截取、按压图、17个稳定按钮、1/2倍几何及声音请求均保留。

键盘输入只收ASCII数字及原`M/C/H/退格/回车`。输入最多九位，`MAX`和量尺可产生十位数；画面依原只显示末九位。`H`依原33级量尺得到上限的17/33，不能改成二分之一。取消与输入0返回值相同；确认先取出并清空旧回调，允许回调立即开启另一块数字板。关闭只取消活跃状态，不清空数值或回调。

`next_key_towards`只提供原重放建议，不实际发键。源码的逐位输入辅助无法达到十位目标（九位限制仍生效）；正式操作可使用`MAX`或量尺，保留这一参考行为并记录，不为测试绕过限制。正式应用接线仍须按原物理键语义派发，不能直接把输入法全文当按键。

## 自动证据

四项定向测试覆盖编号/ASCII/位数、MAX/量尺、钳制/可重入确认和缩放定位。阶段完整Python443/443、Ruff通过。

[直接原组件差分](evidence/number-pad-differential.json)1823命令，852实际640×480画布/261734400像素、全部私有状态、按钮几何、回调数额及声音请求一致。覆盖四种缩放输入（钳制为1/2）、整数最小至最大上限、键盘边界、全部按钮、拖动/释放/越界、关闭/取消及重入回调。每张画布先填非空变化底图，逐字节比较；真实精灵载入故障直接失败。字体与参考使用同机同一FreeType和外部字体；不能外推官方1998年字体或其它平台。

```sh
uv run --project pygame python pygame/tools/differential_number_pad.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/number-pad-differential.json
```

这是组件的明确输入和真实美术对照；不是银行规则的自然触发、实际声音听感、完整主程序或窗口人工操作验收。素材、字体、像素和原商业文字不上传。
