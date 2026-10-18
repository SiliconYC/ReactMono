import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemoGame, dispatchDemoAction } from '../dist/demo3d/session.js';
import { applyAction, createGame, DEFAULT_CONFIG, quoteMarket, stockFee, loanLimit } from '../dist/core/game.js';
import { serializeGame, deserializeGame } from '../dist/core/save.js';

const act = (state, type, extra = {}) => {
  const result = dispatchDemoAction(state, { type, actorId: state.players[state.currentPlayerIndex].id, ...extra });
  assert.equal(result.ok, true, `${type}: ${result.reason}`);
  return result.after;
};
const arrived = () => act(createDemoGame(20261017), 'roll');
const ended = () => act(arrived(), 'decline_property');

test('demo启用分离的现金存款、贷款股市和每次停留单次地产规则', () => {
  const state = createDemoGame(20261017);
  assert.equal(state.players[0].cash, 1200);
  assert.equal(state.players[0].bankBalance, 600);
  assert.ok(state.bank && state.loan && state.market);
  assert.equal(state.propertyVisitOnly, true);
  assert.equal(state.stockAccount, 'bank');
});

test('买地后不能同步建房，远程建设和同次停留重复升级都由核心拒绝', () => {
  const bought = act(arrived(), 'buy_property');
  const rejected = applyAction(bought, { type: 'upgrade_property', actorId: 'p1', tileId: 3 });
  assert.equal(rejected.ok, false);
  assert.equal(rejected.state, bought);
  let state = createDemoGame(20261017);
  state = { ...state, tiles: state.tiles.map(t => [2, 3].includes(t.id) ? { ...t, ownerId: 'p1' } : t) };
  state = act(state, 'roll');
  assert.equal(applyAction(state, { type: 'upgrade_property', actorId: 'p1', tileId: 2 }).ok, false);
  const built = act(state, 'upgrade_property', { tileId: 3 });
  assert.equal(built.tiles[3].level, 1);
  assert.equal(applyAction(built, { type: 'upgrade_property', actorId: 'p1', tileId: 3 }).ok, false);
});

test('存款不能买地或建房；股票仅用存款且卖出回存款，现金不变', () => {
  const landed = arrived();
  const poor = { ...landed, players: landed.players.map(p => p.id === 'p1' ? { ...p, cash: 0, bankBalance: 10000 } : p) };
  assert.equal(applyAction(poor, { type: 'buy_property', actorId: 'p1' }).reason, 'INSUFFICIENT_FUNDS');
  let state = ended();
  const price = quoteMarket(state.market, 'FARM');
  const before = state.players[0];
  state = act(state, 'buy_stock', { stockId: 'FARM', quantity: 2 });
  assert.equal(state.players[0].cash, before.cash);
  assert.equal(state.players[0].bankBalance, before.bankBalance - price * 2 - stockFee(price * 2));
  assert.equal(state.players[0].holdings.FARM.quantity, 2);
  state = act(state, 'sell_stock', { stockId: 'FARM', quantity: 2 });
  assert.equal(state.players[0].cash, before.cash);
  assert.equal(state.players[0].bankBalance, before.bankBalance - 2 * stockFee(price * 2));
  const noDeposit = { ...state, players: state.players.map(p => p.id === 'p1' ? { ...p, bankBalance: 0 } : p) };
  assert.equal(applyAction(noDeposit, { type: 'buy_stock', actorId: 'p1', stockId: 'FARM', quantity: 1 }).ok, false);
});

