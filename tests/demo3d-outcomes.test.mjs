import test from 'node:test';
import assert from 'node:assert/strict';
import { applyAction, createGame, DEFAULT_CONFIG, nextDie } from '../dist/core/game.js';
import { outcomeSequence } from '../dist/demo3d/outcomes.js';

function started(config = DEFAULT_CONFIG) {
  const setup = createGame(17, config);
  const result = applyAction(setup, { type: 'start_game', actorId: 'p1' });
  assert.equal(result.ok, true);
  return result.state;
}

function bankruptLanding(config = DEFAULT_CONFIG) {
  const base = started(config);
  const die = nextDie(base.randomState).value;
  const at = {
    ...base,
    players: base.players.map((player, index) => index === 0
      ? { ...player, cash: 5, position: (1 - die + base.tiles.length) % base.tiles.length }
      : player),
    tiles: base.tiles.map(tile => tile.id === 1 ? { ...tile, ownerId: 'p2', rent: 100 } : tile)
  };
  const result = applyAction(at, { type: 'roll', actorId: 'p1' });
  assert.equal(result.ok, true);
  return result;
}

test('真实租金破产事件先退场，再为真实赢家庆祝；序号稳定且不改变输入', () => {
  const result = bankruptLanding();
  assert.equal(result.state.winnerId, 'p2');
  assert.ok(result.events.some(event => event.type === 'rent_paid'));
  const before = JSON.stringify(result);
  const cues = outcomeSequence(result.events, result.state);
  assert.deepEqual(cues, [
    { stage: 'bankrupt', actorId: 'p1', winnerId: null, nonce: result.state.revision },
    { stage: 'victory', actorId: 'p2', winnerId: 'p2', nonce: result.state.revision + 1 }
  ]);
  assert.deepEqual(outcomeSequence(result.events, result.state), cues);
  assert.equal(JSON.stringify(result), before);
});

test('多人对局中单个玩家破产只退场，不提前庆祝', () => {
  const result = bankruptLanding({ ...DEFAULT_CONFIG, players: [
    { id: 'p1', name: '桃桃' }, { id: 'p2', name: '阿团' }, { id: 'p3', name: '小圆' }
  ] });
  assert.equal(result.state.status, 'playing');
  assert.deepEqual(outcomeSequence(result.events, result.state), [
    { stage: 'bankrupt', actorId: 'p1', winnerId: null, nonce: result.state.revision }
  ]);
});

test('真实轮限结算按净资产赢家庆祝，不虚构破产', () => {
  const base = started();
  const at = { ...base, round: base.maxRounds, currentPlayerIndex: 1, phase: 'await_end_turn',
    tiles: base.tiles.map(tile => tile.id === 1 ? { ...tile, ownerId: 'p2' } : tile) };
  const result = applyAction(at, { type: 'end_turn', actorId: 'p2' });
  assert.equal(result.ok, true);
  assert.equal(result.state.winnerId, 'p2');
  assert.deepEqual(outcomeSequence(result.events, result.state), [
    { stage: 'victory', actorId: 'p2', winnerId: 'p2', nonce: result.state.revision }
  ]);
});

test('真实轮限同分产生中性平局，不将当前玩家当作赢家', () => {
  const base = started();
  const result = applyAction({ ...base, round: base.maxRounds, currentPlayerIndex: 1,
    phase: 'await_end_turn' }, { type: 'end_turn', actorId: 'p2' });
  assert.equal(result.ok, true);
  assert.equal(result.state.winnerId, null);
  assert.deepEqual(outcomeSequence(result.events, result.state), [
    { stage: 'draw', actorId: null, winnerId: null, nonce: result.state.revision }
  ]);
});

test('无新结束事件时，即使状态已结束也不会重播结果', () => {
  const result = bankruptLanding();
  assert.deepEqual(outcomeSequence([], result.state), []);
  assert.deepEqual(outcomeSequence(result.events.filter(event =>
    event.type !== 'player_bankrupt' && event.type !== 'game_finished'), result.state), []);
  const base = started();
  const roll = applyAction(base, { type: 'roll', actorId: 'p1' });
  assert.equal(roll.ok, true);
  assert.deepEqual(outcomeSequence(roll.events, roll.state), []);
});

test('一批多个破产事件按事件顺序全部退场，结束庆祝最后播放', () => {
  const result = bankruptLanding();
  const events = [
    { type: 'player_bankrupt', actorId: 'p3' },
    { type: 'game_finished' },
    { type: 'player_bankrupt', actorId: 'p1' }
  ];
  assert.deepEqual(outcomeSequence(events, result.state).map(cue => [cue.stage, cue.actorId]), [
    ['bankrupt', 'p3'], ['bankrupt', 'p1'], ['victory', 'p2']
  ]);
});
