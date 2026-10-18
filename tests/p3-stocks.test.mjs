import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame,applyAction,DEFAULT_CONFIG,STOCKS,netWorth,stockFee,quoteMarket,advanceMarket} from '../.test-dist/core/game.js';
import {serializeGame,deserializeGame,SaveError} from '../.test-dist/core/save.js';

const now='2026-10-16T00:00:00.000Z';
const players=Array.from({length:4},(_,i)=>({id:'p'+(i+1),name:'玩家'+(i+1),kind:'human'}));
const config={...DEFAULT_CONFIG,players,maxRounds:6,bankEnabled:true,loanEnabled:true,marketEnabled:true,automaticLiquidation:true};
const start=(seed=7)=>{let s=createGame(seed,config);return {...applyAction(s,{type:'start_game',actorId:'p1'}).state,phase:'await_end_turn'}};
function run(s,type,extra={}){
  const result=applyAction(s,{type,actorId:s.players[s.currentPlayerIndex].id,...extra});
  assert.equal(result.ok,true,type+': '+(result.ok?'':result.reason));
  return result.state;
}
test('P3-10: buy/sell cash, fees, fractional cost allocation, stock market value, no free trades',()=>{
  let s=start();
  const before=s.players[0].cash,worth=netWorth(s,'p1');
  const price=quoteMarket(s.market,'FARM'),fee=stockFee(price*3);
  s=run(s,'buy_stock',{stockId:'FARM',quantity:3});
  assert.equal(s.players[0].cash,before-price*3-fee);
  assert.deepEqual(s.players[0].holdings.FARM,{quantity:3,costBasis:price*3+fee});
  assert.equal(netWorth(s,'p1'),worth-fee);
  let cash=s.players[0].cash;
  s=run(s,'sell_stock',{stockId:'FARM',quantity:1});
  assert.equal(s.players[0].cash,cash+price-stockFee(price));
  assert.deepEqual(s.players[0].holdings.FARM,{quantity:2,costBasis:price*3+fee-Math.floor((price*3+fee)/3)});
  s=run(s,'sell_stock',{stockId:'FARM',quantity:2});
  assert.equal(s.players[0].holdings.FARM,undefined);
  assert.equal(s.players[0].cash,before-fee-stockFee(price)-stockFee(price*2));
  assert.equal(applyAction(s,{type:'sell_stock',actorId:'p1',stockId:'FARM',quantity:1}).ok,false);
});
test('P3-10: reject illegal quantities, fake stock codes, other player, no market, insolvency',()=>{
  let s=start();
  for(const quantity of [0,-1,1.1,'2',null,NaN,Infinity,1e12]){
    for(const type of ['buy_stock','sell_stock']){
      const res=applyAction(s,{type,actorId:'p1',stockId:'SEA',quantity});
      assert.equal(res.ok,false,type+' '+quantity);
      assert.equal(res.state,s);
    }
  }
  for(const type of ['buy_stock','sell_stock']){
    assert.equal(applyAction(s,{type,actorId:'p1',stockId:'REAL',quantity:1}).ok,false);
    assert.equal(applyAction(s,{type,actorId:'p2',stockId:'SEA',quantity:1}).ok,false);
  }
  assert.equal(applyAction(s,{type:'buy_stock',actorId:'p1',stockId:'SEA',quantity:1e8}).ok,false);
  const old=createGame(8);
  assert.equal(applyAction({...old,phase:'await_end_turn',status:'playing'},{type:'buy_stock',actorId:'p1',stockId:'SEA',quantity:1}).ok,false);
  s=run(s,'buy_stock',{stockId:'SEA',quantity:2});
  assert.equal(applyAction(s,{type:'sell_stock',actorId:'p1',stockId:'SEA',quantity:3}).ok,false);
});
test('P3-10: multiplayer accounts + deposits + secured loans + saved deterministic quotes',()=>{
  let s=start(44);
  s=run(s,'deposit_bank',{amount:100});
  s=run(s,'buy_stock',{stockId:'SEA',quantity:2});
  s=run(s,'end_turn');
  s={...s,phase:'await_end_turn'};
  s=run(s,'buy_stock',{stockId:'STAR',quantity:1});
  assert.deepEqual(Object.keys(s.players[0].holdings),['SEA']);
  assert.deepEqual(Object.keys(s.players[1].holdings),['STAR']);
  assert.equal(s.players[2].holdings?.STAR,undefined);
  const saved=deserializeGame(serializeGame(s,{now})).game;
  assert.deepEqual(saved,s);
  assert.equal(saved.market.round,1);
  s={...s,market:advanceMarket(s.market,2),round:2};
  const changed=netWorth(s,'p1');
  assert.equal(changed,s.players[0].cash+s.players[0].bankBalance+
    2*quoteMarket(s.market,'SEA'));
});
test('P3-10: tampered positions rejected; old #38 market save remains valid without holdings',()=>{
  const s=start();
  for(const bad of [
    {...s,players:s.players.map((p,i)=>i===0?{...p,holdings:{SEA:{quantity:-1,costBasis:80}}}:p)},
    {...s,players:s.players.map((p,i)=>i===0?{...p,holdings:{SEA:{quantity:2,costBasis:NaN}}}:p)},
    {...s,players:s.players.map((p,i)=>i===0?{...p,holdings:{REAL:{quantity:1,costBasis:3}}}:p)},
    {...s,market:undefined,players:s.players.map((p,i)=>i===0?{...p,holdings:{SEA:{quantity:1,costBasis:81}}}:p)}
  ])assert.throws(()=>serializeGame(bad,{now}),SaveError);
  const legacy=createGame(7,{...DEFAULT_CONFIG,marketEnabled:true});
  assert.ok(legacy.players.every(p=>!Object.hasOwn(p,'holdings')));
  const older={...legacy,players:legacy.players.map(p=>{const v={...p};delete v.holdings;return v;})};
  assert.deepEqual(deserializeGame(serializeGame(older,{now})).game,older);
});
test('P3-10: 100 seed round reproducibility and save resumption with holdings',()=>{
  for(let seed=0;seed<100;seed++){
    let a=start(seed),b=start(seed);
    for(const symbol of STOCKS.map(x=>x.id)){
      a=run(a,'buy_stock',{stockId:symbol,quantity:1});
      b=run(b,'buy_stock',{stockId:symbol,quantity:1});
    }
    for(let seat=0;seat<4;seat++){
      a=run({...a,phase:'await_end_turn'},'end_turn');
      b=run({...b,phase:'await_end_turn'},'end_turn');
    }
    assert.equal(a.round,2);
    assert.deepEqual(a,b);
    assert.deepEqual(deserializeGame(serializeGame(a,{now})).game,a);
    a={...a,phase:'await_end_turn'};
    b={...b,phase:'await_end_turn'};
    for(const symbol of STOCKS.map(x=>x.id)){
      a=run(a,'sell_stock',{stockId:symbol,quantity:1});
      b=run(b,'sell_stock',{stockId:symbol,quantity:1});
    }
    assert.deepEqual(a,b);
    assert.ok(a.players[0].cash>=0);
    assert.ok(Object.keys(a.players[0].holdings).length===0);
  }
});
