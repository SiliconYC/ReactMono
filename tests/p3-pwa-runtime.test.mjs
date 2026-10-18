import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
test('P3-04: PWA precaches ALL same-origin runtime modules for offline fresh load',async()=>{
  const sw=await readFile('dist/sw.js','utf8');
  const modules=(await readdir('dist/assets')).filter(name=>name.endsWith('.js'));
  assert.ok(modules.some(name=>name.startsWith('main-')),'built main application bundle');
  assert.ok(modules.some(name=>name.startsWith('jsx-runtime-')),'built React runtime bundle');
  for(const file of modules)assert.ok(sw.includes('./assets/'+file),'runtime chunk absent from Service Worker precache: '+file);
  assert.doesNotMatch(sw,/__RUNTIME_ASSETS__/);
  assert.doesNotMatch(sw,/__CACHE_VERSION__/);
});
