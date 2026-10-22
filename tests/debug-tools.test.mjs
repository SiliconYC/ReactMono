import test from 'node:test';
import assert from 'node:assert/strict';
import { applyAction, createGame, DEFAULT_CONFIG } from '../.test-dist/core/game.js';
import { LEVELS, levelConfig } from '../.test-dist/core/level-data.js';
import { serializeGame, deserializeGame, validateGameState } from '../.test-dist/core/save.js';
import { setDebugCash, simulateDebugRounds, chooseDebugSimulationAction } from '../.test-dist/core/debug-tools.js';
import { chooseComputerAction } from '../.test-dist/core/agent.js';

function started(mapId = 'classic-24', maxRounds = 60) {
  const game = createGame(261022, {
    ...levelConfig(mapId), maxRounds,
    players: [
      { id: 'p1', name: '甲', kind: 'human' },
      { id: 'p2', name: '乙', kind: 'computer', computerStyle: 'balanced' },
      { id: 'p3', name: '丙', kind: 'human' },
      { id: 'p4', name: '丁', kind: 'computer', computerStyle: 'aggressive' },
    ],
    automaticLiquidation: true, propertyVisitOnly: true,
    bankEnabled: true, marketEnabled: true, stockAccount: 'bank', loanEnabled: true,
    strategyEnabled: true, specialEnabled: !!levelConfig(mapId).facilityConfig,
  });
  return applyAction(game, { type: 'start_game', actorId: 'p1' }).state;
}

test('逐玩家现金赋值保留其他资产、随机状态、产权及历史，且可按旧格式保存', () => {
  let game = started();
  const before = structuredClone(game);
  for (const [i, player] of game.players.entries()) game = setDebugCash(game, player.id, i * 12345);
  assert.deepEqual(game.players.map(p => p.cash), [0, 12345, 24690, 37035]);
  assert.deepEqual(game.players.map(({ cash, ...rest }) => rest), before.players.map(({ cash, ...rest }) => rest));
  assert.deepEqual({ ...game, players: [] }, { ...before, players: [] });
  assert.deepEqual(deserializeGame(serializeGame(game)).game, game);
});

test('现金非法值、未知玩家、未开局和已结束对局拒绝且原局面不变', () => {
  const game = started();
  const before = structuredClone(game);
  for (const cash of [-1, 0.1, NaN, Infinity, 1_000_000_000_001, '10', null]) {
    assert.throws(() => setDebugCash(game, 'p1', cash));
  }
  assert.throws(() => setDebugCash(game, 'missing', 10));
  assert.throws(() => setDebugCash(createGame(3), 'p1', 10));
  const finished = simulateDebugRounds(started('classic-24', 1), 2).state;
  assert.throws(() => setDebugCash(finished, 'p1', 10));
  assert.deepEqual(game, before);
});

test('各注册地图从真实中途阶段推进指定轮数，保留真人与电脑身份且确定可复现', () => {
  for (const level of LEVELS) {
    const initial = started(level.map.id);
    const middle = applyAction(initial, { type: 'roll', actorId: 'p1' }).state;
    const before = structuredClone(middle);
    const result = simulateDebugRounds(middle, 2);
    assert.equal(result.state.round, 3, level.map.id);
    assert.equal(result.state.phase, 'await_roll');
    assert.equal(result.state.currentPlayerIndex, 0);
    assert.ok(result.actions > 0);
    assert.equal(result.state.status, 'playing');
    assert.deepEqual(result.state.players.map(p => [p.id, p.kind, p.computerStyle]), middle.players.map(p => [p.id, p.kind, p.computerStyle]));
    assert.notEqual(result.state.randomState, middle.randomState);
    assert.deepEqual(result.state.map, middle.map);
    assert.equal(result.state.maxRounds, middle.maxRounds);
    assert.deepEqual(result.state.events.slice(0, middle.events.length), middle.events);
    assert.ok(result.state.tiles.some(tile => tile.ownerId !== null), level.map.id);
    assert.deepEqual(simulateDebugRounds(middle, 2), result);
    assert.deepEqual(middle, before);
    validateGameState(result.state);
    assert.deepEqual(deserializeGame(serializeGame(result.state)).game, result.state);
  }
});

