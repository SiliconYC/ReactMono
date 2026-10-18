import { cp, mkdir, rm, writeFile, readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createIcons } from './icons.mjs';
import { build } from 'vite';

// 测试模块由 tsc 输出到 .test-dist；dist 只包含真正发布的静态应用。
await rm('dist', { recursive: true, force: true });
await cp('site/index.html', 'dist/index.html');
await cp('site/style.css', 'dist/style.css');
await cp('site/board-art.css', 'dist/board-art.css');
await cp('site/characters.css', 'dist/characters.css');
await cp('site/action-layout.css', 'dist/action-layout.css');
await cp('site/motion.css', 'dist/motion.css');
await cp('site/audio.css', 'dist/audio.css');
await cp('site/guide.css', 'dist/guide.css');
await cp('site/board-3d.css', 'dist/board-3d.css');
for(const name of ['visual-lab.html','visual-lab.css','visual-tokens.css','art-manifest.json']){
  await cp('site/'+name,'dist/'+name);
}
await mkdir('dist/art',{recursive:true});
await cp('site/art','dist/art',{recursive:true});
await createIcons();
await cp('site/manifest.webmanifest','dist/manifest.webmanifest');
await build({ configFile: 'vite.main.config.ts' });
const viteAssets=(await readdir('dist/assets')).map(name=>'assets/'+name).sort();
const assets=['dist/index.html','dist/style.css','dist/board-art.css','dist/characters.css','dist/action-layout.css','dist/motion.css','dist/audio.css','dist/guide.css','dist/board-3d.css','dist/visual-tokens.css','dist/visual-lab.css','dist/visual-lab.html','dist/art-manifest.json','dist/art/house.svg','dist/art/coin.svg',...['fox','bear','rabbit','bird'].map(x=>'dist/art/character-'+x+'.svg'),...viteAssets.map(path=>'dist/'+path),
  'dist/manifest.webmanifest','dist/icons/icon-192.png','dist/icons/icon-512.png','site/sw.js'];
const fingerprint=createHash('sha256');
for(const name of assets)fingerprint.update(await readFile(name));
const sw=(await readFile('site/sw.js','utf8'))
  .replace('__CACHE_VERSION__',fingerprint.digest('hex').slice(0,16))
  .replace('/* __RUNTIME_ASSETS__ */',viteAssets.map(path=>`'./${path}',`).join('\n '));
await writeFile('dist/sw.js',sw);
await writeFile('dist/.nojekyll', '');
console.log('静态构建成功：dist/（React/Three/R3F 同源 bundle；无运行时 CDN）');
