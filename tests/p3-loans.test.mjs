import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, applyAction, DEFAULT_CONFIG, netWorth, loanLimit, resaleValue } from '../dist/core/game.js';
import { serializeGame, deserializeGame, SaveError } from '../dist/core/save.js';

const config={...DEFAULT_CONFIG,bankEnabled:true,loanEnabled:true,automaticLiquidation:true,
  players:[{id:'p1',name:'甲',kind:'human'},{id:'p2',name:'乙',kind:'human'},{id:'p3',name:'丙',kind:'human'}]};
const now='2026-10-16T00:00:00.000Z';
function doIt(s,type,extra={}){
  const result=applyAction(s,{type,actorId:s.players[s.currentPlayerIndex].id,...extra});
  assert.equal(result.ok,true,type+': '+(result.ok?'':result.reason));
  return result.state;
}
function makeOwned(seed=7){
  let s=createGame(seed,config);
  s=doIt(s,'start_game');
  s={...s,phase:'await_end_turn',tiles:s.tiles.map(t=>t.id===1?{...t,ownerId:'p1'}:t)};
  return s;
}
test('P3-08: lien is owner-only, unique, credit-capped, debt contributes negative net worth',()=>{
  let s=makeOwned(),previous=netWorth(s,'p1');
  assert.equal(loanLimit(s,'p1'),0);
  for(const [type,extra] of [['mortgage_property',{tileId:2}],['borrow_loan',{amount:1}],['repay_loan',{amount:1}],['release_mortgage',{tileId:1}]]){
    assert.equal(applyAction(s,{type,actorId:'p1',...extra}).ok,false);
  }
  s=doIt(s,'mortgage_property',{tileId:1});
  assert.equal(s.tiles[1].mortgaged,true);
  const cap=loanLimit(s,'p1');
  assert.equal(cap,Math.floor(resaleValue(s.tiles[1],s.resaleRules)/2));
  assert.ok(cap>0);
  assert.equal(applyAction(s,{type:'mortgage_property',actorId:'p1',tileId:1}).ok,false);
  assert.equal(applyAction(s,{type:'borrow_loan',actorId:'p1',amount:cap+1}).ok,false);
  s=doIt(s,'borrow_loan',{amount:cap});
  assert.equal(s.players[0].loanBalance,cap);
  assert.equal(netWorth(s,'p1'),previous);
  assert.equal(applyAction(s,{type:'release_mortgage',actorId:'p1',tileId:1}).ok,false);
  assert.equal(applyAction(s,{type:'sell_property',actorId:'p1',tileId:1}).ok,false);
  assert.equal(applyAction(s,{type:'upgrade_property',actorId:'p1',tileId:1}).ok,false);
  for(const amount of [0,-1,1.2,NaN,Infinity,'1',cap+1])
    assert.equal(applyAction(s,{type:'repay_loan',actorId:'p1',amount}).ok,false);
  s=doIt(s,'repay_loan',{amount:cap});
  s=doIt(s,'release_mortgage',{tileId:1});
  assert.equal(s.players[0].loanBalance,0);
  assert.equal(s.tiles[1].mortgaged,undefined);
  assert.equal(netWorth(s,'p1'),previous);
});
test('P3-08: debtor isolation, one deterministic interest per complete round, save/restore',()=>{
  let s=makeOwned(18);
  s=doIt(s,'mortgage_property',{tileId:1});
  s=doIt(s,'borrow_loan',{amount:50});
  const snap=deserializeGame(serializeGame(s,{now})).game;
  assert.deepEqual(s,snap);
  s=doIt(s,'end_turn');
  for(let n=1;n<3;n++){
    s={...s,phase:'await_end_turn'};
    s=doIt(s,'end_turn');
  }
  assert.equal(s.round,2);
  assert.equal(s.loan.lastInterestRound,2);
  assert.equal(s.events.filter(e=>e.type==='loan_interest').length,1);
  assert.deepEqual(s.players.slice(1).map(p=>p.loanBalance),[0,0]);
  assert.equal(s.players[0].loanBalance,50);
  assert.equal(s.players[0].cash,snap.players[0].cash-1);
  assert.deepEqual(deserializeGame(serializeGame(s,{now})).game,s);
});
test('P3-08: over-limit interest causes seizure; no orphan lien or unpaid debt, legacy unaffected',()=>{
  let s=makeOwned(11);
  s=doIt(s,'mortgage_property',{tileId:1});
  const cap=loanLimit(s,'p1');
  s=doIt(s,'borrow_loan',{amount:cap});
  s={...s,players:s.players.map((p,i)=>i===0?{...p,cash:0,bankBalance:0}:p)};
  s=doIt(s,'end_turn');
  for(let n=1;n<3;n++){s={...s,phase:'await_end_turn'};s=doIt(s,'end_turn');}
  assert.equal(s.players[0].loanBalance,0);
  assert.equal(s.tiles[1].ownerId,null);
  assert.equal(s.tiles[1].mortgaged,undefined);
  assert.ok(s.events.some(e=>e.type==='loan_default'));
  const legacy=createGame(7);
  assert.equal(legacy.loan,undefined);
  assert.ok(legacy.players.every(p=>p.loanBalance===undefined));
  assert.deepEqual(deserializeGame(serializeGame(legacy,{now})).game,legacy);
});
test('P3-08: strict finance save rejects negative debt, lien without loan feature or unowned lien',()=>{
  const s=makeOwned();
  for(const bad of [
    {...s,players:s.players.map((p,i)=>i===0?{...p,loanBalance:-1}:p)},
    {...s,tiles:s.tiles.map(t=>t.id===1?{...t,mortgaged:true,ownerId:null}:t)},
    {...s,loan:{...s.loan,lastInterestRound:55}},
    {...s,loan:undefined,tiles:s.tiles.map(t=>t.id===1?{...t,mortgaged:true}:t)}
  ])assert.throws(()=>serializeGame(bad,{now}),SaveError);
});
