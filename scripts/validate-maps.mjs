import { readFile } from 'node:fs/promises';
import { loadLevelCatalog } from '../.test-dist/core/level-data.js';
const path = process.argv[2] ?? 'src/data/levels.json';
try {
  const levels = loadLevelCatalog(JSON.parse(await readFile(path, 'utf8')));
  for (const level of levels) {
    console.log(`${level.map.id}：${level.name}，${level.tiles.length} 格，${level.map.columns}×${level.map.rows}，${level.playable?'可选':'内部测试'}`);
  }
  console.log(`关卡校验通过：${levels.length} 张`);
} catch (error) {
  console.error('关卡校验失败：' + error.message);
  process.exitCode = 1;
}
