import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import { LOT_ANCHORS, TILE_ANCHORS, positionForTile } from '../dist/demo3d/world/layout.js';

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

