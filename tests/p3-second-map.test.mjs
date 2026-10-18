import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, DEFAULT_CONFIG, HARBOR_CONFIG } from '../.test-dist/core/game.js';
import { HARBOR_MAP, validateMap } from '../.test-dist/core/maps.js';
import { runSimulation } from '../.test-dist/core/simulator.js';
import { serializeGame, deserializeGame } from '../.test-dist/core/save.js';

const players=n=>Array.from({length:n},(_,i)=>({id:'p'+(i+1),name:'航海者'+(i+1),kind:i%2?'computer':'human'}));

test('P3-05: 原创海港 20 格地图有独立布局、价格、事件和卡片站',()=>{
  assert.equal(HARBOR_MAP.id,'harbor-20');
  assert.equal(HARBOR_MAP.cells.length,20);
  assert.deepEqual([HARBOR_MAP.columns,HARBOR_MAP.rows],[6,6]);
  assert.equal(HARBOR_CONFIG.map.id,'harbor-20');
  assert.equal(HARBOR_CONFIG.tiles.length,20);
  assert.equal(DEFAULT_CONFIG.tiles.length,24);
  assert.ok(HARBOR_CONFIG.tiles.some(t=>t.kind==='property'&&t.price>0&&t.rent>0));
  assert.ok(HARBOR_CONFIG.tiles.some(t=>t.kind==='neutral'&&HARBOR_CONFIG.eventRules.tileIds.includes(t.id)));
  assert.ok(HARBOR_CONFIG.tiles.some(t=>t.kind==='neutral'&&HARBOR_CONFIG.cardRules.tileIds.includes(t.id)));
  assert.doesNotThrow(()=>validateMap(HARBOR_MAP,20));
});
test('P3-05: 两图 2/3/4 人各 100 个种子完整结束、合法产权、价格及步进',()=>{
  for(const base of [DEFAULT_CONFIG,HARBOR_CONFIG])for(const count of [2,3,4]){
    const config={...base,players:players(count),maxRounds:16};
    for(let seed=0;seed<100;seed++){
      const report=runSimulation(seed,{config,maxActions:3000});
      assert.equal(report.finalState.status,'finished',base.map?.id+' '+count+' '+seed);
      assert.equal(report.rejections,0);
      assert.ok(report.finalState.players.every(p=>p.cash>=0&&p.position<config.tiles.length));
      assert.ok(report.finalState.tiles.every(t=>t.ownerId===null||report.finalState.players.some(p=>p.id===t.ownerId&&!p.bankrupt)));
      assert.equal(report.finalState.map.id,base.map?.id??'classic-24');
    }
  }
});
test('P3-05: 海港地图存档恢复保留原地图及随机进度，篡改地图拒绝',()=>{
  let state=createGame(17,{...HARBOR_CONFIG,players:players(3),maxRounds:12});
  state=applyAction(state,{type:'start_game',actorId:'p1'}).state;
  state=applyAction(state,{type:'roll',actorId:'p1'}).state;
  const restored=deserializeGame(serializeGame(state)).game;
  assert.deepEqual(restored,state);
  assert.equal(restored.randomState,state.randomState);
  assert.equal(restored.map.id,'harbor-20');
  assert.throws(()=>createGame(1,{...HARBOR_CONFIG,map:{...HARBOR_MAP,id:'tampered'}}),/地图/);
  assert.throws(()=>createGame(1,{...HARBOR_CONFIG,map:{...HARBOR_MAP,route:[...HARBOR_MAP.route].reverse()}}),/地图/);
  const copy=JSON.parse(JSON.stringify(restored));
  copy.map.id='forged-20';
  assert.throws(()=>deserializeGame(serializeGame(copy)),/地图/);
});