test('银行存取守恒；抵押取得真实额度，贷款还款和利息正确', () => {
  let state = act(arrived(), 'buy_property');
  const original = state.players[0];
  state = act(state, 'deposit_bank', { amount: 100 });
  assert.equal(state.players[0].cash, original.cash - 100);
  assert.equal(state.players[0].bankBalance, original.bankBalance + 100);
  state = act(state, 'withdraw_bank', { amount: 100 });
  assert.equal(state.players[0].cash, original.cash);
  state = act(state, 'mortgage_property', { tileId: 3 });
  const limit = loanLimit(state, 'p1');
  assert.ok(limit > 0);
  assert.equal(applyAction(state, { type: 'borrow_loan', actorId: 'p1', amount: limit + 1 }).ok, false);
  state = act(state, 'borrow_loan', { amount: limit });
  assert.equal(state.players[0].loanBalance, limit);
  assert.equal(applyAction(state, { type: 'release_mortgage', actorId: 'p1', tileId: 3 }).ok, false);
  state = act(state, 'repay_loan', { amount: 10 });
  assert.equal(state.players[0].loanBalance, limit - 10);
  const beforeRound = state.players[0];
  state = act(state, 'end_turn');
  state = act(state, 'roll');
  if (state.phase === 'await_decision') state = act(state, 'decline_property');
  state = act(state, 'end_turn');
  assert.equal(state.players[0].cash, beforeRound.cash - Math.ceil((limit - 10) * 0.02));
  assert.equal(state.players[0].bankBalance, beforeRound.bankBalance + Math.floor(beforeRound.bankBalance * 0.01));
});

test('新规则/账户随存档往返，旧游戏继续允许现金股票和远程升级', () => {
  const state = act(ended(), 'buy_stock', { stockId: 'SEA', quantity: 1 });
  const loaded = deserializeGame(serializeGame(state)).game;
  assert.equal(loaded.stockAccount, 'bank');
  assert.equal(loaded.propertyVisitOnly, true);
  assert.deepEqual(loaded, state);
  let old = createGame(7, { ...DEFAULT_CONFIG, marketEnabled: true });
  old = { ...applyAction(old, { type: 'start_game', actorId: 'p1' }).state, phase: 'await_end_turn', tiles: old.tiles.map(t => t.id === 1 ? { ...t, ownerId: 'p1' } : t) };
  assert.equal(applyAction(old, { type: 'upgrade_property', actorId: 'p1', tileId: 1 }).ok, true);
  const traded = applyAction(old, { type: 'buy_stock', actorId: 'p1', stockId: 'SEA', quantity: 1 });
  assert.equal(traded.ok, true);
  assert.ok(traded.state.players[0].cash < old.players[0].cash);
  assert.equal(traded.state.players[0].bankBalance, undefined);
  assert.equal(Object.hasOwn(old, 'propertyVisitOnly'), false);
  assert.equal(Object.hasOwn(old, 'stockAccount'), false);
});

test('demo种子链接只选择真实随机序列，非法参数安全回到默认种子', async () => {
  const session = await import('../dist/demo3d/session.js');
  assert.equal(session.demoSeedFromSearch?.('?seed=42'), 42);
  assert.equal(session.demoSeedFromSearch?.('?seed=0'), 0);
  for (const raw of ['', '?seed=-1', '?seed=Infinity', '?seed=1.5', '?seed=4294967296']) {
    assert.equal(session.demoSeedFromSearch?.(raw), 20261017);
  }
});

test('可复现对局链接允许真实轮数配置，不改变初始账户与掷骰', async () => {
  const session = await import('../dist/demo3d/session.js');
  assert.equal(session.demoRoundsFromSearch?.('?rounds=24'), 24);
  for (const raw of ['', '?rounds=0', '?rounds=61', '?rounds=1.2']) assert.equal(session.demoRoundsFromSearch?.(raw), 12);
  const longer = createDemoGame(36, 24);
  assert.equal(longer.maxRounds, 24);
  assert.deepEqual(longer.players, createDemoGame(36).players);
  assert.equal(dispatchDemoAction(longer, { type: 'roll', actorId: 'p1' }).dieValue, dispatchDemoAction(createDemoGame(36), { type: 'roll', actorId: 'p1' }).dieValue);
});
