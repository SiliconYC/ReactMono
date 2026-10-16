import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
test('P3-04: PWA precaches ALL same-origin runtime modules for offline fresh load',async()=>{
  const sw=await readFile('dist/sw.js','utf8');
  for(const folder of ['core','ui','storage']){
    const modules=(await readdir('dist/'+folder)).filter(name=>name.endsWith('.js'));
    assert.ok(modules.length,'empty runtime directory: '+folder);
    for(const file of modules)assert.ok(sw.includes(folder+'/'+file),
      'runtime module absent from Service Worker precache: '+folder+'/'+file);
  }
  assert.doesNotMatch(sw,/__RUNTIME_ASSETS__/);
  assert.doesNotMatch(sw,/__CACHE_VERSION__/);
});
