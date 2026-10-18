import test from 'node:test';import assert from 'node:assert/strict';
import {createGame,applyAction,nextDie,DEFAULT_CONFIG} from '../.test-dist/core/game.js';
import {serializeGame,deserializeGame} from '../.test-dist/core/save.js';
import {runSimulation} from '../.test-dist/core/simulator.js';
const act=(s,type)=>applyAction(s,{type,actorId:s.players[s.currentPlayerIndex].id});
function land(seed=17,initialCash=1500) {
 let s=act(createGame(seed,{...DEFAULT_CONFIG,initialCash}),'start_game').state;
 const value=nextDie(s.randomState).value;
 s={...s,players:s.players.map((p,i)=>i===0?{...p,position:(3-value+s.tiles.length)%s.tiles.length}:p)};
 return act(s,'roll');
}
test('机会格恰好触发一次收益或费用，读档和重复运行仍确定',()=>{
 for(let seed=1;seed<=40;seed++){
   const r=land(seed);assert.equal(r.ok,true);
   const ev=r.events.filter(e=>['event_bonus','event_fee'].includes(e.type));
   assert.equal(ev.length,1);assert.equal(ev[0].details.tileId,3);
   assert.equal(r.state.phase,'await_end_turn');
   assert.equal(act(r.state,'roll').ok,false);
   assert.deepEqual(deserializeGame(serializeGame(r.state)).game,r.state);
   assert.deepEqual(land(seed),r);
 }
});
test('系统费用不足采用封顶扣款，不产生负数或伪造破产',()=>{
 const cases=Array.from({length:40},(_,i)=>land(i+1,10));
 const fee=cases.find(r=>r.events.some(e=>e.type==='event_fee'));
 assert.ok(fee);const charge=fee.events.find(e=>e.type==='event_fee');
 assert.equal(charge.details.amount,10);assert.equal(charge.details.due,60);
 assert.equal(fee.state.players[0].cash,0);assert.equal(fee.state.status,'playing');
 assert.ok(fee.state.players.every(p=>p.cash>=0));
});
test('100 固定种子含机会格完整模拟仍确定，事件顺序复现',()=>{
 let seen=0;
 for(let seed=0;seed<100;seed++){
   const a=runSimulation(seed),b=runSimulation(seed);
   assert.deepEqual(a,b);assert.equal(a.finalState.status,'finished');
   seen+=a.finalState.events.filter(e=>e.type==='event_bonus'||e.type==='event_fee').length;
 }
 assert.ok(seen>0);
});
