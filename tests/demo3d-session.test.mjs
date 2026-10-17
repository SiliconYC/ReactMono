import test from 'node:test';
import assert from 'node:assert/strict';

import { createDemoGame, dispatchDemoAction } from '../dist/demo3d/session.js';
import { routeSteps } from '../dist/demo3d/route.js';

test('3D 演示以固定种子启动两人 16 格真实规则对局', () => {
  const state = createDemoGame(20261017);

  assert.equal(state.map.id, 'internal-square-16');
  assert.equal(state.map.route.length, 16);
  assert.equal(state.players.length, 2);
  assert.deepEqual(state.players.map(player => player.name), ['桃桃', '阿团']);
  assert.equal(state.phase, 'await_roll');
});

test('3D 演示投骰只调用规则结果并返回逐格路径', () => {
  const before = createDemoGame(20261017);
  const result = dispatchDemoAction(before, { type: 'roll', actorId: 'p1' });

  assert.equal(result.ok, true);
  assert.equal(result.before, before);
  assert.equal(result.dieValue, 3);
  assert.deepEqual(result.route, [1, 2, 3]);
  assert.equal(result.after.players[0].position, 3);
  assert.equal(result.after.tiles[3].kind, 'property');
  assert.equal(result.after.phase, 'await_decision');
  assert.equal(result.events.find(event => event.type === 'die_rolled')?.details?.value, 3);
});

test('逐格路径跨越起点时保持正向且不重复原点', () => {
  const route = Array.from({ length: 16 }, (_, index) => index);

  assert.deepEqual(routeSteps(route, 14, 4), [15, 0, 1, 2]);
  assert.deepEqual(routeSteps(route, 5, 0), []);
});

