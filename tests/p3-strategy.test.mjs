import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame,applyAction,DEFAULT_CONFIG,nextDie} from '../.test-dist/core/game.js';
import {serializeGame,deserializeGame,SaveError} from '../.test-dist/core/save.js';
import {runSimulation} from '../.test-dist/core/simulator.js';
const start=(seed=25,more={})=>{
  const s=createGame(seed,{...DEFAULT_CONFIG,strategyEnabled:true,...more});
  return applyAction(s,{type:'start_game',actorId:s.players[0].id}).state;
};
const act=(s,action)=>applyAction(s,{actorId:s.players[s.currentPlayerIndex].id,...action});
const give=(s,hand)=>({...s,players:s.players.map((p,i)=>i===s.currentPlayerIndex?{...p,cards:{...p.cards,...hand}}:p)});
test('遥控骰点可选 1–6，固定种子确定性、一次消耗、不复用；错误输入保持原状态',()=>{
  const source=give(start(),{remote:1});
  for(const dieValue of [0,-1,7,1.1,NaN,undefined]){
    const bad=act(source,{type:'use_card',cardType:'remote',dieValue});
    assert.equal(bad.ok,false);assert.strictEqual(bad.state,source);
  }
  assert.equal(act(source,{type:'use_card',cardType:'remote',dieValue:2,targetId:'p2'}).ok,false);
  const played=act(source,{type:'use_card',cardType:'remote',dieValue:6});
  assert.equal(played.ok,true);assert.equal(played.state.players[0].cards.remote,0);
  assert.equal(act(played.state,{type:'use_card',cardType:'remote',dieValue:3}).ok,false);
  const rolled=act(played.state,{type:'roll'});
  assert.equal(rolled.state.players[0].position,6);
  assert.equal(rolled.events.find(e=>e.type==='die_rolled').details.value,6);
  assert.equal(rolled.state.pendingDie,0);
  assert.deepEqual(act(played.state,{type:'roll'}),rolled);
  assert.deepEqual(deserializeGame(serializeGame(played.state)).game,played.state);
});
test('路障目标验证、只拦对手、触发后清除并结算落点',()=>{
  let s=give(start(18),{roadblock:1,remote:1});
  for(const tileId of [-1,0,24,1.5]){
    const x=act(s,{type:'use_card',cardType:'roadblock',tileId});
    assert.equal(x.ok,false);assert.strictEqual(x.state,s);
  }
  let r=act(s,{type:'use_card',cardType:'roadblock',tileId:3});
  assert.equal(r.ok,true);assert.equal(r.state.roadblocks.length,1);
  assert.equal(act(r.state,{type:'use_card',cardType:'roadblock',tileId:3}).ok,false);
  assert.deepEqual(deserializeGame(serializeGame(r.state)).game,r.state);
  s=act(r.state,{type:'use_card',cardType:'remote',dieValue:6}).state;
  s=act(s,{type:'roll'}).state;
  assert.equal(s.players[0].position,6,'placing owner is not stopped');
  s=act(s,{type:'end_turn'}).state;
  s=give(s,{remote:1});
  s=act(s,{type:'use_card',cardType:'remote',dieValue:6}).state;
  const hit=act(s,{type:'roll'});
  assert.equal(hit.ok,true);assert.equal(hit.state.players[1].position,3);
  assert.ok(hit.events.some(e=>e.type==='roadblock_triggered'));
  assert.equal(hit.state.roadblocks.length,0);
});
test('免租仅保护本次落地，银行、地主租金与多人余额不重复改变',()=>{
  let s=give(start(34,{bankEnabled:true,loanEnabled:true,marketEnabled:true}),{rent_free:1,remote:1});
  const initialCash=s.players[0].cash,landlordCash=s.players[1].cash;
  s={...s,tiles:s.tiles.map(t=>t.id===1?{...t,ownerId:'p2'}:t)};
  const shield=act(s,{type:'use_card',cardType:'rent_free'});
  assert.equal(shield.ok,true);assert.equal(shield.state.players[0].cards.rent_free,0);
  assert.equal(act(shield.state,{type:'use_card',cardType:'rent_free'}).ok,false);
  s=act(shield.state,{type:'use_card',cardType:'remote',dieValue:1}).state;
  const land=act(s,{type:'roll'});
  assert.equal(land.ok,true);
  assert.equal(land.state.players[0].cash,initialCash);
  assert.equal(land.state.players[1].cash,landlordCash);
  assert.ok(land.events.some(e=>e.type==='rent_waived'));
  assert.equal(land.events.find(e=>e.type==='rent_paid').details.amount,0);
  assert.equal(land.state.pendingRentWaiver,false);
  assert.deepEqual(deserializeGame(serializeGame(land.state)).game,land.state);
});
test('旧版 v4 手里只有两张经典卡及未启用策略模式的存档继续可用',()=>{
  let s=applyAction(createGame(21),{type:'start_game',actorId:'p1'}).state;
  const restored=deserializeGame(serializeGame(s)).game;
  assert.deepEqual(restored,s);
  const spoof=give(s,{remote:1});
  assert.equal(act(spoof,{type:'use_card',cardType:'remote',dieValue:6}).ok,false);
  const corrupt={...restored,roadblocks:[{tileId:2,ownerId:'p1',expiresRound:3}]};
  assert.throws(()=>serializeGame(corrupt),e=>e instanceof SaveError&&e.code==='INVALID_STATE');
});
test('100 固定种子完整策略对局、多玩家事件、经济与存档回归',()=>{
  const config={...DEFAULT_CONFIG,strategyEnabled:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,automaticLiquidation:true,
    players:[{id:'p1',name:'甲',kind:'computer'},{id:'p2',name:'乙',kind:'computer'},{id:'p3',name:'丙',kind:'computer'}],
    maxRounds:15};
  let seenNew=false;
  for(let seed=1;seed<=100;seed++){
    const result=runSimulation(seed,{config,maxActions:800});
    assert.equal(result.finalState.status,'finished');
    assert.equal(result.rejections,0);
    assert.ok(result.actions<=800);
    if(result.finalState.events.some(e=>e.type==='card_used'&&['remote','roadblock','rent_free'].includes(e.details?.cardType)))seenNew=true;
    assert.deepEqual(deserializeGame(serializeGame(result.finalState)).game,result.finalState);
  }
  assert.ok(seenNew,'simulations must actually use new strategy cards');
});
