import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, DEFAULT_CONFIG } from '../.test-dist/core/game.js';
import { serializeGame, deserializeGame } from '../.test-dist/core/save.js';

function fixture({ count = 3, due = 120, actorIndex = 1, cash = 0, bank = 0,
  holdings, owned = [], debt = 0, waived = false, mortgaged = false,
  automaticLiquidation = true, maxRounds = 8 } = {}) {
  const config = { ...DEFAULT_CONFIG, initialCash: 100, maxRounds,
    automaticLiquidation, bankEnabled: true, loanEnabled: true,
    marketEnabled: true, strategyEnabled: true,
    players: Array.from({ length: count }, (_, i) => ({ id: `p${i + 1}`, name: `玩家${i + 1}`, kind: 'human' })),
    tiles: [
      { id: 0, kind: 'start', title: '起点' },
      { id: 1, kind: 'property', title: '收租地', price: 100, rent: due },
      { id: 2, kind: 'property', title: '储备地', price: 200, rent: 15 },
      { id: 3, kind: 'property', title: '小储备地', price: 100, rent: 10 }
    ],
    eventRules: { tileIds: [], bonus: 120, fee: 60 },
    cardRules: { tileIds: [], rewardCash: 80, moveBonus: 2, maxHand: 3 }
  };
  const base = applyAction(createGame(2, config), { type: 'start_game', actorId: 'p1' }).state;
  const actorId = `p${actorIndex + 1}`;
  const state = { ...base, currentPlayerIndex: actorIndex, pendingRentWaiver: waived,
    players: base.players.map((p, i) => i === actorIndex
      ? { ...p, cash, bankBalance: bank, loanBalance: debt, ...(holdings ? { holdings } : {}) } : p),
    tiles: base.tiles.map(t => t.id === 1 ? { ...t, ownerId: 'p1', ...(mortgaged ? { mortgaged: true } : {}) }
      : owned.some(x => x.id === t.id) ? { ...t, ownerId: actorId, ...owned.find(x => x.id === t.id) } : t)
  };
  serializeGame(state);
  return state;
}

function roll(state) {
  const before = structuredClone(state);
  const result = applyAction(state, { type: 'roll', actorId: state.players[state.currentPlayerIndex].id });
  assert.equal(result.ok, true);
  assert.deepEqual(state, before);
  assert.equal(result.events.filter(e => e.type === 'rent_paid').length, 1);
  assert.deepEqual(deserializeGame(serializeGame(result.state)).game, result.state);
  return result;
}

function event(result, type) { return result.events.find(e => e.type === type); }

for (const [cash, paid, bankrupt] of [[0, 0, true], [119, 119, true], [120, 120, false], [121, 120, false]]) {
  test(`租金120：现金${cash}，实付${paid}，破产=${bankrupt}`, () => {
    const s = fixture({ cash });
    const r = roll(s);
    assert.equal(r.state.players[1].cash, cash - paid);
    assert.equal(r.state.players[0].cash, 100 + paid);
    assert.equal(r.state.players[1].bankrupt, bankrupt);
    assert.equal(event(r, 'rent_paid').details.amount, paid);
    assert.equal(r.state.currentPlayerIndex, bankrupt ? 2 : 1);
    assert.equal(r.state.phase, bankrupt ? 'await_roll' : 'await_end_turn');
    assert.equal(r.state.players.reduce((sum, p) => sum + p.cash, 0), s.players.reduce((sum, p) => sum + p.cash, 0));
  });
}

for (const [bank, remaining, bankrupt] of [[109, 0, true], [110, 0, false], [111, 1, false]]) {
  test(`现金10与存款${bank}的精确补款边界`, () => {
    const r = roll(fixture({ cash: 10, bank }));
    assert.equal(r.state.players[1].cash, 0);
    assert.equal(r.state.players[1].bankBalance, remaining);
    assert.equal(r.state.players[1].bankrupt, bankrupt);
    assert.equal(event(r, 'bank_withdrawn').details.amount, Math.min(bank, 110));
    assert.equal(r.state.players[0].cash, 100 + Math.min(120, 10 + bank));
  });
}

