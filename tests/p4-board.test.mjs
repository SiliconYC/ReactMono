import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
test('#64 new paper-town board is real React UI and PWA asset, never a fake overlay',async()=>{
 const [html,app,css,sw]=await Promise.all(
   ['dist/index.html','dist/ui/app.js','dist/board-art.css','dist/sw.js'].map(p=>readFile(p,'utf8')));
 assert.match(html,/href="\.\/board-art\.css"/);
 assert.match(app,/tile-artwork/);
 assert.match(app,/selectedTileId/);
 assert.match(app,/gridTemplateColumns/);
 assert.match(app,/data-owner-id/);
 assert.match(css,/board-harbor/);
 assert.match(css,/tile-art-shop/);
 assert.match(css,/tile-mortgaged/);
 assert.match(css,/piece-4/);
 assert.match(css,/prefers-reduced-motion/);
 assert.match(sw,/\.\/board-art\.css/);
 assert.doesNotMatch(sw,/__CACHE_VERSION__/);
});
