import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
test('主程序使用真实 3D 世界组件并预缓存其静态资源',async()=>{
 const [html,app,world,sw]=await Promise.all(
   ['dist/index.html','.test-dist/ui/app.js','src/demo3d/world/WorldCanvas.tsx','dist/sw.js'].map(p=>readFile(p,'utf8')));
 const cssName=(await readdir('dist/assets')).find(x=>x.startsWith('main-')&&x.endsWith('.css'));
 const css=await readFile('dist/assets/'+cssName,'utf8');
 assert.match(html,/assets\/main-[^\"]+\.css/);
 assert.match(app,/WorldCanvas/);
 assert.match(app,/selectedTileId/);
 assert.match(world,/scene-fallback-grid/);
 assert.match(css,/board-viewport-3d/);
 assert.match(css,/canvas-shell/);
 assert.match(css,/scene-hud/);
 assert.match(css,/prefers-reduced-motion/);
 assert.match(sw,/\.\/board-3d\.css/);
 assert.doesNotMatch(sw,/__CACHE_VERSION__/);
});
