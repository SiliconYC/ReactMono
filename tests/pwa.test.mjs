import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,stat} from 'node:fs/promises';
test('PWA Manifest 安装作用域及双尺寸原创 PNG 图标',async()=>{
  const m=JSON.parse(await readFile('dist/manifest.webmanifest','utf8'));
  assert.equal(m.lang,'zh-CN');
  assert.equal(m.start_url,'/ReactMono/');
  assert.equal(m.scope,'/ReactMono/');
  assert.equal(m.display,'standalone');
  for(const size of [192,512]){
    const icon=m.icons.find(i=>i.sizes===size+'x'+size);
    assert.ok(icon&&icon.type==='image/png');
    const png=await readFile('dist/icons/icon-'+size+'.png');
    assert.ok(png.length>500);
    assert.equal(png.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
    assert.equal(png.readUInt32BE(16),size);
    assert.equal(png.readUInt32BE(20),size);
  }
  assert.ok((await stat('dist/sw.js')).size>1000);
});
test('Service Worker 同源预缓存完整运行依赖，不使用 CDN 或缓存私人存档',async()=>{
  const sw=await readFile('dist/sw.js','utf8');
  const html=await readFile('dist/index.html','utf8');
  for(const name of ['index.html','ui/app.js','core/game.js','core/save.js',
    'storage/indexeddb.js','vendor/react.production.min.js','vendor/react-dom.production.min.js'])
      assert.ok(sw.includes(name),'缺少离线预缓存 '+name);
  assert.doesNotMatch(sw,/__CACHE_VERSION__/);
  assert.match(sw,/reactmono-[a-f0-9]{16}/);
  assert.ok(html.includes('manifest.webmanifest'));
  assert.ok(!/unpkg\.com|cdn\.jsdelivr/.test(html));
  assert.ok(!sw.includes('put(userSave')&&!sw.includes('fetch("https:'));
});