test('现金足够时不提存款、不卖股票和地产', () => {
  const r = roll(fixture({ cash: 120, bank: 50, holdings: { SEA: { quantity: 1, costBasis: 81 } }, owned: [{ id: 2 }] }));
  assert.equal(r.state.players[1].bankBalance, 50);
  assert.equal(r.state.players[1].holdings.SEA.quantity, 1);
  assert.equal(r.state.tiles[2].ownerId, 'p2');
  assert.equal(r.events.some(e => ['bank_withdrawn', 'stock_liquidated', 'property_liquidated'].includes(e.type)), false);
});

test('股票清算计入手续费：80减1而非凭空补足租金', () => {
  const r = roll(fixture({ cash: 40, holdings: { SEA: { quantity: 1, costBasis: 81 } } }));
  assert.equal(event(r, 'stock_liquidated').details.amount, 79);
  assert.equal(event(r, 'rent_paid').details.amount, 119);
  assert.equal(r.state.players[0].cash, 219);
  assert.equal(r.state.players[1].cash, 0);
  assert.equal(r.state.players[1].bankrupt, true);
  assert.deepEqual(r.state.players[1].holdings, {});
});

test('股票清算恰好支付后为零但不破产', () => {
  const r = roll(fixture({ cash: 41, holdings: { SEA: { quantity: 1, costBasis: 81 } } }));
  assert.equal(r.state.players[1].cash, 0);
  assert.equal(r.state.players[1].bankrupt, false);
  assert.equal(r.state.players[0].cash, 220);
});

test('多股票按固定顺序清算，顺序不受持仓对象顺序影响', () => {
  const r = roll(fixture({ due: 100, holdings: { FARM: { quantity: 1, costBasis: 56 }, SEA: { quantity: 1, costBasis: 81 } } }));
  assert.equal(r.state.players[1].cash, 33);
  assert.equal(r.state.players[0].cash, 200);
  assert.deepEqual(r.events.filter(e => e.type === 'stock_liquidated').map(e => [e.details.stockId, e.details.amount]), [['SEA', 79], ['FARM', 54]]);
});

test('银行结算股票在紧急清算时用于支付租金且不重复入账', () => {
  const s = { ...fixture({ cash: 10, bank: 31, holdings: { SEA: { quantity: 1, costBasis: 81 } } }), stockAccount: 'bank' };
  serializeGame(s);
  const r = roll(s);
  assert.equal(r.state.players[1].cash, 0);
  assert.equal(r.state.players[1].bankBalance, 0);
  assert.equal(r.state.players[1].bankrupt, false);
  assert.equal(r.state.players[0].cash, 220);
});

test('价值1的股票扣最小手续费后净额0，仍正确清仓并破产', () => {
  const s = fixture({ due: 1, holdings: { SEA: { quantity: 1, costBasis: 1 } } });
  const r = roll({ ...s, market: { ...s.market, prices: { ...s.market.prices, SEA: 1 } } });
  assert.equal(event(r, 'stock_liquidated').details.amount, 0);
  assert.equal(r.state.players[0].cash, 100);
  assert.equal(r.state.players[1].bankrupt, true);
  assert.deepEqual(r.state.players[1].holdings, {});
});

test('依次现金、存款、股票、土地，只出售足够的资产', () => {
  const r = roll(fixture({ due: 250, cash: 10, bank: 20, holdings: { SEA: { quantity: 1, costBasis: 81 } }, owned: [{ id: 2 }, { id: 3 }] }));
  assert.equal(r.state.players[1].cash, 9);
  assert.equal(r.state.players[1].bankBalance, 0);
  assert.deepEqual(r.state.players[1].holdings, {});
  assert.equal(r.state.tiles[2].ownerId, null);
  assert.equal(r.state.tiles[3].ownerId, 'p2');
  assert.equal(r.state.players[0].cash, 350);
  assert.deepEqual(r.events.filter(e => ['bank_withdrawn', 'stock_liquidated', 'property_liquidated', 'rent_paid'].includes(e.type)).map(e => e.type),
    ['bank_withdrawn', 'stock_liquidated', 'property_liquidated', 'rent_paid']);
});

test('升级地产回售75%地价与50%已付升级费后恰好支付', () => {
  const r = roll(fixture({ due: 280, owned: [{ id: 2, level: 2 }] }));
  assert.equal(event(r, 'property_liquidated').details.amount, 280);
  assert.equal(r.state.players[1].cash, 0);
  assert.equal(r.state.players[1].bankrupt, false);
  assert.equal(r.state.tiles[2].ownerId, null);
  assert.equal(r.state.tiles[2].level, 0);
});

