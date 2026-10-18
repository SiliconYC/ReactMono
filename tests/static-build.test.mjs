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
  const runtime=html.match(/href="\.\/assets\/(jsx-runtime-[^\"]+\.js)"/)?.[1];
  assert.ok(runtime,'React runtime chunk');
  assert.ok((await stat('dist/assets/'+runtime)).size>100_000);
});
