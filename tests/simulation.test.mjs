import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_CONFIG } from '../.test-dist/core/game.js';
import { runSimulation } from '../.test-dist/core/simulator.js';
test('种子0到99的整局均结束，无违规指令、死锁、资金和产权错误',()=>{
  for(let seed=0;seed<100;seed++){
    const r=runSimulation(seed);
    assert.equal(r.finalState.status,'finished','seed='+seed);
    assert.equal(r.finalState.phase,'finished');
    assert.equal(r.finalState.events.at(-1).type,'game_finished');
    assert.ok(r.playerTurns<=120,'seed='+seed);
    assert.ok(r.actions<=360,'seed='+seed);
    assert.equal(r.rejections,0);
    assert.ok(r.finalState.players.every(p=>p.cash>=0));
    assert.ok(r.finalState.tiles.every(t=>!t.ownerId || r.finalState.players.some(p=>p.id===t.ownerId)));
  }
});
test('相同种子和策略生成完全一致的历史与结局',()=>{
  assert.deepEqual(runSimulation(42),runSimulation(42));
  assert.deepEqual(runSimulation(73,{reserveCash:40,humanReserveCash:10}),
    runSimulation(73,{reserveCash:40,humanReserveCash:10}));
});
test('回合上限导致结束，净资产相同正确平局',()=>{
  const config={...DEFAULT_CONFIG,tiles:[{id:0,kind:'start',title:'起点'},{id:1,kind:'neutral',title:'空地'}],maxRounds:3};
  const r=runSimulation(1,{config});
  assert.equal(r.finishReason,'round_limit');assert.equal(r.playerTurns,6);
  assert.equal(r.finalState.winnerId,null);
});
test('高租金两格地图可以通过完整合法行动链触发破产',()=>{
  const config={...DEFAULT_CONFIG,initialCash:50,tiles:[
    {id:0,kind:'start',title:'起点'},
    {id:1,kind:'property',title:'高租金',price:1,rent:100}],maxRounds:60};
  const results=Array.from({length:100},(_,seed)=>runSimulation(seed,{config,humanReserveCash:0,reserveCash:0}));
  const r=results.find(x=>x.finishReason==='bankruptcy');
  assert.ok(r,'应当存在破产对局');assert.ok(r.finalState.players.some(p=>p.bankrupt));
});
test('超限和错误输入不能假装完成对局',()=>{
  assert.throws(()=>runSimulation(1,{maxActions:1}),/seed=1/);
  assert.throws(()=>runSimulation(1,{reserveCash:-1}),/保留资金/);
});
