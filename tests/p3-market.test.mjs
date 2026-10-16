import test from 'node:test';
import assert from 'node:assert/strict';
import { STOCKS, createMarket, advanceMarket, quoteMarket, validateMarket } from '../dist/core/market.js';

test('P3-09: 5 invented stocks, finite quotes and independent PRNG',()=>{
  assert.equal(STOCKS.length,5);
  assert.equal(new Set(STOCKS.map(s=>s.id)).size,5);
  const initial=createMarket(42);
  assert.equal(initial.round,1);
  assert.deepEqual(Object.keys(initial.prices),STOCKS.map(s=>s.id));
  assert.ok(STOCKS.every(s=>quoteMarket(initial,s.id)>0));
  assert.doesNotThrow(()=>validateMarket(initial));
  assert.throws(()=>quoteMarket(initial,'REAL'),/股票/);
});
test('P3-09: equal seed and round trajectories reproduce, versioned JSON save retains future quotes',()=>{
  for(let seed=0;seed<100;seed++){
    let left=createMarket(seed),right=createMarket(seed);
    for(let round=2;round<=60;round++){
      left=advanceMarket(left,round);
      if(round===30)right=JSON.parse(JSON.stringify(right));
      right=advanceMarket(right,round);
      assert.deepEqual(left,right,'seed '+seed+' round '+round);
      assert.doesNotThrow(()=>validateMarket(right));
    }
  }
});
test('P3-09: market rejects repeated round settlement, skip, negatives, corruption',()=>{
  const s=createMarket(5);
  const next=advanceMarket(s,2);
  assert.notEqual(next,s);
  assert.equal(s.round,1);
  for(const round of [2,1,0,-1,4,2.5,NaN])assert.throws(()=>advanceMarket(next,round),/轮次/);
  for(const invalid of [
    {...s,version:2},{...s,round:0},{...s,rngState:-1},
    {...s,prices:{...s.prices,[STOCKS[0].id]:0}},
    {...s,prices:{...s.prices,[STOCKS[0].id]:Infinity}},
    {...s,prices:{...s.prices,UNKNOWN:12}}
  ])assert.throws(()=>validateMarket(invalid),/行情/);
});
test('P3-09: 500 seeds × 200 complete rounds prices bounded and never overflow',()=>{
  for(let seed=0;seed<500;seed++){
    let state=createMarket(seed);
    for(let round=2;round<=200;round++){
      state=advanceMarket(state,round);
      assert.ok(STOCKS.every(x=>Number.isSafeInteger(quoteMarket(state,x.id))&&quoteMarket(state,x.id)>=1&&quoteMarket(state,x.id)<=100000));
    }
  }
});
