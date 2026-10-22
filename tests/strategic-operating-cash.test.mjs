import test from 'node:test';
import assert from 'node:assert/strict';
import { applyAction, createGame } from '../.test-dist/core/game.js';
import { levelConfig } from '../.test-dist/core/level-data.js';
import { chooseComputerAction } from '../.test-dist/core/agent.js';
import { chooseDebugSimulationAction } from '../.test-dist/core/debug-tools.js';

function started(style = 'balanced', kind = 'computer', extra = {}) {
  const state = createGame(20261015, {
    ...levelConfig('lime-garden-30'),
    players: [
      { id: 'p1', name: '甲', kind, ...(kind === 'computer' ? { computerStyle: style } : {}) },
      { id: 'p2', name: '乙', kind: 'computer', computerStyle: style },
    ],
    bankEnabled: true, propertyVisitOnly: true, strategyEnabled: true,
    ...extra,
  });
  return act(state, { type: 'start_game', actorId: 'p1' });
}
function act(state, action) {
  const result = applyAction(state, action);
  assert.equal(result.ok, true, JSON.stringify(action));
  return result.state;
}
function finance(state, cash, bankBalance) {
  return { ...state, players: state.players.map((p, i) => i === 0 ? { ...p, cash, bankBalance } : p) };
}
function choose(state) {
  return state.players[0].kind === 'human' ? chooseDebugSimulationAction(state) : chooseComputerAction(state);
}
function endTurnState(state) {
  state = act({ ...state, pendingDie: 1 }, { type: 'roll', actorId: 'p1' });
  return act(state, { type: 'decline_property', actorId: 'p1' });
}

test('银行有经营资金时，普通电脑与后台代玩为后续购地取款且保留原身份', () => {
  for (const kind of ['computer', 'human']) {
    let state = finance(endTurnState(started('balanced', kind)), 350, 1000);
    const before = structuredClone(state);
    const action = choose(state);
    assert.equal(action.type, 'withdraw_bank');
    state = act(state, action);
    assert.ok(state.players[0].cash >= 565, '可覆盖地图最贵未售地产245及平衡储备320');
    assert.equal(state.players[0].cash + state.players[0].bankBalance, 1350);
    assert.equal(state.players[0].kind, kind);
    assert.deepEqual(before.players[0], { ...state.players[0], cash: 350, bankBalance: 1000 });
    assert.equal(choose(state).type, 'end_turn');
    state = act(state, { type: 'end_turn', actorId: 'p1' });
    state = act({ ...state, pendingDie: 1 }, { type: 'roll', actorId: 'p2' });
    if (state.phase === 'await_decision') state = act(state, { type: 'decline_property', actorId: 'p2' });
    state = act(state, { type: 'end_turn', actorId: 'p2' });
    state = { ...state, pendingDie: 1, players: state.players.map((p, i) => i === 0 ? { ...p, position: 28 } : p) };
    state = act(state, { type: 'roll', actorId: 'p1' });
    assert.equal(choose(state).type, 'buy_property');
    state = act(state, choose(state));
    assert.ok(state.players[0].cash >= 320);
  }
});

test('只有当前到访可建设地产才动用银行资金，取款不会重开已用建设机会', () => {
  let state = started();
  state = { ...state, tiles: state.tiles.map(t => t.kind === 'property' ? { ...t, ownerId: 'p1', level: 0 } : t) };
  state = act({ ...state, pendingDie: 1 }, { type: 'roll', actorId: 'p1' });
  state = finance(state, 350, 1000);
  const offsite = { ...state, players: state.players.map((p, i) => i === 0 ? { ...p, position: 0 } : p) };
  assert.equal(choose(offsite).type, 'end_turn');
  assert.equal(choose(state).type, 'withdraw_bank');
  state = act(state, choose(state));
  assert.deepEqual(choose(state), { type: 'upgrade_property', actorId: 'p1', tileId: 1 });
  state = act(state, choose(state));
  assert.equal(state.tiles[1].level, 1);
  assert.ok(state.players[0].cash >= 320);
  assert.equal(choose(state).type, 'end_turn');
  const noVisit = { ...finance(state, 350, 1000), players: state.players.map((p, i) => i === 0 ? { ...p, position: 0, cash: 350, bankBalance: 1000 } : p) };
  assert.equal(choose(noVisit).type, 'end_turn');
});

