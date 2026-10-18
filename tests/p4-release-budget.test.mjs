/** P4/11 release asset gate: track real built bytes and all offline/LICENSE entries. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync,statSync,mkdirSync,writeFileSync} from 'node:fs';
import {join,relative} from 'node:path';
const ROOT='dist',OUT='artifacts/main3d';
function walk(dir){return readdirSync(dir,{withFileTypes:true}).flatMap(x=>{
  const path=join(dir,x.name);return x.isDirectory()?walk(path):[path];
});}
test('#72 build footprint, CDN-free original art, and exact service-worker cache budget',()=>{
 const files=walk(ROOT).filter(x=>!x.endsWith('/.nojekyll'));
 const assets=files.map(path=>({path:relative(ROOT,path).replaceAll('\\','/'),bytes:statSync(path).size}));
 const byPath=new Map(assets.map(x=>[x.path,x.bytes]));
 const total=assets.reduce((a,x)=>a+x.bytes,0);
 const js=assets.filter(x=>x.path.endsWith('.js')).reduce((a,x)=>a+x.bytes,0);
 const css=assets.filter(x=>x.path.endsWith('.css')).reduce((a,x)=>a+x.bytes,0);
 const art=assets.filter(x=>x.path.startsWith('art/')).reduce((a,x)=>a+x.bytes,0);
 const budget={total:8_000_000,js:2_500_000,css:180_000,art:120_000,svgFile:35_000};
 const manifest=JSON.parse(readFileSync(join(ROOT,'art-manifest.json'),'utf8'));
 assert.equal(manifest.schemaVersion,1);
 assert.equal(manifest.assets.length,6);
 for(const a of manifest.assets){
  assert.equal(a.license,'CC0-1.0',a.path);
  assert.ok(byPath.has(a.path),a.path);
  assert.ok(byPath.get(a.path)<=budget.svgFile,a.path);
  const svg=readFileSync(join(ROOT,a.path),'utf8');
  assert.match(svg,/<svg\b/);
  assert.doesNotMatch(svg.replace('http://www.w3.org/2000/svg',''),/(?:<script\b|https?:\/\/|data:image\/|<foreignObject\b)/i);
 }
 const index=readFileSync(join(ROOT,'index.html'),'utf8');
 const sw=readFileSync(join(ROOT,'sw.js'),'utf8');
 const runtime=assets.filter(x=>/^assets\/.*\.js$/.test(x.path));
 for(const file of runtime)assert.ok(sw.includes("'./"+file.path+"'"),'missing runtime precache '+file.path);
 for(const file of manifest.assets)assert.ok(sw.includes("'./"+file.path+"'"),'missing art precache '+file.path);
 assert.match(sw,/reactmono-[a-f0-9]{16}/);
 assert.doesNotMatch(sw,/__CACHE_VERSION__|__RUNTIME_ASSETS__/);
 assert.doesNotMatch(index,/(https?:\/\/(?:unpkg|cdn|esm\.sh)|<script[^>]+src=['"]https?:)/i);
 for(const [name,value] of Object.entries({total,js,css,art}))
  assert.ok(value<=budget[name],'release budget exceeded '+name+': '+value+' > '+budget[name]);
 mkdirSync(OUT,{recursive:true});
 writeFileSync(join(OUT,'asset-budgets.json'),JSON.stringify({
  measuredFrom:'actual dist built by npm test',budgets:budget,totals:{total,js,css,art},
  files:assets,licenseManifest:manifest.assets.map(a=>({path:a.path,license:a.license})),
  noExternalRuntime:true,precachedModules:runtime.length
 },null,2)+'\n');
 console.log('P4/11 RELEASE BUDGET '+JSON.stringify({total,js,css,art,runtimeModules:runtime.length,files:assets.length}));
});
