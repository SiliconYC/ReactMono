import {test} from 'node:test';import assert from 'node:assert/strict';import {readFile,readdir} from 'node:fs/promises';
import {createGame,applyAction,DEFAULT_CONFIG} from '../.test-dist/core/game.js';
import {walkPath,eventCue} from '../.test-dist/ui/feedback.js';
test('#67 pure visuals never mutate engine dice or finances',()=>{
 const a=createGame(17);const started=applyAction(a,{type:'start_game',actorId:'p1'});assert.ok(started.ok);
 const roll=applyAction(started.state,{type:'roll',actorId:'p1'});assert.ok(roll.ok);
 const before=JSON.stringify(roll.state);const cue=eventCue(started.state,roll.state,roll.events);
 assert.equal(JSON.stringify(roll.state),before);assert.ok(cue);assert.equal(cue.revision,roll.state.revision);
 assert.deepEqual(cue.path,walkPath(started.state,roll.state,'p1'));
 assert.ok(cue.path.length>=1);assert.equal(cue.path.at(-1),roll.state.players[0].position);
});
test('#67 PWA caches animation CSS',async()=>{
 const [html,sw]=await Promise.all(['dist/index.html','dist/sw.js'].map(x=>readFile(x,'utf8')));
 const cssName=(await readdir('dist/assets')).find(x=>x.startsWith('main-')&&x.endsWith('.css'));
 const css=await readFile('dist/assets/'+cssName,'utf8');
 assert.match(html,/assets\/main-[^\"]+\.css/);assert.match(sw,/\.\/motion.css/);assert.match(css,/prefers-reduced-motion:reduce/);
});

test('终局发生在落地时，移动演出仍绑定实际走路的玩家',()=>{
 let game=createGame(17,{...DEFAULT_CONFIG,propertyVisitOnly:true,bankEnabled:true,loanEnabled:true,marketEnabled:true});
 game=applyAction(game,{type:'start_game',actorId:'p1'}).state;
 game={...game,players:game.players.map((p,i)=>i===0?{...p,cash:1}:p),tiles:game.tiles.map(t=>t.id===1?{...t,ownerId:'p2',level:2}:t)};
 const result=applyAction(game,{type:'roll',actorId:'p1'});
 assert.ok(result.ok);assert.equal(result.state.status,'finished');
 const cue=eventCue(game,result.state,result.events);
 assert.deepEqual(cue.path,[1]);assert.equal(cue.actorId,'p1');
});

test('两位真人之间经过电脑回合，仍需确认设备交接',async()=>{
 const {needsHumanHandoff}=await import('../.test-dist/ui/feedback.js');
 let game=createGame(17,{...DEFAULT_CONFIG,players:[{id:'p1',name:'甲',kind:'human'},{id:'p2',name:'电脑',kind:'computer'},{id:'p3',name:'乙',kind:'human'}]});
 game=applyAction(game,{type:'start_game',actorId:'p1'}).state;
 const before={...game,currentPlayerIndex:1,phase:'await_end_turn'};
 const after=applyAction(before,{type:'end_turn',actorId:'p2'}).state;
 assert.equal(needsHumanHandoff(before,after),true);
 assert.equal(needsHumanHandoff({...before,players:before.players.map(p=>p.id==='p1'?{...p,kind:'computer'}:p)},after),false);
});