test('各风格保留自己的购地储备，不在购地阶段非法取款或无钱时循环取款', () => {
  for (const [style, target] of [['conservative', 895], ['balanced', 565], ['aggressive', 280]]) {
    let state = finance(endTurnState(started(style)), 200, 1000);
    state = { ...state, players: state.players.map((p, i) => i === 1 ? { ...p, cash: 1200 } : p) };
    const action = choose(state);
    assert.equal(action.type, 'withdraw_bank');
    state = act(state, action);
    assert.equal(state.players[0].cash, target);
    assert.notEqual(choose(state).type, 'withdraw_bank');
    const decision = { ...finance(state, 0, 1000), phase: 'await_decision' };
    assert.equal(choose(decision).type, 'decline_property');
  }
  const noFunds = finance(endTurnState(started()), 350, 0);
  assert.equal(choose(noFunds).type, 'end_turn');
});

test('存款后同回合不取款，经营预算不会被再次存入银行', () => {
  let state = finance(endTurnState(started()), 100, 1000);
  state = act(state, { type: 'deposit_bank', actorId: 'p1', amount: 20 });
  assert.notEqual(choose(state).type, 'withdraw_bank');
  state = finance(endTurnState(started()), 2500, 1000);
  state = { ...state, tiles: state.tiles.map(t => t.id === 29 ? { ...t, price: 2000, rent: 400 } : t) };
  for (let count = 0; count < 4; count++) {
    const action = choose(state);
    if (action.type === 'end_turn') break;
    state = act(state, action);
  }
  assert.ok(state.players[0].cash >= 2320);
  assert.equal(choose(state).type, 'end_turn');
});

test('现金股票账户不会花掉已筹备的购地预算', () => {
  let state = finance(endTurnState(started('balanced', 'computer', { marketEnabled: true })), 2320, 1000);
  state = { ...state, tiles: state.tiles.map(t => t.id === 29 ? { ...t, price: 2000, rent: 400 } : t) };
  assert.equal(choose(state).type, 'end_turn');
});

test('同一次取款同时覆盖到访升级及下一次购地，建设后仍保留经营预算', () => {
  let state = started();
  state = { ...state, tiles: state.tiles.map(t => t.id === 1 ? { ...t, ownerId: 'p1' } : t) };
  state = act({ ...state, pendingDie: 1 }, { type: 'roll', actorId: 'p1' });
  state = finance(state, 565, 1000);
  state = { ...state, players: state.players.map((p, i) => i === 1 ? { ...p, cash: 1685 } : p) };
  assert.deepEqual(choose(state), { type: 'withdraw_bank', actorId: 'p1', amount: 60 });
  state = act(state, choose(state));
  assert.equal(choose(state).type, 'upgrade_property');
  state = act(state, choose(state));
  assert.equal(state.players[0].cash, 565);
  assert.equal(choose(state).type, 'end_turn');
});

test('银行接近或达到存款上限时，电脑只存剩余容量且不生成被拒绝动作', () => {
  for(const [bankBalance,deposit] of [[1_000_000_000_000,0],[999_999_999_900,100]]){
    let state=finance(endTurnState(started()),2000,bankBalance);
    const action=choose(state);
    assert.equal(action.type,deposit>0?'deposit_bank':'end_turn');
    if(deposit>0){
      assert.equal(action.amount,deposit);
      state=act(state,action);
      assert.equal(state.players[0].bankBalance,1_000_000_000_000);
      assert.equal(choose(state).type,'end_turn');
    }else state=act(state,action);
  }
});
