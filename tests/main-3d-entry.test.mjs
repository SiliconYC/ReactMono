import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

test('主程序页面使用单一同源 React/R3F bundle 并预缓存实际入口', async () => {
  const html = await readFile('dist/index.html', 'utf8');
  const sw = await readFile('dist/sw.js', 'utf8');
  const bundlePath = html.match(/src="(\.\/assets\/[^\"]+\.js)"/)?.[1];
  assert.ok(bundlePath, '首页应加载 Vite 生成的 ESM 主程序 bundle');
  assert.doesNotMatch(html, /vendor\/react(?:-dom)?\.production\.min\.js/);
  assert.match(sw, new RegExp(bundlePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  const bundle = await readFile(join('dist', bundlePath.slice(2)), 'utf8');
  assert.match(bundle, /WebGLRenderer|WebGLRenderingContext/);
  assert.match(bundle, /createRoot/);
  const chunks = await readdir('dist/assets');
  assert.ok(chunks.some(name => name.endsWith('.js')));
});

test('主程序规则入口保留 demo 已验证的到访建造与存款股市分账规则', async () => {
  const source = await readFile('src/ui/app.tsx', 'utf8');
  const start = source.slice(source.indexOf('startGame ='), source.indexOf('componentWillUnmount'));
  assert.match(start, /propertyVisitOnly:\s*true/);
  assert.match(start, /stockAccount:\s*["']bank["']/);
  assert.match(start, /bankEnabled:\s*true/);
  assert.match(start, /marketEnabled:\s*true/);
});

test('Vite 开发预览不会注册占位 Service Worker 覆盖热更新资源', async () => {
  const source = await readFile('src/ui/app.tsx', 'utf8');
  assert.match(source, /import\.meta\.env\.DEV/);
  assert.match(source, /registration\.unregister\(\)/);
});