test('指定轮数不放宽原轮数上限，终局提前停止且再次运行不产生动作', () => {
  const game = started('classic-24', 1);
  const result = simulateDebugRounds(game, 50);
  assert.equal(result.state.status, 'finished');
  assert.equal(result.state.round, 1);
  assert.equal(result.state.maxRounds, 1);
  assert.equal(result.state.events.at(-1).type, 'game_finished');
  assert.deepEqual(simulateDebugRounds(result.state, 1), { state: result.state, actions: 0 });
  validateGameState(result.state);
});

test('后台代玩在真人与平衡电脑互换身份后保留逐轮动作、事件和最终经济结果', () => {
  for (const mapId of ['classic-24', 'lime-garden-30']) for (const cash of [3000, 1000000]) {
    const fresh = createGame(20261015, {
      ...levelConfig(mapId), initialCash: cash, maxRounds: 40,
      players: [
        { id: 'p1', name: '甲', kind: 'computer', computerStyle: 'balanced' },
        { id: 'p2', name: '乙', kind: 'computer', computerStyle: 'balanced' },
      ],
      automaticLiquidation: true, propertyVisitOnly: true, stockAccount: 'bank',
      bankEnabled: true, loanEnabled: true, marketEnabled: true, strategyEnabled: true,
      specialEnabled: !!levelConfig(mapId).facilityConfig,
    });
    const ready = applyAction(fresh, { type: 'start_game', actorId: 'p1' }).state;
    const comparable = state => ({
      ...state, players: state.players.map(({ kind, computerStyle, ...player }) => player),
    });
    for (const humanSeat of [0, 1]) {
      let reference = ready;
      let actual = {
        ...ready,
        players: ready.players.map((player, seat) => {
          if (seat !== humanSeat) return player;
          const { computerStyle, ...human } = player;
          return { ...human, kind: 'human' };
        }),
      };
      const initial = actual;
      const snapshot = structuredClone(actual);
      while (reference.status === 'playing') {
        const expected = simulateDebugRounds(reference, 1);
        const result = simulateDebugRounds(actual, 1);
        assert.equal(result.actions, expected.actions, `${mapId}/${cash}/human-seat-${humanSeat}/round-${reference.round}`);
        assert.deepEqual(comparable(result.state), comparable(expected.state));
        reference = expected.state;
        actual = result.state;
      }
      assert.equal(actual.status, 'finished');
      assert.equal(actual.players[humanSeat].kind, 'human');
      assert.equal(actual.players[humanSeat].computerStyle, undefined);
      assert.deepEqual(initial, snapshot);
      validateGameState(actual);
      assert.deepEqual(deserializeGame(serializeGame(actual)).game, actual);
    }
  }
});

test('旧存档中未声明风格的电脑在后台也采用平衡策略且不补写存档字段', () => {
  const initial = started();
  const legacy = {
    ...initial,
    players: initial.players.map(player => {
      if (player.id !== 'p2') return player;
      const { computerStyle, ...unstyled } = player;
      return unstyled;
    }),
  };
  const result = simulateDebugRounds(legacy, 20);
  const expected = simulateDebugRounds(initial, 20);
  assert.equal(result.actions, expected.actions);
  assert.deepEqual(result.state.events, expected.state.events);
  assert.deepEqual(result.state.tiles, expected.state.tiles);
  assert.deepEqual(result.state.players.map(({ computerStyle, ...player }) => player),
    expected.state.players.map(({ computerStyle, ...player }) => player));
  assert.equal(result.state.players[1].computerStyle, undefined);
  assert.deepEqual(deserializeGame(serializeGame(result.state)).game, result.state);
});

