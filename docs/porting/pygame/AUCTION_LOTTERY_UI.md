# 原拍卖室与彩票柜台

## 实现与源码边界（2026-10-24，#153）

拍卖三模块244行、彩票模块156行，对应固定`market.cpp::AuctionRoom/draw_room/announce/draw_bidders/draw_lottery/neon_frames`。使用原Panel26及十二人物出价/不能出价/成交精灵，Panel12柜台、Panel13奖池数位、Panel14五帧霓虹。规则仍由真实会话决策与成交通知提供，组件不自行扣款、出票、抽奖或转移地产。

拍卖保留七出价键、合法选项的原索引、第一次点击后五帧200毫秒演出、第二次全画布点击提前完成、换决策丢弃旧演出，以及成交3500毫秒/1750毫秒改字幕/100毫秒庆祝帧。声音请求29/63及原按钮点击声按原顺序产生。时钟为零的成交演出因`started=max(ticks,1)`后无符号差回绕立即结束，按源码保留并单测；这不是重新设计的计时规则。

原房屋展示尚未建模建筑类型，按原参考使用type0；设施使用原通用地块图。`preview_bid`仅为原画廊工具，不作为运行API移植。原成交缺声音回调会抛`bad_function_call`，Python明确报`ValueError`；正式宿主必须提供声音接口。

彩票保留36格占有暗化/圈选、柜员眨眼与嘴帧、奖池分组数字、告别选项0有效、等待`max(2000,voice_ms)`及点击跳过、过期选项复位。13/14/15/16台词从外部PE读取，14按源码插入换行。霓虹按资源集缓存，坏资源记录并保留已解码帧或空哨兵，不每帧重试；验收预检要求真实霓虹完整解码，避免两端同时跳过而虚假通过。

## 自动证据

四项定向测试通过；同工作树含交易公告栏的阶段测试483/483、Ruff通过。[直接原组件差分](evidence/auction-lottery-differential.json)2416条命令、1738完整640×480画布、533913600像素，完整私有状态、按钮、声音/语音时长请求、响应回调一致。每次绘制及按钮操作均检查两端完整World DAT不变。

显式显示夹具覆盖八图/六地产等级/业主及设施、十二人物与四当前槽独立交叉、全部七动作及即时/非即时、五出价帧/五成交帧与计时边界、无效赢家、重置、四彩票槽/已占号格/最大正奖池、霓虹与嘴帧、告别时长0/1999/2000/2001/3500及无告别状态。夹具不冒充自然交易或抽奖；负奖池等无效状态未验。直接原`market.cpp`编入测试工具，正式Python运行时不加载C++。

```sh
uv run --project pygame python pygame/tools/differential_auction_lottery.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/auction-lottery-initial.json
```

## 尚未验收

完整主应用、真实核心输出到专属屏幕/返回决策的接线、自然拍卖/彩票与真实窗口操作、音频播放和听感仍待验收。画布比较使用同机同字体/FreeType，不能证明1998年官方字体或所有平台一致。商业素材、字体、台词内容和截图不进入Git。
