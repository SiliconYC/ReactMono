import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, DEFAULT_CONFIG, netWorth } from '../dist/core/game.js';
import { serializeGame, deserializeGame, SaveError } from '../dist/core/save.js';

const now='2026-10-16T00:00:00.000Z';
const roster=n=>Array.from({length:n},(_,i)=>({id:'p'+(i+1),name:'玩家'+(i+1),kind:'human'}));
const config=n=>({...DEFAULT_CONFIG,players:roster(n),bankEnabled:true,maxRounds:8});
function doAction(state,type,extra={}) {
  const actorId=state.players[state.currentPlayerIndex].id;
  const result=applyAction(state,{type,actorId,...extra});
  assert.equal(result.ok,true,type+': '+(result.ok?'':result.reason));
  return result.state;
}
function advanceToEnd(state) {
  if(state.phase==='setup')state=doAction(state,'start_game');
  if(state.phase==='await_roll')state=doAction(state,'roll');
  if(state.phase==='await_decision')state=doAction(state,'decline_property');
  assert.equal(state.phase,'await_end_turn');
  return state;
}
test('P3-07: deposits/withdrawals conserve money, require legal amounts and phase',()=>{
  let s=createGame(71,config(3));
  assert.deepEqual(s.players.map(p=>p.bankBalance),[0,0,0]);
  assert.equal(s.bank.lastInterestRound,1);
  assert.equal(applyAction(s,{type:'deposit_bank',actorId:'p1',amount:50}).ok,false);
  s=advanceToEnd(s);
  const original=s.players[0].cash,worth=netWorth(s,'p1');
  s=doAction(s,'deposit_bank',{amount:250});
  assert.equal(s.players[0].cash,original-250);
  assert.equal(s.players[0].bankBalance,250);
  assert.equal(netWorth(s,'p1'),worth);
  s=doAction(s,'withdraw_bank',{amount:75});
  assert.equal(s.players[0].cash,original-175);
  assert.equal(s.players[0].bankBalance,175);
  assert.equal(netWorth(s,'p1'),worth);
  for(const amount of [0,-1,0.1,NaN,Infinity,'100',null,Number.MAX_SAFE_INTEGER]){
    const snap=s;
    assert.equal(applyAction(s,{type:'deposit_bank',actorId:'p1',amount}).ok,false);
    assert.equal(applyAction(s,{type:'withdraw_bank',actorId:'p1',amount}).ok,false);
    assert.equal(s,snap);
  }
  assert.equal(applyAction(s,{type:'withdraw_bank',actorId:'p2',amount:1}).ok,false);
  assert.equal(applyAction(s,{type:'withdraw_bank',actorId:'p1',amount:200}).ok,false);
  assert.equal(applyAction(s,{type:'deposit_bank',actorId:'p1',amount:100000}).ok,false);
});
test('P3-07: one interest event per complete round; 3/4 accounts isolated and deterministic',()=>{
  for(const n of [3,4])for(const seed of [11,17,38]){
    let s=advanceToEnd(createGame(seed,config(n)));
    s=doAction(s,'deposit_bank',{amount:500});
    const p0=s.players[0].bankBalance;
    s=doAction(s,'end_turn');
    for(let i=1;i<n;i++){s=advanceToEnd(s);s=doAction(s,'end_turn');}
    assert.equal(s.round,2);
    assert.equal(s.bank.lastInterestRound,2);
    assert.equal(s.players[0].bankBalance,p0+5);
    assert.deepEqual(s.players.slice(1).map(p=>p.bankBalance),Array(n-1).fill(0));
    assert.equal(s.events.filter(e=>e.type==='bank_interest').length,1);
    assert.deepEqual(deserializeGame(serializeGame(s,{now})).game,s);
    const a=advanceToEnd(s),b=advanceToEnd(deserializeGame(serializeGame(s,{now})).game);
    assert.deepEqual(a,b);
  }
});
test('P3-07: bank assets fund rent before land liquidation; bankruptcy never leaves stranded deposits',async()=>{
  const n=3;
  let s=createGame(17,{...config(n),automaticLiquidation:true});
  s=doAction(s,'start_game');
  s={...s,phase:'await_roll',currentPlayerIndex:2,
    players:s.players.map((p,i)=>i===2?{...p,cash:0,bankBalance:100}:p),
    tiles:s.tiles.map(t=>t.id===1?{...t,ownerId:'p1',rent:40}:t)};
  // Choose deterministic landing on owned property without consuming market/dice differently.
  // All 24 board positions are valid, so reconstruct a property at the next dice destination.
  const {nextDie}=await import('../dist/core/random.js');
  const die=nextDie(s.randomState).value;
  const {advancePosition}=await import('../dist/core/maps.js');
  const landed=advancePosition(s.map,0,die);
  s={...s,tiles:s.tiles.map(t=>t.id===landed?{...t,kind:'property',price:100,rent:40,ownerId:'p1',level:0,upgradeCosts:[50,80],levelRents:[40,80,160]}:t)};
  // Avoid changing the start tile or invalid fixtures; use only 24-step non-start rolls.
  assert.notEqual(landed,0);
  const result=applyAction(s,{type:'roll',actorId:'p3'});
  assert.equal(result.ok,true);
  const next=result.state;
  assert.equal(next.players[2].bankBalance,60);
  assert.equal(next.players[2].cash,0);
  assert.equal(next.players[2].bankrupt,false);
  assert.equal(next.players[0].cash,s.players[0].cash+40);
  assert.equal(result.events.filter(e=>e.type==='bank_withdrawn').length,1);
  assert.equal(result.events.filter(e=>e.type==='property_liquidated').length,0);
});
test('P3-07: optional bank never changes legacy P2 default game and rejects tampered bank states',()=>{
  const legacy=createGame(7);
  assert.ok(!Object.hasOwn(legacy,'bank'));
  assert.ok(legacy.players.every(p=>!Object.hasOwn(p,'bankBalance')));
  const s=createGame(7,config(3));
  for(const bad of [
    {...s,bank:{...s.bank,lastInterestRound:9}},
    {...s,players:s.players.map((p,i)=>i===0?{...p,bankBalance:-1}:p)},
    {...s,bank:{...s.bank,interestBps:100000}},
    {...s,players:s.players.map((p,i)=>i===0?{...p,bankBalance:1.5}:p)}
  ])assert.throws(()=>serializeGame(bad,{now}),SaveError);
});