for (const [due, paid, bankrupt] of [[205, 205, false], [206, 205, true]]) {
  test(`抵押清算先还银行30，剩45支付租金${due}`, () => {
    const r = roll(fixture({ due, cash: 10, debt: 30, owned: [{ id: 2 }, { id: 3, mortgaged: true }] }));
    assert.equal(r.state.players[0].cash, 100 + paid);
    assert.equal(r.state.players[1].cash, 0);
    assert.equal(r.state.players[1].loanBalance, 0);
    assert.equal(r.state.players[1].bankrupt, bankrupt);
    assert.equal(event(r, 'loan_default').details.recovered, 30);
    assert.equal(event(r, 'loan_default').details.writtenOff, 0);
    assert.equal(event(r, 'rent_paid').details.amount, paid);
    assert.ok(r.state.tiles.filter(t => [2, 3].includes(t.id)).every(t => t.ownerId === null && t.mortgaged === undefined));
  });
}

test('零债务的抵押地产可直接清算，不遗留抵押标记', () => {
  const r = roll(fixture({ due: 75, owned: [{ id: 3, mortgaged: true }] }));
  assert.equal(r.state.players[1].bankrupt, false);
  assert.equal(r.state.tiles[3].mortgaged, undefined);
  assert.equal(event(r, 'loan_default'), undefined);
});

for (const mode of ['零租金', '免租卡', '抵押免租']) {
  test(`${mode}不会把零现金玩家错误破产或强制出售资产`, () => {
    const r = roll(fixture({ due: mode === '零租金' ? 0 : 120, waived: mode === '免租卡', mortgaged: mode === '抵押免租',
      bank: 30, holdings: { SEA: { quantity: 1, costBasis: 81 } }, owned: [{ id: 2 }] }));
    assert.equal(r.state.players[1].bankrupt, false);
    assert.equal(r.state.players[1].bankBalance, 30);
    assert.equal(r.state.players[1].holdings.SEA.quantity, 1);
    assert.equal(r.state.tiles[2].ownerId, 'p2');
    assert.equal(event(r, 'rent_paid').details.amount, 0);
    assert.equal(r.state.pendingRentWaiver, false);
  });
}

for (const count of [2, 3, 4]) {
  test(`${count}人支付不足后立即破产并推进到有效后继状态`, () => {
    const r = roll(fixture({ count }));
    assert.equal(r.state.players[1].bankrupt, true);
    assert.equal(r.state.status, count === 2 ? 'finished' : 'playing');
    assert.equal(r.state.phase, count === 2 ? 'finished' : 'await_roll');
    assert.equal(r.state.winnerId, count === 2 ? 'p1' : null);
    assert.equal(r.events.filter(e => e.type === 'player_bankrupt').length, 1);
    const repeated = applyAction(r.state, { type: 'roll', actorId: 'p2' });
    assert.equal(repeated.ok, false);
    assert.equal(repeated.state, r.state);
  });
}

test('四人局破产自动跳过既有破产席位', () => {
  let s = fixture({ count: 4 });
  s = { ...s, players: s.players.map((p, i) => i === 2 ? { ...p, cash: 0, bankrupt: true } : p) };
  serializeGame(s);
  const r = roll(s);
  assert.equal(r.state.currentPlayerIndex, 3);
  assert.equal(r.state.status, 'playing');
});

test('跨轮破产只结一次存款利息、贷款利息和行情', () => {
  let s = fixture({ actorIndex: 2 });
  s = { ...s, players: s.players.map((p, i) => i === 0 ? { ...p, bankBalance: 10000 } : i === 1 ? { ...p, loanBalance: 30 } : p),
    tiles: s.tiles.map(t => t.id === 3 ? { ...t, ownerId: 'p2', mortgaged: true } : t) };
  serializeGame(s);
  const r = roll(s);
  assert.equal(r.state.round, 2);
  assert.equal(r.state.currentPlayerIndex, 0);
  assert.equal(r.state.players[0].bankBalance, 10100);
  assert.equal(r.state.players[1].cash, 99);
  assert.equal(r.state.players[1].loanBalance, 30);
  assert.equal(r.events.filter(e => e.type === 'bank_interest').length, 1);
  assert.equal(r.events.filter(e => e.type === 'loan_interest').length, 1);
  assert.equal(r.state.bank.lastInterestRound, 2);
  assert.equal(r.state.loan.lastInterestRound, 2);
  assert.equal(r.state.market.round, 2);
  const next = applyAction({ ...r.state, phase: 'await_end_turn' }, { type: 'end_turn', actorId: 'p1' });
  assert.equal(next.ok, true);
  assert.equal(next.state.round, 2);
  assert.equal(next.state.players[0].bankBalance, 10100);
  assert.equal(next.events.some(e => ['bank_interest', 'loan_interest'].includes(e.type)), false);
});

