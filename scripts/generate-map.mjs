/** Generic offline authoring tool. All level-specific shape and text come from JSON. */
import { readFile, writeFile } from 'node:fs/promises';
import { loadLevelCatalog } from '../.test-dist/core/level-data.js';
const [source, destination] = process.argv.slice(2);
try {
  if (!source || !destination) throw new Error('用法：node scripts/generate-map.mjs 轮廓.json 输出目录.json');
  const recipe = JSON.parse(await readFile(source, 'utf8'));
  if (!recipe || !Array.isArray(recipe.outline) || recipe.outline.length < 4 || recipe.outline.length > 512 ||
      recipe.outline.some(p => !Array.isArray(p) || p.length !== 2 || !p.every(n => Number.isSafeInteger(n) && Math.abs(n) <= 10000)))
    throw new Error('轮廓必须由至少四个有限整数坐标组成');
  const cells = [];
  for (let i = 0; i < recipe.outline.length; i++) {
    let [x, y] = recipe.outline[i];
    const [endX, endY] = recipe.outline[(i + 1) % recipe.outline.length];
    if ((x === endX) === (y === endY)) throw new Error('轮廓边必须非零且平行于坐标轴');
    const dx = Math.sign(endX - x), dy = Math.sign(endY - y);
    while (x !== endX || y !== endY) {
      if (cells.length >= 512) throw new Error('当前存档兼容上限为 512 格');
      cells.push({column:x, row:y}); x += dx; y += dy;
    }
  }
  const minX = Math.min(...cells.map(c => c.column)), minY = Math.min(...cells.map(c => c.row));
  for (const cell of cells) { cell.column += 1 - minX; cell.row += 1 - minY; }
  const tiles = cells.map((_, id) => ({id,
    kind:id === 0 ? 'start' : id % 3 === 0 ? 'neutral' : 'property',
    title:recipe.name + (id === 0 ? '起点' : `${id % 3 === 0 ? '驿站' : '街区'}${String(id).padStart(3,'0')}`),
    ...(id !== 0 && id % 3 !== 0 ? {price:100 + id % 24 * 10, rent:20 + id % 24 * 2} : {})
  }));
  const neutralIds = tiles.filter(t => t.kind === 'neutral').map(t => t.id);
  const facilityConfig = neutralIds.length >= 3 ? {hospitalTiles:[neutralIds[0]], prisonTiles:[neutralIds[1]], shopTiles:[neutralIds[2]],
    hospitalTurns:2, prisonTurns:3, hospitalFee:50, prisonFee:80,
    prices:{reward:120,stride:110,remote:210,roadblock:180,rent_free:160},
    stock:{reward:2,stride:2,remote:2,roadblock:2,rent_free:2}} : null;
  const level = {facilityConfig, name:recipe.name, description:recipe.description, playable:true,
    map:{id:recipe.id, version:1, columns:Math.max(...cells.map(c=>c.column)), rows:Math.max(...cells.map(c=>c.row)), cells, route:cells.map((_,i)=>i)},
    tiles, initialCash:1500, maxRounds:60,
    eventRules:{tileIds:tiles.filter(t=>t.id % 6 === 3).map(t=>t.id), bonus:120, fee:60},
    cardRules:{tileIds:tiles.filter(t=>t.id > 0 && t.id % 6 === 0).map(t=>t.id), rewardCash:80, moveBonus:2, maxHand:3}};
  const catalog = {schemaVersion:1, levels:[level]};
  loadLevelCatalog(catalog); // Also rejects self-intersections, duplicate cells and invalid metadata.
  await writeFile(destination, JSON.stringify(catalog, null, 2) + '\n', {flag:'wx'});
  console.log(`已生成 ${recipe.name}：${cells.length} 格 → ${destination}`);
} catch (error) {
  console.error('地图生成失败：' + error.message);
  process.exitCode = 1;
}
