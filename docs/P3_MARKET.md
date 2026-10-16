# P3-09：虚构股票行情引擎（Issue #38）

- `src/core/market.ts` 包含五家虚构公司：海岚科技、碧波航运、青禾农业、星河能源、远山工业。仅有游戏币报价，**不连接真实交易所、不访问网络或真实金融账户**。
- 每只股票价格为 1～100000 的整数。每完成完整的一轮玩家轮换，独立随机数流生成一次每只股票的 ±6% 有界变动，四舍五入并截断于合法范围；请求重复、跳轮或非法快照一律报错。行情种子由对局种子派生，但永不改变掷骰随机数。
- `GameConfig.marketEnabled:true` 可开启行情，`GameState.market` 使用 `version:1`、`round`、`rngState` 和 `prices` 存储；现有不带行情的 P1/P2/P3 状态及旧档保持兼容。本轮不包含买卖、持仓、股息或下单 UI，这些属于 #39。
- 测试 `tests/p3-market.test.mjs`：5 股标识和价格校验、100 种子逐轮确定性重演、JSON 往返后继续一致、非法快照/非连续轮次拒绝、500 种子×200 轮压力、市场与骰子 RNG 独立及同步保存。当前 PR CI [#38855724654](https://github.com/SiliconYC/ReactMono/actions/runs/38855724654) success。
- [PR #52](https://github.com/SiliconYC/ReactMono/pull/52)，分支 `p3/issue-38-market-engine`，与 #35 并行的独立检查点。必须在 #35 整合后完成 dev 合并、Pages 部署和 Issue 关闭，以上 CI 不能代替最终发布验收。
