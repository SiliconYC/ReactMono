import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, DEFAULT_CONFIG } from '../.test-dist/core/game.js';
import * as flow from '../.test-dist/ui/human-turn-flow.js';
const {canAutoContinue,canCommitAutoContinue,HUMAN_CONTINUE_DELAY,canManageAssets}=flow;

function settled() {
  const initial = createGame(11, { ...DEFAULT_CONFIG, propertyVisitOnly: true });
  const started = applyAction(initial, { type: 'start_game', actorId: initial.players[0].id }).state;
  return { ...started, phase: 'await_end_turn' };
}
function context(game, patch = {}) {
  return { blocked: false, ...patch };
}

test('settled human turn continues automatically only after presentation and pause barriers clear', () => {
  const game = settled();
  assert.equal(canAutoContinue(game, context(game)), true);
  assert.equal(canAutoContinue(game, context(game, { blocked: true })), false);
  assert.equal(HUMAN_CONTINUE_DELAY, 0, 'presentation completion must not add a management countdown');
  assert.equal(canAutoContinue({...game}, {blocked:false}), true, 'restored settled games continue without extra confirmation');
});

test('property purchase and shop choices cannot be skipped by automatic continuation', () => {
  const game = settled();
  for (const phase of ['await_roll', 'await_decision', 'await_shop']) {
    assert.equal(canAutoContinue({ ...game, phase }, context(game)), false);
  }
  const target = game.tiles.find(tile => tile.kind === 'property');
  const owner = game.players[game.currentPlayerIndex];
  const visiting = { ...game,
    players: game.players.map(player => player.id === owner.id ? { ...player, position: target.id } : player),
    tiles: game.tiles.map(tile => tile.id === target.id ? { ...tile, ownerId: owner.id } : tile),
    events: [...game.events, { type: 'die_rolled', actorId: owner.id, details: { value: 1 } }],
  };
  assert.equal(canAutoContinue(visiting, context(visiting)), false);
  assert.equal(canAutoContinue({ ...visiting, events: [...visiting.events,
    { type: 'property_upgraded', actorId: owner.id, details: { tileId: target.id, level: 1 } },
  ] }, context(visiting)), true);
});

test('real purchase and decline commands settle the visit and leave no extra end-turn decision', () => {
  let landed;
  for (let seed = 1; seed < 50 && !landed; seed++) {
    const initial = createGame(seed, { ...DEFAULT_CONFIG, propertyVisitOnly: true });
    const actorId = initial.players[0].id;
    const started = applyAction(initial, { type: 'start_game', actorId }).state;
    const rolled = applyAction(started, { type: 'roll', actorId });
    if (rolled.ok && rolled.state.phase === 'await_decision') landed = rolled.state;
  }
  assert.ok(landed, 'fixture must reach a property purchase decision');
  const actorId = landed.players[landed.currentPlayerIndex].id;
  for (const type of ['buy_property', 'decline_property']) {
    const result = applyAction(landed, { type, actorId });
    assert.equal(result.ok, true);
    assert.equal(canAutoContinue(result.state, context(result.state)), true);
    const continued = applyAction(result.state, { type: 'end_turn', actorId });
    assert.equal(continued.ok, true);
    assert.notEqual(continued.state.players[continued.state.currentPlayerIndex].id, actorId);
  }
});

test('old timer cannot replace a changed, restored, or restarted game with the same turn identifiers', () => {
  const game = settled();
  assert.equal(canCommitAutoContinue(game, game, context(game)), true);
  assert.equal(canCommitAutoContinue(game, { ...game }, context(game)), false);
  assert.equal(canCommitAutoContinue(game, { ...game, revision: game.revision + 1 }, context(game)), false);
  assert.equal(canCommitAutoContinue(game, game, context(game, { blocked: true })), false);
});

test('computer turns and finished games retain their own continuation rules', () => {
  const game = settled();
  assert.equal(canAutoContinue({ ...game, status: 'finished' }, context(game)), false);
  assert.equal(canAutoContinue({ ...game, players: game.players.map(player => ({ ...player, kind: 'computer' })) }, context(game)), false);
});

test('human asset management is available before rolling, never as an extra landing decision', () => {
 const game=settled();
 assert.equal(typeof canManageAssets,'function');
 assert.equal(canManageAssets({...game,phase:'await_roll'}),true);
 for(const phase of ['await_decision','await_shop','await_end_turn'])assert.equal(canManageAssets({...game,phase}),false);
 assert.equal(canManageAssets({...game,phase:'await_roll',players:game.players.map(p=>({...p,kind:'computer'}))}),false);
});
