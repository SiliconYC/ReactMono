import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame,applyAction} from '../.test-dist/core/game.js';
import {levelConfig} from '../.test-dist/core/level-data.js';
import {serializeGame,deserializeGame,validateGameState} from '../.test-dist/core/save.js';
import * as debug from '../.test-dist/core/debug-tools.js';

function started(options={}) {
  const cfg={...levelConfig('lime-garden-30'),initialCash:1_000_000,
    players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'电脑',kind:'computer',computerStyle:'balanced'}],
    automaticLiquidation:true,propertyVisitOnly:true,stockAccount:'bank',
    bankEnabled:true,loanEnabled:true,marketEnabled:true,strategyEnabled:true,specialEnabled:false,...options};
  return applyAction(createGame(20261015,cfg),{type:'start_game',actorId:'p1'}).state;
}

test('破产决胜一百万资金真实推进200轮，不在地图默认36轮截断且完整存档可往返',()=>{
  const initial=started({endCondition:'bankruptcy'});
  const result=debug.simulateDebugRounds(initial,200);
  assert.equal(result.state.round,201);
  assert.equal(result.state.status,'playing');
  assert.equal(result.state.maxRounds,36);
  assert.equal(result.state.endCondition,'bankruptcy');
  assert.equal(result.state.events.some(e=>e.type==='game_finished'),false);
  assert.ok(result.state.tiles.filter(t=>t.ownerId).length>=20);
  assert.ok(result.state.tiles.filter(t=>(t.level??0)>0).length>=18);
  assert.deepEqual(deserializeGame(serializeGame(result.state)).game,result.state);
  assert.equal(initial.round,1);
});

test('旧对局与显式限轮继续在原上限结算，旧存档不自动改为破产决胜',()=>{
  const initial=started();
  const result=debug.simulateDebugRounds(initial,200);
  assert.equal(result.state.status,'finished');
  assert.equal(result.state.round,36);
  assert.equal(result.state.endCondition,undefined);
  assert.equal(result.state.events.at(-1).details.reason,'round_limit');
  assert.deepEqual(deserializeGame(serializeGame(result.state)).game,result.state);
});

test('破产决胜中淘汰末席跨过原轮数上限仍继续，最后仅一人存活才胜出',()=>{
  let state=started({maxRounds:1,endCondition:'bankruptcy',players:[
    {id:'p1',name:'甲',kind:'human'},{id:'p2',name:'乙',kind:'human'},{id:'p3',name:'丙',kind:'human'}]});
  state={...state,currentPlayerIndex:2,pendingDie:1,
    players:state.players.map(p=>p.id==='p3'?{...p,cash:0}:p),
    tiles:state.tiles.map(t=>t.id===1?{...t,ownerId:'p1'}:t)};
  const result=applyAction(state,{type:'roll',actorId:'p3'});
  assert.equal(result.ok,true);
  assert.equal(result.state.players[2].bankrupt,true);
  assert.equal(result.state.status,'playing');
  assert.equal(result.state.round,2);
  assert.equal(result.state.currentPlayerIndex,0);
  assert.equal(result.events.some(e=>e.type==='game_finished'),false);
  validateGameState(result.state);
});

test('结束条件严格校验，旧模式不能借字段非法跨越轮数',()=>{
  assert.throws(()=>started({endCondition:'anything'}));
  assert.throws(()=>validateGameState({...started(),endCondition:false}));
  assert.throws(()=>validateGameState({...started(),round:37}));
});

test('破产决胜超过旧轮数上限后的合法路障仍可保存，期限按当前轮次校验',()=>{
  let state=started({endCondition:'bankruptcy',maxRounds:1,bankEnabled:false,loanEnabled:false,marketEnabled:false,stockAccount:'cash'});
  state={...state,round:2,players:state.players.map((p,i)=>i===0?{...p,cards:{...p.cards,roadblock:1}}:p)};
  validateGameState(state);
  const result=applyAction(state,{type:'use_card',actorId:'p1',cardType:'roadblock',tileId:4});
  assert.equal(result.ok,true);
  assert.equal(result.state.roadblocks[0].expiresRound,4);
  assert.deepEqual(deserializeGame(serializeGame(result.state)).game,result.state);
  assert.throws(()=>validateGameState({...result.state,roadblocks:[{...result.state.roadblocks[0],expiresRound:5}]}));
});

test('调试资金草稿和结束方式在独立快照一次应用，非法第二项不会部分写入原局',()=>{
  assert.equal(typeof debug.prepareDebugSimulation,'function');
  const initial=started({initialCash:2200});
  const before=structuredClone(initial);
  const configured=debug.prepareDebugSimulation(initial,{cashById:{p1:1_000_000,p2:1_000_000},endCondition:'bankruptcy'});
  assert.deepEqual(configured.players.map(p=>p.cash),[1_000_000,1_000_000]);
  assert.equal(configured.endCondition,'bankruptcy');
  assert.deepEqual(configured.events,initial.events);
  assert.equal(configured.randomState,initial.randomState);
  assert.throws(()=>debug.prepareDebugSimulation(initial,{cashById:{p1:1_000_000,p2:-1}}));
  assert.throws(()=>debug.prepareDebugSimulation(initial,{cashById:{missing:50}}));
  assert.deepEqual(initial,before);
  const restored=debug.prepareDebugSimulation(configured,{endCondition:'round_limit'});
  assert.equal(restored.endCondition,undefined);
  assert.deepEqual(deserializeGame(serializeGame(configured)).game,configured);
});
