import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';

test('页面只启动同源 Vite 模块 bundle，React 18 由本地依赖一起打包', async () => {
  const html = await readFile('dist/index.html', 'utf8');
  assert.ok(!html.includes('http://') && !html.includes('https://'));
  const entry=html.match(/src="(\.\/assets\/main-[^\"]+\.js)"/)?.[1];
  assert.ok(entry,'Vite 主入口');
  assert.ok(!html.includes('vendor/react'));
  assert.ok((await stat('dist/'+entry.slice(2))).size>100_000);
  assert.match(html,/\.\/assets\/main-[^\"]+\.css/);
  const shared=[...html.matchAll(/rel="modulepreload"[^>]+href="(\.\/assets\/[^"]+\.js)"/g)].map(m=>m[1]);
  assert.ok(shared.length,'shared runtime chunks');
  const contents=await Promise.all(shared.map(path=>readFile('dist/'+path.slice(2),'utf8')));
  assert.ok(contents.some(code=>code.includes('18.3.1')),'React 18.3.1 bundled locally');
});
