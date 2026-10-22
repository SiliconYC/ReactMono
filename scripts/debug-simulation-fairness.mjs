import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { applyAction, createGame, netWorth } from '../.test-dist/core/game.js';
import { chooseComputerAction, choosePhaseAction } from '../.test-dist/core/agent.js';
import { levelConfig } from '../.test-dist/core/level-data.js';
import { simulateDebugRounds, chooseDebugSimulationAction } from '../.test-dist/core/debug-tools.js';

const label = process.argv[2] ?? 'current';
if (!/^[a-z0-9-]+$/.test(label)) throw new Error('输出标签只能使用小写字母、数字或连字符');
const file = `artifacts/simulation-fairness/${label}.json`;
if (existsSync(file)) throw new Error(`保留已有证据，请使用新的输出标签：${file}`);
const sampleCount = Number(process.env.FAIRNESS_SEEDS ?? 64);
assert.ok(Number.isSafeInteger(sampleCount) && sampleCount > 0 && sampleCount <= 1000);
const seeds = [
  { family: 'ui-default', seed: 20261015 },
  ...Array.from({ length: 16 }, (_, i) => ({ family: 'consecutive', seed: i + 1 })),
  ...Array.from({ length: sampleCount }, (_, i) => {
    const hash = createHash('sha256').update(`ReactMono-debug-fairness-v1:${i}`).digest();
    return { family: 'sha256-dispersed', seed: hash.readUInt32LE(0) || 1 };
  }),
];
const modes = ['legacy-human-first', 'legacy-human-second', 'both-basic', 'both-balanced'];
const rows = [];
const started = performance.now();
function startedGame(seed, map, initialCash, humanSeat = 0, bothComputer = false) {
  const fresh = createGame(seed, {
    ...levelConfig(map), initialCash, maxRounds: 40,
    players: [0, 1].map(seat => ({
      id: `p${seat + 1}`, name: seat === 0 ? '甲' : '乙',
      kind: !bothComputer && seat === humanSeat ? 'human' : 'computer',
      ...(!bothComputer && seat === humanSeat ? {} : { computerStyle: 'balanced' }),
    })),
    automaticLiquidation: true, propertyVisitOnly: true, stockAccount: 'bank',
    bankEnabled: true, loanEnabled: true, marketEnabled: true, strategyEnabled: true,
    specialEnabled: !!levelConfig(map).facilityConfig,
  });
  const ready = applyAction(fresh, { type: 'start_game', actorId: 'p1' });
  assert.equal(ready.ok, true);
  return ready.state;
}
function experiment(initial, mode) {
  let state = initial;
  const actionCounts = { p1: {}, p2: {} }, trace = createHash('sha256');
  let actions = 0;
  while (state.status === 'playing') {
    assert.ok(actions < 100000, '动作预算耗尽');
    const player = state.players[state.currentPlayerIndex];
    const action = mode === 'actual-debug' ? chooseDebugSimulationAction(state)
      : mode === 'both-basic' ? choosePhaseAction(state, 200)
      : player.kind === 'computer' ? chooseComputerAction(state, { reserveCash: 200 })
      : choosePhaseAction(state, 200);
    assert.ok(action);
    const result = applyAction(state, action);
    assert.equal(result.ok, true, JSON.stringify(action));
    actionCounts[player.id][action.type] = (actionCounts[player.id][action.type] ?? 0) + 1;
    trace.update(JSON.stringify(action) + '\n');
    state = result.state;
    actions++;
  }
  return { state, actions, actionCounts, traceSha256: trace.digest('hex') };
}
function summarize(state, actions) {
  return {
    winnerId: state.winnerId, reason: state.events.at(-1).details.reason, rounds: state.round, actions,
    players: state.players.map(p => ({
      id: p.id, kind: p.kind, style: p.computerStyle ?? null, cash: p.cash,
      bankBalance: p.bankBalance ?? 0, loanBalance: p.loanBalance ?? 0,
      netWorth: netWorth(state, p.id), bankrupt: p.bankrupt,
    })),
  };
}
for (const map of ['classic-24', 'lime-garden-30']) {
  for (const cash of [3000, 1000000]) {
    for (const { family, seed } of seeds) {
      for (const mode of modes) {
        const initial = startedGame(seed, map, cash, mode === 'legacy-human-second' ? 1 : 0, mode === 'both-balanced');
        const result = experiment(initial, mode);
        rows.push({ map, cash, family, seed, mode,
          actualStrategies: mode === 'both-basic' ? ['basic-200', 'basic-200']
            : mode === 'both-balanced' ? ['balanced', 'balanced']
            : mode === 'legacy-human-second' ? ['balanced', 'basic-200'] : ['basic-200', 'balanced'],
          ...summarize(result.state, result.actions), actionCounts: result.actionCounts,
          traceSha256: result.traceSha256,
        });
      }
      const initial = startedGame(seed, map, cash);
      const current = simulateDebugRounds(initial, 40);
      const traced = experiment(initial, 'actual-debug');
      assert.deepEqual(traced.state, current.state);
      assert.equal(traced.actions, current.actions);
      rows.push({ map, cash, family, seed, mode: 'actual-debug', actualStrategies: ['balanced', 'balanced'],
        ...summarize(current.state, current.actions), actionCounts: traced.actionCounts,
        traceSha256: traced.traceSha256 });
    }
    console.log(`${label}: ${map} cash=${cash} 完成 ${seeds.length * (modes.length + 1)} 局`);
  }
}
const groups = [];
for (const map of ['classic-24', 'lime-garden-30']) for (const cash of [3000, 1000000]) {
  for (const family of ['ui-default', 'consecutive', 'sha256-dispersed']) for (const mode of [...modes, 'actual-debug']) {
    const subset = rows.filter(row => row.map === map && row.cash === cash && row.family === family && row.mode === mode);
    groups.push({ map, cash, family, mode, games: subset.length,
      p1Wins: subset.filter(row => row.winnerId === 'p1').length,
      p2Wins: subset.filter(row => row.winnerId === 'p2').length,
      draws: subset.filter(row => row.winnerId === null).length,
      bankruptcy: subset.filter(row => row.reason === 'bankruptcy').length,
      roundLimit: subset.filter(row => row.reason === 'round_limit').length,
      meanNetWorth: [0, 1].map(seat => subset.reduce((sum, row) => sum + row.players[seat].netWorth, 0) / subset.length),
      meanActions: subset.reduce((sum, row) => sum + row.actions, 0) / subset.length,
      totalDeposits: [0, 1].map(seat => subset.reduce((sum, row) => sum + (row.actionCounts?.[`p${seat + 1}`]?.deposit_bank ?? 0), 0)),
    });
  }
}
mkdirSync('artifacts/simulation-fairness', { recursive: true });
writeFileSync(file, JSON.stringify({
  schemaVersion: 1, label, maxRounds: 40, requestedRounds: 40,
  seedDesign: 'UI默认种子；1至16连续小种子；sha256(ReactMono-debug-fairness-v1:i)前4字节小端uint32的分散种子',
  policyDesign: 'legacy模式冻结修复前的调试选择规则；both-basic和both-balanced为同策略控制；actual-debug运行生产入口',
  seeds, groups, rows, elapsedMs: Math.round(performance.now() - started),
}, null, 2) + '\n');
console.log(JSON.stringify({ file, games: rows.length, elapsedMs: Math.round(performance.now() - started),
  dispersed: groups.filter(group => group.family === 'sha256-dispersed') }));
