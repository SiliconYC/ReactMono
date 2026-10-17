import {test} from 'node:test';import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {GUIDE_STEPS,contextHint} from '../dist/ui/guide.js';
import {createGame,applyAction} from '../dist/core/game.js';
test('#69 guide is short, accessible Chinese, read-only',()=>{
 assert.equal(GUIDE_STEPS.length,3);
 for(const step of GUIDE_STEPS){assert.ok(step.title&&step.body.length>10&&step.body.length<80);}
 const state=createGame(17),before=JSON.stringify(state);assert.match(contextHint(state),/地图/);
 assert.equal(JSON.stringify(state),before);
 const started=applyAction(state,{type:'start_game',actorId:'p1'});assert.ok(started.ok);
 assert.match(contextHint(started.state),/骰/);
});
test('#69 offline static tutorial matches same-origin React bundle',async()=>{
 const [html,css,sw,js]=await Promise.all(['dist/index.html','dist/guide.css','dist/sw.js','dist/ui/app.js'].map(x=>readFile(x,'utf8')));
 assert.match(html,/guide.css/);assert.match(sw,/\.\/guide.css/);
 assert.match(css,/guide-inline/);assert.match(css,/min-height:44px/);
 assert.match(js,/guideStep/);assert.match(js,/contextHint/);
 assert.doesNotMatch(css,/https?:\/\//);
});
