import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,stat} from 'node:fs/promises';

test('P4 #63 visual slice is real React and local and licensed',async()=>{
  const html=await readFile('dist/visual-lab.html','utf8');
  const js=await readFile('dist/ui/visual-lab.js','utf8');
  assert.match(html,/\.\/ui\/visual-lab\.js/);
  assert.match(js,/applyAction/);
  assert.match(js,/createGame/);
  assert.match(js,/await_decision/);
  const manifest=JSON.parse(await readFile('dist/art-manifest.json','utf8'));
  assert.equal(manifest.schemaVersion,1);
  assert.ok(manifest.assets.length>=2);
  for(const asset of manifest.assets){
    assert.match(asset.path,/^art\/[a-z0-9-]+\.svg$/);
    assert.match(asset.license,/^CC0-1\.0$/);
    const svg=await readFile('dist/'+asset.path,'utf8');
    assert.match(svg,/<svg/);
    assert.doesNotMatch(svg,/(<script|https?:\/\/|foreignObject)/i);
  }
  assert.ok((await stat('dist/visual-tokens.css')).size>1000);
  assert.ok((await stat('dist/visual-lab.css')).size>1000);
  const sw=await readFile('dist/sw.js','utf8');
  for(const path of ['visual-lab.html','visual-tokens.css','visual-lab.css','art/house.svg','art/coin.svg','ui/visual-lab.js','art-manifest.json'])
    assert.ok(sw.includes(path),'SW missing offline resource '+path);
  assert.doesNotMatch(sw,/__CACHE_VERSION__|__RUNTIME_ASSETS__/);
  const index=await readFile('dist/index.html','utf8');
  assert.match(index,/visual-tokens\.css/);
  assert.doesNotMatch(index,/https?:\/\/(?:unpkg|cdn|esm\.sh)/);
});
