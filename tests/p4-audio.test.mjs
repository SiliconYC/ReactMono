import {test} from 'node:test';import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {classifySound,SoundController} from '../dist/ui/audio.js';
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
 const [html,css,sw,js]=await Promise.all(['dist/index.html','dist/audio.css','dist/sw.js','dist/ui/audio.js'].map(x=>readFile(x,'utf8')));
 assert.match(html,/audio.css/);assert.match(sw,/\.\/audio.css/);
 assert.match(js,/createOscillator/);assert.match(js,/createGain/);
 assert.doesNotMatch(js,/\.mp3|\.ogg|https:\/\//);
 assert.match(css,/audio-toggle/);
});
