import {test} from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
import {createGame,applyAction} from '../dist/core/game.js';
import {walkPath,eventCue} from '../dist/ui/feedback.js';
test('#67 pure visuals never mutate engine dice or finances',()=>{
 const a=createGame(17);const started=applyAction(a,{type:'start_game',actorId:'p1'});assert.ok(started.ok);
 const roll=applyAction(started.state,{type:'roll',actorId:'p1'});assert.ok(roll.ok);
 const before=JSON.stringify(roll.state);const cue=eventCue(started.state,roll.state,roll.events);
 assert.equal(JSON.stringify(roll.state),before);assert.ok(cue);assert.equal(cue.revision,roll.state.revision);
 assert.deepEqual(cue.path,walkPath(started.state,roll.state,'p1'));
 assert.ok(cue.path.length>=1);assert.equal(cue.path.at(-1),roll.state.players[0].position);
});
test('#67 PWA caches animation CSS',async()=>{
 const [html,css,sw]=await Promise.all(['dist/index.html','dist/motion.css','dist/sw.js'].map(x=>readFile(x,'utf8')));
 assert.match(html,/motion.css/);assert.match(sw,/\.\/motion.css/);assert.match(css,/prefers-reduced-motion:reduce/);
});
