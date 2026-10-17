import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,stat} from 'node:fs/promises';
const assets=['fox','bear','rabbit','bird'];

test('#65 ships four distinct licensed original characters and no network assets',async()=>{
  const manifest=JSON.parse(await readFile('dist/art-manifest.json','utf8'));
  for(const name of assets){
    const path='art/character-'+name+'.svg';
    const entry=manifest.assets.find(a=>a.path===path);
    assert.ok(entry,path+' missing from manifest');
    assert.equal(entry.license,'CC0-1.0');
    const svg=await readFile('dist/'+path,'utf8');
    assert.match(svg,/<svg[^>]+viewBox="0 0 64 64"/);
    assert.ok(svg.includes('<path')||svg.includes('<circle'));
    assert.doesNotMatch(svg,/<script|foreignObject|href="https?:|<image/i);
    assert.ok((await stat('dist/'+path)).size<3200,path+' must stay light');
  }
  const unique=await Promise.all(assets.map(n=>readFile('dist/art/character-'+n+'.svg','utf8')));
  assert.equal(new Set(unique).size,4);
  const [html,css,sw,app,characters]=await Promise.all([
    'dist/index.html','dist/characters.css','dist/sw.js','dist/ui/app.js','dist/ui/characters.js'
  ].map(p=>readFile(p,'utf8')));
  assert.match(html,/href="\.\/characters\.css"/);
  assert.match(css,/prefers-reduced-motion:reduce/);
  assert.match(css,/character-moving/);
  assert.match(app,/characterMarker/);
  assert.match(app,/lastMotion/);
  assert.match(characters,/CHARACTER_NAMES/);
  assert.match(characters,/character-.*\.svg/);
  for(const name of assets)assert.ok(sw.includes('art/character-'+name+'.svg'),'missing SW '+name);
  assert.ok(sw.includes('./characters.css'));
  assert.doesNotMatch(sw,/__CACHE_VERSION__|__RUNTIME_ASSETS__/);
});
