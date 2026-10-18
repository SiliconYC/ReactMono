import {test} from 'node:test';import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import {classifySound,SoundController} from '../.test-dist/ui/audio.js';
const e=type=>[{type,actorId:'p1'}];
test('#68 seven distinguishable event families without downloaded audio',()=>{
 assert.equal(classifySound(e('die_rolled')),'dice');
 assert.equal(classifySound(e('player_moved')),'step');
 assert.equal(classifySound(e('rent_paid')),'pay');
 assert.equal(classifySound(e('event_bonus')),'gain');
 assert.equal(classifySound(e('card_used')),'card');
 assert.equal(classifySound(e('facility_entered')),'facility');
 assert.equal(classifySound(e('game_finished')),'finish');
 assert.equal(classifySound([]),null);
 const controller=new SoundController();controller.setVolume(5);assert.equal(controller.level,1);
 controller.setVolume(-5);assert.equal(controller.level,0);controller.dispose();
});
test('#68 all audio is procedural, same-origin, offline',async()=>{
 const [html,sw,js]=await Promise.all(['dist/index.html','dist/sw.js','.test-dist/ui/audio.js'].map(x=>readFile(x,'utf8')));
 const cssName=(await readdir('dist/assets')).find(x=>x.startsWith('main-')&&x.endsWith('.css'));
 const css=await readFile('dist/assets/'+cssName,'utf8');
 assert.match(html,/assets\/main-[^\"]+\.css/);assert.match(sw,/\.\/audio.css/);
 assert.match(js,/createOscillator/);assert.match(js,/createGain/);
 assert.doesNotMatch(js,/\.mp3|\.ogg|https:\/\//);
 assert.match(css,/setting-line/);
 const app=await readFile('src/ui/app.tsx','utf8');
 assert.match(app,/开启音效/);assert.match(app,/音效音量/);assert.match(app,/setEnabled/);
});
