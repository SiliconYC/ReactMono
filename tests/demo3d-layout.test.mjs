import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import { LOT_ANCHORS, TILE_ANCHORS, anchorsForMap, positionForTile } from '../.test-dist/demo3d/world/layout.js';
import { MASCOT_SEAT_COLORS, MASCOT_SEAT_OFFSETS, mascotSeatLayout } from '../.test-dist/demo3d/world/seats.js';
import { worldForMap } from '../.test-dist/core/level-data.js';
import { DEFAULT_MAP, HARBOR_MAP } from '../.test-dist/core/maps.js';

test('开发入口先进入 Vite 根目录内模块，避免父目录脚本被回退为 HTML', async () => {
  const html = await readFile(new URL('../demo3d/index.html', import.meta.url), 'utf8');
  const entry = await readFile(new URL('../demo3d/main.ts', import.meta.url), 'utf8');

  assert.match(html, /src="\.\/main\.ts"/);
  assert.match(entry, /src\/demo3d\/main\.tsx/);
});

test('16 个行走锚点唯一且完整', () => {
  assert.equal(TILE_ANCHORS.length, 16);
  assert.equal(new Set(TILE_ANCHORS.map(point => `${point.x},${point.z}`)).size, 16);
  assert.deepEqual(positionForTile(0), { x: -4, z: -4 });
  assert.deepEqual(positionForTile(8), { x: 4, z: 4 });
});

test('2～4 名玩家在同一格有独立颜色和站位', () => {
  const seats = MASCOT_SEAT_COLORS.map((_, seat) => mascotSeatLayout(seat));
  assert.equal(new Set(seats.map(({color}) => color)).size, 4);
  assert.equal(new Set(seats.map(({x,z}) => `${x},${z}`)).size, 4);
  assert.deepEqual(MASCOT_SEAT_OFFSETS[0], [-0.24, 0.24]);
  assert.deepEqual(mascotSeatLayout(4), mascotSeatLayout(0));
});

test('所有相邻格保持两单位连续距离，包括尾格回到起点', () => {
  for (let index = 0; index < TILE_ANCHORS.length; index += 1) {
    const current = TILE_ANCHORS[index];
    const next = TILE_ANCHORS[(index + 1) % TILE_ANCHORS.length];
    assert.equal(Math.hypot(next.x - current.x, next.z - current.z), 2);
  }
});

test('每个地产锚点都位于道路外侧而不是角色行走线上', () => {
  assert.equal(LOT_ANCHORS.length, TILE_ANCHORS.length);
  for (let index = 0; index < TILE_ANCHORS.length; index += 1) {
    const road = TILE_ANCHORS[index];
    const lot = LOT_ANCHORS[index];
    assert.ok(Math.hypot(lot.x, lot.z) > Math.hypot(road.x, road.z));
    assert.ok(Math.hypot(lot.x - road.x, lot.z - road.z) >= 1.2);
  }
});

test('正式地图使用关卡指定的世界坐标，规则方格不再限制道路形状', () => {
  for (const map of [DEFAULT_MAP, HARBOR_MAP]) {
    const layout = anchorsForMap(map);
    assert.equal(layout.tiles.length, map.cells.length);
    assert.equal(layout.lots.length, map.cells.length);
    assert.equal(new Set(layout.tiles.map(p => `${p.x},${p.z}`)).size, map.cells.length);
    for (let index = 0; index < map.route.length; index += 1) {
      const current = layout.tiles[map.route[index]];
      const next = layout.tiles[map.route[(index + 1) % map.route.length]];
      assert.ok(Math.hypot(next.x - current.x, next.z - current.z) > 2);
      assert.deepEqual(current,{x:worldForMap(map).tiles[map.route[index]].x,z:worldForMap(map).tiles[map.route[index]].z});
      const lot = layout.lots[map.route[index]];
      assert.ok(Math.hypot(lot.x - current.x, lot.z - current.z) >= 1.2);
    }
  }
});

