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
  s=doIt(s,'borrow_loan',{amount:25});
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
  assert.equal(s.players[0].loanBalance,25);
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

test('P3-08: 100 deterministic seeded secured accounts across three local players',()=>{
  for(let seed=0;seed<100;seed++){
    let a=makeOwned(seed),b=makeOwned(seed);
    for(const type of ['mortgage_property','borrow_loan']){
      const extra=type==='mortgage_property'?{tileId:1}:{amount:20};
      a=doIt(a,type,extra);b=doIt(b,type,extra);
    }
    a=doIt(a,'end_turn');b=doIt(b,'end_turn');
    for(let i=1;i<3;i++){
      a=doIt({...a,phase:'await_end_turn'},'end_turn');
      b=doIt({...b,phase:'await_end_turn'},'end_turn');
    }
    assert.deepEqual(a,b);
    assert.equal(a.loan.lastInterestRound,2);
    assert.equal(a.players[0].loanBalance,20);
    assert.equal(a.events.filter(e=>e.type==='loan_interest').length,1);
    assert.deepEqual(deserializeGame(serializeGame(a,{now})).game,a);
  }
});
test('P3-08: pledged land yields zero rent to the lender without losing ownership',async()=>{
  const {nextDie}=await import('../dist/core/random.js');
  const {advancePosition}=await import('../dist/core/maps.js');
  let s=doIt(createGame(72,config),'start_game');
  const target=advancePosition(s.map,0,nextDie(s.randomState).value);
  s={...s,currentPlayerIndex:1,tiles:s.tiles.map(t=>t.id===target?
    {...t,kind:'property',ownerId:'p1',price:200,rent:80,level:0,upgradeCosts:[100,160],
      levelRents:[80,160,320],mortgaged:true}:t)};
  const money=s.players.map(p=>p.cash);
  const result=applyAction(s,{type:'roll',actorId:'p2'});
  assert.equal(result.ok,true);
  assert.deepEqual(result.state.players.map(p=>p.cash),money);
  assert.equal(result.state.tiles[target].ownerId,'p1');
  assert.ok(result.events.some(e=>e.type==='rent_paid'&&e.details.amount===0));
});