test('调试逐动作仅借用平衡电脑决策视图，原电脑接口仍拒绝真人并保留显式电脑风格', () => {
  let state = started('lime-garden-30', 40);
  const initial = structuredClone(state);
  const identity = state.players.map(({ id, kind, computerStyle }) => ({ id, kind, computerStyle }));
  while (state.status === 'playing') {
    const before = structuredClone(state);
    const player = state.players[state.currentPlayerIndex];
    const action = chooseDebugSimulationAction(state);
    assert.deepEqual(state, before);
    if (player.kind === 'human') {
      assert.equal(chooseComputerAction(state), null);
      const computerView = {
        ...state,
        players: state.players.map(entry => entry.id === player.id
          ? { ...entry, kind: 'computer', computerStyle: 'balanced' } : entry),
      };
      assert.deepEqual(action, chooseComputerAction(computerView));
    } else {
      assert.deepEqual(action, chooseComputerAction(state));
    }
    assert.ok(action);
    const result = applyAction(state, action);
    assert.equal(result.ok, true);
    state = result.state;
  }
  assert.deepEqual(state.players.map(({ id, kind, computerStyle }) => ({ id, kind, computerStyle })), identity);
  assert.deepEqual(simulateDebugRounds(initial, 40).state, state);
  assert.deepEqual(deserializeGame(serializeGame(state)).game, state);
});

test('轮数非法值、未开局与动作预算耗尽均不修改输入局面', () => {
  const game = started();
  const before = structuredClone(game);
  for (const rounds of [0, -1, 1.5, NaN, Infinity, 100001, '2']) assert.throws(() => simulateDebugRounds(game, rounds));
  assert.throws(() => simulateDebugRounds(createGame(1), 2));
  assert.throws(() => simulateDebugRounds(game, 2, 1), /上限/);
  assert.deepEqual(game, before);
});

test('现金设置不会复活破产玩家，模拟遇到破产胜负立即停止', () => {
  const initial = applyAction(createGame(1, { ...DEFAULT_CONFIG, strategyEnabled: true }), { type: 'start_game', actorId: 'p1' }).state;
  const game = {
    ...initial, currentPlayerIndex: 1, pendingDie: 1,
    players: initial.players.map((player, i) => i === 1 ? { ...player, cash: 0 } : player),
    tiles: initial.tiles.map(tile => tile.id === 1 ? { ...tile, ownerId: 'p1' } : tile),
  };
  validateGameState(game);
  const result = simulateDebugRounds(game, 20);
  assert.equal(result.state.status, 'finished');
  assert.equal(result.state.winnerId, 'p1');
  assert.equal(result.state.round, 1);
  assert.equal(result.state.players[1].bankrupt, true);
  assert.equal(result.state.events.at(-1).details.reason, 'bankruptcy');
  const continuing = started();
  const withBankrupt = {
    ...continuing,
    players: continuing.players.map((player, i) => i === 3 ? { ...player, bankrupt: true } : player),
  };
  const adjusted = setDebugCash(withBankrupt, 'p4', 500);
  assert.equal(adjusted.players[3].cash, 500);
  assert.equal(adjusted.players[3].bankrupt, true);
  validateGameState(adjusted);
});

test('Worker 接口返回独立最终快照，非法输入返回失败且可再次运行', { timeout: 10000 }, async t => {
  const { Worker } = await import('node:worker_threads');
  const workerUrl = new URL('../.test-dist/ui/debug-simulation.worker.js', import.meta.url);
  const worker = new Worker(`
    const { parentPort } = require('node:worker_threads');
    globalThis.self = { postMessage: value => parentPort.postMessage(value) };
    import(${JSON.stringify(workerUrl.href)}).then(() => {
      parentPort.on('message', data => self.onmessage({ data }));
    });
  `, { eval: true });
  t.after(() => worker.terminate());
  const exchange = request => new Promise((resolve, reject) => {
    const onError = error => { worker.off('message', onMessage); reject(error); };
    const onMessage = reply => { worker.off('error', onError); resolve(reply); };
    worker.once('message', onMessage);
    worker.once('error', onError);
    worker.postMessage(request);
  });
  const game = started('lime-garden-30');
  const before = structuredClone(game);
  const invalid = await exchange({ requestId: 17, game, rounds: -1 });
  assert.equal(invalid.requestId, 17);
  assert.equal(invalid.ok, false);
  assert.match(invalid.error, /轮数/);
  const valid = await exchange({ requestId: 18, game, rounds: 2 });
  assert.equal(valid.requestId, 18);
  assert.equal(valid.ok, true);
  assert.equal(valid.result.state.round, 3);
  assert.deepEqual(valid.result, simulateDebugRounds(game, 2));
  validateGameState(valid.result.state);
  assert.deepEqual(deserializeGame(serializeGame(valid.result.state)).game, valid.result.state);
  assert.deepEqual(game, before);
});
