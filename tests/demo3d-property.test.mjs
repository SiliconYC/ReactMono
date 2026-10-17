import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemoGame, dispatchDemoAction } from '../dist/demo3d/session.js';
import * as properties from '../dist/demo3d/properties.js';

const own = (state, ids, level = 1, ownerId = 'p1') => ({ ...state, tiles: state.tiles.map(tile => ids.includes(tile.id) ? { ...tile, ownerId, level } : tile) });

test('买地、建房、升级独立收费，最高两级，拒绝无钱与他人地产', () => {
  let game = createDemoGame(20261017);
  game = dispatchDemoAction(game, { type: 'roll', actorId: 'p1' }).after;
  game = dispatchDemoAction(game, { type: 'buy_property', actorId: 'p1' }).after;
  assert.equal(game.tiles[3].level, 0);
  assert.equal(game.players[0].cash, 1064);
  assert.equal(properties.propertyStage?.(game.tiles[3]), '空地');
  for (const [level, title] of [[1, '住宅'], [2, '高级住宅']]) {
    const before = game;
    const result = dispatchDemoAction(game, { type: 'upgrade_property', actorId: 'p1', tileId: 3 });
    assert.equal(result.ok, true);
    game = result.after;
    assert.equal(game.tiles[3].level, level);
    assert.equal(game.players[0].cash, before.players[0].cash - before.tiles[3].upgradeCosts[level - 1]);
    assert.equal(properties.propertyStage?.(game.tiles[3]), title);
  }
  assert.equal(dispatchDemoAction(game, { type: 'upgrade_property', actorId: 'p1', tileId: 3 }).ok, false);
  assert.equal(dispatchDemoAction(game, { type: 'upgrade_property', actorId: 'p1', tileId: 2 }).ok, false);
  const poor = { ...game, tiles: game.tiles.map(t => t.id === 3 ? { ...t, level: 0 } : t), players: game.players.map(p => ({ ...p, cash: 0 })) };
  assert.equal(dispatchDemoAction(poor, { type: 'upgrade_property', actorId: 'p1', tileId: 3 }).reason, 'INSUFFICIENT_FUNDS');
});

test('同街区连续建好的同业主房屋组成联排，允许不同等级', () => {
  let game = own(createDemoGame(1), [1, 2, 3]);
  game = { ...game, tiles: game.tiles.map(t => t.id === 2 ? { ...t, level: 2 } : t) };
  assert.deepEqual(properties.rowHouses?.(game), [{ blockId: 'north', ownerId: 'p1', tileIds: [1, 2, 3] }]);
});

test('空地、未买地、其他业主及街区边界都会截断联排', () => {
  const base = createDemoGame(1);
  for (const middle of [{ ownerId: 'p1', level: 0 }, { ownerId: null, level: 0 }, { ownerId: 'p2', level: 1 }]) {
    const game = own(base, [1, 2, 3]);
    assert.deepEqual(properties.rowHouses?.({ ...game, tiles: game.tiles.map(t => t.id === 2 ? { ...t, ...middle } : t) }), []);
  }
  assert.deepEqual(properties.rowHouses?.(own(base, [3, 5])), []);
  assert.deepEqual(properties.rowHouses?.(own(base, [13, 14, 1, 2])), [
    { blockId: 'north', ownerId: 'p1', tileIds: [1, 2] },
    { blockId: 'west', ownerId: 'p1', tileIds: [13, 14] }
  ]);
});

test('租金演出使用真实支付事件的双方与金额，不把应付金额当实付', async () => {
  const { rentCueFor } = await import('../dist/demo3d/presentation.js');
  let state = createDemoGame(20261017);
  // First roll lands on tile 3; another player owns its upgraded residence.
  state = { ...own(state, [3], 2, 'p2'), players: state.players.map(p => p.id === 'p1' ? { ...p, cash: 10 } : p) };
  const result = dispatchDemoAction(state, { type: 'roll', actorId: 'p1' });
  assert.equal(result.ok, true);
  assert.deepEqual(rentCueFor(result.events), { fromId: 'p1', toId: 'p2', tileId: 3, amount: 10 });
  assert.equal(result.after.status, 'finished');
  assert.equal(result.after.winnerId, 'p2');
  assert.equal(rentCueFor([{ type: 'tile_landed' }]), null);
});
