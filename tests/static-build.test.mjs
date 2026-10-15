import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';

test('页面所有必需脚本同源，且编译后存在本地 React 18 运行时', async () => {
  const html = await readFile('dist/index.html', 'utf8');
  assert.ok(!html.includes('http://') && !html.includes('https://'));
  for (const url of ['./vendor/react.production.min.js','./vendor/react-dom.production.min.js','./ui/app.js']) {
    assert.ok(html.includes('src="' + url + '"'), url);
    const file = 'dist/' + url.slice(2);
    assert.ok((await stat(file)).size > 1000, file);
  }
});