test('到回合上限的跨轮破产直接结束，不额外结息', () => {
  const r = roll(fixture({ actorIndex: 2, maxRounds: 1 }));
  assert.equal(r.state.status, 'finished');
  assert.equal(r.state.round, 1);
  assert.equal(r.state.bank.lastInterestRound, 1);
  assert.equal(r.state.loan.lastInterestRound, 1);
  assert.equal(r.state.market.round, 1);
});

test('合法大额现金的租金转账仍可保存', () => {
  let s = fixture({ cash: 120 });
  s = { ...s, players: s.players.map((p, i) => i === 0 ? { ...p, cash: 999999999999 } : p) };
  serializeGame(s);
  const result = applyAction(s, { type: 'roll', actorId: 'p2' });
  assert.equal(result.ok, true);
  assert.equal(result.state.players[0].cash, 1000000000119);
  assert.doesNotThrow(() => serializeGame(result.state));
});

test('合法最大银行存款不应阻止其他玩家跨轮破产', () => {
  let s = fixture({ actorIndex: 2 });
  s = { ...s, players: s.players.map((p, i) => i === 0 ? { ...p, bankBalance: 1000000000000 } : p) };
  serializeGame(s);
  let result;
  assert.doesNotThrow(() => { result = applyAction(s, { type: 'roll', actorId: 'p3' }); });
  assert.equal(result.ok, true);
  assert.equal(result.state.players[2].bankrupt, true);
  assert.equal(result.state.currentPlayerIndex, 0);
  assert.equal(result.state.players[0].bankBalance, 1000000000000);
  assert.equal(result.events.filter(e => e.type === 'bank_interest').length, 0);
  assert.doesNotThrow(() => serializeGame(result.state));
});

test('银行距离上限仅1时只实际发息1并记录真实金额', () => {
  let s = fixture({ actorIndex: 2 });
  s = { ...s, players: s.players.map((p, i) => i === 0 ? { ...p, bankBalance: 999999999999 } : p) };
  serializeGame(s);
  let result;
  assert.doesNotThrow(() => { result = applyAction(s, { type: 'roll', actorId: 'p3' }); });
  assert.equal(result.ok, true);
  assert.equal(result.state.players[0].bankBalance, 1000000000000);
  assert.equal(event(result, 'bank_interest').details.amount, 1);
  assert.doesNotThrow(() => serializeGame(result.state));
});

test('大额租金差1时股票清算不应因为临时现金超过银行上限而失败', () => {
  let s = fixture({ cash: 999999999999, holdings: { SEA: { quantity: 1, costBasis: 81 } } });
  s = { ...s, tiles: s.tiles.map(t => t.id === 1 ? { ...t, rent: 1000000000000, levelRents: [1000000000000, 1000000000000, 1000000000000] } : t) };
  serializeGame(s);
  let result;
  assert.doesNotThrow(() => { result = applyAction(s, { type: 'roll', actorId: 'p2' }); });
  assert.equal(result.ok, true);
  assert.equal(result.state.players[1].cash, 78);
  assert.equal(result.state.players[1].bankrupt, false);
  assert.equal(result.state.players[0].cash, 1000000000100);
  assert.doesNotThrow(() => serializeGame(result.state));
});

test('总毛资产恰好为安全整数上限时可保存且租金仍精确守恒', () => {
  let s = fixture({ cash: 120 });
  s = { ...s, players: s.players.map((p, i) => i === 0 ? { ...p, cash: Number.MAX_SAFE_INTEGER - 320 } : p) };
  assert.doesNotThrow(() => serializeGame(s));
  const r = roll(s);
  assert.equal(r.state.players[0].cash, Number.MAX_SAFE_INTEGER - 200);
  assert.equal(r.state.players[1].cash, 0);
  assert.equal(r.state.players[1].bankrupt, false);
});

