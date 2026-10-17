import { cp, mkdir, stat, writeFile, readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { createIcons } from './icons.mjs';

// tsc 先输出 dist/core、dist/ui；此处仅收集同源静态资源。
// 构建必须从已安装的锁文件依赖读取，严禁运行时加载第三方 CDN。
await mkdir('dist/vendor', { recursive: true });
await cp('site/index.html', 'dist/index.html');
await cp('site/style.css', 'dist/style.css');
await cp('site/board-art.css', 'dist/board-art.css');
await cp('site/characters.css', 'dist/characters.css');
await cp('site/action-layout.css', 'dist/action-layout.css');
for(const name of ['visual-lab.html','visual-lab.css','visual-tokens.css','art-manifest.json']){
  await cp('site/'+name,'dist/'+name);
}
await mkdir('dist/art',{recursive:true});
await cp('site/art','dist/art',{recursive:true});
// Keep manifest, attribution and every original sprite in both fingerprint and offline precache.
for (const [packageName, filename] of [
  ['react', 'react.production.min.js'],
  ['react-dom', 'react-dom.production.min.js']
]) {
  const source = join('node_modules', packageName, 'umd', filename);
  const info = await stat(source);
  if (info.size < 10000) throw new Error('React 本地运行时文件异常：' + source);
  await cp(source, join('dist/vendor', filename));
}
await createIcons();
await cp('site/manifest.webmanifest','dist/manifest.webmanifest');
// Include EVERY emitted same-origin runtime module in both SW cache and cache version.
const runtimeFiles=(await Promise.all(['core','ui','storage'].map(async dir=>
  (await readdir('dist/'+dir)).filter(name=>name.endsWith('.js')).map(name=>dir+'/'+name)))).flat().sort();
const assets=['dist/index.html','dist/style.css','dist/board-art.css','dist/characters.css','dist/action-layout.css','dist/visual-tokens.css','dist/visual-lab.css','dist/visual-lab.html','dist/art-manifest.json','dist/art/house.svg','dist/art/coin.svg',...['fox','bear','rabbit','bird'].map(x=>'dist/art/character-'+x+'.svg'),...runtimeFiles.map(path=>'dist/'+path),
  'dist/vendor/react.production.min.js','dist/vendor/react-dom.production.min.js',
  'dist/manifest.webmanifest','dist/icons/icon-192.png','dist/icons/icon-512.png','site/sw.js'];
const fingerprint=createHash('sha256');
for(const name of assets)fingerprint.update(await readFile(name));
const sw=(await readFile('site/sw.js','utf8'))
  .replace('__CACHE_VERSION__',fingerprint.digest('hex').slice(0,16))
  .replace('/* __RUNTIME_ASSETS__ */',runtimeFiles.map(path=>`'./${path}',`).join('\n '));
await writeFile('dist/sw.js',sw);
await writeFile('dist/.nojekyll', '');
console.log('静态构建成功：dist/（React 18.3.1 同源文件；无运行时 CDN）');