test('导入时单钱包安全但合计毛资产超安全整数也必须拒绝', () => {
  let s = fixture();
  s = { ...s, players: s.players.map((p, i) => i === 0 ? { ...p, cash: Number.MAX_SAFE_INTEGER - 199 } : p) };
  assert.throws(() => serializeGame(s), /安全|资产/);
});

test('合法总账新增收益超安全范围时明确失败且不改变原态', () => {
  let s = fixture();
  s = { ...s, currentPlayerIndex: 0, players: s.players.map((p, i) => i === 0
    ? { ...p, cash: Number.MAX_SAFE_INTEGER - 200, cards: { ...p.cards, reward: 1 } } : p) };
  assert.doesNotThrow(() => serializeGame(s));
  const before = structuredClone(s);
  assert.throws(() => applyAction(s, { type: 'use_card', actorId: 'p1', cardType: 'reward' }), /安全|资产/);
  assert.deepEqual(s, before);
});

test('大额股票部分卖出按精确成本分摊，不在中间乘法丢1元', () => {
  const s = { ...fixture({ holdings: { SEA: { quantity: 1000000, costBasis: 999999999000 } } }), phase: 'await_end_turn' };
  const r = applyAction(s, { type: 'sell_stock', actorId: 'p2', stockId: 'SEA', quantity: 999000 });
  assert.equal(r.ok, true);
  assert.equal(r.state.players[1].holdings.SEA.costBasis, 999999999);
  assert.equal(r.state.players[1].cash, 79520400);
  assert.equal(event(r, 'stock_sold').details.realized, -998920478601);
});

function voluntaryState(options = {}) {
  return { ...fixture({ cash: 1000000000000, bank: 1,
    holdings: { SEA: { quantity: 1, costBasis: 81 } }, owned: [{ id: 3, mortgaged: true }], ...options }),
    phase: 'await_end_turn' };
}

function voluntaryAction(state, action) {
  const before = structuredClone(state);
  const result = applyAction(state, { ...action, actorId: 'p2' });
  assert.deepEqual(state, before);
  if (result.ok) assert.deepEqual(deserializeGame(serializeGame(result.state)).game, result.state);
  return result;
}

test('现金已达1e12仍可提取1元存款且银行现金守恒', () => {
  const r = voluntaryAction(voluntaryState(), { type: 'withdraw_bank', amount: 1 });
  assert.equal(r.ok, true);
  assert.equal(r.state.players[1].cash, 1000000000001);
  assert.equal(r.state.players[1].bankBalance, 0);
});

test('现金已达1e12仍可凭抵押借款1元并增加对应债务', () => {
  const r = voluntaryAction(voluntaryState(), { type: 'borrow_loan', amount: 1 });
  assert.equal(r.ok, true);
  assert.equal(r.state.players[1].cash, 1000000000001);
  assert.equal(r.state.players[1].loanBalance, 1);
  assert.equal(r.state.players[1].bankBalance, 1);
});

test('现金已达1e12仍可卖股收到扣除手续费的79元', () => {
  const r = voluntaryAction(voluntaryState(), { type: 'sell_stock', stockId: 'SEA', quantity: 1 });
  assert.equal(r.ok, true);
  assert.equal(r.state.players[1].cash, 1000000000079);
  assert.equal(r.state.players[1].bankBalance, 1);
  assert.deepEqual(r.state.players[1].holdings, {});
  assert.equal(event(r, 'stock_sold').details.fee, 1);
});

test('现金高于1e12仍可存入1元且剩余现金保持精确', () => {
  const r = voluntaryAction(voluntaryState({ cash: 1000000000002 }), { type: 'deposit_bank', amount: 1 });
  assert.equal(r.ok, true);
  assert.equal(r.state.players[1].cash, 1000000000001);
  assert.equal(r.state.players[1].bankBalance, 2);
});

test('银行满1e12时拒绝卖股入账并保持现金存款持仓原态', () => {
  const s = { ...voluntaryState({ bank: 1000000000000 }), stockAccount: 'bank' };
  const r = voluntaryAction(s, { type: 'sell_stock', stockId: 'SEA', quantity: 1 });
  assert.equal(r.ok, false);
  assert.equal(r.reason, 'INVALID_PHASE');
  assert.equal(r.state, s);
  assert.deepEqual(r.events, []);
});
